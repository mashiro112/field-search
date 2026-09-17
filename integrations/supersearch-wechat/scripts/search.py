#!/usr/bin/env python3

import argparse
import http.cookiejar
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Callable, Optional, TypedDict


SEARCH_URL: str = "https://weixin.sogou.com/weixin?type=2&query="
USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
)


class SearchResult(TypedDict):
    title: str
    account: str
    published_at: str
    summary: str
    sogou_url: str


class ResolvedSearchResult(SearchResult):
    url: str


class SearchResponse(TypedDict):
    search_executed: bool
    fallback: Optional[str]
    results: list[ResolvedSearchResult]


class _ResultParser(HTMLParser):
    def __init__(self, limit: int) -> None:
        super().__init__(convert_charrefs=True)
        self.limit: int = limit
        self.results: list[SearchResult] = []
        self.current: Optional[dict[str, str]] = None
        self.capture: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attributes: dict[str, str] = {
            key: value or "" for key, value in attrs
        }
        element_id: str = attributes.get("id", "")

        if tag == "li" and element_id.startswith("sogou_vr_11002601_box_"):
            self.current = {
                "title": "",
                "account": "",
                "published_at": "",
                "summary": "",
                "sogou_url": "",
            }
            return

        if self.current is None:
            return

        if tag == "a" and element_id.startswith("sogou_vr_11002601_title_"):
            self.capture = "title"
            href: str = attributes.get("href", "")
            absolute_url: str = urllib.parse.urljoin("https://weixin.sogou.com", href)
            self.current["sogou_url"] = urllib.parse.quote(
                absolute_url,
                safe=":/?&=%#[]@!$'()*+,;-._~",
            )
            return

        if tag == "p" and element_id.startswith("sogou_vr_11002601_summary_"):
            self.capture = "summary"
            return

        classes: list[str] = attributes.get("class", "").split()
        if tag == "span" and "all-time-y2" in classes:
            self.capture = "account"

    def handle_endtag(self, tag: str) -> None:
        if self.current is None:
            return

        if tag in {"a", "p", "span"}:
            self.capture = None

        if tag == "li":
            result: SearchResult = SearchResult(
                title=_clean_text(self.current["title"]),
                account=_clean_text(self.current["account"]),
                published_at=self.current["published_at"],
                summary=_clean_text(self.current["summary"]),
                sogou_url=self.current["sogou_url"],
            )
            if result["title"] and len(self.results) < self.limit:
                self.results.append(result)
            self.current = None
            self.capture = None

    def handle_data(self, data: str) -> None:
        if self.current is None:
            return

        if self.capture is not None:
            self.current[self.capture] += data

        match: Optional[re.Match[str]] = re.search(r"timeConvert\(['\"](\d+)['\"]\)", data)
        if match is not None:
            timestamp: int = int(match.group(1))
            self.current["published_at"] = datetime.fromtimestamp(
                timestamp,
                timezone.utc,
            ).isoformat()


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def parse_search_results(source: str, limit: int) -> list[SearchResult]:
    parser: _ResultParser = _ResultParser(limit)
    parser.feed(source)
    return parser.results


def parse_redirect_url(source: str) -> str:
    fragments: list[str] = re.findall(r"url\s*\+=\s*['\"]([^'\"]+)['\"]", source)
    if not fragments:
        raise ValueError("WeChat redirect URL not found")
    return "".join(fragments).replace("&amp;", "&")


def _http_fetcher() -> Callable[[str], str]:
    cookie_jar: http.cookiejar.CookieJar = http.cookiejar.CookieJar()
    opener: urllib.request.OpenerDirector = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar)
    )

    def fetch(url: str) -> str:
        request: urllib.request.Request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT},
        )
        with opener.open(request, timeout=20) as response:
            body: bytes = response.read()
            charset: Optional[str] = response.headers.get_content_charset()
            return body.decode(charset or "utf-8", errors="replace")

    return fetch


def _fetch_with_retry(fetch: Callable[[str], str], url: str) -> str:
    for retry in range(4):
        try:
            return fetch(url)
        except Exception:
            if retry == 3:
                raise
        time.sleep(1)


def search(
    query: str,
    limit: int = 5,
    fetch: Optional[Callable[[str], str]] = None,
) -> SearchResponse:
    get: Callable[[str], str] = fetch or _http_fetcher()
    source: str = _fetch_with_retry(get, SEARCH_URL + urllib.parse.quote(query))
    blocked_markers: tuple[str, ...] = (
        "\u8bf7\u8f93\u5165\u9a8c\u8bc1\u7801",
        "\u8bbf\u95ee\u8fc7\u4e8e\u9891\u7e41",
        "antispider",
    )
    blocked: bool = any(marker in source for marker in blocked_markers)
    if blocked:
        return {"search_executed": False, "fallback": "browser", "results": []}

    parsed_results: list[SearchResult] = parse_search_results(source, limit)
    resolved_results: list[ResolvedSearchResult] = []
    for item in parsed_results:
        redirect_source: str = _fetch_with_retry(get, item["sogou_url"])
        article_url: str = parse_redirect_url(redirect_source)
        resolved: ResolvedSearchResult = ResolvedSearchResult(**item, url=article_url)
        resolved_results.append(resolved)

    return {
        "search_executed": True,
        "fallback": None,
        "results": resolved_results,
    }


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    arguments: argparse.Namespace = parser.parse_args()
    response: SearchResponse = search(arguments.query, arguments.limit)
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
