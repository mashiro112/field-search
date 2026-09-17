"""Bounded, public Discourse topic reader.

The route uses the documented JSON topic/posts endpoints directly.  It keeps
post order, author/time/URL fields, reply targets and explicit completeness
state.  It does not log in, read cookies, or treat the first topic response as
the complete thread.
"""
from __future__ import annotations

import argparse
import html
import ipaddress
import json
from pathlib import Path
import re
import time
from urllib import error, parse, request
from typing import Any, Sequence


MAX_BYTES = 4 * 1024 * 1024
LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home", ".test", ".invalid")


class DiscourseError(RuntimeError):
    pass


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DiscourseError("redirect_not_followed")


def _clean_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"(?is)<(?:br\s*/?|/p|/div|/li|/blockquote)>", "\n", text)
    text = re.sub(r"(?is)<[^>]*>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _clip(value: Any, limit: int = 12000) -> dict[str, Any]:
    text = _clean_text(value)
    result: dict[str, Any] = {"text": text[:limit], "text_truncated": len(text) > limit}
    if len(text) > limit:
        result["text_full"] = text
    return result


def _validate_public(url: str) -> parse.SplitResult:
    target = parse.urlsplit(url)
    host = (target.hostname or "").casefold().rstrip(".")
    if target.scheme != "https" or not host or target.username or target.password or target.port not in (None, 443):
        raise ValueError("expected_public_discourse_https_url")
    if "." not in host or host.endswith(LOCAL_SUFFIXES):
        raise ValueError("nonpublic_discourse_host")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("nonpublic_discourse_host")
    return target


def _topic_target(value: str) -> tuple[str, int, str, str | None]:
    target = _validate_public(value)
    parts = [part for part in target.path.split("/") if part]
    if len(parts) < 2 or parts[0] != "t":
        raise ValueError("expected_discourse_topic_url")
    numeric = next((part for part in parts[1:] if part.isdigit()), None)
    if numeric is None:
        raise ValueError("discourse_topic_id_missing")
    topic_id = int(numeric)
    slug = parts[1] if not parts[1].isdigit() else None
    root = f"https://{target.hostname}"
    canonical = f"{root}/t/{slug + '/' if slug else ''}{topic_id}"
    return root, topic_id, canonical, slug


def _request_json(url: str, timeout: float) -> dict[str, Any]:
    _validate_public(url)
    req = request.Request(
        url,
        headers={
            "User-Agent": "field-search/1.0 (public Discourse reader)",
            "Accept": "application/json",
        },
    )
    try:
        with request.build_opener(NoRedirect()).open(req, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise DiscourseError("response_too_large")
            value = json.loads(raw.decode("utf-8", errors="strict"))
    except error.HTTPError as exc:
        suffix = "_check_access_or_rate_limit" if exc.code in (401, 403, 429) else ""
        raise DiscourseError(f"http_{exc.code}{suffix}") from None
    except (error.URLError, TimeoutError, OSError):
        raise DiscourseError("network_error_or_timeout; external_job_may_have_run") from None
    except (UnicodeError, json.JSONDecodeError):
        raise DiscourseError("invalid_json_response") from None
    if not isinstance(value, dict):
        raise DiscourseError("response_object_expected")
    return value


def _post_url(root: str, topic_id: int, slug: str | None, post_number: Any) -> str:
    suffix = slug + "/" if slug else ""
    try:
        number = int(post_number)
    except (TypeError, ValueError):
        number = 1
    return f"{root}/t/{suffix}{topic_id}/{number}"


def _normalize_post(post: dict[str, Any], root: str, topic_id: int, slug: str | None) -> dict[str, Any]:
    post_number = post.get("post_number")
    result: dict[str, Any] = {
        "url": _post_url(root, topic_id, slug, post_number),
        "title": "Discourse post",
        "kind": "discourse_post",
        "post_id": post.get("id"),
        "post_number": post_number,
        "topic_id": topic_id,
        "author": post.get("username") or post.get("name"),
        "published_at": post.get("created_at"),
        "updated_at": post.get("updated_at"),
        "reply_to_post_number": post.get("reply_to_post_number"),
        "reply_to_post_id": post.get("reply_to_post_id"),
    }
    result.update(_clip(post.get("cooked") or post.get("raw") or ""))
    return result


def _post_map(value: Any) -> dict[int, dict[str, Any]]:
    posts = value if isinstance(value, list) else []
    result: dict[int, dict[str, Any]] = {}
    for post in posts:
        if isinstance(post, dict) and isinstance(post.get("id"), int):
            result[post["id"]] = post
    return result


def read_topic(
    url: str,
    *,
    post_limit: int = 50,
    request_budget: int = 6,
    batch_size: int = 20,
    timeout: float = 20.0,
) -> dict[str, Any]:
    root, topic_id, canonical, slug = _topic_target(url)
    started = time.monotonic()
    requests_used = 0
    later_failure: str | None = None
    try:
        topic = _request_json(f"{canonical}.json", timeout)
        requests_used += 1
    except DiscourseError as exc:
        return {
            "status": "unavailable",
            "source": "discourse",
            "url": canonical,
            "records": [],
            "reason": str(exc),
            "read": {
                "complete": False,
                "partial": False,
                "requests_used": requests_used + 1,
                "request_budget": request_budget,
                "post_limit": post_limit,
                "batch_size": batch_size,
            },
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }

    stream = topic.get("post_stream") if isinstance(topic.get("post_stream"), dict) else {}
    first_posts = _post_map(stream.get("posts"))
    raw_stream = stream.get("stream")
    stream_available = isinstance(raw_stream, list) and bool(raw_stream)
    stream_ids = [value for value in (raw_stream or []) if isinstance(value, int)]
    if not stream_ids:
        stream_ids = list(first_posts)
    target_ids = stream_ids[:post_limit]
    posts = dict(first_posts)
    missing = [post_id for post_id in target_ids if post_id not in posts]
    while missing and requests_used < request_budget:
        batch = missing[:batch_size]
        params = [("post_ids[]", str(post_id)) for post_id in batch]
        endpoint = f"{root}/t/{topic_id}/posts.json?{parse.urlencode(params)}"
        requests_used += 1
        try:
            fetched = _request_json(endpoint, timeout)
        except DiscourseError as exc:
            later_failure = str(exc)
            break
        new_posts = _post_map((fetched.get("post_stream") or {}).get("posts"))
        before = len(posts)
        posts.update(new_posts)
        if len(posts) == before:
            later_failure = "posts_endpoint_returned_no_requested_posts"
            break
        missing = [post_id for post_id in target_ids if post_id not in posts]

    records = [
        _normalize_post(posts[post_id], root, topic_id, slug)
        for post_id in target_ids
        if post_id in posts
    ]
    post_limit_truncated = len(stream_ids) > post_limit
    expected_posts = topic.get("posts_count", len(first_posts))
    if not isinstance(expected_posts, int):
        expected_posts = len(first_posts)
    stream_missing = bool(not stream_available and expected_posts > len(first_posts))
    incomplete_reasons: list[str] = []
    if post_limit_truncated:
        incomplete_reasons.append("post_limit")
    if missing:
        if later_failure:
            incomplete_reasons.append(later_failure)
        elif requests_used >= request_budget:
            incomplete_reasons.append("request_budget_exhausted")
        else:
            incomplete_reasons.append("requested_posts_not_returned")
    if stream_missing:
        incomplete_reasons.append("post_stream_incomplete_unknown")
    complete = bool(records) and not incomplete_reasons
    partial = bool(records) and not complete
    if not records and not later_failure and not incomplete_reasons:
        status = "no_results"
    elif complete:
        status = "ok"
    elif records:
        status = "partial"
    else:
        status = "unavailable"
    topic_summary = {
        "id": topic.get("id", topic_id),
        "title": topic.get("title"),
        "slug": topic.get("slug") or slug,
        "category_id": topic.get("category_id"),
        "created_at": topic.get("created_at"),
        "last_posted_at": topic.get("last_posted_at"),
        "posts_count": topic.get("posts_count"),
        "first_batch_count": len(first_posts),
        "stream_count": len(stream_ids),
    }
    known_unread_ids = (missing + stream_ids[post_limit:]) if stream_available else []
    unknown_unread_count = max(0, expected_posts - len(records)) if stream_missing else 0
    result: dict[str, Any] = {
        "schema_version": 1,
        "status": status,
        "source": "discourse",
        "url": canonical,
        "topic": topic_summary,
        "records": records,
        "read": {
            "complete": complete,
            "partial": partial,
            "requests_used": requests_used,
            "request_budget": request_budget,
            "post_limit": post_limit,
            "batch_size": batch_size,
            "first_batch_count": len(first_posts),
            "stream_count": len(stream_ids),
            "returned_posts": len(records),
            "unread_post_ids_count": len(known_unread_ids),
            "unread_post_ids": known_unread_ids[:100],
            "unread_post_count_unknown": unknown_unread_count,
            "incomplete_reasons": incomplete_reasons,
            "next_action": "raise post_limit/request_budget or retry the failed batch" if incomplete_reasons else None,
        },
        "scope": "public Discourse JSON; no login/cookies; first topic batch is not assumed complete",
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    if later_failure:
        result["failure"] = {"kind": later_failure}
    return result


def _emit(result: dict[str, Any], out: str | None) -> None:
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if out:
        path = Path(out)
        if path.exists():
            raise ValueError("--out already exists; choose a new artifact path")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text + "\n")
        read = result.get("read") if isinstance(result.get("read"), dict) else {}
        preview = {
            "status": result.get("status"),
            "source": result.get("source", "discourse"),
            "url": result.get("url"),
            "topic": result.get("topic"),
            "returned_posts": read.get("returned_posts", len(result.get("records", []))),
            "complete": read.get("complete"),
            "partial": read.get("partial"),
            "requests_used": read.get("requests_used"),
            "request_budget": read.get("request_budget"),
            "incomplete_reasons": read.get("incomplete_reasons"),
            "output_file": str(path),
            "note": "full topic result saved; use the file for post/text lookup instead of refetching",
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))
    else:
        print(text)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read a public Discourse topic with bounded post batches")
    parser.add_argument("url", help="public https://<host>/t/<slug>/<topic-id> URL")
    parser.add_argument("--post-limit", type=int, default=50, help="maximum posts to return, 1..200")
    parser.add_argument("--request-budget", type=int, default=6, help="total topic+post requests, 1..20")
    parser.add_argument("--batch-size", type=int, default=20, help="post IDs per follow-up request, 1..50")
    parser.add_argument("--timeout", type=float, default=20.0, help="per-request timeout, 1..60 seconds")
    parser.add_argument("--out", help="new JSON output path; existing files are never overwritten")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        if args.out and Path(args.out).exists():
            raise ValueError("--out already exists; choose a new artifact path")
        if not 1 <= args.post_limit <= 200:
            parser.error("--post-limit must be between 1 and 200")
        if not 1 <= args.request_budget <= 20:
            parser.error("--request-budget must be between 1 and 20")
        if not 1 <= args.batch_size <= 50:
            parser.error("--batch-size must be between 1 and 50")
        if not 1 <= args.timeout <= 60:
            parser.error("--timeout must be between 1 and 60")
        result = read_topic(
            args.url,
            post_limit=args.post_limit,
            request_budget=args.request_budget,
            batch_size=args.batch_size,
            timeout=args.timeout,
        )
        _emit(result, args.out)
        return 0 if result.get("status") in {"ok", "partial", "no_results"} else 2
    except (ValueError, DiscourseError) as exc:
        result = {
            "status": "error",
            "source": "discourse",
            "records": [],
            "reason": str(exc),
            "scope": "public Discourse JSON; no login/cookies",
        }
        try:
            _emit(result, getattr(locals().get("args"), "out", None))
        except ValueError:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
