"""Convert a bounded local material file to a reusable Markdown report.

MarkItDown runs in a configured isolated Python runtime.  This route accepts
only already acquired local files, disables MarkItDown plugins, and passes no
URL, LLM client, Azure endpoint, or other remote option to the converter.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.parse import urlsplit
import zipfile

try:
    import report
    import runtime_config
except ImportError:  # pragma: no cover - supports package-style imports
    from . import report  # type: ignore
    from . import runtime_config  # type: ignore


SCHEMA_VERSION = 1
EXPECTED_VERSION = "0.1.8"
MAX_INPUT_BYTES = 25 * 1024 * 1024
MAX_OUTPUT_BYTES = 32 * 1024 * 1024
MAX_WORKER_STDOUT_BYTES = MAX_OUTPUT_BYTES + 1024 * 1024
MAX_TIMEOUT = 180.0
DEFAULT_TIMEOUT = 60.0
MAX_OFFICE_EXPANDED_BYTES = 256 * 1024 * 1024
PREVIEW_CHARS = 600
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".txt", ".csv"}
OFFICE_EXTENSIONS = {".docx", ".pptx", ".xlsx"}


class MaterialError(ValueError):
    """A safe, bounded material route error."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_path(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_INPUT_BYTES:
                    raise MaterialError("input_too_large")
                digest.update(chunk)
    except MaterialError:
        raise
    except (OSError, PermissionError):
        raise MaterialError("input_file_unreadable") from None
    return digest.hexdigest(), total


def _validate_source_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    candidate = value.strip()
    try:
        parsed = urlsplit(candidate)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise MaterialError("source_url_invalid")
    except ValueError:
        raise MaterialError("source_url_invalid") from None
    return candidate


def _resolve_input(value: str) -> tuple[Path, str, int]:
    try:
        path = Path(value).expanduser().resolve()
    except (OSError, RuntimeError):
        raise MaterialError("input_file_invalid") from None
    if not path.is_file():
        raise MaterialError("input_file_missing")
    extension = path.suffix.casefold()
    if extension not in SUPPORTED_EXTENSIONS:
        raise MaterialError("unsupported_material_type")
    try:
        size = path.stat().st_size
    except OSError:
        raise MaterialError("input_file_unreadable") from None
    if size > MAX_INPUT_BYTES:
        raise MaterialError("input_too_large")
    return path, extension, size


def _office_container_check(path: Path, extension: str) -> None:
    if extension not in OFFICE_EXTENSIONS:
        return
    try:
        with zipfile.ZipFile(path) as archive:
            expanded = sum(max(0, item.file_size) for item in archive.infolist())
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile):
        raise MaterialError("office_container_invalid") from None
    if expanded > MAX_OFFICE_EXPANDED_BYTES:
        raise MaterialError("office_container_too_large")


def _runtime_python(explicit: str | None, config_path: str | None) -> Path:
    value = explicit
    if not value:
        loaded = runtime_config.load_config(config_path)
        if loaded.get("status") != "ok":
            raise MaterialError("material_runtime_not_configured")
        value = runtime_config.runtime_path(loaded.get("data") or {}, "material")
    if not isinstance(value, str) or not value.strip():
        raise MaterialError("material_runtime_not_configured")
    candidate = Path(value).expanduser()
    if not candidate.is_file():
        found = shutil.which(value)
        if found:
            candidate = Path(found)
    try:
        candidate = candidate.resolve()
    except OSError:
        raise MaterialError("material_runtime_unavailable") from None
    if not candidate.is_file():
        raise MaterialError("material_runtime_unavailable")
    return candidate


def _safe_environment() -> dict[str, str]:
    allowed = {
        "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
        "LOCALAPPDATA", "PROGRAMDATA", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
        "SSL_CERT_FILE", "SSL_CERT_DIR",
    }
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    env.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    return env


def _request_key(input_hash: str, source_url: str | None, extension: str, timeout: float) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "input_sha256": input_hash,
        "source_url": source_url,
        "extension": extension,
        "converter": {"name": "markitdown", "version": EXPECTED_VERSION},
        "options": {"plugins_enabled": False, "llm": False, "remote_fetch": False, "timeout_seconds": timeout},
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _preview(raw: bytes) -> tuple[str, bool]:
    text = raw.decode("utf-8")
    display = text.lstrip("\ufeff")
    return display[:PREVIEW_CHARS], len(display) > PREVIEW_CHARS


