"""Read one public RSS or Atom feed through the configured isolated runtime."""
from __future__ import annotations

import hashlib
import json
import os
import datetime as dt
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence
from urllib.parse import urlsplit

import runtime_config


SKILL_ROOT = Path(__file__).resolve().parents[1]
WORKER = Path(__file__).with_name("feed_worker.py")
MAX_OUTPUT_BYTES = 4 * 1024 * 1024
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


def _configure_stdio() -> None:
    """Keep JSON output usable when imported by a GBK-configured parent."""
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8", errors="strict")
        except (AttributeError, OSError, ValueError):
            pass


def _validate_arguments(url: str, limit: int, since: str | None, timeout: float) -> None:
    if not isinstance(url, str):
        raise ValueError("expected_public_feed_https_url")
    target = urlsplit(url)
    if target.scheme != "https" or not target.hostname or target.username or target.password or target.port not in (None, 443):
        raise ValueError("expected_public_feed_https_url")
    if not 1 <= limit <= 30:
        raise ValueError("limit_out_of_range")
    if since is not None:
        import datetime as dt

        try:
            parsed = dt.date.fromisoformat(since)
        except (TypeError, ValueError):
            raise ValueError("since_must_be_yyyy_mm_dd") from None
        if parsed.isoformat() != since:
            raise ValueError("since_must_be_yyyy_mm_dd")
    if not 1 <= timeout <= 60:
        raise ValueError("timeout_out_of_range")


def _request_key(url: str, limit: int, since: str | None) -> str:
    value = json.dumps({"url": url, "limit": limit, "since": since}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _content_hash(result: dict[str, Any]) -> str:
    payload = dict(result)
    payload.pop("result_sha256", None)
    value = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_cached(path: Path, request_sha256: str) -> dict[str, Any] | None:
    try:
        if path.stat().st_size > MAX_OUTPUT_BYTES:
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict) or value.get("status") not in {"ok", "partial"}:
        return None
    if value.get("request_sha256") != request_sha256:
        return None
    saved_hash = value.get("result_sha256")
    if not isinstance(saved_hash, str) or saved_hash != _content_hash(value):
        return None
    return value


def _worker(runtime: Path, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    command = [str(runtime), "-X", "utf8", "-I", "-B", str(WORKER)]
    try:
        completed = subprocess.run(
            command,
            cwd=str(SKILL_ROOT),
            input=json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 2,
            env=_safe_env(),
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        return {"status": "unavailable", "source": payload.get("url"), "entries": [], "reason": "feed_deadline"}
    except OSError:
        return {"status": "unavailable", "source": payload.get("url"), "entries": [], "reason": "runtime_process_error"}
    if len(completed.stdout.encode("utf-8", errors="replace")) > MAX_OUTPUT_BYTES:
        return {"status": "error", "source": payload.get("url"), "entries": [], "reason": "worker_output_too_large"}
    try:
        result = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError):
        return {"status": "error", "source": payload.get("url"), "entries": [], "reason": "worker_invalid_json"}
    if not isinstance(result, dict):
        return {"status": "error", "source": payload.get("url"), "entries": [], "reason": "worker_result_not_object"}
    if completed.returncode != 0 and result.get("status") in {"ok", "partial"}:
        return {"status": "error", "source": payload.get("url"), "entries": [], "reason": "worker_nonzero_exit"}
    return result


def _emit(result: dict[str, Any], out: str | None, *, reused: bool = False) -> None:
    shown = dict(result)
    if reused:
        shown["network_used"] = False
        shown["reused"] = True
        shown["route_reason"] = "offline valid output reuse"
    print(json.dumps(shown, ensure_ascii=False, separators=(",", ":")))


def _runtime_path(args: Any, config_result: dict[str, Any]) -> tuple[Path | None, str | None]:
    value = args.python_path or runtime_config.runtime_path(config_result.get("data") or {}, "feed")
    if not value:
        return None, "runtime_not_configured"
    path = Path(value).expanduser()
    if not path.is_file():
        return None, "runtime_path_missing"
    return path.resolve(), None


def _parser() -> Any:
    import argparse

    parser = argparse.ArgumentParser(description="Read one public RSS/Atom feed")
    parser.add_argument("url", help="public HTTPS RSS or Atom feed URL")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--since")
    parser.add_argument("--out", help="new JSON output path; valid matching output is reused")
    parser.add_argument("--python-path", help="explicit isolated Python path; overrides config")
    parser.add_argument("--config", help="local non-secret runtime config JSON")
    parser.add_argument("--timeout", type=float, default=15)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _configure_stdio()
    parser = _parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        _validate_arguments(args.url, args.limit, args.since, args.timeout)
        out_path = Path(args.out).expanduser() if args.out else None
        request_sha256 = _request_key(args.url, args.limit, args.since)
        if out_path is not None and out_path.exists():
            cached = _read_cached(out_path, request_sha256)
            if cached is None:
                raise ValueError("--out exists but is not a valid matching feed result; choose a new path")
            _emit(cached, args.out, reused=True)
            return 0
        config_result = runtime_config.load_config(args.config)
        runtime, reason = _runtime_path(args, config_result)
        if reason:
            result = {"status": "unavailable", "source": args.url, "entries": [], "reason": reason,
                      "config": runtime_config.redacted_config_summary(config_result), "network_used": False}
            _emit(result, args.out)
            return 2
        payload = {"url": args.url, "limit": args.limit, "since": args.since, "timeout": args.timeout}
        result = _worker(runtime, payload, args.timeout)
        result["request_sha256"] = request_sha256
        result["network_used"] = True
        result["config"] = runtime_config.redacted_config_summary(config_result)
        if result.get("status") in {"ok", "partial"}:
            result["fetched_at"] = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
            result["result_sha256"] = _content_hash(result)
            if out_path is not None:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with out_path.open("x", encoding="utf-8") as handle:
                    json.dump(result, handle, ensure_ascii=False, separators=(",", ":"))
                    handle.write("\n")
                result["output_file"] = str(out_path.resolve())
        _emit(result, args.out)
        return 0 if result.get("status") in {"ok", "partial"} else 2
    except ValueError as exc:
        result = {"status": "error", "source": "feed", "entries": [], "reason": str(exc), "network_used": False}
        _emit(result, getattr(locals().get("args"), "out", None))
        return 2
    except OSError:
        result = {"status": "error", "source": "feed", "entries": [], "reason": "output_write_error", "network_used": False}
        _emit(result, getattr(locals().get("args"), "out", None))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
