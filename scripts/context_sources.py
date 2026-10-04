#!/usr/bin/env python3
"""Bounded GitHub PR context and public community retrieval.

Every successful command preserves decoded upstream payloads in ``upstream`` and
can save the complete result with ``--out``. No write actions or credential
extraction are implemented. GitHub REST uses anonymous public access by default;
community commands can reuse an installed OpenCLI executable.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from urllib import error, parse, request

MAX_BYTES = 4 * 1024 * 1024
UA = "field-search-context/0.1 (read-only public research)"
LEMMY_INSTANCES = ("lemmy.world", "programming.dev")


class SourceError(RuntimeError):
    pass


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SourceError("redirect_not_followed")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_json(url: str, timeout: float = 20.0) -> tuple[object, dict]:
    req = request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json, application/json"})
    try:
        with request.build_opener(NoRedirect()).open(req, timeout=timeout) as response:
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise SourceError("response_too_large")
            return json.loads(data.decode("utf-8")), {"status_code": response.status, "content_type": response.headers.get("Content-Type"), "bytes": len(data), "url": url, "link_header": response.headers.get("Link")}
    except error.HTTPError as exc:
        raise SourceError(f"http_{exc.code}_check_access_or_rate_limit" if exc.code in (401, 403, 429) else f"http_{exc.code}") from None
    except (error.URLError, TimeoutError, OSError):
        raise SourceError("network_error_or_timeout") from None
    except (UnicodeError, json.JSONDecodeError):
        raise SourceError("invalid_json_response") from None


def api_json(url: str, timeout: float) -> tuple[object, dict]:
    return get_json(url, timeout)


def pages(url: str, limit: int, timeout: float) -> tuple[list, list, bool]:
    rows, upstream, more = [], [], False
    page_no = 1
    while len(rows) < limit:
        sep = "&" if "?" in url else "?"
        endpoint = f"{url}{sep}per_page={min(100, limit-len(rows))}&page={page_no}"
        payload, meta = api_json(endpoint, timeout)
        if not isinstance(payload, list):
            raise SourceError("list_response_expected")
        upstream.append({"meta": meta, "data": payload})
        rows.extend(payload)
        has_next = bool(re.search(r'<[^>]+;\s*rel="next"', meta.get("link_header") or "", re.I))
        if not has_next:
            more = False
            break
        page_no += 1
        more = True
    if len(rows) > limit:
        rows = rows[:limit]
    return rows, upstream, more


def github_pr(repo: str, number: int, limit: int, timeout: float) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or number < 1:
        raise SourceError("expected_owner_repo_and_positive_pr_number")
    root = f"https://api.github.com/repos/{repo}/pulls/{number}"
    pr, pr_meta = api_json(root, timeout)
    if not isinstance(pr, dict):
        raise SourceError("pull_request_object_expected")
    reviews, raw_reviews, more_reviews = pages(root + "/reviews", limit, timeout)
    inline, raw_inline, more_inline = pages(root + "/comments", limit, timeout)
    conversation, raw_conversation, more_conversation = pages(f"https://api.github.com/repos/{repo}/issues/{number}/comments", limit, timeout)
    files, raw_files, more_files = pages(root + "/files", limit, timeout)
    patch_url = f"https://patch-diff.githubusercontent.com/raw/{repo}/pull/{number}.patch"
    req = request.Request(patch_url, headers={"User-Agent": UA, "Accept": "text/x-patch"})
    try:
        with request.build_opener(NoRedirect()).open(req, timeout=timeout) as response:
            patch_bytes = response.read(MAX_BYTES + 1)
            patch = patch_bytes.decode("utf-8", errors="replace")
            patch_meta = {"status_code": response.status, "content_type": response.headers.get("Content-Type"), "bytes": len(patch_bytes), "text_truncated": len(patch_bytes) > MAX_BYTES}
            patch = patch[:MAX_BYTES]
    except error.HTTPError as exc:
        patch, patch_meta = "", {"status_code": exc.code, "unavailable": True}
    except (error.URLError, TimeoutError, OSError):
        patch, patch_meta = "", {"unavailable": True, "reason": "network_error_or_timeout"}
    partial = any(x is True for x in (more_reviews, more_inline, more_conversation, more_files)) or patch_meta.get("unavailable", False) or patch_meta.get("text_truncated", False)
    return {
        "status": "partial" if partial else "ok", "source": "github_rest", "url": pr.get("html_url"), "retrieved_at": now(),
        "pull_request": {k: pr.get(k) for k in ("number", "title", "body", "state", "merged", "draft", "created_at", "updated_at", "closed_at", "user", "base", "head", "html_url")},
        "reviews": reviews, "inline_review_comments": inline, "conversation_comments": conversation, "files": files,
        "patch": {"text": patch, **patch_meta},
        "read": {"limit_per_collection": limit, "reviews_more_available": more_reviews, "inline_comments_more_available": more_inline, "conversation_comments_more_available": more_conversation, "files_more_available": more_files, "review_count_reported": pr.get("review_comments"), "issue_comment_count_reported": pr.get("comments"), "partial": partial, "complete": not partial},
        "upstream": {"pull_request": {"meta": pr_meta, "data": pr}, "reviews": raw_reviews, "inline_review_comments": raw_inline, "conversation_comments": raw_conversation, "files": raw_files, "patch_meta": patch_meta},
    }


def bsky_search(query: str, limit: int, timeout: float) -> dict:
    endpoint = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?" + parse.urlencode({"q": query, "limit": limit})
    payload, meta = get_json(endpoint, timeout)
    posts = payload.get("posts", []) if isinstance(payload, dict) else []
    return {"status": "ok", "source": "bluesky_public_api", "query": query, "records": posts,
            "read": {"returned": len(posts), "limit": limit, "complete": False, "scope": "bounded public search result; platform does not expose census completeness"},
            "upstream": {"meta": meta, "data": payload}}


def bsky_thread(uri: str, limit: int, timeout: float) -> dict:
    endpoint = "https://public.api.bsky.app/xrpc/app.bsky.feed.getPostThread?" + parse.urlencode({"uri": uri, "depth": 6, "parentHeight": 3})
    payload, meta = get_json(endpoint, timeout)
    records = []
    def visit(node, depth=0):
        if not isinstance(node, dict): return
        post = node.get("post") if isinstance(node.get("post"), dict) else {}
        author = post.get("author") if isinstance(post.get("author"), dict) else {}
        record = {"uri": post.get("uri"), "url": post.get("uri"), "author": author.get("handle"),
                  "text": ((post.get("record") or {}).get("text") if isinstance(post.get("record"), dict) else None),
                  "created_at": ((post.get("record") or {}).get("createdAt") if isinstance(post.get("record"), dict) else None),
                  "reply_count_reported": post.get("replyCount"), "depth": depth, "kind": "bluesky_post"}
        if post: records.append(record)
        for child in (node.get("replies") or [])[:limit]: visit(child, depth + 1)
    visit((payload.get("thread") or {}) if isinstance(payload, dict) else {})
    return {"status": "ok", "source": "bluesky_public_api", "url": uri, "records": records, "thread": payload,
            "read": {"reply_limit_requested": limit, "returned_posts": len(records), "complete": False, "scope": "API thread response; reply depth is bounded and may omit branches; full upstream tree retained"},
            "upstream": {"meta": meta, "data": payload}}


def hn_search(query: str, limit: int, timeout: float) -> dict:
    endpoint = "https://hn.algolia.com/api/v1/search?" + parse.urlencode({"query": query, "hitsPerPage": limit})
    payload, meta = get_json(endpoint, timeout)
    return {"status": "ok", "source": "hn_algolia", "query": query, "records": payload.get("hits", []),
            "read": {"returned": len(payload.get("hits", [])), "limit": limit, "total_matches": payload.get("nbHits"), "complete": False},
            "upstream": {"meta": meta, "data": payload}}


def hn_thread(item_id: str, limit: int, timeout: float) -> dict:
    if not item_id.isdigit():
        raise SourceError("expected_numeric_hn_item_id")
    payload, meta = get_json(f"https://hn.algolia.com/api/v1/items/{item_id}", timeout)
    def take(node, depth=0):
        if not isinstance(node, dict): return node
        out = dict(node)
        kids = out.get("children")
        if isinstance(kids, list):
            out["children_returned"] = min(len(kids), limit)
            out["children_truncated"] = len(kids) > limit
            out["children"] = [take(x, depth + 1) for x in kids[:limit]]
        return out
    bounded = take(payload)
    records = []
    def flatten(node, depth=0):
        if not isinstance(node, dict): return
        records.append({"id": node.get("id"), "kind": node.get("type"), "title": node.get("title"),
                        "text": node.get("text"), "author": node.get("author"), "created_at": node.get("created_at"),
                        "parent_id": node.get("parent_id"), "url": f"https://news.ycombinator.com/item?id={node.get('id')}",
                        "depth": depth, "child_count_reported": node.get("children_count"), "children_returned": node.get("children_returned", 0),
                        "children_truncated": node.get("children_truncated", False)})
        for child in node.get("children") or []: flatten(child, depth + 1)
    flatten(bounded)
    return {"status": "ok", "source": "hn_algolia", "url": f"https://news.ycombinator.com/item?id={item_id}", "thread": take(payload),
            "records": records, "read": {"children_per_parent_limit": limit, "returned_posts": len(records), "complete": False, "scope": "bounded child count at each returned node; per-node truncation flags are explicit"},
            "upstream": {"meta": meta, "data": payload}}


def discourse_search(query: str, limit: int, timeout: float) -> dict:
    endpoint = "https://discuss.python.org/search.json?" + parse.urlencode({"q": query})
    payload, meta = get_json(endpoint, timeout)
    topics = payload.get("topics", []) if isinstance(payload, dict) else []
    base = "https://discuss.python.org/t/"
    records = [{"url": f"{base}{parse.quote(str(x.get('slug') or 'topic'))}/{x.get('id')}",
                "title": x.get("title"), "kind": "discourse_topic_search_result",
                "excerpt": x.get("excerpt"), "posts_count": x.get("posts_count"),
                "reply_count": x.get("reply_count"), "created_at": x.get("created_at"),
                "last_posted_at": x.get("last_posted_at"), "username": x.get("username")}
               for x in topics[:limit] if isinstance(x, dict)]
    return {"status": "ok", "source": "discourse_search", "query": query, "records": records,
            "read": {"returned": len(records), "limit": limit, "api_topic_count": len(topics), "complete": False, "scope": "bounded public Discourse search endpoint result"},
            "upstream": {"meta": meta, "data": payload}}


def discourse_thread(url: str, limit: int, timeout: float) -> dict:
    reader = Path(__file__).with_name("discourse.py")
    if not reader.is_file(): raise SourceError("existing_discourse_reader_missing")
    cmd = [sys.executable, str(reader), url, "--post-limit", str(limit), "--request-budget", "6", "--timeout", str(timeout)]
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * 8, encoding="utf-8", errors="replace", shell=False)
    except subprocess.TimeoutExpired:
        raise SourceError("discourse_reader_timeout") from None
    try: payload = json.loads(run.stdout)
    except json.JSONDecodeError: raise SourceError(f"discourse_reader_invalid_output_exit_{run.returncode}") from None
    return {"status": payload.get("status", "unavailable"), "source": "existing_discourse_reader", "url": payload.get("url", url),
            "records": payload.get("records", []), "read": payload.get("read", {"complete": False}),
            "upstream": {"existing_reader_result": payload, "stderr": run.stderr}}


def lemmy_api(instance: str, timeout: float) -> tuple[int, list[dict]]:
    host = instance.casefold().rstrip(".")
    if host not in LEMMY_INSTANCES:
        raise SourceError("lemmy_instance_not_in_public_allowlist")
    attempts = []
    for version in (4, 3):
        url = f"https://{host}/api/v{version}/site"
        try:
            payload, meta = get_json(url, timeout)
            attempts.append({"version": version, "status": "available", "meta": meta, "data": payload})
            return version, attempts
        except SourceError as exc:
            attempts.append({"version": version, "status": "unavailable", "reason": str(exc)})
    raise SourceError("lemmy_api_v4_and_v3_unavailable; see version probes")


def lemmy_search(query: str, limit: int, timeout: float, instance: str, page: int) -> dict:
    version, probes = lemmy_api(instance, timeout)
    host = instance.casefold().rstrip(".")
    url = f"https://{host}/api/v{version}/search?" + parse.urlencode({"q": query, "type_": "Posts", "sort": "TopAll", "listing_type": "All", "limit": limit, "page": page})
    payload, meta = get_json(url, timeout)
    posts = payload.get("posts", []) if isinstance(payload, dict) else []
    records = []
    for item in posts[:limit]:
        view = ((item.get("post_view") or item) if isinstance(item, dict) else None)
        post = (view or {}).get("post") or {}
        creator = (view or {}).get("creator") or {}
        community = (view or {}).get("community") or {}
        counts = (view or {}).get("counts") or {}
        records.append({"id": post.get("id"), "kind": "lemmy_post", "url": f"https://{host}/post/{post.get('id')}",
                        "ap_id": post.get("ap_id"), "title": post.get("name"), "text": post.get("body"),
                        "author": creator.get("name"), "community": community.get("name"), "community_actor_id": community.get("actor_id"),
                        "published_at": post.get("published"), "updated_at": post.get("updated"), "comments_reported": counts.get("comments"),
                        "score": counts.get("score"), "removed": post.get("removed"), "deleted": post.get("deleted")})
    maybe_more = len(posts) >= limit
    return {"status": "ok", "source": "lemmy_public_api", "instance": host, "query": query, "records": records,
            "read": {"api_version": version, "page": page, "limit": limit, "returned": len(records), "more_may_be_available": maybe_more,
                     "next_page": page + 1 if maybe_more else None, "total_matches": None, "complete": False,
                     "scope": "public federated post search; per-instance search sample, no census claim"},
            "upstream": {"version_probes": probes, "search": {"meta": meta, "data": payload}}}


def lemmy_thread(post_id: str, limit: int, timeout: float, instance: str, page: int) -> dict:
    if not post_id.isdigit() or int(post_id) < 1:
        raise SourceError("expected_numeric_lemmy_post_id")
    version, probes = lemmy_api(instance, timeout)
    host = instance.casefold().rstrip(".")
    root, post_meta = get_json(f"https://{host}/api/v{version}/post?" + parse.urlencode({"id": int(post_id)}), timeout)
    view = (root.get("post_view") or {}) if isinstance(root, dict) else {}
    post = view.get("post") or {}
    comment_route = "comment/list/slim" if version == 4 else "comment/list"
    comments_url = f"https://{host}/api/v{version}/{comment_route}?" + parse.urlencode({"post_id": int(post_id), "sort": "New", "limit": limit, "page": page})
    comments_payload, comments_meta = get_json(comments_url, timeout)
    comments = comments_payload.get("comments", []) if isinstance(comments_payload, dict) else []
    comments_total = ((view.get("counts") or {}).get("comments"))
    returned_before = (page - 1) * limit + len(comments)
    more = returned_before < comments_total if isinstance(comments_total, int) else (True if len(comments) == limit else None)
    records = [{"id": post.get("id"), "kind": "lemmy_post", "url": f"https://{host}/post/{post.get('id')}",
                "ap_id": post.get("ap_id"), "title": post.get("name"), "text": post.get("body"),
                "author": ((view.get("creator") or {}).get("name")), "published_at": post.get("published"),
                "comments_reported": comments_total}]
    for item in comments:
        cv = ((item.get("comment_view") or item) if isinstance(item, dict) else None)
        comment = (cv or {}).get("comment") or {}
        counts = (cv or {}).get("counts") or {}
        records.append({"id": comment.get("id"), "kind": "lemmy_comment", "url": f"https://{host}/comment/{comment.get('id')}",
                        "post_id": comment.get("post_id"), "parent_id": comment.get("parent_id"), "text": comment.get("content"),
                        "author": ((cv or {}).get("creator") or {}).get("name"), "published_at": comment.get("published"),
                        "score": counts.get("score"), "removed": comment.get("removed"), "deleted": comment.get("deleted")})
    return {"status": "partial" if more is True else "ok", "source": "lemmy_public_api", "instance": host, "url": f"https://{host}/post/{post_id}",
            "records": records, "read": {"api_version": version, "comment_route": comment_route, "partial": more is True, "page": page, "limit": limit, "returned_comments": len(comments),
                     "reported_comments": comments_total, "more_available": more,
                     "next_page": page + 1 if more else None, "complete": more is False,
                     "scope": "post plus one bounded public comment-list page; comment pagination state uses reported count"},
            "upstream": {"version_probes": probes, "post": {"meta": post_meta, "data": root}, "comments": {"meta": comments_meta, "data": comments_payload}}}


class DiscussionParser(HTMLParser):
    """Extract visible GitHub discussion body blocks while retaining raw HTML."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks, self.current, self.depth = [], [], 0
        self.void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.depth == 0 and "markdown-body" in (attrs.get("class") or "").split():
            self.current = []
            self.depth = 1
        elif self.depth and tag not in self.void:
            self.depth += 1
        if self.depth and tag == "br": self.current.append("\n")
    def handle_endtag(self, tag):
        if self.depth and tag not in self.void:
            self.depth -= 1
            if self.depth == 0:
                text = re.sub(r"[ \t]+", " ", "".join(self.current)).strip()
                if text: self.blocks.append(text)
    def handle_data(self, data):
        if self.depth: self.current.append(data)


