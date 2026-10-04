#!/usr/bin/env python3
"""Bounded, visible-DOM Bluesky retrieval through OpenCLI Browser Bridge."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from urllib.parse import quote, urlsplit


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def thread_url(value: str) -> tuple[str, str, str]:
    try:
        parsed = urlsplit(value)
    except ValueError:
        raise ValueError("expected_strict_bsky_post_url") from None
    match = re.fullmatch(r"/profile/([A-Za-z0-9.:-]+)/post/([A-Za-z0-9]+)", parsed.path)
    if (parsed.scheme != "https" or parsed.netloc != "bsky.app" or parsed.username is not None or
            parsed.password is not None or parsed.port is not None or parsed.query or parsed.fragment or not match):
        raise ValueError("expected_strict_bsky_post_url")
    return value, match.group(1), match.group(2)


def executable() -> tuple[str, list[str]]:
    """Run the installed OpenCLI JS entry directly to avoid shelling through a .cmd shim."""
    shim = shutil.which("opencli.cmd") or shutil.which("opencli")
    node = shutil.which("node")
    if not shim or not node:
        raise RuntimeError("opencli_or_node_not_found")
    from pathlib import Path
    main = Path(shim).resolve().parent / "node_modules" / "@jackwener" / "opencli" / "dist" / "src" / "main.js"
    if not main.is_file():
        raise RuntimeError("opencli_entry_not_found")
    return node, [str(main)]


class BrowserRun:
    def __init__(self, profile: str, timeout: float):
        if not profile or len(profile) > 128 or not re.fullmatch(r"[A-Za-z0-9_.-]+", profile):
            raise ValueError("invalid_browser_profile")
        if not 1 <= timeout <= 30:
            raise ValueError("timeout_must_be_1_to_30_seconds")
        self.profile = profile
        self.session = "fs-bsky-" + uuid.uuid4().hex
        self.started = time.monotonic()
        self.deadline = self.started + 87
        self.hard_deadline = self.started + 90
        self.step_timeout = min(30.0, timeout)
        self.base = executable()
        self.opened = False

    def call(self, *args: str) -> str:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("bluesky_browser_total_timeout")
        cmd = [self.base[0], *self.base[1], "--profile", self.profile, "browser", self.session, *args]
        try:
            run = subprocess.run(cmd, capture_output=True, text=True, timeout=min(30.0, self.step_timeout, remaining),
                                 encoding="utf-8", errors="replace", shell=False)
        except subprocess.TimeoutExpired:
            raise RuntimeError("bluesky_browser_step_timeout") from None
        if run.returncode:
            message = re.search(r"(?m)^\s*code:\s*([A-Z0-9_]+)", run.stderr)
            raise RuntimeError(message.group(1).lower() if message else f"opencli_exit_{run.returncode}")
        return run.stdout

    def open(self, url: str) -> None:
        self.opened = True
        self.call("open", url, "--window", "background")

    def eval(self, script: str):
        output = self.call("eval", script)
        # OpenCLI prints its evaluated value as JSON; tolerate fenced or labelled wrappers.
        start = output.find("{")
        end = output.rfind("}")
        if start < 0 or end < start:
            raise RuntimeError("opencli_eval_invalid_output")
        try:
            return json.loads(output[start:end + 1])
        except json.JSONDecodeError:
            raise RuntimeError("opencli_eval_invalid_json") from None

    def close(self) -> None:
        if self.opened:
            try:
                self.deadline = self.hard_deadline
                self.step_timeout = min(self.step_timeout, 3)
                self.call("close")
            except Exception:
                pass
            self.opened = False


SEARCH_CAPTURE = r'''(() => {
  const active = root => {
    if (!root || root.closest('[aria-hidden="true"], [hidden]')) return false;
    for (let e = root; e && e !== document.documentElement; e = e.parentElement) {
      const s = getComputedStyle(e), r = e.getBoundingClientRect();
      if (s.display === 'none' || s.visibility === 'hidden' || r.width <= 0 || r.height <= 0) return false;
    }
    return true;
  };
  const roots = [...document.querySelectorAll('[data-testid="searchScreen"]')].filter(active);
  const root = roots.at(-1);
  if (!root) return {ready:false, reason:'active_search_screen_missing', url:location.href};
  const records = [];
  for (const body of root.querySelectorAll('[data-testid="postText"]')) {
    const card = body.closest('[role="link"]');
    if (!card || !active(card)) continue;
    const outer = card.parentElement && card.parentElement.closest('[role="link"]');
    if (outer && root.contains(outer)) continue;
    const anchors = [...card.querySelectorAll('a[href]')];
    const post = anchors.find(a => {const u=new URL(a.href); return u.hostname === 'bsky.app' && !u.hash && !u.search && !a.getAttribute('href').startsWith('#') && /\/profile\/[^/]+\/post\/[^/]+$/.test(u.pathname);});
    if (!post) continue;
    const profile = anchors.find(a => /\/profile\/[^/]+$/.test(new URL(a.href).pathname) && (a.innerText || '').trim());
    const external = anchors.filter(a => { try { return new URL(a.href).hostname !== 'bsky.app'; } catch { return false; } })
      .map(a => ({url:a.href, text:(a.innerText || a.textContent || '').trim()}));
    records.push({source_url:post.href, url:post.href, text:(body.innerText || body.textContent || '').trim(),
      author:profile ? (profile.innerText || profile.textContent || '').trim() : null,
      author_handle:new URL(post.href).pathname.split('/')[2],
      timestamp_label:post.getAttribute('aria-label'), external_links:external,
      relation:'search_result', relation_known:true});
  }
  const empty = /No (?:posts|results) found|没有找到|未找到|找不到任何|找不到符合[^\n]*的结果/i.test(root.innerText || '');
  return {ready:records.length > 0 || empty,reason:records.length || empty ? null : 'search_results_not_ready',empty,url:location.href,records};
})()'''


THREAD_CAPTURE = r'''(target => {
  const active = root => {
    if (!root || root.closest('[aria-hidden="true"], [hidden]')) return false;
    for (let e = root; e && e !== document.documentElement; e = e.parentElement) {
      const s = getComputedStyle(e), r = e.getBoundingClientRect();
      if (s.display === 'none' || s.visibility === 'hidden' || r.width <= 0 || r.height <= 0) return false;
    }
    return true;
  };
  const screen = [...document.querySelectorAll('[data-testid="postThreadScreen"]')].filter(active).at(-1);
  if (!screen) return {ready:false,reason:'active_thread_screen_missing',url:location.href};
  const cards = [...screen.querySelectorAll('[data-testid^="postThreadItem-by-"]')].filter(active);
  const records = cards.map((card,index) => {
    const anchors = [...card.querySelectorAll('a[href]')];
    const exact = anchors.find(a => {const u=new URL(a.href); return u.hostname === 'bsky.app' && !u.hash && !u.search && !a.getAttribute('href').startsWith('#') && /\/profile\/[^/]+\/post\/[^/]+$/.test(u.pathname);});
    const action = anchors.find(a => new URL(a.href).hostname === 'bsky.app' && /\/(liked-by|reposted-by)\/?$/.test(new URL(a.href).pathname));
    const inferred = action ? action.href.replace(/\/(liked-by|reposted-by)\/?$/, '') : null;
    const bodies = [...card.querySelectorAll('[data-word-wrap="1"]')].map(e => (e.innerText || e.textContent || '').trim()).filter(Boolean);
    const profile = anchors.find(a => /\/profile\/[^/]+$/.test(new URL(a.href).pathname) && (a.innerText || '').trim());
    const source = inferred || (exact ? exact.href : null);
    return {source_url:source, url:source, text:bodies[0] || null,
      related_texts:bodies.slice(1).map(text => ({text,relation:'unknown_quoted_or_embedded_content'})),
      author:profile ? (profile.innerText || profile.textContent || '').trim() : null,
      author_handle:source ? new URL(source).pathname.split('/')[2] : null,
      timestamp_label:exact && exact.href === source ? exact.getAttribute('aria-label') : null,
      external_links:anchors.filter(a => { try { return new URL(a.href).hostname !== 'bsky.app'; } catch { return false; } })
        .map(a => ({url:a.href,text:(a.innerText || a.textContent || '').trim()})),
      kind:index === 0 ? 'thread_root_candidate' : 'thread_reply_candidate', relation_known:false,
      source_url_inferred:!!inferred};
  });
  return {ready:true,url:location.href,records,target};
})(__TARGET__)'''


def search(query: str, limit: int, timeout: float, profile: str, max_scrolls: int, sort: str = "top") -> dict:
    if not query.strip() or len(query) > 300:
        raise ValueError("query_must_be_nonempty_and_at_most_300_chars")
    if not 1 <= limit <= 10 or not 0 <= max_scrolls <= 3:
        raise ValueError("limit_must_be_1_to_10_and_max_scrolls_0_to_3")
    run = BrowserRun(profile, timeout)
    if sort not in ("top", "latest"):
        raise ValueError("unsupported_bluesky_sort")
    url = "https://bsky.app/search?q=" + quote(query, safe="")
    try:
        run.open(url)
        run.call("click", "--testid", "undefined-selector-1" if sort == "latest" else "undefined-selector-0")
        data = None
        for _ in range(3):
            data = run.eval(SEARCH_CAPTURE)
            if isinstance(data, dict) and data.get("ready"):
                break
            time.sleep(min(0.6, max(0.1, run.deadline - time.monotonic())))
        if not isinstance(data, dict) or not data.get("ready"):
            raise RuntimeError((data or {}).get("reason", "search_not_ready"))
        collected = {r["source_url"]: r for r in data.get("records", [])}
        for _ in range(max_scrolls):
            run.call("scroll", "down")
            data = run.eval(SEARCH_CAPTURE)
            for record in data.get("records", []):
                collected.setdefault(record["source_url"], record)
        records = list(collected.values())[:limit]
        return {"status":"partial", "source":"bluesky_visible_dom", "query":query, "url":url,
                "retrieved_at":now(), "records":records,
                "read":{"sort":sort, "limit":limit, "max_scrolls":max_scrolls,
                        "returned":len(records), "empty":bool(data.get("empty")), "complete":False, "coverage":"bounded rendered search results; census completeness unknown"},
                "upstream":{"capture":{"current_url":data.get("url"), "visible_dom_records":records}}}
    finally:
        run.close()


def thread(url: str, limit: int, timeout: float, profile: str) -> dict:
    canonical, handle, post_id = thread_url(url)
    if not 1 <= limit <= 10:
        raise ValueError("limit_must_be_1_to_10")
    run = BrowserRun(profile, timeout)
    try:
        run.open(canonical)
        script = THREAD_CAPTURE.replace("__TARGET__", json.dumps(canonical))
        data = None
        for _ in range(3):
            data = run.eval(script)
            if isinstance(data, dict) and data.get("ready"):
                break
            time.sleep(min(0.6, max(0.1, run.deadline - time.monotonic())))
        if not isinstance(data, dict) or not data.get("ready"):
            raise RuntimeError((data or {}).get("reason", "thread_not_ready"))
        records = data.get("records", [])
        root = next((r for r in records if r.get("source_url") == canonical), None)
        if root is None:
            raise RuntimeError("requested_thread_root_not_verified")
        root["kind"] = "thread_root"
        context = [r for r in records if r is not root][:limit]
        for record in context:
            record["kind"] = "thread_context"
        selected = [root, *context]
        return {"status":"partial", "source":"bluesky_visible_dom", "url":canonical, "retrieved_at":now(),
                "records":selected, "read":{"limit":limit, "returned_context":len(context), "complete":False,
                "coverage":"requested root verified; rendered surrounding context may include ancestors or replies; relationships and completeness unknown"},
                "upstream":{"capture":{"current_url":data.get("url"), "target":{"handle_or_did":handle,"post_id":post_id},
                                         "visible_dom_records":selected}}}
    finally:
        run.close()


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("search")
    p.add_argument("query"); p.add_argument("--limit", type=int, default=10); p.add_argument("--timeout", type=float, default=20)
    p.add_argument("--browser-profile", required=True); p.add_argument("--max-scrolls", type=int, default=0)
    p.add_argument("--sort", choices=("top", "latest"), default="top")
    t = sub.add_parser("thread")
    t.add_argument("url"); t.add_argument("--limit", type=int, default=10); t.add_argument("--timeout", type=float, default=20)
    t.add_argument("--browser-profile", required=True)
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.timeout <= 30:
            raise ValueError("timeout_must_be_1_to_30_seconds")
        result = search(args.query, args.limit, args.timeout, args.browser_profile, args.max_scrolls, args.sort) if args.command == "search" else thread(args.url, args.limit, args.timeout, args.browser_profile)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"status":"unavailable", "source":"bluesky_visible_dom", "reason":str(exc), "read":{"complete":False}}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