def _load_existing(target: Path, request_key: str, input_hash: str) -> dict[str, Any] | None:
    report_path = target / "report.md"
    metadata_path = target / "metadata.json"
    if not report_path.exists() and not metadata_path.exists():
        if target.exists() and any(target.iterdir()):
            raise MaterialError("destination_not_empty")
        return None
    if not report_path.is_file() or not metadata_path.is_file() or report_path.is_symlink() or metadata_path.is_symlink():
        raise MaterialError("destination_artifacts_incomplete")
    try:
        body = report_path.read_bytes()
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise MaterialError("destination_artifact_damaged") from None
    if len(body) > MAX_OUTPUT_BYTES:
        raise MaterialError("destination_artifact_damaged")
    if not isinstance(metadata, dict) or metadata.get("schema_version") != SCHEMA_VERSION:
        raise MaterialError("destination_metadata_invalid")
    report_info = metadata.get("report")
    source_info = metadata.get("input")
    recorded_hash = report_info.get("sha256") if isinstance(report_info, dict) else None
    recorded_input = source_info.get("sha256") if isinstance(source_info, dict) else None
    if not isinstance(recorded_hash, str) or not isinstance(recorded_input, str):
        raise MaterialError("destination_metadata_invalid")
    if hashlib.sha256(body).hexdigest() != recorded_hash:
        raise MaterialError("destination_artifact_damaged")
    if recorded_input != input_hash or metadata.get("request_key") != request_key:
        raise MaterialError("destination_exists_with_different_request")
    preview, truncated = _preview(body)
    return {
        "status": "reused",
        "report_dir": str(target),
        "report_file": str(report_path),
        "metadata_file": str(metadata_path),
        "source_url": (metadata.get("source") or {}).get("url"),
        "input_name": (source_info or {}).get("name"),
        "input_sha256": input_hash,
        "input_byte_length": (source_info or {}).get("byte_length"),
        "request_key": request_key,
        "converter_version": (metadata.get("tool") or {}).get("version"),
        "body_sha256": recorded_hash,
        "byte_length": len(body),
        "preview": preview,
        "preview_truncated": truncated,
        "network_used": False,
        "untrusted_source_data": True,
    }


