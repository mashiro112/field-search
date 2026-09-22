"""Isolated MarkItDown 0.1.8 worker for local material conversion.

The parent route communicates through one UTF-8 JSON request and response. The
worker accepts only a local path supplied by the parent, disables plugins, and
never receives a URL, LLM client, or cloud endpoint.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys


MAX_REQUEST_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 32 * 1024 * 1024
EXPECTED_VERSION = "0.1.8"


def _emit(payload: dict[str, object]) -> None:
    raw = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def main() -> int:
    try:
        request_raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        if len(request_raw) > MAX_REQUEST_BYTES:
            _emit({"status": "error", "reason": "worker_request_too_large"})
            return 2
        request = json.loads(request_raw.decode("utf-8"))
        source_value = request.get("source_path") if isinstance(request, dict) else None
        if not isinstance(source_value, str) or not source_value:
            _emit({"status": "error", "reason": "worker_source_invalid"})
            return 2
        source = Path(source_value)
        if not source.is_file():
            _emit({"status": "error", "reason": "input_file_missing"})
            return 2

        from markitdown import MarkItDown, __version__

        if __version__ != EXPECTED_VERSION:
            _emit({"status": "error", "reason": "converter_version_mismatch", "converter_version": __version__})
            return 2
        converter = MarkItDown(enable_plugins=False)
        result = converter.convert(source)
        markdown = result.markdown if isinstance(result.markdown, str) else str(result.markdown)
        encoded = markdown.encode("utf-8")
        if len(encoded) > MAX_OUTPUT_BYTES:
            _emit({"status": "error", "reason": "converted_output_too_large"})
            return 2
        if not markdown.strip():
            _emit({
                "status": "no_results",
                "reason": "no_extractable_text",
                "converter_version": __version__,
                "markdown": "",
                "title": result.title,
            })
            return 0
        _emit({
            "status": "ok",
            "converter_version": __version__,
            "markdown": markdown,
            "title": result.title,
        })
        return 0
    except ModuleNotFoundError:
        _emit({"status": "error", "reason": "material_runtime_missing"})
        return 2
    except (UnicodeDecodeError, json.JSONDecodeError):
        _emit({"status": "error", "reason": "worker_request_invalid"})
        return 2
    except Exception:
        # Do not echo converter exception text: it may include local paths or
        # untrusted document data. The parent reports this bounded reason.
        _emit({"status": "error", "reason": "conversion_failed"})
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
