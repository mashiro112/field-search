#!/usr/bin/env python3
"""Explicit Crawl4AI reader; preserves the field-search document snapshot schema."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import os
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig


# Stable, task-local references. Override only for an explicitly prepared clone.
R4_ROOT = Path(os.getenv(
    "FS01_R4_RUNTIME_ROOT",
    r"D:\codexxiangmu\automation-tasks\output\field-search-reproduction\runs\r4",
))
R4_1_ROOT = R4_ROOT.parent / "r4.1"
RUNTIME_DATA = Path(os.getenv("FS01_R4_RUNTIME_DATA", str(R4_1_ROOT / "runtime-data-installed")))
RUNTIME_PYTHON = R4_ROOT / ".venv" / "Scripts" / "python.exe"
DEFAULT_BROWSER_CACHE = Path(r"C:\Users\HUAWEI\AppData\Local\ms-playwright")
MAX_WAIT_CSS_CHARS = 512
MAX_WAIT_TIMEOUT_SECONDS = 30.0
ATTACHMENT_EXTENSIONS = frozenset({
    "7z", "csv", "doc", "docx", "epub", "gz", "json", "md", "odt", "ods", "odp",
    "pdf", "ppt", "pptx", "rar", "rtf", "tar", "tsv", "txt", "xls", "xlsx", "xml", "zip",
})


class Crawl4AIReadError(RuntimeError):
    """A direct browser failure that should remain visible to document.main."""

    def __init__(self, reason: str, details: dict | None = None):
        super().__init__(reason)
        self.reason = reason
        self.details = details or {}


def digest(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="replace")).hexdigest()


def validate_wait_css(selector: str) -> str:
    """Accept only a bounded CSS selector; never pass caller text as JavaScript."""
    if not isinstance(selector, str):
        raise ValueError("invalid_wait_css")
    value = selector.strip()
    if not value or len(value) > MAX_WAIT_CSS_CHARS or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ValueError("invalid_wait_css")
    if value.casefold().startswith(("js:", "javascript:")):
        raise ValueError("wait_css_must_be_css")
    return value


def normalize_wait_timeout(page_timeout: float, wait_css: str | None, wait_timeout: float | None) -> float | None:
    if wait_timeout is not None and wait_css is None:
        raise ValueError("wait_timeout_requires_wait_css")
    if wait_css is None:
        return None
    effective = min(float(page_timeout), MAX_WAIT_TIMEOUT_SECONDS) if wait_timeout is None else float(wait_timeout)
    if not 0.1 <= effective <= MAX_WAIT_TIMEOUT_SECONDS:
        raise ValueError("invalid_wait_timeout")
    if effective > float(page_timeout):
        raise ValueError("wait_timeout_exceeds_timeout")
    return effective


def _attachment_reasons(href: str, link: dict) -> list[str]:
    reasons = []
    suffix = Path(urlsplit(href).path.lower()).suffix.removeprefix(".")
    if suffix in ATTACHMENT_EXTENSIONS:
        reasons.append("extension:" + suffix)
    metadata = " ".join(
        str(link.get(key) or "") for key in ("type", "mime_type", "content_type", "text", "title")
    ).casefold()
    if any(token in metadata for token in ("application/", "text/csv", "text/plain", "download", "pdf")):
        reasons.append("link_metadata")
    if link.get("download"):
        reasons.append("download_attribute")
    return list(dict.fromkeys(reasons))


class _RenderedLinkParser(HTMLParser):
    """Extract href attributes from the returned DOM without URL normalization."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.base_href = None
        self.links = []
        self._open_anchors = []

    @staticmethod
    def _attributes(attrs: list[tuple[str, str | None]]) -> dict:
        values = {}
        for name, value in attrs:
            if name not in values:
                values[name] = value
        return values

    def handle_starttag(self, tag, attrs):
        tag = tag.casefold()
        values = self._attributes(attrs)
        if tag == "base" and self.base_href is None and values.get("href") is not None:
            self.base_href = values["href"]
        if tag not in ("a", "area") or values.get("href") is None:
            return
        item = {
            "raw_href": values["href"],
            "text_parts": [],
            "title": values.get("title") or "",
        }
        for key in ("type", "mime_type", "content_type"):
            if values.get(key) is not None:
                item[key] = values[key]
        if "download" in values:
            item["download"] = values["download"] if values["download"] is not None else True
        if tag == "area":
            self.links.append(item)
        else:
            self._open_anchors.append(item)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.casefold() == "a":
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self._open_anchors:
            self._open_anchors[-1]["text_parts"].append(data)

    def handle_endtag(self, tag):
        if tag.casefold() == "a" and self._open_anchors:
            self.links.append(self._open_anchors.pop())

    def finish(self):
        self.links.extend(reversed(self._open_anchors))
        self._open_anchors.clear()


