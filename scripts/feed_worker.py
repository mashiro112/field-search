"""Isolated public RSS/Atom fetch and parse worker.

The parent route gives this worker a JSON request over stdin.  The worker only
receives bytes from a validated public HTTPS feed URL, then parses those bytes
with feedparser.  It never gives an untrusted URL to feedparser, so parsing
cannot trigger feedparser's own URL or file handling.
"""
from __future__ import annotations

import calendar
import datetime as dt
import html
import ipaddress
import io
import json
import re
import socket
import sys
import time
from pathlib import Path
from urllib import error, parse, request
from typing import Any


MAX_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
MAX_SUMMARY_CHARS = 2_000
MAX_TITLE_CHARS = 500
MAX_URL_CHARS = 2_048
MAX_ID_CHARS = 1_024
LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home", ".test", ".invalid", ".onion")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
TAG_RE = re.compile(r"(?is)<[^>]*>")
ROOT_TAG_RE = re.compile(r"(?is)^\s*<\s*([a-z][a-z0-9_.:-]*)\b")
CHALLENGE_RE = re.compile(r"(?i)(?:captcha|verify\s+(?:you\s+are\s+human|that\s+you)|cloudflare\s+ray|access\s+denied|just\s+a\s+moment|安全验证|请输入验证码)")


class FeedError(RuntimeError):
    """A safe, user-facing worker failure without untrusted payload text."""


def _configure_stdio() -> None:
    """Make worker JSON independent of the Windows console code page."""
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8", errors="strict")
        except (AttributeError, OSError, ValueError):
            pass


def _validate_url(value: str) -> parse.SplitResult:
    """Apply the document route's URL policy with HTTPS-only transport."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("expected_public_feed_https_url")
    try:
        # Reuse the established syntax/host policy without importing any
        # optional runtime.  document.py is beside this worker in the skill.
        scripts_dir = str(Path(__file__).resolve().parent)
        if scripts_dir not in sys.path:
            # The worker intentionally runs with Python -I; isolated mode
            # removes the script directory from sys.path.
            sys.path.insert(0, scripts_dir)
        from document import validate_url as document_validate_url

        document_validate_url(value)
    except (ImportError, ValueError):
        raise ValueError("expected_public_feed_https_url") from None
    target = parse.urlsplit(value)
    host = (target.hostname or "").casefold().rstrip(".")
    if target.scheme != "https" or target.port not in (None, 443):
        raise ValueError("expected_public_feed_https_url")
    if "." not in host or host.endswith(LOCAL_SUFFIXES):
        raise ValueError("nonpublic_feed_host")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if not literal.is_global:
            raise ValueError("nonpublic_feed_host")
        return target
    # Do not pre-resolve domain names here.  The configured HTTPS transport
    # may use a transparent proxy whose synthetic DNS address is not routable
    # from this process.  Literal private IPs and reserved host suffixes were
    # rejected above; every redirect is sent through the same checks.
    return target


def _validate_redirect(url: str) -> None:
    _validate_url(url)


class PublicRedirectHandler(request.HTTPRedirectHandler):
    """Follow at most three redirects, validating each destination first."""

    def __init__(self) -> None:
        super().__init__()
        self.redirects = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        self.redirects += 1
        if self.redirects > MAX_REDIRECTS:
            raise FeedError("too_many_redirects")
        _validate_redirect(newurl)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None and parse.urlsplit(newurl).netloc.casefold() != parse.urlsplit(req.full_url).netloc.casefold():
            for header_map in (redirected.headers, redirected.unredirected_hdrs):
                for key in list(header_map):
                    if key.casefold() in {"if-none-match", "if-modified-since"}:
                        header_map.pop(key, None)
        return redirected


def _clean_text(value: Any, limit: int) -> tuple[str, bool]:
    if value is None:
        return "", False
    if isinstance(value, (list, tuple)):
        value = " ".join(str(item) for item in value)
    text = html.unescape(str(value))
    text = TAG_RE.sub(" ", text)
    text = CONTROL_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit], len(text) > limit


def _field_text(value: Any, limit: int) -> str | None:
    text, _ = _clean_text(value, limit)
    return text or None


def _entry_date(entry: Any) -> tuple[str | None, dt.date | None]:
    """Use feedparser's parsed date fields, preferring publication time."""
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        value = entry.get(key)
        if value is None:
            continue
        try:
            timestamp = calendar.timegm(tuple(value)[:9])
            moment = dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
        except (TypeError, ValueError, OverflowError, OSError):
            continue
        return moment.isoformat().replace("+00:00", "Z"), moment.date()
    return None, None


def _entry_summary(entry: Any) -> tuple[str | None, bool]:
    value = entry.get("summary") or entry.get("description")
    if not value:
        content = entry.get("content")
        if isinstance(content, list) and content and isinstance(content[0], dict):
            value = content[0].get("value")
    text, truncated = _clean_text(value, MAX_SUMMARY_CHARS)
    return (text or None), truncated


