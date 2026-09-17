"""Free collectors and reviewed upstream adapters, isolated from account configuration."""
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib import parse, request, error
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('reddit', 'wechat', 'keyless-web', 'findarepo', 'arxiv', 'stackexchange', 'x-public')
READERS = ('reddit-read', 'x-post', 'x-profile', 'jina')


def organic_result(item):
    p = parse.urlsplit(item.get('url', ''))
    return p.scheme in ('http', 'https') and not (
        p.hostname in ('duckduckgo.com', 'www.duckduckgo.com') and
        (p.path.startswith('/y.js') or 'ad_domain=' in p.query or 'ad_provider=' in p.query))


def invoke(source, query, args):
    # A public collector never inherits an API key, cookies, or upstream user config.
    allowed = {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH', 'SSL_CERT_FILE', 'SSL_CERT_DIR',
               'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY'}
    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    env.update(PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1',
               LAST30DAYS_CONFIG_DIR='', LAST30DAYS_SKIP_KEYCHAIN='1')
    payload = dict(source=source, query=query, limit=args.limit, page=args.page,
                   timeout=args.timeout, since=args.since)
    try:
        p = subprocess.run([sys.executable, '-I', '-B', str(Path(__file__).resolve())],
                           input=json.dumps(payload), encoding='utf-8', capture_output=True,
                           timeout=args.timeout + 1, env=env,
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if p.returncode:
            return dict(status='error', records=[], reason='collector_process_failed')
        return json.loads(p.stdout)
    except subprocess.TimeoutExpired:
        return dict(status='unavailable', records=[], reason='collector_deadline',
                    fallback='native web search/read; no paid fallback')
    except (ValueError, OSError):
        return dict(status='error', records=[], reason='collector_invalid_output')


class PublicFetch:
    def __init__(self, timeout):
        self.deadline = time.monotonic() + timeout
    def text(self, url, hosts):
        def validate(target):
            p = parse.urlsplit(target)
            if p.scheme != 'https' or p.hostname not in hosts or p.username or p.password or p.port not in (None, 443):
                raise ValueError('unexpected_endpoint')
        validate(url)
        class Redirect(request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, hdrs, target):
                validate(target)
                return super().redirect_request(req, fp, code, msg, hdrs, target)
        seconds = self.deadline - time.monotonic()
        if seconds <= 0: raise TimeoutError()
        req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0 field-search/2.0',
                                          'Accept': 'application/json,text/html,application/atom+xml,text/plain'})
        with request.build_opener(Redirect()).open(req, timeout=min(seconds, 15)) as response:
            raw = response.read(4 * 1024 * 1024 + 1)
            if len(raw) > 4 * 1024 * 1024: raise ValueError('response_too_large')
            return raw.decode('utf-8', errors='replace')
    def json(self, url, hosts):
        return json.loads(self.text(url, hosts))


def upstream_http(deadline):
    sys.path.insert(0, str(ROOT / 'integrations/last30days/scripts'))
    from lib import http
    original = http.request
    def bounded(*args, **kwargs):
        kwargs.update(deadline_monotonic=deadline, retries=1, max_429_retries=0)
        return original(*args, **kwargs)
    http.request = bounded
    return http


