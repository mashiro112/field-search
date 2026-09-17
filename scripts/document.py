#!/usr/bin/env python3
"""Read long public documents through Jina; reuse websearch extraction and pagination.

No direct-host override, paid API, account files or global cache. Snapshots require
an explicit new path. Local open/find never make a network request.
"""
import argparse
from bisect import bisect_right
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit

MAX_BYTES = 16 * 1024 * 1024
MAX_WAIT_CSS_CHARS = 512
MAX_WAIT_TIMEOUT_SECONDS = 30.0


def validate_wait_css(selector):
    """Accept a bounded CSS selector; caller text is never treated as JavaScript."""
    if not isinstance(selector, str):
        raise ValueError('invalid_wait_css')
    value = selector.strip()
    if not value or len(value) > MAX_WAIT_CSS_CHARS or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ValueError('invalid_wait_css')
    if value.casefold().startswith(('js:', 'javascript:')):
        raise ValueError('wait_css_must_be_css')
    return value


def validate_url(url):
    p = urlsplit(url)
    if p.scheme not in ('https', 'http') or not p.hostname or p.username or p.password or p.port not in (None, 80, 443):
        raise ValueError('expected_public_web_url')
    host = p.hostname.lower().rstrip('.')
    if '.' not in host or host.endswith(('.localhost', '.local', '.internal', '.lan', '.home', '.test', '.invalid', '.onion')):
        raise ValueError('nonpublic_url')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError('nonpublic_url')


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def fetch_document(url, timeout, capture=None, reader='jina', wait_css=None,
                   wait_timeout=None, include_links=False):
    validate_url(url)
    if reader == 'crawl4ai':
        from crawl4ai_reader import fetch_document as fetch_crawl4ai
        return fetch_crawl4ai(url, timeout, capture, wait_css, wait_timeout, include_links)
    # This module uses only the fixed, allowlisted public Reader endpoint. It never
    # weakens websearch's DNS/SSRF guard or downloads from the target directly.
    from integrated import PublicFetch
    if capture is None:
        capture = {}
    capture.update(schema_version=1, url=url, fetched_at=datetime.now(timezone.utc).isoformat(),
                   network_used=True, untrusted_source_data=True)
    try:
        raw = PublicFetch(timeout).text('https://r.jina.ai/' + url, {'r.jina.ai'})
    except HTTPError as exc:
        raw_bytes = exc.read(4 * 1024 * 1024 + 1)
        raw = raw_bytes[:4 * 1024 * 1024].decode('utf-8', errors='replace')
        capture.update(raw=raw, raw_sha256=digest(raw), http_status=exc.code,
                       raw_truncated=len(raw_bytes)>4 * 1024 * 1024)
        raise
    capture.update(raw=raw, raw_sha256=digest(raw), raw_truncated=False)
    body = raw.split('Markdown Content:', 1)[-1].strip()
    # Guard actual access interstitials; ordinary articles discussing CAPTCHA are
    # not themselves a gate. Keep this conservative and surface uncertain content.
    gate = re.search(r'(?im)^(?:title:\s*)?(?:access denied|just a moment|sign in to continue|verify you are human|captcha required|请输入验证码|安全验证)\s*[.!…]*$', body[:2000] + '\n' + raw[:300])
    if gate or any(x in body for x in ('此验证码用于', '需要您协助验证', '请完成验证')):
        raise ValueError('access_gate_in_reader_response')
    warnings = ['Third-party public extraction; not independent corroboration or proof of completeness.']
    extraction = 'jina_markdown'
    if re.search(r'(?i)<!doctype\s+html|<html[\s>]', body[:2000]):
        from websearch.layer2_extract.extractors.trafilatura_extractor import TrafilaturaExtractor
        from websearch.layer2_extract.models import ExtractRequest
        result = TrafilaturaExtractor().extract(ExtractRequest(html=body, base_url=url, favor='recall'))
        body = result.content_markdown
        warnings.extend(result.warnings)
        extraction = 'jina_html_then_websearch_trafilatura'
    if not body.strip():
        raise ValueError('empty_extraction')
    return dict(schema_version=1, url=url, fetched_at=datetime.now(timezone.utc).isoformat(),
                extraction=extraction, content=body, content_sha256=digest(body), raw=raw,
                raw_sha256=digest(raw), warnings=warnings, untrusted_source_data=True)