def _normalize_entry(entry: Any) -> dict[str, Any]:
    date, _ = _entry_date(entry)
    summary, summary_truncated = _entry_summary(entry)
    title_raw, title_truncated = _clean_text(entry.get("title"), MAX_TITLE_CHARS)
    link_raw, link_truncated = _clean_text(entry.get("link"), MAX_URL_CHARS)
    id_raw, id_truncated = _clean_text(entry.get("id") or entry.get("guid"), MAX_ID_CHARS)
    return {
        "title": title_raw or None,
        # A clipped URL is omitted rather than emitted as a misleading URL.
        "link": None if link_truncated else (link_raw or None),
        "id": None if id_truncated else (id_raw or None),
        "date": date,
        "summary": summary,
        "date_unknown": date is None,
        "_truncation": {
            "title": title_truncated,
            "link": link_truncated,
            "id": id_truncated,
            "summary": summary_truncated,
        },
    }


def _content_type(headers: Any) -> str:
    value = headers.get("Content-Type", "") if headers is not None else ""
    return str(value).split(";", 1)[0].strip().casefold()


def _looks_like_feed(raw: bytes, content_type: str) -> bool:
    prefix = raw[:16 * 1024].decode("utf-8", errors="replace")
    if content_type in {"text/html", "application/xhtml+xml"}:
        return False
    # Ignore BOM, XML declaration, comments, and a doctype before checking the
    # document root.  Feed summaries may legitimately contain XHTML tags.
    remainder = prefix.lstrip("\ufeff \t\r\n")
    while True:
        updated = re.sub(r"(?is)^(?:<\?xml[^>]*>\s*|<!--.*?-->\s*|<!doctype[^>]*>\s*)", "", remainder, count=1)
        if updated == remainder:
            break
        remainder = updated.lstrip("\ufeff \t\r\n")
    match = ROOT_TAG_RE.match(remainder)
    if not match:
        return False
    root = match.group(1).casefold()
    if root not in {"rss", "feed", "rdf:rdf"}:
        return False
    # A challenge page occasionally carries an XML-looking wrapper.  A real
    # feed with entries may mention these words in an article; an empty wrapper
    # containing only the challenge marker is not a feed result.
    if CHALLENGE_RE.search(prefix) and not re.search(r"(?is)<\s*(?:item|entry)\b", prefix):
        return False
    return True


def _fetch_response(url: str, timeout: float, *, etag: str | None = None,
                    last_modified: str | None = None) -> tuple[bytes, Any, str, int]:
    _validate_url(url)
    handler = PublicRedirectHandler()
    opener = request.build_opener(handler)
    headers = {
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.1",
        "User-Agent": "field-search/1.0 (public RSS/Atom reader)",
    }
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    req = request.Request(
        url,
        method="GET",
        headers=headers,
    )
    try:
        with opener.open(req, timeout=timeout) as response:
            final_url = str(response.geturl())
            _validate_url(final_url)
            content_length = response.headers.get("Content-Length")
            try:
                if content_length is not None and int(content_length) > MAX_BYTES:
                    raise FeedError("response_too_large")
            except ValueError:
                pass
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise FeedError("response_too_large")
            return raw, response.headers, final_url, 200
    except FeedError:
        raise
    except error.HTTPError as exc:
        if exc.code == 304 and (etag or last_modified):
            final_url = str(exc.geturl())
            _validate_url(final_url)
            return b"", exc.headers, final_url, 304
        raise FeedError(f"http_{exc.code}") from None
    except (error.URLError, TimeoutError, socket.timeout, OSError):
        raise FeedError("network_error_or_timeout") from None


def _fetch_bytes(url: str, timeout: float) -> tuple[bytes, Any, str]:
    """Keep the existing bounded fetch interface used by site discovery."""
    raw, headers, final_url, _ = _fetch_response(url, timeout)
    return raw, headers, final_url


