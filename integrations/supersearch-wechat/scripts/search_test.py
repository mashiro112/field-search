import unittest
import urllib.error
from unittest.mock import patch

from search import parse_redirect_url, parse_search_results, search


SEARCH_HTML: str = """
<html><body><ul class="news-list">
  <li id="sogou_vr_11002601_box_0">
    <a href="/link?url=abc&amp;type=2&amp;query=DeepSeek V4 Flash" id="sogou_vr_11002601_title_0">
      <em>DeepSeek</em> V4 Flash Review
    </a>
    <p id="sogou_vr_11002601_summary_0">Fast for simple work but weaker on complex tasks.</p>
    <span class="all-time-y2">Test Account</span>
    <script>document.write(timeConvert('1785594723'))</script>
  </li>
</ul></body></html>
"""

REDIRECT_HTML: str = """
<script>
var url = '';
url += 'https://mp.';
url += 'weixin.qq.com/s?src=11&amp;timestamp=123&amp;signature=abc';
window.location.replace(url);
</script>
"""


class WeChatSearchTest(unittest.TestCase):
    def test_parses_search_result_fields(self) -> None:
        results: list[dict[str, str]] = parse_search_results(SEARCH_HTML, 5)

        self.assertEqual(results, [{
            "title": "DeepSeek V4 Flash Review",
            "account": "Test Account",
            "published_at": "2026-08-01T14:32:03+00:00",
            "summary": "Fast for simple work but weaker on complex tasks.",
            "sogou_url": "https://weixin.sogou.com/link?url=abc&type=2&query=DeepSeek%20V4%20Flash",
        }])

    def test_parses_fragmented_wechat_redirect(self) -> None:
        url: str = parse_redirect_url(REDIRECT_HTML)

        self.assertEqual(
            url,
            "https://mp.weixin.qq.com/s?src=11&timestamp=123&signature=abc",
        )

    def test_returns_browser_fallback_for_captcha(self) -> None:
        def fetch(_url: str) -> str:
            return "\u8bbf\u95ee\u8fc7\u4e8e\u9891\u7e41\uff0c\u8bf7\u8f93\u5165\u9a8c\u8bc1\u7801"

        result: dict[str, object] = search("DeepSeek", fetch=fetch)

        self.assertEqual(result["search_executed"], False)
        self.assertEqual(result["fallback"], "browser")
        self.assertEqual(result["results"], [])

    def test_resolves_article_urls(self) -> None:
        responses: list[str] = [SEARCH_HTML, REDIRECT_HTML]

        def fetch(_url: str) -> str:
            response: str = responses.pop(0)
            return response

        result: dict[str, object] = search("DeepSeek V4 Flash", fetch=fetch)
        results: list[dict[str, str]] = result["results"]  # type: ignore[assignment]

        self.assertEqual(result["search_executed"], True)
        self.assertEqual(
            results[0]["url"],
            "https://mp.weixin.qq.com/s?src=11&timestamp=123&signature=abc",
        )

    @patch("search.time.sleep")
    def test_retries_transient_request_failures_three_times(self, _sleep: object) -> None:
        request_count: int = 0

        def fetch(_url: str) -> str:
            nonlocal request_count
            request_count += 1
            if request_count < 4:
                raise urllib.error.URLError("Unavailable")
            return "<html></html>"

        result: dict[str, object] = search("DeepSeek V4 Flash", fetch=fetch)

        self.assertEqual(request_count, 4)
        self.assertEqual(result["search_executed"], True)

    @patch("search.time.sleep")
    def test_retries_forbidden_responses_three_times(self, _sleep: object) -> None:
        request_count: int = 0

        def fetch(_url: str) -> str:
            nonlocal request_count
            request_count += 1
            if request_count < 4:
                raise urllib.error.HTTPError(
                    "https://weixin.sogou.com",
                    403,
                    "Forbidden",
                    {},
                    None,
                )
            return "<html></html>"

        result: dict[str, object] = search("DeepSeek V4 Flash", fetch=fetch)

        self.assertEqual(request_count, 4)
        self.assertEqual(result["search_executed"], True)


if __name__ == "__main__":
    unittest.main()
