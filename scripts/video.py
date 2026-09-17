"""Explicit YouTube caption retrieval with timestamp search.

This is a thin bridge to an isolated youtube-transcript-api runtime.  The
route deliberately does not download media, use cookies, invoke ASR, or
silently fall back to a paid transcription service.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib import parse
from typing import Any, Sequence

import runtime_config


SKILL_ROOT = Path(__file__).resolve().parents[1]
WORKER = Path(__file__).with_name("video_worker.py")
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
ALLOWED_ENV = {
    "SYSTEMROOT",
    "WINDIR",
    "TEMP",
    "TMP",
    "PATH",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
}


def _safe_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key.upper() in ALLOWED_ENV}
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    return env


def parse_video_ref(value: str) -> tuple[str, str]:
    value = str(value or "").strip()
    if VIDEO_ID_RE.fullmatch(value):
        return value, f"https://www.youtube.com/watch?v={value}"
    parsed = parse.urlsplit(value)
    host = (parsed.hostname or "").casefold().rstrip(".")
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        raise ValueError("expected_youtube_url_or_video_id")
    if host in {"youtu.be"}:
        candidate = parsed.path.strip("/").split("/", 1)[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            candidate = parse.parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            candidate = parsed.path.split("/", 2)[2] if len(parsed.path.split("/", 2)) > 2 else ""
        else:
            candidate = ""
    else:
        candidate = ""
    if not VIDEO_ID_RE.fullmatch(candidate):
        raise ValueError("expected_youtube_url_or_video_id")
    return candidate, f"https://www.youtube.com/watch?v={candidate}"


def _error(reason: str, *, failure: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "unavailable",
        "records": [],
        "reason": reason,
        "scope": "captions_only; no_media_download; no_asr",
        "integration": {
            "route": "field-search video",
            "provider": "youtube-transcript-api",
            "runtime": "isolated configured Python path",
            "media_downloaded": False,
            "asr_used": False,
        },
    }
    if failure:
        result["failure"] = {"kind": failure}
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
        matches = result.get("matches") if isinstance(result.get("matches"), list) else []
        preview = {
            "status": result.get("status"),
            "source": result.get("source", "youtube"),
            "url": result.get("url"),
            "language_code": result.get("language_code"),
            "subtitle_type": result.get("subtitle_type"),
            "segment_count": result.get("segment_count"),
            "returned_segment_count": result.get("returned_segment_count"),
            "match_count": result.get("match_count"),
            "match_preview": [
                {
                    "index": item.get("index"),
                    "start_seconds": item.get("start_seconds"),
                    "end_seconds": item.get("end_seconds"),
                    "text": str(item.get("text", ""))[:240],
                    "text_truncated": len(str(item.get("text", ""))) > 240,
                }
                for item in matches[:5] if isinstance(item, dict)
            ],
            "output_file": str(path),
            "note": "full caption result saved; use the file for further find/location instead of refetching",
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))
    else:
        print(text)


def _languages(value: str) -> list[str]:
    values = [part.strip() for part in (value or "").split(",") if part.strip()]
    if not values or len(values) > 12 or any(len(part) > 40 for part in values):
        raise ValueError("language_list_invalid")
    return values


def _runtime_path(args: argparse.Namespace, config_result: dict[str, Any]) -> tuple[Path | None, str | None]:
    value = args.python_path or runtime_config.runtime_path(config_result.get("data") or {}, "youtube_transcript_python")
    if not value:
        return None, "runtime_not_configured"
    path = Path(value).expanduser()
    if not path.is_file():
        return None, "runtime_path_missing"
    return path.resolve(), None


def _worker(runtime: Path, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    command = [str(runtime), "-I", "-B", str(WORKER)]
    try:
        completed = subprocess.run(
            command,
            cwd=str(SKILL_ROOT),
            input=json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 1,
            env=_safe_env(),
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        return _error("transcript_deadline", failure="worker_timeout")
    except OSError:
        return _error("runtime_process_error", failure="worker_process_error")
    try:
        result = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError):
        return _error("worker_invalid_json", failure="worker_output_invalid")
    if not isinstance(result, dict):
        return _error("worker_result_not_object", failure="worker_output_invalid")
    if completed.returncode != 0 and result.get("status") in {"ok", "partial"}:
        result = _error("worker_nonzero_exit", failure="worker_nonzero_exit")
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read public YouTube captions and locate text by timestamp")
    parser.add_argument("url_or_id", help="YouTube watch/shorts/embed URL or 11-character video ID")
    parser.add_argument("--language", default="en", help="comma-separated language codes, preferred order")
    parser.add_argument("--subtitle-type", choices=("any", "manual", "auto"), default="any")
    parser.add_argument("--find", help="case-insensitive text to locate in caption segments")
    parser.add_argument("--max-segments", type=int, default=5000)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--config", help="local non-secret runtime config JSON")
    parser.add_argument("--python-path", help="explicit isolated Python path; overrides config")
    parser.add_argument("--out", help="new JSON output path; existing files are never overwritten")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        if args.out and Path(args.out).exists():
            raise ValueError("--out already exists; choose a new artifact path")
        video_id, canonical_url = parse_video_ref(args.url_or_id)
        languages = _languages(args.language)
        if not 1 <= args.max_segments <= 10000:
            parser.error("--max-segments must be between 1 and 10000")
        if not 5 <= args.timeout <= 60:
            parser.error("--timeout must be between 5 and 60")
        config_result = runtime_config.load_config(args.config)
        runtime, reason = _runtime_path(args, config_result)
        if reason:
            result = _error(reason, failure="runtime_unavailable")
            result["config"] = runtime_config.redacted_config_summary(config_result)
            _emit(result, args.out)
            return 2
        payload = {
            "video_id": video_id,
            "languages": languages,
            "subtitle_type": args.subtitle_type,
            "find": args.find or "",
            "max_segments": args.max_segments,
        }
        result = _worker(runtime, payload, args.timeout)
        result["url"] = canonical_url
        result["source"] = "youtube"
        result["config"] = runtime_config.redacted_config_summary(config_result)
        result.setdefault("integration", {
            "route": "field-search video",
            "provider": "youtube-transcript-api",
            "runtime": "isolated configured Python path",
            "media_downloaded": False,
            "asr_used": False,
        })
        _emit(result, args.out)
        return 0 if result.get("status") in {"ok", "partial"} else 2
    except ValueError as exc:
        result = _error(str(exc), failure="invalid_argument")
        try:
            _emit(result, getattr(locals().get("args"), "out", None))
        except ValueError:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