def github_discussion(url: str, timeout: float) -> dict:
    match = re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/discussions/(\d+)/?", url)
    if not match: raise SourceError("expected_public_github_discussion_url")
    req = request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with request.build_opener(NoRedirect()).open(req, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES: raise SourceError("response_too_large")
            source = raw.decode("utf-8", errors="replace")
            http_meta = {"status_code": response.status, "content_type": response.headers.get("Content-Type"), "bytes": len(raw), "url": url}
    except error.HTTPError as exc:
        raise SourceError(f"http_{exc.code}_check_access_or_rate_limit" if exc.code in (401, 403, 429) else f"http_{exc.code}") from None
    except (error.URLError, TimeoutError, OSError):
        raise SourceError("network_error_or_timeout") from None
    title_match = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', source, re.I)
    descr_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', source, re.I)
    parser = DiscussionParser(); parser.feed(source)
    return {"status": "ok", "source": "github_discussion_html", "url": url,
            "title": html.unescape(title_match.group(1)) if title_match else None,
            "description": html.unescape(descr_match.group(1)) if descr_match else None,
            "records": [{"kind": "visible_discussion_markdown_block", "text": t} for t in parser.blocks],
            "read": {"visible_markdown_blocks": len(parser.blocks), "complete": False, "scope": "public rendered HTML page; reply pagination/completeness is unknown"},
            "upstream": {"meta": http_meta, "raw_html": source, "raw_truncated": False}}


def opencli_linuxdo_search(query: str, limit: int, timeout: float) -> dict:
    executable = shutil.which("opencli.cmd") or shutil.which("opencli")
    if not executable:
        raise SourceError("opencli_not_found")
    cmd = [executable, "linux-do", "search", query, "--limit", str(limit), "-f", "json", "--site-session", "persistent"]
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=False)
    except subprocess.TimeoutExpired:
        raise SourceError("opencli_timeout") from None
    # OpenCLI emits YAML even when json is requested on some adapter versions;
    # keep stdout/stderr intact and expose parse status instead of guessing.
    try:
        parsed = json.loads(run.stdout)
        parse_status = "json"
    except json.JSONDecodeError:
        parsed, parse_status = None, "non_json_raw_preserved"
    code_match = re.search(r"(?m)^\s*code:\s*([A-Z0-9_]+)", run.stderr)
    failure = code_match.group(1) if code_match else (None if run.returncode == 0 else f"opencli_exit_{run.returncode}")
    return {"status": "ok" if run.returncode == 0 else "unavailable", "source": "opencli_linux_do", "query": query,
            "records": parsed, "reason": failure,
            "read": {"requested_limit": limit, "complete": False, "output_parse": parse_status},
            "upstream": {"command": ["opencli", "linux-do", "search", "<query>", "--limit", str(limit), "-f", "json", "--site-session", "persistent"], "stdout": run.stdout, "stderr": run.stderr}}