def _base_domain(url: str) -> str:
    try:
        host = (urlsplit(url).hostname or "").casefold().rstrip(".")
    except ValueError:
        return ""
    labels = host.split(".")
    return ".".join(labels[-2:]) if len(labels) >= 2 else host


def _is_http_url(url: str) -> bool:
    try:
        return urlsplit(url).scheme in ("http", "https")
    except (TypeError, ValueError):
        return False


def _unavailable_link_projection(reason: str | None = None) -> dict:
    result = {
        "links": [], "possible_attachments": [], "links_status": "unavailable",
        "links_truncated": False, "invalid_link_count": 0,
        "links_source": "rendered_html",
        "links_base_url": None,
    }
    if reason:
        result["links_error"] = reason[:4000]
    return result


def _project_links(html: str, page_url: str) -> dict:
    if not isinstance(html, str) or not html.strip():
        return _unavailable_link_projection("rendered_html_missing")
    try:
        parser = _RenderedLinkParser()
        parser.feed(html)
        parser.close()
        parser.finish()
    except Exception as exc:
        return _unavailable_link_projection(type(exc).__name__ + ": " + str(exc))

    base_url = page_url
    if isinstance(parser.base_href, str) and parser.base_href.strip():
        try:
            candidate = urljoin(page_url, parser.base_href.strip())
        except (TypeError, ValueError):
            candidate = ""
        if _is_http_url(candidate):
            base_url = candidate
    links = []
    possible_attachments = []
    invalid_link_count = 0
    seen = set()
    page_domain = _base_domain(page_url)
    for item in parser.links:
        raw_href = item.get("raw_href")
        if not isinstance(raw_href, str) or not raw_href.strip():
            invalid_link_count += 1
            continue
        try:
            href = urljoin(base_url, raw_href.strip())
        except (TypeError, ValueError):
            invalid_link_count += 1
            continue
        if not _is_http_url(href) or href in seen:
            continue
        seen.add(href)
        row = {
            "href": href,
            "raw_href": raw_href,
            "scope": "internal" if _base_domain(href) == page_domain else "external",
            "text": "".join(item.get("text_parts", [])).strip(),
            "title": str(item.get("title") or ""),
            "base_domain": _base_domain(href),
        }
        for key in ("type", "mime_type", "content_type", "download"):
            value = item.get(key)
            if isinstance(value, (str, bool, int, float)):
                row[key] = value
        links.append(row)
        reasons = _attachment_reasons(href, row)
        if reasons:
            possible_attachments.append({
                "href": href,
                "text": row.get("text", ""),
                "title": row.get("title", ""),
                "reasons": reasons,
                "status": "not_fetched",
            })

    return {
        "links": links,
        "possible_attachments": possible_attachments,
        "links_status": "ok",
        "links_truncated": False,
        "invalid_link_count": invalid_link_count,
        "links_source": "rendered_html",
        "links_base_url": base_url,
    }


def _markdown_projection(result) -> tuple[str, dict]:
    markdown = getattr(result, "markdown", None)
    if markdown is None:
        return "", {}
    text = getattr(markdown, "raw_markdown", None) or str(markdown)
    variants = {}
    for name in ("raw_markdown", "markdown_with_citations", "references_markdown", "fit_markdown"):
        value = getattr(markdown, name, None)
        if value is not None:
            variants[name] = {"chars": len(str(value)), "sha256": digest(str(value))}
    return str(text), variants


