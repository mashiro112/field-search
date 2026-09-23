"""Task-local bounded batch runner with result reuse and failure-only reruns.

The manifest is deliberately small and file-based.  Each item owns its target
and options; no global index, vector store, planner, or cross-session cache is
created.  A successful item is reused by request key unless the caller asks
for an explicit refresh.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Sequence

import runtime_config


SCRIPT = Path(__file__).with_name("search.py")
SUCCESS = {"ok", "no_results", "imported", "reused"}
ALLOWED_ENV = {
    "SYSTEMROOT",
    "WINDIR",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "HOME",
    "HOMEDRIVE",
    "HOMEPATH",
    "PATH",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
}
KIND_OPTIONS = {
    "read": {"reader", "wait_css", "wait_timeout", "include_links", "limit", "page", "timeout", "sort", "since"},
    "video": {"language", "subtitle_type", "find", "max_segments", "timeout", "config", "python_path", "session_path"},
    "discourse": {"post_limit", "request_budget", "batch_size", "timeout"},
    "feed": {"limit", "since", "timeout", "config", "python_path"},
    "discover": {"kind", "limit", "contains", "request_budget", "timeout"},
    "convert": {"out_dir", "config", "python_path", "source_url", "timeout"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_env() -> dict[str, str]:
    env = {
        **{key: value for key, value in os.environ.items() if key.upper() in ALLOWED_ENV},
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    # A config path is a non-sensitive reference and is part of the child's
    # selected runtime. Do not forward unrelated credentials or cookies.
    if os.getenv(runtime_config.CONFIG_ENV):
        env[runtime_config.CONFIG_ENV] = os.environ[runtime_config.CONFIG_ENV]
    return env


def _load(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("manifest_must_be_object")
    return value


def _validate_items(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        raise ValueError("manifest_items_must_be_nonempty_list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"item_{index}_must_be_object")
        item_id = str(item.get("id", "")).strip()
        kind = str(item.get("kind", "")).strip()
        target = str(item.get("target", "")).strip()
        options = item.get("options", {})
        if not item_id or item_id in seen:
            raise ValueError("item_ids_must_be_nonempty_unique")
        if kind not in KIND_OPTIONS:
            raise ValueError("item_kind_unsupported")
        if not target:
            raise ValueError(f"item_{item_id}_target_required")
        if not isinstance(options, dict) or any(key not in KIND_OPTIONS[kind] for key in options):
            raise ValueError(f"item_{item_id}_options_invalid")
        if kind == "convert" and not str(options.get("out_dir", "")).strip():
            raise ValueError(f"item_{item_id}_out_dir_required")
        seen.add(item_id)
        normalized.append({"id": item_id, "kind": kind, "target": target, "options": dict(options)})
    return normalized


def _write_new(path: str, value: dict[str, Any]) -> None:
    target = Path(path)
    if target.exists():
        raise ValueError("--out already exists; choose a new artifact path")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _replace_checkpoint(path: str, value: dict[str, Any]) -> None:
    """Replace a completed checkpoint atomically, keeping the prior file on failure."""
    target = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent,
                                         prefix=target.name + ".", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _config_fingerprint(options: dict[str, Any]) -> str:
    explicit = options.get("config") or os.getenv(runtime_config.CONFIG_ENV)
    path, _ = runtime_config.selected_config_path(explicit)
    try:
        content = path.read_bytes()
    except OSError:
        return "missing"
    return hashlib.sha256(content).hexdigest()


def _request_key(item: dict[str, Any]) -> str:
    options = item.get("options", {})
    target_sha256 = None
    if item["kind"] == "convert":
        digest = hashlib.sha256()
        try:
            target_path = Path(item["target"])
            size = target_path.stat().st_size
            if size > 25 * 1024 * 1024:
                target_sha256 = f"over_material_limit:{size}"
            else:
                with target_path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
                target_sha256 = digest.hexdigest()
        except OSError:
            target_sha256 = "missing_or_unreadable"
    body = json.dumps(
        {
            "kind": item["kind"],
            "target": item["target"],
            "options": options,
            # The same config path with changed contents is a different
            # effective runtime and must not reuse a prior success.
            "config_fingerprint": _config_fingerprint(options)
            if item["kind"] in {"video", "read", "feed", "convert"}
            else None,
            "target_sha256": target_sha256,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _options_summary(options: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, value in options.items():
        if key in {"config", "python_path"}:
            result[key] = "<path-reference>" if value else None
        else:
            result[key] = value
    return result


def _child_args(item: dict[str, Any]) -> list[str]:
    kind = item["kind"]
    command = [kind, item["target"]]
    for key, value in item.get("options", {}).items():
        if value is None or value is False:
            continue
        flag = "--" + key.replace("_", "-")
        if value is True:
            command.append(flag)
        else:
            command.extend((flag, str(value)))
    return command


def _run_item(item: dict[str, Any]) -> tuple[dict[str, Any], float]:
    default_timeout = 60 if item["kind"] == "convert" else 20
    maximum_timeout = 180 if item["kind"] == "convert" else 60
    timeout = float(item.get("options", {}).get("timeout", default_timeout))
    timeout = max(1.0, min(timeout, maximum_timeout))
    started = time.monotonic()
    try:
        completed = subprocess.run(
            # Keep the trusted scripts directory on sys.path; the environment
            # is already reduced to non-credential variables below.
            [sys.executable, "-B", str(SCRIPT), *_child_args(item)],
            cwd=str(SCRIPT.parent),
            input=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            timeout=timeout + 2,
            env=_safe_env(),
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        return {"status": "unavailable", "records": [], "reason": "child_deadline"}, round(time.monotonic() - started, 3)
    except OSError:
        return {"status": "error", "records": [], "reason": "child_process_error"}, round(time.monotonic() - started, 3)
    try:
        result = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError):
        result = {"status": "error", "records": [], "reason": "child_invalid_json"}
    if not isinstance(result, dict):
        result = {"status": "error", "records": [], "reason": "child_result_not_object"}
    if completed.returncode != 0 and result.get("status") in SUCCESS:
        result = {"status": "error", "records": [], "reason": "child_nonzero_exit"}
    return result, round(time.monotonic() - started, 3)


def create(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="search.py batch create")
    parser.add_argument("input", help="JSON object/list containing task items")
    parser.add_argument("--out", required=True, help="new manifest path")
    args = parser.parse_args(list(argv))
    try:
        source = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
        items = _validate_items(source.get("items") if isinstance(source, dict) else source)
        manifest = {
            "schema_version": 1,
            "created_at": _now(),
            "items": items,
            "results": {},
            "scope": "task-local; no global index; each item has isolated parameters",
        }
        _write_new(args.out, manifest)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "reason": str(exc), "records": []}, ensure_ascii=False, indent=2))
        return 2


def run(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="search.py batch run")
    parser.add_argument("manifest")
    parser.add_argument("--out", help="new result manifest; original is never overwritten")
    parser.add_argument("--refresh", action="store_true", help="re-fetch every item, including successful ones")
    parser.add_argument("--refresh-id", action="append", default=[], help="re-fetch one item; repeatable")
    args = parser.parse_args(list(argv))
    try:
        # Reject a clearly unusable destination before any child invocation or
        # external read. The exclusive create below still handles races.
        if args.out and Path(args.out).exists():
            raise ValueError("--out already exists; choose a new artifact path")
        manifest = _load(args.manifest)
        items = _validate_items(manifest.get("items"))
        previous = manifest.get("results") if isinstance(manifest.get("results"), dict) else {}
        refreshed = set(args.refresh_id)
        unknown_refresh = refreshed - {item["id"] for item in items}
        if unknown_refresh:
            raise ValueError("refresh_id_unknown")
        # Keep already completed items in the first checkpoint. Explicitly
        # refreshed items are removed, so an interrupted refresh stays pending.
        results: dict[str, Any] = {
            item["id"]: previous[item["id"]] for item in items
            if not args.refresh and item["id"] not in refreshed
            and isinstance(previous.get(item["id"]), dict)
        }
        executed = reused = 0
        result_manifest = dict(manifest)
        result_manifest.update(last_run_at=_now(), status="in_progress", results=results,
                               summary={"items": len(items), "executed": 0, "reused": 0,
                                        "pending_or_failed": len(items) - len(results),
                                        "refresh_all": args.refresh, "refresh_ids": sorted(refreshed)})
        if args.out:
            _write_new(args.out, result_manifest)
        for item in items:
            item_id = item["id"]
            key = _request_key(item)
            old = previous.get(item_id)
            can_reuse = (
                not args.refresh
                and item_id not in refreshed
                and isinstance(old, dict)
                and old.get("request_key") == key
                and old.get("status") in SUCCESS
                and isinstance(old.get("output"), dict)
            )
            if can_reuse:
                entry = dict(old)
                entry.update(action="reused", options_summary=_options_summary(item.get("options", {})))
                reused += 1
            else:
                output, elapsed = _run_item(item)
                entry = {
                    "request_key": key,
                    "action": "executed",
                    "status": output.get("status", "error"),
                    "elapsed_seconds": elapsed,
                    "attempt": int(old.get("attempt", 0)) + 1 if isinstance(old, dict) else 1,
                    "options_summary": _options_summary(item.get("options", {})),
                    "output": output,
                }
                executed += 1
            results[item_id] = entry
            if args.out:
                result_manifest["last_run_at"] = _now()
                result_manifest["summary"].update(
                    executed=executed, reused=reused,
                    pending_or_failed=sum(
                        candidate["id"] not in results or results[candidate["id"]].get("status") not in SUCCESS
                        for candidate in items))
                _replace_checkpoint(args.out, result_manifest)
        statuses = [entry.get("status") for entry in results.values()]
        if all(status in SUCCESS for status in statuses):
            status = "ok"
        elif any(status in SUCCESS for status in statuses):
            status = "partial"
        else:
            status = "unavailable"
        result_manifest.update(
            {
                "last_run_at": _now(),
                "status": status,
                "results": results,
                "summary": {
                    "items": len(items),
                    "executed": executed,
                    "reused": reused,
                    "failed": [item_id for item_id, entry in results.items() if entry.get("status") not in SUCCESS],
                    "refresh_all": args.refresh,
                    "refresh_ids": sorted(refreshed),
                },
            }
        )
        if args.out:
            _replace_checkpoint(args.out, result_manifest)
            print(json.dumps({
                "status": status,
                "summary": result_manifest["summary"],
                "output_file": str(Path(args.out)),
                "note": "full task results saved; inspect item output on demand instead of replaying network reads",
            }, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result_manifest, ensure_ascii=False, indent=2))
        return 0 if status in {"ok", "partial"} else 2
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "reason": str(exc), "records": []}, ensure_ascii=False, indent=2))
        return 2


def status(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="search.py batch status")
    parser.add_argument("manifest")
    args = parser.parse_args(list(argv))
    try:
        manifest = _load(args.manifest)
        results = manifest.get("results") if isinstance(manifest.get("results"), dict) else {}
        statuses = [entry.get("status") for entry in results.values() if isinstance(entry, dict)]
        summary = {
            "status": manifest.get("status", "not_run"),
            "items": len(manifest.get("items", [])) if isinstance(manifest.get("items"), list) else None,
            "results": len(results),
            "successful": sum(value in SUCCESS for value in statuses),
            "pending_or_failed": max(0, len(manifest.get("items", [])) - len(results))
            + sum(value not in SUCCESS for value in statuses),
            "scope": "task-local; no network request",
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args or args[0] not in {"create", "run", "status"}:
        print("usage: search.py batch {create|run|status} ...")
        return 2
    if args[0] == "create":
        return create(args[1:])
    if args[0] == "run":
        return run(args[1:])
    return status(args[1:])


if __name__ == "__main__":
    raise SystemExit(main())