def short_summary(result: dict, out: str | None) -> dict:
    read = result.get("read") if isinstance(result.get("read"), dict) else {}
    keep = ("complete", "partial", "requests_used", "request_budget", "post_limit", "returned_posts",
            "returned", "returned_comments", "reported_comments", "limit", "total_matches", "api_topic_count", "incomplete_reasons", "scope",
            "children_per_parent_limit", "reply_limit_requested", "output_parse", "api_version", "page", "next_page",
            "more_available", "more_may_be_available")
    summary = {k: result.get(k) for k in ("status", "source", "url", "query", "title", "reason", "instance") if result.get(k) is not None}
    if "pull_request" in result:
        summary["pull_request"] = {k: (result["pull_request"] or {}).get(k) for k in ("number", "title", "state", "merged", "html_url")}
        summary["counts"] = {"reviews": len(result.get("reviews") or []), "inline_review_comments": len(result.get("inline_review_comments") or []),
                              "conversation_comments": len(result.get("conversation_comments") or []), "files": len(result.get("files") or [])}
        summary["patch_truncated"] = (result.get("patch") or {}).get("text_truncated", False)
        summary["patch_unavailable"] = (result.get("patch") or {}).get("unavailable", False)
    else:
        summary["returned_records"] = len(result.get("records") or [])
        if "visible_markdown_blocks" in read: summary["visible_markdown_blocks"] = read.get("visible_markdown_blocks")
        if "thread" in result and isinstance(result["thread"], dict): summary["thread_root"] = (result["thread"].get("post") or {}).get("post", {}).get("name") or result.get("url")
    summary["read"] = {k: read.get(k) for k in keep if k in read}
    if out: summary["output_file"] = str(Path(out))
    return summary


