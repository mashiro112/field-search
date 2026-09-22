"""Bounded, read-only discovery of llms.txt, sitemaps and feed links."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET

try:
    import feed_worker
except ImportError:  # pragma: no cover
    from . import feed_worker  # type: ignore

MAX_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
MAX_LIMIT = 100
MAX_BUDGET = 8
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
LINK_START_RE = re.compile(r"^\s*-\s*\[([^\]]+)\]\(")


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str, str]] = []
        self._title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {k.casefold(): v or "" for k, v in attrs}
        if tag.casefold() == "title":
            self._in_title = True
        if tag.casefold() in {"a", "link"} and values.get("href"):
            rel = values.get("rel", "")
            typ = values.get("type", "")
            self.links.append((values["href"], rel, typ))

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title += data


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _result_hash(value: dict[str, object]) -> str:
    return _sha({k: v for k, v in value.items() if k not in {"result_sha256", "output_file", "reused", "network_used"}})


def _same_origin(base: str, target: str) -> bool:
    a, b = urlsplit(base), urlsplit(target)
    return (a.scheme.casefold(), a.hostname.casefold() if a.hostname else "", a.port or 443) == (b.scheme.casefold(), b.hostname.casefold() if b.hostname else "", b.port or 443)


def _candidate(url: str, source: str, kind: str, title: str | None = None, external: bool = False, description: str | None = None) -> dict[str, object]:
    value: dict[str, object] = {"url": url, "kind": kind, "source": source, "title": (title or "")[:500] or None, "external": external}
    if description:
        value["description"] = description[:2000]
    if len(url) > 2048:
        value["url"] = None
        value["url_omitted"] = True
    return value


def _parse_llms(raw: bytes, base: str, contains: str | None) -> list[dict[str, object]]:
    text = raw.decode("utf-8", errors="replace")
    probe = text.lstrip("\ufeff \t\r\n").casefold()
    if probe.startswith("<!doctype html") or probe.startswith("<html") or "<title>404" in probe[:2048]:
        raise ValueError("llms_html_or_error_page")
    found = []
    for line in text.splitlines():
        match = LINK_START_RE.match(line)
        if not match:
            continue
        title = match.group(1)
        rest = line[match.end():]
        if rest.startswith("<"):
            end = rest.find(">")
            if end < 0:
                continue
            href, rest = rest[1:end], rest[end + 1:]
        else:
            depth = 0
            end = -1
            for index, char in enumerate(rest):
                if char == "(":
                    depth += 1
                elif char == ")":
                    if depth == 0:
                        end = index
                        break
                    depth -= 1
            if end < 0:
                continue
            href, rest = rest[:end].strip(), rest[end + 1:]
        note = rest.split(":", 1)[1].strip() if ":" in rest else None
        absolute = urljoin(base, href)
        if urlsplit(absolute).scheme not in {"http", "https"}:
            continue
        if contains and contains.casefold() not in (title + " " + (note or "") + " " + absolute).casefold():
            continue
        found.append(_candidate(absolute, base, "llms", title, external=not _same_origin(base, absolute), description=note))
    return found


def _parse_sitemap(raw: bytes, base: str) -> tuple[list[dict[str, object]], list[str], str]:
    if b"<!DOCTYPE" in raw.upper():
        raise ValueError("xml_dtd_rejected")
    root = ET.fromstring(raw)
    tag = root.tag.rsplit("}", 1)[-1].casefold()
    if tag not in {"urlset", "sitemapindex"}:
        raise ValueError("xml_root_not_sitemap")
    links: list[dict[str, object]] = []
    children: list[str] = []
    for parent in list(root):
        parent_tag = parent.tag.rsplit("}", 1)[-1].casefold()
        if parent_tag not in ({"url"} if tag == "urlset" else {"sitemap"}):
            continue
        node = next((child for child in list(parent) if child.tag.rsplit("}", 1)[-1].casefold() == "loc" and child.text), None)
        if node is None or not node.text:
            continue
        target = urljoin(base, node.text.strip())
        if urlsplit(target).scheme not in {"http", "https"}:
            continue
        if tag == "sitemapindex":
            children.append(target)
        else:
            links.append(_candidate(target, base, "sitemap"))
    return links, children, tag


def _parse_html(raw: bytes, base: str, contains: str | None) -> list[dict[str, object]]:
    parser = LinkParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    found = []
    for href, rel, typ in parser.links:
        absolute = urljoin(base, href)
        if urlsplit(absolute).scheme not in {"http", "https"}:
            continue
        hint = (rel + " " + typ + " " + absolute).casefold()
        if "alternate" not in rel.casefold() and not any(x in hint for x in ("rss", "atom", "feed")):
            continue
        if contains and contains.casefold() not in absolute.casefold():
            continue
        found.append(_candidate(absolute, base, "feed" if any(x in hint for x in ("rss", "atom", "feed")) else "document", external=not _same_origin(base, absolute)))
    return found


def discover(url: str, kind: str, limit: int, contains: str | None, budget: int, timeout: float) -> dict[str, object]:
    base = feed_worker._validate_url(url)
    root = f"{base.scheme}://{base.netloc}"
    path = urlsplit(url).path.casefold()
    initial_kind = kind
    if kind == "auto":
        initial_kind = "llms" if path.endswith("/llms.txt") else "sitemap" if path.endswith("/sitemap.xml") else "html"
    queue: list[tuple[str, str]] = [(url, initial_kind)]
    if kind == "auto":
        parsed = urlsplit(url)
        if parsed.path.endswith("/"):
            scope_path = parsed.path
        else:
            scope_path = parsed.path.rsplit("/", 1)[0] + "/" if "/" in parsed.path else "/"
        scope = parsed._replace(path=scope_path, query="", fragment="").geturl()
        if initial_kind == "html":
            queue.extend((urljoin(scope, p), k) for p, k in (("llms.txt", "llms"), ("robots.txt", "robots"), ("sitemap.xml", "sitemap")))
    fetched: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    candidates: list[dict[str, object]] = []
    seen: set[str] = set()
    attempts = 0
    while queue and attempts < budget:
        target, current_kind = queue.pop(0)
        if target in seen:
            continue
        seen.add(target)
        attempts += 1
        try:
            raw, headers, final = feed_worker._fetch_bytes(target, timeout)
            if current_kind == "llms":
                parsed_candidates = _parse_llms(raw, final, contains)
                candidates.extend(parsed_candidates)
            elif current_kind == "sitemap":
                links, children, root_tag = _parse_sitemap(raw, final)
                candidates.extend(links)
                if root_tag == "sitemapindex":
                    queue.extend((child, "sitemap") for child in children if _same_origin(root, child))
            elif current_kind in {"html", "auto", "feeds"}:
                parsed_candidates = _parse_html(raw, final, contains)
                candidates.extend(parsed_candidates)
            elif current_kind == "robots":
                for line in raw.decode("utf-8", errors="replace").splitlines():
                    if line.casefold().startswith("sitemap:"):
                        child = urljoin(final, line.split(":", 1)[1].strip())
                        if _same_origin(root, child):
                            queue.append((child, "sitemap"))
            fetched.append({"url": target, "final_url": final, "kind": current_kind, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        except Exception as exc:
            failures.append({"url": target, "kind": current_kind, "reason": str(exc) or "fetch_failed"})
    unique: list[dict[str, object]] = []
    seen_urls: set[str] = set()
    for item in candidates:
        target = str(item.get("url"))
        if target in seen_urls:
            continue
        seen_urls.add(target)
        unique.append(item)
    if contains:
        needle = contains.casefold()
        unique = [item for item in unique if needle in str(item.get("url") or "").casefold() or needle in str(item.get("title") or "").casefold() or needle in str(item.get("description") or "").casefold()]
    total_matching = len(unique)
    truncated = total_matching > limit
    unique = unique[:limit]
    pending_total = len(queue)
    pending = [{"url": u, "kind": k} for u, k in queue[:limit]]
    if not fetched and failures:
        status = "error"
    elif queue or failures or truncated:
        status = "partial"
    elif not unique:
        status = "no_results"
    else:
        status = "ok"
    return {"status": status, "source": url, "kind": kind, "candidates": unique, "total_matching": total_matching, "truncated": truncated, "fetched": fetched, "unvisited": pending, "pending_count": pending_total, "failures": failures, "partial": status == "partial", "limit": limit, "request_budget": budget, "attempts_count": attempts, "fetched_count": len(fetched), "fetched_at": _now()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--kind", choices=("auto", "llms", "sitemap", "feeds"), default="auto")
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--contains")
    parser.add_argument("--request-budget", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= MAX_LIMIT or not 1 <= args.request_budget <= MAX_BUDGET or not 1 <= args.timeout <= 60:
        parser.error("limit, request-budget or timeout out of range")
    request_key = _sha({"url": args.url, "kind": args.kind, "limit": args.limit, "contains": args.contains, "request_budget": args.request_budget})
    try:
        if args.out and Path(args.out).exists():
            if not Path(args.out).is_file():
                raise ValueError("cache_path_not_file")
            if Path(args.out).stat().st_size > 4 * 1024 * 1024:
                raise ValueError("cache_too_large")
            try:
                value = json.loads(Path(args.out).read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                raise ValueError("cache_invalid_json") from None
            if not isinstance(value, dict) or value.get("request_sha256") != request_key or value.get("result_sha256") != _result_hash(value):
                raise ValueError("cache_invalid_or_conflicting")
            value["reused"] = True
            value["network_used"] = False
            print(json.dumps(value, ensure_ascii=False))
            return 0 if value.get("status") in {"ok", "partial", "no_results"} else 2
        result = discover(args.url, args.kind, args.limit, args.contains, args.request_budget, args.timeout)
        result["request_sha256"] = request_key
        result["network_used"] = True
        if args.out:
            path = Path(args.out)
            path.parent.mkdir(parents=True, exist_ok=True)
            result["output_file"] = str(path.resolve())
        result["result_sha256"] = _result_hash(result)
        if args.out:
            with path.open("x", encoding="utf-8") as handle:
                json.dump(result, handle, ensure_ascii=False, separators=(",", ":"))
                handle.write("\n")
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] in {"ok", "partial", "no_results"} else 2
    except Exception as exc:
        result = {"status": "error", "source": args.url, "candidates": [], "fetched": [], "failures": [], "reason": str(exc) or "discovery_error", "network_used": False}
        print(json.dumps(result, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