def execute(p):
    source, query, limit = p['source'], p['query'], p['limit']
    fetch = PublicFetch(p['timeout'])
    records, extra = [], {}
    if p['since']:
        extra['date_filter'] = {'requested': p['since'], 'applied': source in ('reddit','arxiv'),
                                'note': 'Unknown dates retained; other routes require caller verification'}
    if p['page'] != 1 and source not in ('arxiv', 'stackexchange', 'findarepo'):
        return dict(status='unavailable', records=[], reason='pagination_not_supported')
    if source in ('reddit', 'reddit-read', 'keyless-web', 'x-public'):
        http = upstream_http(fetch.deadline)
        with http.capture_failures() as failures:
            if source == 'reddit':
                from lib import reddit_rss
                records = reddit_rss.search_rss(query, depth='quick')
                for item in records:
                    item.update(kind='reddit_feed_excerpt', source_read='feed_excerpt',
                                engagement=None, engagement_known=False, score=None, num_comments=None)
                    item['retrieval_relevance'] = item.pop('relevance', None)
                if p['since']:
                    records = [r for r in records if not r.get('date') or r['date'] >= p['since']]
                extra.update(date_scope='Reddit feed sample; not all-time/archive search',
                             next_action='Read promising original threads with read URL --reader reddit-read')
            elif source == 'reddit-read':
                if not re.fullmatch(r'https://(?:www\.)?reddit\.com/r/[A-Za-z0-9_]+/comments/[a-z0-9]+(?:/[^?#]*)?', query):
                    raise ValueError('expected_reddit_thread_url')
                from lib import reddit_shreddit
                data = reddit_shreddit.fetch_comments(query, timeout=min(15, p['timeout']))
                records = data['top_comments']
                for item in records: item.update(kind='reddit_comment_excerpt', source_read='comment_excerpt')
                extra.update(thread_url=query,
                             comment_insights=data.get('comment_insights'),
                             num_comments=data.get('num_comments'))
            else:
                from lib import web_search_keyless
                q = '(site:x.com OR site:twitter.com) ' + query if source == 'x-public' else query
                records, artifact = web_search_keyless.keyless_search(q, ('', ''), {}, count=limit)
                artifact['raw_result_count'] = artifact.pop('resultCount', len(records))
                records = [r for r in records if organic_result(r)]
                if source == 'x-public':
                    records = [r for r in records if parse.urlsplit(r['url']).hostname in ('x.com','www.x.com','twitter.com','www.twitter.com')]
                for item in records:
                    item.update(kind='search_index_snippet', source_read=False)
                    item['retrieval_relevance'] = item.pop('relevance', None)
                artifact['returned_result_count'] = len(records)
                extra.update(artifact=artifact, scope='Public web index; not direct platform search or complete coverage')
            extra['transport_failures'] = [dict(status_code=getattr(f, 'status_code', None),
                                                kind=type(f).__name__) for f in failures]
        extra['upstream'] = 'mvanhorn/last30days-skill@56ba5ace27e4697aedc60aa0b1e1bfdcd592ff20'
        if source == 'reddit-read':
            if records and extra['transport_failures']:
                comment_fetch_status = 'partial'
            elif extra['transport_failures']:
                comment_fetch_status = 'failed'
            elif records:
                comment_fetch_status = 'ok'
            else:
                comment_fetch_status = 'unknown'
            selection_limit = getattr(reddit_shreddit, 'MAX_COMMENTS', None)
            extra['comment_fetch_status'] = comment_fetch_status
            if not records:
                extra['comment_insights'] = None
            extra['comment_coverage'] = {
                'mode': 'selected_top_comments' if records else 'unknown',
                'selected_count': len(records),
                'returned_count': min(len(records), limit),
                'selection_limit': selection_limit,
                'reported_total_comments': extra.get('num_comments'),
                'complete': False if records else None,
                'partial': comment_fetch_status == 'partial',
            }
        if not records:
            return dict(status='unavailable', records=[], reason='no_verified_records_from_public_route', **extra)
    elif source == 'wechat':
        path = ROOT / 'integrations/supersearch-wechat/scripts/search.py'
        spec = importlib.util.spec_from_file_location('upstream_wechat', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        page = fetch.text(module.SEARCH_URL + parse.quote(query), {'weixin.sogou.com'})
        records = module.parse_search_results(page, limit)
        # Keep discovered leads when one opaque Sogou redirect cannot be resolved.
        for item in records:
            item['url'] = item['sogou_url']
            try:
                redirect = fetch.text(item['sogou_url'], {'weixin.sogou.com', 'mp.weixin.qq.com'})
                item['url'] = module.parse_redirect_url(redirect)
                item['original_url_resolved'] = True
            except (ValueError, OSError):
                item['original_url_resolved'] = False
        for item in records: item.update(kind='wechat_search_snippet', source_read=False)
        extra['upstream'] = 'glidea/supersearch-skills@a3d3829a64d68ad199089f8afc541f3ff6e5ae02'
        if not records:
            return dict(status='unavailable', records=[], reason='blocked_or_unrecognized_search_page', **extra)
    elif source == 'findarepo':
        # Bounded catalogs supplement GitHub search; never label this a full index.
        terms = query.casefold().split()
        all_items, catalogs = {}, []
        for name in ('skills', 'trending'):
            data = fetch.json(f'https://findarepo.com/data/{name}.json', {'findarepo.com'})
            catalogs.append({k: data.get(k) for k in ('source','dataDate','generated','count','attribution','methodology')})
            for item in data['items']:
                haystack = ((item.get('repo') or '') + ' ' + (item.get('summary') or '')).casefold()
                matches = sum(term in haystack for term in terms)
                if matches:
                    all_items[item['github']] = dict(item, url=item['github'], title=item['repo'],
                                                    kind='catalog_lead', source_read=False, keyword_matches=matches)
        records = sorted(all_items.values(), key=lambda r: -r['keyword_matches'])
        start = (p['page']-1)*limit
        extra.update(catalogs=catalogs, matches=len(records), scope='Two limited daily catalogs; not GitHub-wide search',
                     attribution='findarepo (findarepo.com); star-velocity measurements CC BY 4.0')
        records = records[start:start+limit]
    elif source == 'arxiv':
        q = query if re.search(r'\b(?:all|ti|au|cat|abs):',query) else ' AND '.join('all:"'+s.replace('"','')+'"' for s in query.split())
        if p['since']: q += ' AND submittedDate:['+p['since'].replace('-','')+'0000 TO 299912312359]'
        url = 'https://export.arxiv.org/api/query?' + parse.urlencode(dict(search_query=q,start=(p['page']-1)*limit,max_results=limit,sortBy='relevance'))
        doc = ET.fromstring(fetch.text(url, {'export.arxiv.org'}))
        ns = {'a':'http://www.w3.org/2005/Atom'}
        for e in doc.findall('a:entry',ns):
            records.append(dict(url=e.findtext('a:id','',ns), title=e.findtext('a:title','',ns),
                                text=e.findtext('a:summary','',ns), published_at=e.findtext('a:published','',ns),
                                authors=[a.text for a in e.findall('a:author/a:name',ns)],
                                kind='paper_abstract',source_read='abstract'))
    elif source == 'stackexchange':
        params = dict(site='stackoverflow',q=query,pagesize=limit,page=p['page'],order='desc',sort='relevance',filter='withbody')
        url='https://api.stackexchange.com/2.3/search/advanced?'+parse.urlencode(params)
        data=fetch.json(url, {'api.stackexchange.com'})
        for r in data.get('items',[]):
            records.append(dict(url=r['link'],title=r['title'],text=r.get('body',''),kind='question_body',
                                source_read='question_body',score=r.get('score'),accepted_answer_id=r.get('accepted_answer_id')))
        extra.update(backoff_seconds=data.get('backoff'),has_more=data.get('has_more'),quota_remaining=data.get('quota_remaining'))
        if data.get('error_id'): return dict(status='error',records=[],reason='stackexchange_api_error',**extra)
    elif source == 'x-post':
        if not re.fullmatch(r'https://(?:www\.)?(?:x|twitter)\.com/[A-Za-z0-9_]+/status/[0-9]+(?:\?[^#]*)?',query):
            raise ValueError('expected_public_x_post_url')
        data=fetch.json('https://publish.x.com/oembed?'+parse.urlencode(dict(url=query,omit_script='true',dnt='true')),{'publish.twitter.com','publish.x.com'})
        records=[dict(url=query,title=data.get('author_name','X post'),author=data.get('author_name'),
                      text=data.get('html',''),kind='public_post_embed',source_read='embed')]
        extra['scope']='Known public post only; embed may omit media, thread and context'
    elif source == 'x-profile':
        handle=query.removeprefix('@')
        if not re.fullmatch('[A-Za-z0-9_]{1,15}',handle): raise ValueError('expected_x_handle')
        page=fetch.text('https://syndication.twitter.com/srv/timeline-profile/screen-name/'+handle,{'syndication.twitter.com'})
        match=re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',page,re.S)
        if not match: return dict(status='unavailable',records=[],reason='no_public_timeline_data')
        data=json.loads(match[1])
        for e in data.get('props',{}).get('pageProps',{}).get('timeline',{}).get('entries',[]):
            tweet=e.get('content',{}).get('tweet',{})
            if tweet.get('id_str'):
                records.append(dict(url=f'https://x.com/{handle}/status/'+tweet['id_str'],
                                    title=handle,text=tweet.get('full_text',tweet.get('text','')),kind='public_timeline_post',source_read='timeline'))
        extra['scope']='Unofficial public timeline sample; not X search or guaranteed chronological completeness'
    elif source == 'jina':
        target=parse.urlsplit(query)
        if target.scheme not in ('https','http') or not target.hostname or target.username or target.password or target.port not in (None,80,443):
            raise ValueError('expected_public_web_url')
        # The remote reader resolves the public hostname. Local proxy fake-IP DNS
        # is not evidence of the target server's address. Block local names/literals.
        host=target.hostname.lower().rstrip('.')
        if '.' not in host or host.endswith(('.localhost','.local','.internal','.lan','.home','.test','.invalid')):
            raise ValueError('nonpublic_url')
        try:
            address=ipaddress.ip_address(host)
        except ValueError:
            address=None
        if address is not None and not address.is_global: raise ValueError('nonpublic_url')
        body=fetch.text('https://r.jina.ai/'+query,{'r.jina.ai'})
        if any(marker in body.casefold() for marker in ('captcha','access denied','sign in to continue',
                                                       'verifycode','此验证码用于','需要您协助验证','请输入验证码',
                                                       '访问过于频繁','请完成验证','安全验证')):
            return dict(status='unavailable',records=[],reason='access_gate_in_reader_response')
        records=[dict(url=query,title=query,text=body,kind='reader_extraction',source_read='third_party_extraction')]
        extra['scope']='Public URL sent to Jina Reader, no account/key; verify extraction and timestamps'
    else:
        raise ValueError('unknown_collector')
    # Keep provenance, but bound source text before handing it to the reasoning model.
    for r in records:
        for k in ('text','snippet','excerpt','summary','selftext'):
            if isinstance(r.get(k),str) and len(r[k])>6000:
                r[k+'_full']=r[k]
                r[k]=r[k][:6000]; r[k+'_truncated']=True
    return dict(status='ok' if records else 'no_results', records=records[:limit], **extra)


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')
    try:
        result=execute(json.loads(sys.stdin.read()))
    except error.HTTPError as e:
        result=dict(status='unavailable',records=[],reason='http_'+str(e.code))
    except (TimeoutError,error.URLError,OSError):
        result=dict(status='unavailable',records=[],reason='network_or_deadline')
    except Exception as e:
        result=dict(status='error',records=[],reason=type(e).__name__)
    print(json.dumps(result,ensure_ascii=False))
