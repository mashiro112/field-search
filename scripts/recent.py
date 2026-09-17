#!/usr/bin/env python3
"""Run the pinned last30days keyless workflow and preserve every source record.

The caller supplies a research plan, then reads originals and synthesizes. This
command is a research engine, not a completed research answer.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SOURCES = {'reddit', 'hackernews', 'github'}


def evidence_index(bundle):
    reports = bundle.get('reports', [])
    result = []
    for entry in reports:
        report = entry['report']
        statuses = report.get('source_status', {})
        degraded = {name: value for name, value in statuses.items()
                    if value.get('state') != 'ok' or value.get('lane_failure_state') or value.get('detail')}
        rows = []
        for source, items in report.get('items_by_source', {}).items():
            for item in items:
                rows.append(dict(source=source, item=item))
        result.append(dict(entity=entry.get('entity'), range_from=report.get('range_from'),
                           range_to=report.get('range_to'), effective_plan=report.get('query_plan'),
                           source_status=statuses, degraded_sources=degraded,
                           errors_by_source=report.get('errors_by_source'),
                           warnings=report.get('warnings'), records=rows,
                           record_count=len(rows), ranked_count=len(report.get('ranked_candidates', []))))
    return dict(schema_version=1, untrusted_source_data=True, reports=result,
                note='Full source records, not only compact top clusters. Publication/update date does not prove event date; inspect nested source status and read decisive originals.')


def validate_plan(plan, sources):
    queries = plan.get('subqueries')
    if not isinstance(queries, list) or not 1 <= len(queries) <= 5:
        raise ValueError('plan requires 1..5 subqueries')
    for q in queries:
        if not isinstance(q.get('search_query'), str) or not q['search_query'].strip():
            raise ValueError('nonempty search_query required')
        lanes = q.get('sources', sources)
        if not isinstance(lanes, list) or not lanes or not set(lanes) <= set(sources):
            raise ValueError('plan sources must stay within selected keyless lanes')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('topic')
    p.add_argument('--plan', required=True, help='Caller-authored JSON query plan; no automatic LLM planner')
    p.add_argument('--out-dir', required=True, help='A new task-local run directory')
    p.add_argument('--as-of', required=True, help='YYYY-MM-DD, explicit date in the caller task timezone')
    p.add_argument('--days', type=int, default=30)
    p.add_argument('--sources', default='reddit,hackernews,github')
    p.add_argument('--subreddits')
    p.add_argument('--timeout', type=int, default=180)
    a = p.parse_args(argv)
    sources = list(dict.fromkeys(a.sources.split(',')))
    try:
        datetime.strptime(a.as_of, '%Y-%m-%d')
        if not sources or not set(sources) <= ALLOWED_SOURCES:
            raise ValueError('only reddit,hackernews,github are enabled')
        if not 1 <= a.days <= 90 or not 10 <= a.timeout <= 300:
            raise ValueError('days 1..90; timeout 10..300')
        plan = json.loads(Path(a.plan).read_text(encoding='utf-8-sig'))
        validate_plan(plan, sources)
    except (ValueError, OSError, TypeError, AttributeError) as e:
        p.error(str(e))
    out = Path(a.out_dir).resolve()
    if out.exists():
        p.error('--out-dir already exists; use a new run directory')
    upstream = ROOT/'integrations/last30days/scripts/last30days.py'
    if not upstream.is_file():
        p.error('pinned last30days integration is missing')
    out.mkdir(parents=True)
    for folder in ('config','home','cache','tmp','output'):
        (out/folder).mkdir()
    plan_file = out/'requested-plan.json'
    plan_file.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    env = {k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT'}}
    # Construct child-only home/config roots. No parent or global variables change.
    env.update(HOME=str(out/'home'), USERPROFILE=str(out/'home'), APPDATA=str(out/'home'),
               LOCALAPPDATA=str(out/'home'), XDG_CONFIG_HOME=str(out/'config'), XDG_CACHE_HOME=str(out/'cache'),
               TEMP=str(out/'tmp'), TMP=str(out/'tmp'), PYTHONIOENCODING='utf-8', PYTHONUTF8='1',
               PATH=os.pathsep.join([str(Path(sys.executable).parent),str(Path(os.environ.get('SYSTEMROOT','C:/Windows'))/'System32')]),
               LAST30DAYS_CONFIG_DIR=str(out/'config'), LAST30DAYS_SKIP_KEYCHAIN='1',
               LAST30DAYS_TRUST_PROJECT_CONFIG='0', LAST30DAYS_NATIVE_SEARCH='1', LAST30DAYS_LIBRARY_CONTEXT='off',
               FROM_BROWSER='off', AGENTCOOKIE='off', GH_CONFIG_DIR=str(out/'config/gh'), PASSWORD_STORE_DIR=str(out/'home/empty-password-store'))
    cmd = [sys.executable, str(upstream), a.topic, '--plan', str(plan_file), '--search', ','.join(sources),
           '--as-of', a.as_of, '--days', str(a.days), '--no-browser-cookies', '--emit', 'compact', '--save-dir', str(out/'output')]
    if a.subreddits:
        cmd += ['--subreddits', a.subreddits]
    meta = dict(command=cmd,started_at=datetime.now(timezone.utc).isoformat(),requested_as_of=a.as_of,
                requested_days=a.days, sources=sources, paid_api_keys_forwarded=False,
                host_synthesis_complete=False, host_cost='not observable')
    start = time.monotonic()
    with (out/'stdout.txt').open('w',encoding='utf-8') as stdout, (out/'stderr.txt').open('w',encoding='utf-8') as stderr:
        try:
            run = subprocess.run(cmd,cwd=out,env=env,stdout=stdout,stderr=stderr,timeout=a.timeout,
                                 creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            meta.update(returncode=run.returncode, timed_out=False)
        except subprocess.TimeoutExpired:
            meta.update(returncode=None,timed_out=True)
        except OSError:
            meta.update(returncode=None,timed_out=False,error='process_start_failed')
    meta['seconds'] = round(time.monotonic()-start,3)
    cached = out/'config/last-report.json'
    if cached.exists():
        try:
            index = evidence_index(json.loads(cached.read_text(encoding='utf-8')))
            (out/'evidence-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
            meta['evidence_index'] = str(out/'evidence-index.json')
            meta['reports'] = [{k:r[k] for k in ('entity','range_from','range_to','degraded_sources','record_count','ranked_count')} for r in index['reports']]
        except (ValueError,KeyError,TypeError,AttributeError):
            meta['error'] = 'upstream_report_schema_changed; raw report retained'
    else:
        meta['error'] = 'no_full_report; inspect stderr'
    complete = meta.get('returncode') == 0 and not meta.get('error')
    meta['degraded_sources'] = {str(i): r['degraded_sources']
                                for i, r in enumerate(meta.get('reports', [])) if r['degraded_sources']}
    meta['status'] = ('partial' if meta['degraded_sources'] else 'ok') if complete else 'incomplete'
    meta['engine_complete'] = complete
    meta['cost'] = {'host_monetary_cost': None, 'upstream_http_requests': None,
                    'note': 'No paid API keys forwarded; engine logs do not expose every HTTP request. Unknown is not zero.'}
    meta['next_action'] = 'Read full evidence-index.json, choose decision-relevant records beyond top clusters, verify originals and dates, then synthesize with native search supplements.'
    (out/'run.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))
    return 0 if complete else 2


if __name__ == '__main__':
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