def load_document(path):
    with Path(path).open('rb') as f:
        raw = f.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('snapshot_too_large')
    doc = json.loads(raw)
    if doc.get('schema_version') != 1 or doc.get('status', 'ok') != 'ok' or not isinstance(doc.get('content'), str):
        raise ValueError('invalid_document_schema')
    validate_url(doc['url'])
    if digest(doc['content']) != doc.get('content_sha256'):
        raise ValueError('snapshot_content_hash_mismatch')
    return doc


def page_result(doc, page, page_chars):
    from websearch.layer3_agentio.pagination import paginate
    pages = paginate(doc['content'], page_size_tokens=page_chars, chars_per_token=1.0)
    if not 1 <= page <= len(pages):
        raise ValueError('page_out_of_range')
    result = dict(status='ok', url=doc['url'], fetched_at=doc['fetched_at'],
                  content_sha256=doc['content_sha256'], extraction=doc['extraction'],
                  page=page, total_pages=len(pages), has_more=page < len(pages),
                  text=pages[page-1], page_chars=page_chars, text_truncated=False,
                  source_read=doc.get('source_read', 'third_party_extraction_page'), untrusted_source_data=True,
                  warnings=doc['warnings'])
    for key in ('links', 'possible_attachments', 'links_status', 'links_truncated',
                'invalid_link_count', 'links_source', 'links_base_url', 'links_error'):
        if key in doc:
            result[key] = doc[key]
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('fetch', 'open', 'find'))
    p.add_argument('target', help='Public URL for fetch, explicit snapshot path otherwise')
    p.add_argument('term', nargs='?', help='Literal case-insensitive term for find')
    p.add_argument('--out', help='Save full public response and extraction to a NEW JSON snapshot')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--page-chars', type=int, default=6000)
    p.add_argument('--timeout', type=float, default=25)
    p.add_argument('--reader', choices=('jina', 'crawl4ai'), default='jina')
    p.add_argument('--wait-css', help='Bounded CSS selector to wait for with the explicit Crawl4AI reader')
    p.add_argument('--wait-timeout', type=float, help='Bounded CSS wait timeout in seconds, 0.1..30')
    p.add_argument('--include-links', action='store_true',
                   help='Retain Crawl4AI page links and possible attachment hints without fetching them')
    a = p.parse_args(argv)
    if a.page < 1 or not 1000 <= a.page_chars <= 12000 or not 1 <= a.timeout <= 60:
        p.error('page >=1, page-chars 1000..12000 and timeout 1..60 required')
    if a.command != 'fetch' and a.out:
        p.error('--out is only valid for fetch')
    if a.command == 'find' and not a.term:
        p.error('find requires a literal term')
    if a.command != 'find' and a.term:
        p.error('term is only valid for find')
    if a.command != 'fetch' and a.reader != 'jina':
        p.error('--reader crawl4ai is only valid for fetch')
    if a.command != 'fetch' and (a.wait_css is not None or a.wait_timeout is not None or a.include_links):
        p.error('--wait-css, --wait-timeout and --include-links are only valid for fetch')
    if a.reader != 'crawl4ai' and (a.wait_css is not None or a.wait_timeout is not None or a.include_links):
        p.error('Crawl4AI wait and link options require --reader crawl4ai')
    if a.wait_css is not None:
        try:
            a.wait_css = validate_wait_css(a.wait_css)
        except ValueError as exc:
            p.error(str(exc))
    if a.wait_timeout is not None:
        if not 0.1 <= a.wait_timeout <= MAX_WAIT_TIMEOUT_SECONDS:
            p.error('--wait-timeout must be between 0.1 and 30 seconds')
        if a.wait_css is None:
            p.error('--wait-timeout requires --wait-css')
        if a.wait_timeout > a.timeout:
            p.error('--wait-timeout cannot exceed --timeout')
    if a.out and Path(a.out).exists():
        p.error('--out exists; choose a new snapshot path')
    capture = {}
    started = time.monotonic()
    try:
        doc = (fetch_document(a.target, a.timeout, capture, a.reader, a.wait_css,
                              a.wait_timeout, a.include_links)
               if a.command == 'fetch' else load_document(a.target))
        # Validate page before creating output, so a bad page leaves no claimed artifact.
        result = page_result(doc, a.page, a.page_chars)
        if a.command == 'find':
            from websearch.layer3_agentio.pagination import paginate
            pages = paginate(doc['content'], page_size_tokens=a.page_chars, chars_per_token=1.0)
            ends, end = [], 0
            for text in pages:
                end += len(text)
                ends.append(end)
            hits = []
            count = 0
            # Search the complete snapshot, then map match offsets to pages. A
            # term crossing a page break must not be mistaken for absence.
            for match in re.finditer(re.escape(a.term), doc['content'], flags=re.IGNORECASE):
                count += 1
                if len(hits) < 20:
                    hits.append(dict(page=bisect_right(ends, match.start())+1,
                                     end_page=bisect_right(ends, match.end()-1)+1,
                                     excerpt=doc['content'][max(0,match.start()-100):match.end()+250]))
            result.pop('text')
            result.update(matches=hits, total_matches=count, matches_truncated=count>len(hits),
                          query=a.term, match_scope='literal case-insensitive match over complete extraction; first 20 excerpts')
        if a.out:
            target = Path(a.out)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('x', encoding='utf-8') as f:
                json.dump(doc, f, ensure_ascii=False, indent=2)
            result['snapshot'] = str(target.resolve())
        result['network_used'] = a.command == 'fetch'
        result['elapsed_seconds'] = round(time.monotonic()-started, 3)
        result['route_reason'] = 'public document retained before paginated display' if a.command == 'fetch' else 'offline snapshot reuse'
        if a.command == 'fetch' and not a.out:
            result['warnings'] = result['warnings'] + ['No snapshot saved; use --out for consistent offline pagination.']
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ImportError as exc:
        missing = 'websearch_runtime_missing' if 'websearch' in str(exc).casefold() else (
            'crawl4ai_runtime_missing' if a.reader == 'crawl4ai' else 'websearch_runtime_missing')
        result = dict(status='unavailable', reason=missing,
                      next_action='Use the verified isolated Python runtime documented in references/providers.md.')
    except (ValueError, KeyError, TypeError) as exc:
        known = {'access_gate_in_reader_response','empty_extraction','expected_public_web_url','nonpublic_url',
                 'snapshot_too_large','invalid_document_schema','snapshot_content_hash_mismatch','page_out_of_range',
                 'invalid_wait_css','wait_css_must_be_css','wait_timeout_requires_wait_css',
                 'invalid_wait_timeout','wait_timeout_exceeds_timeout'}
        reason = str(exc) if str(exc) in known else 'invalid_document; check URL, snapshot hash and page'
        result = dict(status='unavailable' if reason in ('access_gate_in_reader_response','empty_extraction') else 'error', reason=reason)
    except OSError:
        result = dict(status='unavailable', reason='network_or_filesystem_error')
    except Exception as exc:
        if exc.__class__.__name__ == 'Crawl4AIReadError':
            result = dict(status='unavailable', reason=getattr(exc, 'reason', 'crawl4ai_failed'),
                          crawl4ai=getattr(exc, 'details', {}),
                          next_action='Inspect retained Crawl4AI failure; native/Jina remains the default route.')
        else:
            result = dict(status='error', reason='crawl4ai_runtime_error' if a.reader == 'crawl4ai' else 'unexpected_document_error')
    result.update(network_used=capture.get('network_used', False), elapsed_seconds=round(time.monotonic()-started, 3))
    if capture.get('http_status'):
        result['reason'] = 'http_' + str(capture['http_status'])
    if a.out and 'raw' in capture and not Path(a.out).exists():
        # Keep failed/gated/unsupported-runtime responses inspectable. These are
        # explicitly failed snapshots and cannot be opened as successful content.
        target = Path(a.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        failed = dict(capture, status=result['status'], reason=result['reason'])
        with target.open('x', encoding='utf-8') as f:
            json.dump(failed, f, ensure_ascii=False, indent=2)
        result['failed_snapshot'] = str(target.resolve())
    result['next_action'] = result.get('next_action', 'Inspect retained failure; continue a relevant accessible native route. Failure is not absence.')
    print(json.dumps(result))
    return 2


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
