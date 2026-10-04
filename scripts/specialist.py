"""Bounded US Federal Register discovery and original-text handoff; no API key."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import tempfile
from urllib import error, parse, request
import report

BASE = 'https://www.federalregister.gov/'
MAX_BYTES = 4 * 1024 * 1024
DOCS = BASE + 'developers/documentation/api/v1'


def get(url, timeout, calls):
    parsed = parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname != 'www.federalregister.gov' or parsed.username or parsed.password:
        raise ValueError('source_url_not_allowed')
    req = request.Request(url, headers={'User-Agent': 'field-search/1.0 read-only', 'Accept': 'application/json, text/plain'})
    record = {'url': url}
    calls.append(record)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            if parse.urlsplit(response.geturl()).hostname != parsed.hostname:
                raise ValueError('source_redirect_not_allowed')
            raw = response.read(MAX_BYTES + 1)
            record.update(status='ok', http_status=response.status, bytes=len(raw))
        if len(raw) > MAX_BYTES:
            raise ValueError('response_limit')
        return raw.decode('utf-8')
    except error.HTTPError as exc:
        record.update(status='error', http_status=exc.code)
        raise ValueError('source_http_' + str(exc.code)) from None
    except (error.URLError, TimeoutError):
        record['status'] = 'error'
        raise ValueError('source_unavailable_or_timeout') from None


def brief(doc):
    keys = ['document_number', 'title', 'abstract', 'type', 'subtype', 'publication_date', 'effective_on',
            'dates', 'html_url', 'pdf_url', 'json_url', 'agencies', 'cfr_references', 'correction_of', 'corrections']
    return {k: doc.get(k) for k in keys}


def execute(args):
    calls = []
    result = {'schema_version': 1, 'status': 'ok', 'source': 'US Federal Register', 'jurisdiction': 'US federal',
              'retrieved_at': datetime.now(timezone.utc).isoformat(), 'api_docs': DOCS, 'requests': calls,
              'boundary': 'FederalRegister.gov is an informational XML/text rendition. Verify against linked govinfo official PDF for legal use. Publication date is not effective date; Notice, Proposed Rule and Rule are distinct.',
              'legal_status_checked': False}
    if args.command == 'search':
        query = {'conditions[term]': args.query, 'per_page': args.limit, 'order': 'relevance'}
        if args.type:
            query['conditions[type][]'] = args.type
        data = json.loads(get(BASE + 'api/v1/documents.json?' + parse.urlencode(query), args.timeout, calls))
        result.update(query=args.query, reported_total=data.get('count'),
                      results=[brief(x) for x in data.get('results', [])], next_page_url=data.get('next_page_url'),
                      truncated=bool(data.get('next_page_url')), upstream=data)
    else:
        if not re.fullmatch(r'\d{4}-\d{4,6}', args.number):
            raise ValueError('invalid_document_number')
        data = json.loads(get(BASE + 'api/v1/documents/' + args.number + '.json', args.timeout, calls))
        if data.get('document_number') != args.number:
            raise ValueError('document_identity_mismatch')
        result.update(document=brief(data), upstream=data, body_status='not_requested')
        if args.report_out:
            target = Path(args.report_out).expanduser().resolve()
            if target.exists():
                raise ValueError('report_destination_exists_choose_new_path')
            text_url = data.get('raw_text_url')
            if not text_url:
                result.update(status='partial', body_status='source_has_no_text_url')
            else:
                try:
                    text = get(text_url, args.timeout, calls)
                    if not text.strip():
                        raise ValueError('empty_document_text')
                    body = '# ' + str(data.get('title') or args.number) + '\n\n' + text
                    with tempfile.TemporaryDirectory(prefix='fs-regulation-') as temp:
                        md = Path(temp) / 'document.md'
                        md.write_text(body, encoding='utf-8')
                        saved = report.import_report(str(md), str(target), data['html_url'], 'federal_register_raw_text', 0)
                    metadata_path = target / 'metadata.json'
                    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
                    metadata['specialist'] = {'document_number': args.number, 'jurisdiction': result['jurisdiction'],
                                              'publication_date': data.get('publication_date'), 'effective_on': data.get('effective_on'),
                                              'document_type': data.get('type'), 'official_pdf_url': data.get('pdf_url'),
                                              'raw_text_url': text_url, 'legal_status_checked': False}
                    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
                    result.update(body_status='saved', report_dir=saved['report_dir'])
                except (ValueError, OSError) as exc:
                    result.update(status='partial', body_status='failed', body_error=str(exc))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    search = sub.add_parser('search'); search.add_argument('query'); search.add_argument('--limit', type=int, default=3)
    search.add_argument('--type', choices=['RULE', 'PRORULE', 'NOTICE', 'PRESDOCU'])
    read = sub.add_parser('read'); read.add_argument('number'); read.add_argument('--report-out')
    for p in [search, read]:
        p.add_argument('--timeout', type=float, default=12); p.add_argument('--out')
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 30 or not 1 <= getattr(args, 'limit', 1) <= 10:
        parser.error('budget_out_of_range')
    if args.out and Path(args.out).exists():
        parser.error('output_exists_choose_new_path')
    try:
        value = execute(args)
        if args.out:
            target = Path(args.out); target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('x', encoding='utf-8') as handle:
                json.dump(value, handle, ensure_ascii=False, indent=2)
            displayed = {k: value[k] for k in ['status', 'source', 'jurisdiction', 'reported_total', 'truncated',
                         'body_status', 'body_error', 'report_dir'] if k in value}
            displayed['saved_result'] = str(target.resolve())
            displayed['requests'] = value.get('requests', [])
            keys = ['document_number', 'title', 'type', 'publication_date', 'effective_on', 'html_url', 'pdf_url']
            for key in ['results', 'document']:
                if key in value:
                    rows = value[key] if isinstance(value[key], list) else [value[key]]
                    displayed[key] = [{k: row.get(k) for k in keys} for row in rows]
            value = displayed
    except (ValueError, OSError, TypeError, KeyError) as exc:
        value = {'status': 'error', 'reason': str(exc)}
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 1 if value['status'] == 'error' else 0


if __name__ == '__main__':
    raise SystemExit(main())