def save(result: dict, out: str | None, full: bool = False) -> None:
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if out:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as handle:
            handle.write(encoded + "\n")
    print(json.dumps(result if full or not out else short_summary(result, out), ensure_ascii=False, indent=2))


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    def common(p):
        p.add_argument("--out")
        p.add_argument("--timeout", type=float, default=20.0)
        p.add_argument("--full", action="store_true", help="print the full result to stdout (default with --out is a short summary)")
    pr = sub.add_parser("github-pr", help="read a public GitHub PR and review/diff context")
    common(pr)
    pr.add_argument("repo"); pr.add_argument("number", type=int); pr.add_argument("--limit", type=int, default=50)
    disc = sub.add_parser("community-search", help="search a public community source")
    common(disc)
    disc.add_argument("source", choices=("bluesky", "hn", "linux-do", "discourse", "lemmy")); disc.add_argument("query"); disc.add_argument("--limit", type=int, default=10)
    disc.add_argument("--instance", choices=LEMMY_INSTANCES, default="lemmy.world"); disc.add_argument("--page", type=int, default=1)
    thread = sub.add_parser("community-thread", help="read a bounded public community thread")
    common(thread)
    thread.add_argument("source", choices=("bluesky", "hn", "discourse", "lemmy")); thread.add_argument("id_or_uri"); thread.add_argument("--limit", type=int, default=20)
    thread.add_argument("--instance", choices=LEMMY_INSTANCES, default="lemmy.world"); thread.add_argument("--page", type=int, default=1)
    gd = sub.add_parser("github-discussion", help="read a public GitHub discussion rendered page")
    common(gd)
    gd.add_argument("url")
    args = parser.parse_args(argv)
    if args.out and Path(args.out).exists():
        parser.error('output_exists_choose_new_path')
    if (hasattr(args, "limit") and not 1 <= args.limit <= 100) or not 1 <= args.timeout <= 60 or (hasattr(args, "page") and not 1 <= args.page <= 1000):
        parser.error("limit must be 1..100, page 1..1000, and timeout 1..60 seconds")
    try:
        if args.command == "github-pr": result = github_pr(args.repo, args.number, args.limit, args.timeout)
        elif args.command == "community-search":
            if args.source == "lemmy": result = lemmy_search(args.query, args.limit, args.timeout, args.instance, args.page)
            else: result = {"bluesky": bsky_search, "hn": hn_search, "linux-do": opencli_linuxdo_search, "discourse": discourse_search}[args.source](args.query, args.limit, args.timeout)
        elif args.command == "github-discussion": result = github_discussion(args.url, args.timeout)
        elif args.source == "bluesky": result = bsky_thread(args.id_or_uri, args.limit, args.timeout)
        elif args.source == "discourse": result = discourse_thread(args.id_or_uri, args.limit, args.timeout)
        elif args.source == "lemmy": result = lemmy_thread(args.id_or_uri, args.limit, args.timeout, args.instance, args.page)
        else: result = hn_thread(args.id_or_uri, args.limit, args.timeout)
    except SourceError as exc:
        result = {"status": "unavailable", "source": args.command, "reason": str(exc), "read": {"complete": False}}
    save(result, args.out, args.full)
    return 0 if result.get("status") in ("ok", "partial") else 2


if __name__ == "__main__":
    raise SystemExit(main())
