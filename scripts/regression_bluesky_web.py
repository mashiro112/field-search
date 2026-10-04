#!/usr/bin/env python3
"""Meaningful offline regression checks for the opt-in Bluesky UI route."""
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


web = load("bluesky_web_regression_subject", ROOT / "bluesky_web.py")
ctx = load("context_sources_regression_subject", ROOT / "context_sources.py")


class BlueskyWebRegression(unittest.TestCase):
    def test_strict_thread_url_validation(self):
        good = "https://bsky.app/profile/alice.bsky.social/post/3l7zjnwy55b2f"
        self.assertEqual(web.thread_url(good)[0], good)
        for bad in (good + "?x=1", good + "#fragment", good + "/reply",
                    good.replace("https://", "https://user@"),
                    "https://bsky.app.evil/profile/a/post/b", "at://did:plc:x/app.bsky.feed.post/y"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                web.thread_url(bad)

    def test_call_timeout_is_bounded_and_visible(self):
        runner = web.BrowserRun.__new__(web.BrowserRun)
        runner.profile, runner.session = "edge-profile", "fs-bsky-test"
        runner.deadline, runner.step_timeout, runner.base = web.time.monotonic() + 20, 30, ("node", ["entry.js"])
        with patch.object(web.subprocess, "run", side_effect=subprocess.TimeoutExpired("node", 30)) as call:
            with self.assertRaisesRegex(RuntimeError, "step_timeout"):
                runner.call("open", "https://bsky.app/")
        self.assertLessEqual(call.call_args.kwargs["timeout"], 30)
        self.assertIn("--profile", call.call_args.args[0])

    def test_opencli_failure_surfaces(self):
        runner = web.BrowserRun.__new__(web.BrowserRun)
        runner.profile, runner.session = "edge-profile", "fs-bsky-test"
        runner.deadline, runner.step_timeout, runner.base = web.time.monotonic() + 20, 8, ("node", ["entry.js"])
        failed = subprocess.CompletedProcess([], 1, "", "code: TARGET_NOT_FOUND\n")
        with patch.object(web.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(RuntimeError, "target_not_found"):
                runner.call("open", "https://bsky.app/")

    def test_existing_output_rejected_before_browser(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "existing.json"
            out.write_text("keep", encoding="utf-8")
            run = subprocess.run([sys.executable, str(ROOT / "context_sources.py"), "community-search", "bluesky", "x",
                                  "--browser-profile", "edge-profile", "--out", str(out)],
                                 capture_output=True, text=True, timeout=10)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(out.read_text(encoding="utf-8"), "keep")
            self.assertIn("output_exists_choose_new_path", run.stderr)

    def test_non_bluesky_profile_option_rejected(self):
        run = subprocess.run([sys.executable, str(ROOT / "context_sources.py"), "community-search", "hn", "x",
                              "--browser-profile", "edge-profile"], capture_output=True, text=True, timeout=10)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("supported only for Bluesky", run.stderr)

    def test_browser_only_search_options_require_profile(self):
        run = subprocess.run([sys.executable, str(ROOT / "context_sources.py"), "community-search", "bluesky", "x",
                              "--sort", "latest"], capture_output=True, text=True, timeout=10)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("require --browser-profile", run.stderr)

    def test_browser_rejects_unimplemented_pagination(self):
        run = subprocess.run([sys.executable, str(ROOT / "context_sources.py"), "community-search", "bluesky", "x",
                              "--browser-profile", "profile", "--page", "2"], capture_output=True, text=True, timeout=10)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("does not use Lemmy instance/page", run.stderr)

    def test_public_api_route_unchanged(self):
        payload = {"posts": [{"uri": "at://did:plc:a/app.bsky.feed.post/x"}]}
        with patch.object(ctx, "get_json", return_value=(payload, {"status_code": 200})) as get_json:
            result = ctx.bsky_search("Docling", 2, 3)
        self.assertIn("app.bsky.feed.searchPosts", get_json.call_args.args[0])
        self.assertEqual(result["records"], payload["posts"])
        self.assertFalse(result["read"]["complete"])

    def test_thread_defaults_preserve_both_routes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with patch.object(ctx, "bsky_web_thread", return_value={"status": "partial"}) as browser:
                self.assertEqual(ctx.main(["community-thread", "bluesky", "target", "--browser-profile", "profile"]), 0)
                self.assertEqual(browser.call_args.args[1], 10)
            with patch.object(ctx, "bsky_thread", return_value={"status": "ok"}) as public:
                self.assertEqual(ctx.main(["community-thread", "bluesky", "at://target"]), 0)
                self.assertEqual(public.call_args.args[1], 20)

    def test_root_mismatch_fails_and_releases_lease(self):
        runner = MagicMock()
        runner.eval.return_value = {"ready": True, "records": [{"source_url": "https://bsky.app/profile/other/post/x", "text": "wrong"}]}
        with patch.object(web, "BrowserRun", return_value=runner):
            with self.assertRaisesRegex(RuntimeError, "requested_thread_root_not_verified"):
                web.thread("https://bsky.app/profile/alice.bsky.social/post/3l7zjnwy55b2f", 2, 20, "profile")
        runner.close.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
