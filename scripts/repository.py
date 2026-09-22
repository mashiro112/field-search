"""Bounded public GitHub repository context through Repomix.

This adapter deliberately keeps repository acquisition in the pinned upstream
Repomix CLI.  It validates the public source URL, supplies an explicit JSON
configuration, and imports the resulting Markdown through :mod:`report`.
The report body is upstream output; this module does not parse repository
contents or implement another pagination/search engine.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import urlsplit

try:
    import report
    import runtime_config
except ImportError:  # pragma: no cover - supports package-style imports
    from . import report  # type: ignore
    from . import runtime_config  # type: ignore


SCHEMA_VERSION = 1
REPOMIX_NAME = "repomix"
DEFAULT_INCLUDE_PATTERNS = (
    "README*",
    "SKILL.md",
    "package.json",
    "pyproject.toml",
    "LICENSE*",
)
MAX_PATTERN_LENGTH = 512
MAX_REF_LENGTH = 256
DEFAULT_TIMEOUT = 60.0
MAX_TIMEOUT = 180.0
_OWNER_RE = re.compile(r"^[A-Za-z0-9-]{1,39}$")
_REPO_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


class RepositoryError(ValueError):
    """A safe, user-facing repository route error."""

    def __init__(self, reason: str, *, network_used: bool | None = False) -> None:
        super().__init__(reason)
        self.network_used = network_used


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _validate_pattern(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RepositoryError(f"{label}_must_be_nonempty")
    if len(value) > MAX_PATTERN_LENGTH or any(ord(char) < 32 for char in value):
        raise RepositoryError(f"{label}_invalid")
    # The upstream scanner is rooted at the temporary clone.  Reject path
    # escapes and absolute paths before handing patterns to its globber.
    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        raise RepositoryError(f"{label}_must_be_relative")
    if any(part == ".." for part in normalized.split("/")):
        raise RepositoryError(f"{label}_must_stay_within_repository")
    return value


def _validate_ref(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value or len(value) > MAX_REF_LENGTH:
        raise RepositoryError("ref_invalid")
    if value.startswith("-") or value.endswith(".") or value.endswith(".lock"):
        raise RepositoryError("ref_invalid")
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value):
        raise RepositoryError("ref_invalid")
    if any(token in value for token in ("..", "@{")):
        raise RepositoryError("ref_invalid")
    if any(char in value for char in ("~", "^", ":", "?", "*", "[", "\\")):
        raise RepositoryError("ref_invalid")
    if "//" in value or value.startswith("/") or value.endswith("/"):
        raise RepositoryError("ref_invalid")
    return value


def _validate_source(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise RepositoryError("source_url_invalid")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise RepositoryError("source_url_invalid") from None
    if (
        parsed.scheme.casefold() != "https"
        or parsed.hostname is None
        or parsed.hostname.casefold() != "github.com"
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.query
        or parsed.fragment
    ):
        raise RepositoryError("source_url_invalid")
    parts = parsed.path.split("/")
    if len(parts) == 4 and parts[-1] == "":
        parts = parts[:-1]
    if len(parts) != 3 or not _OWNER_RE.fullmatch(parts[1]) or not _REPO_RE.fullmatch(parts[2]):
        raise RepositoryError("source_url_invalid")
    if parts[2].casefold().endswith(".git"):
        raise RepositoryError("source_url_invalid")
    return f"https://github.com/{parts[1]}/{parts[2]}"


def _safe_environment(stage: Path) -> dict[str, str]:
    """Build a small environment with credentials and user Git config removed."""

    allowed = {
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "TEMP",
        "TMP",
        "LOCALAPPDATA",
        "PROGRAMDATA",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
    }
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    empty_global = stage / "empty-git-config"
    empty_global.touch()
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(empty_global),
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    # The allow-list intentionally excludes GITHUB_TOKEN, GH_TOKEN, and all
    # other ambient credential or code-injection variables.
    return env


def _runtime_entry(runtime_root: str | None) -> tuple[Path, str, str]:
    if runtime_root:
        root = Path(runtime_root).expanduser()
        if root.is_file():
            entry = root
        else:
            entry = root / "node_modules" / REPOMIX_NAME / "bin" / "repomix.cjs"
    else:
        config_result = runtime_config.load_config()
        paths = runtime_config.reader_paths(config_result.get("data") or {}, "repository")
        configured = paths.get("adapter_path")
        if not configured:
            raise RepositoryError("runtime_not_configured")
        entry = Path(configured).expanduser()
    try:
        entry = entry.resolve()
    except OSError:
        raise RepositoryError("runtime_not_ready") from None
    if not entry.is_file() or entry.name.casefold() != "repomix.cjs":
        raise RepositoryError("runtime_not_ready")
    node = shutil.which("node")
    if not node:
        raise RepositoryError("node_not_found")
    return entry, str(Path(node).resolve()), str(entry.parent.parent / "package.json")


def _tool_info(entry: Path, package_json_path: str) -> dict[str, str]:
    try:
        entry_hash = _sha256(entry.read_bytes())
    except OSError:
        raise RepositoryError("runtime_not_ready") from None
    version = "unknown"
    package_path = Path(package_json_path)
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
        if isinstance(package, dict) and isinstance(package.get("version"), str):
            version = package["version"]
    except (OSError, UnicodeError, json.JSONDecodeError):
        # The entrypoint hash remains a useful immutable identity for a
        # self-contained runtime even when package.json is unavailable.
        pass
    return {"name": REPOMIX_NAME, "version": version, "entrypoint_sha256": entry_hash}


def _request_key(source: str, ref: str | None, include: list[str], exclude: list[str], tool: dict[str, str]) -> str:
    payload = {
        "source_url": source,
        "ref": ref,
        "include": include,
        "exclude": exclude,
        "tool": tool,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256(raw)


def _load_existing(target: Path, request_key: str) -> dict[str, Any] | None:
    report_path = target / "report.md"
    metadata_path = target / "metadata.json"
    if not report_path.exists() and not metadata_path.exists():
        if target.exists() and any(target.iterdir()):
            raise RepositoryError("destination_not_empty")
        return None
    if not report_path.is_file() or not metadata_path.is_file() or report_path.is_symlink() or metadata_path.is_symlink():
        raise RepositoryError("destination_artifacts_incomplete")
    try:
        raw = report_path.read_bytes()
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise RepositoryError("destination_artifact_damaged") from None
    recorded = metadata.get("report", {}).get("sha256") if isinstance(metadata, dict) else None
    if not isinstance(metadata, dict) or metadata.get("schema_version") != SCHEMA_VERSION or not isinstance(recorded, str):
        raise RepositoryError("destination_metadata_invalid")
    if _sha256(raw) != recorded:
        raise RepositoryError("destination_artifact_damaged")
    existing_key = metadata.get("request_key")
    if not isinstance(existing_key, str):
        raise RepositoryError("destination_metadata_missing_request")
    if existing_key != request_key:
        raise RepositoryError("destination_exists_with_different_request")
    return {
        "status": "reused",
        "report_dir": str(target),
        "report_file": str(report_path),
        "metadata_file": str(metadata_path),
        "source_url": (metadata.get("source") or {}).get("url"),
        "ref": (metadata.get("source") or {}).get("ref"),
        "request_key": existing_key,
        "sha256": recorded,
        "byte_length": len(raw),
        "files_count": metadata.get("packed_file_count", 0),
        "tool": metadata.get("tool"),
        "options": metadata.get("options"),
        "status_detail": metadata.get("fetch_status", "imported"),
        "network_used": False,
        "untrusted_source_data": True,
    }


def _write_config(path: Path, include: list[str], exclude: list[str]) -> None:
    # This is the only configuration Repomix receives.  In particular, it
    # has no instructionFilePath, processors, remote-trust flag, logs, or diffs.
    config = {
        "output": {
            "filePath": "repomix-output.md",
            "style": "markdown",
            "filePathStyle": "target-relative",
            "fileSummary": True,
            "directoryStructure": True,
            "files": True,
            "copyToClipboard": False,
            "git": {
                "sortByChanges": False,
                "includeDiffs": False,
                "includeLogs": False,
            },
        },
        "include": include,
        "ignore": {
            "useGitignore": True,
            "useDotIgnore": True,
            "useDefaultPatterns": True,
            "customPatterns": exclude,
        },
        "security": {"enableSecurityCheck": True},
    }
    try:
        path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    except OSError:
        raise RepositoryError("config_write_failed") from None


def _run_repomix(
    node: str,
    entry: Path,
    source: str,
    ref: str | None,
    config: Path,
    stage: Path,
    timeout: float,
) -> None:
    command = [
        node,
        str(entry),
        "--remote",
        source,
        "--config",
        str(config),
        "--output",
        "repomix-output.md",
        "--style",
        "markdown",
        "--quiet",
    ]
    if ref is not None:
        command.extend(["--remote-branch", ref])
    try:
        completed = subprocess.run(
            command,
            cwd=str(stage),
            env=_safe_environment(stage),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise RepositoryError("upstream_timeout") from None
    except OSError:
        raise RepositoryError("upstream_process_failed") from None
    if completed.returncode != 0:
        # Upstream stderr is intentionally kept private: it can contain URLs,
        # local paths, or provider messages that should not reach stdout.
        raise RepositoryError("upstream_failed")


def _augment_metadata(
    metadata_path: Path,
    source: str,
    ref: str | None,
    request_key: str,
    tool: dict[str, str],
    include: list[str],
    exclude: list[str],
    timeout: float,
    started_at: str,
    finished_at: str,
    packed_file_count: int,
) -> dict[str, Any]:
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise RepositoryError("destination_metadata_invalid") from None
    if not isinstance(metadata, dict):
        raise RepositoryError("destination_metadata_invalid")
    report_info = metadata.get("report") if isinstance(metadata.get("report"), dict) else {}
    report_info["packed_file_count"] = packed_file_count
    metadata["report"] = report_info
    metadata["source"] = {
        **(metadata.get("source") if isinstance(metadata.get("source"), dict) else {}),
        "url": source,
        "ref": ref,
        "acquisition_method": "repomix_remote",
    }
    metadata.update(
        {
            "request_key": request_key,
            "packed_file_count": packed_file_count,
            "fetch_status": "no_results" if packed_file_count == 0 else "ok",
            "tool": tool,
            "options": {
                "include": include,
                "exclude": exclude,
                "timeout_seconds": timeout,
                "output_style": "markdown",
                "remote_config_trust": False,
                "instruction_file": False,
                "file_processors": False,
                "git_logs": False,
                "git_diffs": False,
                "submodules": False,
            },
            "timing": {"started_at": started_at, "finished_at": finished_at},
            "completeness_boundary": {
                "scope": "Repomix Markdown output for the selected include and exclude patterns.",
                "limitations": [
                    "The remote clone or archive acquisition remains controlled by Repomix.",
                    "Repository files outside the selected patterns are outside this report.",
                    "Repository ignore files and Repomix default exclusions remain active.",
                    "This import does not verify facts, links, or source completeness.",
                ],
            },
        }
    )
    integrity = metadata.get("integrity") if isinstance(metadata.get("integrity"), dict) else {}
    integrity["status"] = "unverified"
    integrity["artifact_sha256"] = report_info.get("sha256")
    integrity["artifact_byte_length"] = report_info.get("byte_length")
    metadata["integrity"] = integrity
    try:
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    except OSError:
        raise RepositoryError("destination_metadata_write_failed") from None
    return metadata


def fetch(
    source_value: str,
    out_dir: str,
    include_values: list[str],
    exclude_values: list[str],
    ref_value: str | None,
    runtime_root: str | None,
    timeout: float,
) -> dict[str, Any]:
    source = _validate_source(source_value)
    ref = _validate_ref(ref_value)
    include = [_validate_pattern(item, "include_pattern") for item in _dedupe(list(DEFAULT_INCLUDE_PATTERNS) + include_values)]
    exclude = [_validate_pattern(item, "exclude_pattern") for item in _dedupe(exclude_values)]
    if not 1.0 <= timeout <= MAX_TIMEOUT:
        raise RepositoryError("timeout_out_of_range")
    entry, node, package_path = _runtime_entry(runtime_root)
    tool = _tool_info(entry, package_path)
    request_key = _request_key(source, ref, include, exclude, tool)
    target = Path(out_dir).expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise RepositoryError("destination_must_be_directory")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise RepositoryError("destination_parent_unwritable") from None
    existing = _load_existing(target, request_key) if target.exists() else None
    if existing is not None:
        return existing

    started_at = _now()
    stage: Path | None = None
    upstream_started = False
    try:
        stage = Path(tempfile.mkdtemp(prefix=".field-search-repo-", dir=str(target.parent)))
        config_path = stage / "repomix.config.json"
        _write_config(config_path, include, exclude)
        upstream_started = True
        _run_repomix(node, entry, source, ref, config_path, stage, timeout)
        upstream_output = stage / "repomix-output.md"
        if not upstream_output.is_file():
            raise RepositoryError("upstream_output_missing")
        try:
            upstream_raw = upstream_output.read_bytes()
        except OSError:
            raise RepositoryError("upstream_output_unreadable") from None
        # This counts Repomix's own file-entry markers in its generated
        # document; it does not inspect or parse repository files.
        packed_file_count = len(re.findall(rb"(?m)^## File: ", upstream_raw))
        # import_report preserves the upstream body byte-for-byte and applies
        # the existing report artifact contract before metadata is extended.
        result = report.import_report(
            str(upstream_output),
            str(target),
            source,
            "repomix_remote",
            report.DEFAULT_PREVIEW_CHARS,
        )
        finished_at = _now()
        metadata = _augment_metadata(
            target / "metadata.json",
            source,
            ref,
            request_key,
            tool,
            include,
            exclude,
            timeout,
            started_at,
            finished_at,
            packed_file_count,
        )
        return {
            "status": "no_results" if packed_file_count == 0 else result.get("status", "imported"),
            "report_dir": str(target),
            "report_file": str(target / "report.md"),
            "metadata_file": str(target / "metadata.json"),
            "source_url": source,
            "ref": ref,
            "request_key": request_key,
            "sha256": (metadata.get("report") or {}).get("sha256"),
            "byte_length": (metadata.get("report") or {}).get("byte_length"),
            "files_count": packed_file_count,
            "tool": tool,
            "options": metadata.get("options"),
            "network_used": True,
            "untrusted_source_data": True,
        }
    except (RepositoryError, ValueError, OSError) as exc:
        if upstream_started:
            raise RepositoryError(str(exc), network_used=None) from None
        raise
    except Exception:
        if upstream_started:
            raise RepositoryError("upstream_result_invalid", network_used=None) from None
        raise
    finally:
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)


def _print(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="search.py repo", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fetch_parser = commands.add_parser("fetch", help="fetch and pack a public GitHub repository")
    fetch_parser.add_argument("source", help="https://github.com/owner/repo")
    fetch_parser.add_argument("--out-dir", required=True)
    fetch_parser.add_argument("--include", action="append", default=[], help="additional glob pattern; repeatable")
    fetch_parser.add_argument("--exclude", action="append", default=[], help="additional ignore glob; repeatable")
    fetch_parser.add_argument("--ref", help="branch, tag, or commit")
    fetch_parser.add_argument("--runtime-root", help="runtime root or direct repomix.cjs path")
    fetch_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    opener = commands.add_parser("open", help="open a local report through report.py")
    opener.add_argument("target")
    opener.add_argument("--page", type=int, default=1)
    opener.add_argument("--page-chars", type=int, default=report.DEFAULT_PAGE_CHARS)
    finder = commands.add_parser("find", help="find in a local report through report.py")
    finder.add_argument("target")
    finder.add_argument("term")
    finder.add_argument("--page-chars", type=int, default=report.DEFAULT_PAGE_CHARS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "fetch":
            result = fetch(args.source, args.out_dir, args.include, args.exclude, args.ref, args.runtime_root, args.timeout)
            _print(result)
            return 0
        if args.command == "open":
            return report.main(["open", args.target, "--page", str(args.page), "--page-chars", str(args.page_chars)])
        return report.main(["find", args.target, args.term, "--page-chars", str(args.page_chars)])
    except (RepositoryError, ValueError, OSError) as exc:
        _print({"status": "error", "reason": str(exc), "network_used": getattr(exc, "network_used", False)})
        return 2
    except Exception:
        _print({"status": "error", "reason": "repository_route_error", "network_used": False})
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