def _run_worker(python_path: Path, source: Path, timeout: float) -> dict[str, Any]:
    worker = Path(__file__).with_name("material_worker.py")
    request = json.dumps({"source_path": str(source)}, ensure_ascii=False).encode("utf-8")
    command = [str(python_path), "-X", "utf8", "-I", "-B", str(worker)]
    try:
        completed = subprocess.run(
            command,
            input=request,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_safe_environment(),
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise MaterialError("conversion_timeout") from None
    except OSError:
        raise MaterialError("material_worker_failed") from None
    if len(completed.stdout) > MAX_WORKER_STDOUT_BYTES:
        raise MaterialError("converted_output_too_large")
    try:
        payload = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise MaterialError("material_worker_protocol_invalid") from None
    if not isinstance(payload, dict):
        raise MaterialError("material_worker_protocol_invalid")
    if completed.returncode != 0 or payload.get("status") == "error":
        reason = payload.get("reason")
        if reason in {"material_runtime_missing", "converter_version_mismatch", "input_file_missing", "converted_output_too_large"}:
            raise MaterialError(str(reason))
        raise MaterialError("conversion_failed" if not isinstance(reason, str) else reason)
    return payload


def _augment_metadata(
    metadata_path: Path,
    source_url: str | None,
    source: Path,
    input_hash: str,
    input_bytes: int,
    request_key: str,
    timeout: float,
    started_at: str,
    finished_at: str,
    converter_version: str,
) -> dict[str, Any]:
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise MaterialError("destination_metadata_invalid") from None
    if not isinstance(metadata, dict):
        raise MaterialError("destination_metadata_invalid")
    metadata["source"] = {
        **(metadata.get("source") if isinstance(metadata.get("source"), dict) else {}),
        "url": source_url,
        "acquisition_method": "markitdown_local",
    }
    metadata.update(
        {
            "request_key": request_key,
            "input": {"name": source.name, "sha256": input_hash, "byte_length": input_bytes},
            "tool": {"name": "markitdown", "version": converter_version},
            "options": {
                "plugins_enabled": False,
                "llm_client": False,
                "azure_endpoint": False,
                "remote_url": False,
                "timeout_seconds": timeout,
            },
            "timing": {"started_at": started_at, "finished_at": finished_at},
            "lossy_boundary": {
                "statement": "Conversion produces Markdown context and does not promise source-layout or table fidelity.",
                "known_limits": [
                    "PDFs are supported for text-layer extraction; scanned PDFs may have no extractable text.",
                    "Images, formatting, formulas, links, and tables may be simplified or omitted by the converter.",
                    "The local input was converted without factual, link, or citation verification.",
                ],
            },
        }
    )
    try:
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    except OSError:
        raise MaterialError("destination_metadata_write_failed") from None
    return metadata


def convert(
    input_value: str,
    out_dir: str,
    python_path: str | None,
    config_path: str | None,
    source_url_value: str | None,
    timeout: float,
) -> dict[str, Any]:
    source_url = _validate_source_url(source_url_value)
    source, extension, _ = _resolve_input(input_value)
    input_hash, input_bytes = _sha256_path(source)
    _office_container_check(source, extension)
    if not 1.0 <= timeout <= MAX_TIMEOUT:
        raise MaterialError("timeout_out_of_range")
    request_key = _request_key(input_hash, source_url, extension, timeout)
    target = Path(out_dir).expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise MaterialError("destination_must_be_directory")
    existing = _load_existing(target, request_key, input_hash) if target.exists() else None
    if existing is not None:
        return existing

    runtime = _runtime_python(python_path, config_path)
    started_at = _now()
    worker_result = _run_worker(runtime, source, timeout)
    if worker_result.get("status") == "no_results" or not str(worker_result.get("markdown") or "").strip():
        raise MaterialError("no_extractable_text")
    markdown = worker_result.get("markdown")
    converter_version = worker_result.get("converter_version")
    if not isinstance(markdown, str) or not isinstance(converter_version, str):
        raise MaterialError("material_worker_protocol_invalid")
    body = markdown.encode("utf-8")
    if len(body) > MAX_OUTPUT_BYTES:
        raise MaterialError("converted_output_too_large")

    parent = target.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise MaterialError("destination_parent_unwritable") from None
    stage = Path(tempfile.mkdtemp(prefix="field-search-material-", dir=str(parent)))
    try:
        stage_report = stage / "converted.md"
        stage_report.write_bytes(body)
        stage_artifact = stage / "artifact"
        result = report.import_report(str(stage_report), str(stage_artifact), source_url, "markitdown_local", PREVIEW_CHARS)
        finished_at = _now()
        metadata = _augment_metadata(
            stage_artifact / "metadata.json",
            source_url,
            source,
            input_hash,
            input_bytes,
            request_key,
            timeout,
            started_at,
            finished_at,
            converter_version,
        )
        try:
            os.replace(stage_artifact, target)
        except OSError:
            raise MaterialError("destination_create_failed") from None
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    preview, truncated = _preview(body)
    return {
        "status": result.get("status", "imported"),
        "report_dir": str(target),
        "report_file": str(target / "report.md"),
        "metadata_file": str(target / "metadata.json"),
        "source_url": source_url,
        "input_name": source.name,
        "input_sha256": input_hash,
        "input_byte_length": input_bytes,
        "request_key": request_key,
        "converter_version": converter_version,
        "body_sha256": (metadata.get("report") or {}).get("sha256"),
        "byte_length": (metadata.get("report") or {}).get("byte_length"),
        "preview": preview,
        "preview_truncated": truncated,
        "network_used": False,
        "untrusted_source_data": True,
    }


def _print(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="search.py convert", description=__doc__)
    parser.add_argument("input", help="local PDF, DOCX, PPTX, XLSX, HTML/HTM, TXT, or CSV")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--python-path")
    parser.add_argument("--config")
    parser.add_argument("--source-url")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    try:
        result = convert(args.input, args.out_dir, args.python_path, args.config, args.source_url, args.timeout)
        _print(result)
        return 0
    except (MaterialError, ValueError, OSError) as exc:
        _print({"status": "error", "reason": str(exc), "network_used": False})
        return 2
    except Exception:
        _print({"status": "error", "reason": "material_route_error", "network_used": False})
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