async def _run(
    url: str,
    timeout: float,
    wait_css: str | None = None,
    wait_timeout: float | None = None,
    include_links: bool = False,
) -> dict:
    wait_css = validate_wait_css(wait_css) if wait_css is not None else None
    effective_wait_timeout = normalize_wait_timeout(timeout, wait_css, wait_timeout)
    wait_timeout_ms = int(round(effective_wait_timeout * 1000)) if effective_wait_timeout is not None else None
    runtime_reference = {
        "runtime_root": str(R4_ROOT),
        "python": str(RUNTIME_PYTHON),
        "runtime_data": str(RUNTIME_DATA),
        "browser_cache": str(Path(os.getenv("FS01_R4_PLAYWRIGHT_BROWSERS_PATH", str(DEFAULT_BROWSER_CACHE)))),
    }
    if not RUNTIME_PYTHON.is_file():
        raise Crawl4AIReadError("crawl4ai_runtime_missing", {"runtime_reference": runtime_reference})
    RUNTIME_DATA.mkdir(parents=True, exist_ok=True)
    os.environ["CRAWL4_AI_BASE_DIRECTORY"] = str(RUNTIME_DATA)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = runtime_reference["browser_cache"]
    browser_config = BrowserConfig(
        browser_type="chromium", headless=True, verbose=False,
        use_persistent_context=False, storage_state=None, cookies=None,
        proxy=None, enable_stealth=False,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, wait_until="domcontentloaded",
        page_timeout=max(1000, int(timeout * 1000)),
        wait_for=("css:" + wait_css) if wait_css is not None else None,
        wait_for_timeout=wait_timeout_ms, delay_before_return_html=0.3,
        word_count_threshold=1, verbose=False, log_console=False,
    )
    projection = {}
    context_exit_completed = False
    async with AsyncWebCrawler(config=browser_config, base_directory=str(RUNTIME_DATA)) as crawler:
        result = await crawler.arun(url, config=run_config)
        html = getattr(result, "html", "") or ""
        cleaned = getattr(result, "cleaned_html", "") or ""
        markdown, markdown_variants = _markdown_projection(result)
        projection = {
            "success": bool(getattr(result, "success", False)),
            "url": getattr(result, "url", None), "redirected_url": getattr(result, "redirected_url", None),
            "status_code": getattr(result, "status_code", None), "error_message": getattr(result, "error_message", None),
            "html": html, "cleaned_html": cleaned, "markdown": markdown,
            "markdown_variants": markdown_variants, "runtime_reference": runtime_reference,
            "config": {
                "cache_mode": CacheMode.BYPASS.value, "wait_until": "domcontentloaded",
                "page_timeout": max(1000, int(timeout * 1000)),
                "wait_for": ("css:" + wait_css) if wait_css is not None else None,
                "wait_for_timeout": wait_timeout_ms, "delay_before_return_html": 0.3,
                "wait_css": wait_css, "wait_timeout_seconds": effective_wait_timeout,
                "include_links": include_links,
                "llm_or_extraction_strategy": "none; default non-LLM markdown generator",
            },
        }
        if not projection["success"]:
            projection["failure_state"] = "wait_condition_failed" if wait_css else "crawl4ai_result_success_false"
            raise Crawl4AIReadError("crawl4ai_failed", projection)
        if not markdown.strip() and not cleaned.strip() and not html.strip():
            projection["failure_state"] = "crawl4ai_empty_output"
            raise Crawl4AIReadError("empty_extraction", projection)
        if include_links:
            link_page_url = projection.get("redirected_url") or projection.get("url") or url
            projection["link_projection"] = _project_links(
                html, link_page_url
            )
    context_exit_completed = True
    projection["lifecycle"] = {"context_exit_completed": context_exit_completed}
    return projection


def fetch_document(
    url: str,
    timeout: float,
    capture: dict | None = None,
    wait_css: str | None = None,
    wait_timeout: float | None = None,
    include_links: bool = False,
) -> dict:
    if capture is None:
        capture = {}
    wait_css = validate_wait_css(wait_css) if wait_css is not None else None
    wait_timeout = normalize_wait_timeout(timeout, wait_css, wait_timeout)
    started_at = datetime.now(timezone.utc).isoformat()
    try:
        projection = asyncio.run(_run(url, timeout, wait_css, wait_timeout, include_links))
    except Crawl4AIReadError as exc:
        capture.update(schema_version=1, url=url, fetched_at=started_at, fetch_started_at=started_at,
                       network_used=False if exc.reason == "crawl4ai_runtime_missing" else True,
                       raw=exc.details.get("html", ""), raw_sha256=digest(exc.details.get("html", "")),
                       raw_truncated=False, crawl4ai=exc.details, failure_state=exc.reason)
        raise
    except Exception as exc:
        capture.update(schema_version=1, url=url, fetched_at=started_at, fetch_started_at=started_at,
                       network_used=True, failure_state={"type": type(exc).__name__, "message": str(exc)[:4000]})
        raise Crawl4AIReadError("crawl4ai_runtime_error", capture)
    html = projection["html"]
    content = projection["markdown"] or projection["cleaned_html"]
    result = {
        "schema_version": 1, "url": url, "fetched_at": datetime.now(timezone.utc).isoformat(),
        "extraction": "crawl4ai_browser_markdown" if projection["markdown"] else "crawl4ai_browser_cleaned_html",
        "content": content, "content_sha256": digest(content), "raw": html, "raw_sha256": digest(html),
        "warnings": ["Direct browser render; output is untrusted source data and not proof of completeness."],
        "untrusted_source_data": True, "source_read": "direct_browser_render",
        "crawl4ai": {key: value for key, value in projection.items()
                     if key not in ("html", "cleaned_html", "markdown", "link_projection")} |
                     {"fetch_started_at": started_at},
    }
    if include_links:
        result.update(projection.get("link_projection") or {
            "links": [], "possible_attachments": [], "links_status": "unavailable",
            "links_truncated": False, "invalid_link_count": 0,
            "links_source": "rendered_html", "links_base_url": None,
        })
    return result