def parse_feed_bytes(
    raw: bytes,
    *,
    requested_url: str,
    final_url: str | None = None,
    headers: Any = None,
    limit: int = 5,
    since: str | None = None,
) -> dict[str, Any]:
    """Parse already-fetched bytes.  This helper makes local fixture tests safe."""
    if not isinstance(raw, (bytes, bytearray)):
        raise FeedError("feed_bytes_invalid")
    if len(raw) > MAX_BYTES:
        raise FeedError("response_too_large")
    if not 1 <= limit <= 30:
        raise ValueError("limit_out_of_range")
    since_date: dt.date | None = None
    if since is not None:
        try:
            since_date = dt.date.fromisoformat(since)
        except (TypeError, ValueError):
            raise ValueError("since_must_be_yyyy_mm_dd") from None
        if since_date.isoformat() != since:
            raise ValueError("since_must_be_yyyy_mm_dd")
    ctype = _content_type(headers)
    if not _looks_like_feed(bytes(raw), ctype):
        raise FeedError("html_or_non_feed_response")
    try:
        import feedparser
    except ImportError:
        raise FeedError("feedparser_runtime_missing") from None
    parsed = feedparser.parse(
        io.BytesIO(bytes(raw)),
        response_headers={
            "content-location": final_url or requested_url,
            "content-type": ctype or "application/xml",
        },
    )
    parser_version = str(getattr(feedparser, "__version__", "unknown"))
    bozo = bool(parsed.get("bozo"))
    if bozo:
        raise FeedError("invalid_feed_xml")
    entries = parsed.get("entries") or []
    normalized: list[dict[str, Any]] = []
    unknown_count = 0
    for item in entries:
        if not isinstance(item, dict):
            continue
        item_date, item_date_value = _entry_date(item)
        if item_date is None:
            unknown_count += 1
        if since_date is not None and (item_date_value is None or item_date_value < since_date):
            continue
        normalized.append(_normalize_entry(item))
    selected = normalized[:limit]
    field_truncation = {"title": 0, "link": 0, "id": 0, "summary": 0}
    for item in selected:
        flags = item.pop("_truncation", {})
        for name in field_truncation:
            if flags.get(name):
                field_truncation[name] += 1
    total_matching = len(normalized)
    feed = parsed.get("feed") or {}
    feed_title = _field_text(feed.get("title"), MAX_TITLE_CHARS)
    feed_link = _field_text(feed.get("link"), MAX_URL_CHARS)
    truncation = {
        "entries": total_matching > len(selected),
        "summaries": field_truncation["summary"] > 0,
        "summary_count": field_truncation["summary"],
        "title_count": field_truncation["title"],
        "link_count": field_truncation["link"],
        "id_count": field_truncation["id"],
    }
    return {
        "status": "partial" if truncation["entries"] else "ok",
        "source": requested_url,
        "source_final": final_url or requested_url,
        "feed": {"title": feed_title, "link": feed_link},
        "feed_type": str(parsed.get("version") or "unknown"),
        "entries": selected,
        "limit": limit,
        "since": since,
        "since_policy": "unknown_dates_excluded_when_since_is_set; included_without_since",
        "total_entries": len(entries),
        "matching_entries": total_matching,
        "date_unknown_count": unknown_count,
        "partial": bool(truncation["entries"]),
        "truncation": truncation,
        "parser": "feedparser",
        "parser_version": parser_version,
        "bozo": bozo,
    }


def fetch_feed(url: str, *, limit: int, since: str | None, timeout: float,
               etag: str | None = None, last_modified: str | None = None) -> dict[str, Any]:
    raw, headers, final_url, http_status = _fetch_response(
        url, timeout, etag=etag, last_modified=last_modified)
    validators = {"etag": headers.get("ETag"), "last_modified": headers.get("Last-Modified")}
    if http_status == 304:
        validators = {"etag": validators["etag"] or etag,
                      "last_modified": validators["last_modified"] or last_modified}
        return {"status": "unchanged", "source": url, "source_final": final_url,
                "http_status": 304, "validators": validators, "entries": []}
    result = parse_feed_bytes(raw, requested_url=url, final_url=final_url,
                              headers=headers, limit=limit, since=since)
    result.update(http_status=200, validators=validators)
    return result


def _emit(value: dict[str, Any]) -> int:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
    return 0 if value.get("status") in {"ok", "partial", "unchanged"} else 2


def main() -> int:
    _configure_stdio()
    payload: dict[str, Any] = {}
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("worker_payload_must_be_object")
        url = payload.get("url")
        limit = int(payload.get("limit", 5))
        since = payload.get("since")
        timeout = float(payload.get("timeout", 15))
        if not isinstance(url, str):
            raise ValueError("expected_public_feed_https_url")
        if not 1 <= limit <= 30:
            raise ValueError("limit_out_of_range")
        if not 1 <= timeout <= 60:
            raise ValueError("timeout_out_of_range")
        etag = payload.get("etag")
        last_modified = payload.get("last_modified")
        if any(value is not None and (not isinstance(value, str) or "\r" in value or "\n" in value or len(value) > 1024)
               for value in (etag, last_modified)):
            raise ValueError("conditional_header_invalid")
        result = fetch_feed(url, limit=limit, since=since, timeout=timeout,
                            etag=etag, last_modified=last_modified)
        return _emit(result)
    except FeedError as exc:
        return _emit({"status": "unavailable", "source": payload.get("url"), "entries": [], "reason": str(exc)})
    except ValueError as exc:
        return _emit({"status": "error", "source": payload.get("url"), "entries": [], "reason": str(exc)})
    except Exception:
        return _emit({"status": "error", "source": payload.get("url"), "entries": [], "reason": "feed_worker_error"})


if __name__ == "__main__":
    raise SystemExit(main())
