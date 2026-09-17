"""Thin explicit bridge to the verified R22 read-only Xiaohongshu adapter.

This module is intentionally not a collector.  It only validates the small
public surface, forwards the caller's explicit local runtime/session paths,
and preserves the adapter's result envelope and uncertainty fields.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


ROUTE = "field-search xiaohongshu"
FEED_REF_RE = re.compile(r"^r22:[A-Za-z0-9._~%:-]{1,512}$")
FORBIDDEN_TEXT_RE = re.compile(
    r"(?i)(?:[?&](?:xsec_token|access_token|refresh_token|cookie)=|"
    r"(?:xsec_token|access_token|refresh_token)\s*[:=]\s*[^,\s\"'}]+)"
)
FORBIDDEN_KEYS = frozenset(
    {
        "xsec_token",
        "access_token",
        "refresh_token",
        "cookie",
        "cookies",
        "set-cookie",
        "cookie_path",
        "qrcode_path",
        "qr_code",
        "browser_data",
        "user_data_dir",
        "session_root",
        "profile_dir",
        "storage_state",
        "worker_stdout",
        "stderr_tail",
    }
)
SUCCESS_STATUSES = frozenset(
    {
        "ok",
        "already_logged_in",
        "empty_or_upstream_failure",
        "partial_unknown",
        "unavailable",
    }
)


class BridgeError(ValueError):
    """A local argument, process, or output-boundary rejection."""


def _add_runtime_options(parser: argparse.ArgumentParser, *, suppress_default: bool = False) -> None:
    default = argparse.SUPPRESS if suppress_default else None
    parser.add_argument(
        "--session-root",
        default=default,
        help="authorized existing isolated session directory (required for a live run)",
    )
    parser.add_argument(
        "--adapter-path",
        default=default,
        help="verified read-only adapter script (required for a live run)",
    )
    parser.add_argument(
        "--python-path",
        default=default,
        help="Python runtime for the adapter (required for a live run)",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Explicit Xiaohongshu search/feed bridge; uses a caller-supplied "
            "R22 read-only adapter and isolated session"
        )
    )
    _add_runtime_options(parser)
    subparsers = parser.add_subparsers(dest="operation", required=True)

    search_parser = subparsers.add_parser("search", help="bounded read-only search")
    _add_runtime_options(search_parser, suppress_default=True)
    search_parser.add_argument("keyword")
    search_parser.add_argument("--limit", type=int, default=1, help="returned-result target, 1..5")

    feed_parser = subparsers.add_parser("feed", help="read-only note detail and bounded comment loading")
    _add_runtime_options(feed_parser, suppress_default=True)
    feed_parser.add_argument(
        "feed_ref",
        help="opaque r22: reference returned by search; access tokens are not accepted",
    )
    feed_parser.add_argument(
        "--max-comments",
        type=int,
        default=1,
        help="评论加载目标 1..3；不是返回条数硬上限",
    )
    return parser


def _error(operation: str, kind: str, message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "operation": operation,
        "integration": {
            "route": ROUTE,
            "adapter": "R22 verified read-only adapter",
            "runtime": "explicit local --python-path/--adapter-path/--session-root",
            "write_scope": "read-only search/feed; adapter-local feed context only",
        },
        "failure": {"kind": kind, "message": message},
    }


def _emit(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _bounded(value: int | None, lower: int, upper: int, label: str) -> int:
    if value is None or not lower <= value <= upper:
        raise BridgeError(f"{label}_out_of_range")
    return value


def _path(value: str | None, label: str, *, file: bool) -> Path:
    if not value:
        raise BridgeError(f"missing_{label}")
    candidate = Path(value).expanduser()
    if file and not candidate.is_file():
        raise BridgeError(f"invalid_{label}")
    if not file and not candidate.is_dir():
        raise BridgeError(f"invalid_{label}")
    return candidate.resolve()


def _validate_feed_ref(value: str) -> str:
    if not FEED_REF_RE.fullmatch(value or ""):
        raise BridgeError("feed_ref_must_be_opaque_r22_reference")
    return value


def _has_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_KEYS or _has_forbidden_key(item):
                return True
        return False
    if isinstance(value, list):
        return any(_has_forbidden_key(item) for item in value)
    return False


def _iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_string_values(item)


def _decode_stdout(value: bytes) -> str:
    try:
        return value.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        # Never include the offending bytes or their repr in the result.
        raise BridgeError("adapter_stdout_decode_error") from exc


def _load_result(stdout: bytes, operation: str, paths: Sequence[Path]) -> dict[str, Any]:
    text = _decode_stdout(stdout)
    try:
        result = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        raise BridgeError("adapter_did_not_return_json") from None
    if not isinstance(result, dict):
        raise BridgeError("adapter_result_was_not_an_object")
    if _has_forbidden_key(result):
        raise BridgeError("adapter_result_contained_sensitive_key")
    serialized = json.dumps(result, ensure_ascii=False)
    if FORBIDDEN_TEXT_RE.search(serialized):
        raise BridgeError("adapter_result_contained_sensitive_value")
    for path in paths:
        protected_path = str(path).casefold()
        if any(protected_path in item.casefold() for item in _iter_string_values(result)):
            raise BridgeError("adapter_result_contained_local_path")
    return result


def _command(args: argparse.Namespace) -> tuple[list[str], Path, Path, Path]:
    session_root = _path(args.session_root, "session_root", file=False)
    adapter_path = _path(args.adapter_path, "adapter_path", file=True)
    python_path = _path(args.python_path, "python_path", file=True)
    if args.operation == "search":
        limit = _bounded(args.limit, 1, 5, "limit")
        command = [
            str(python_path),
            str(adapter_path),
            "--session-root",
            str(session_root),
            "search",
            args.keyword,
            "--limit",
            str(limit),
        ]
    else:
        feed_ref = _validate_feed_ref(args.feed_ref)
        max_comments = _bounded(args.max_comments, 1, 3, "max_comments")
        command = [
            str(python_path),
            str(adapter_path),
            "--session-root",
            str(session_root),
            "feed",
            feed_ref,
            "--max-comments",
            str(max_comments),
        ]
    return command, session_root, adapter_path, python_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        command, session_root, adapter_path, python_path = _command(args)
        completed = subprocess.run(
            command,
            cwd=str(adapter_path.parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        result = _load_result(completed.stdout, args.operation, (session_root, adapter_path, python_path))
        result["integration"] = {
            "route": ROUTE,
            "adapter": "R22 verified read-only adapter",
            "runtime": "explicit local --python-path/--adapter-path/--session-root",
            "write_scope": "read-only search/feed; adapter-local feed context only",
        }
        if completed.returncode != 0 and result.get("status") in SUCCESS_STATUSES:
            result["status"] = "worker_error"
            result["failure"] = {
                "kind": "adapter_nonzero_exit",
                "message": "adapter exited non-zero; result is not considered successful",
            }
        _emit(result)
        return 0 if completed.returncode == 0 and result.get("status") in SUCCESS_STATUSES else 2
    except BridgeError as exc:
        operation = getattr(locals().get("args"), "operation", "unknown")
        kind = str(exc)
        status = "decode_error" if kind == "adapter_stdout_decode_error" else "error"
        result = _error(operation, kind, "adapter output was rejected; sensitive details are suppressed")
        result["status"] = status
        _emit(result)
        return 2
    except OSError:
        operation = getattr(locals().get("args"), "operation", "unknown")
        _emit(_error(operation, "adapter_process_error", "adapter process could not be started; details are suppressed"))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
