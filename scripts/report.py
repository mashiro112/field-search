"""Import and read a local Markdown research report without network access.

The report body is copied byte-for-byte to ``report.md``.  Metadata is kept in
an independent ``metadata.json`` file so source attribution and integrity state
do not become part of the untrusted report body.  ``open`` and ``find`` are
offline operations; report links, commands, and prompt-like text are data only.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib import parse
from typing import Any


SCHEMA_VERSION = 1
MAX_BYTES = 32 * 1024 * 1024
MAX_OUTLINE = 60
MAX_MATCHES = 20
MAX_DISPLAY_CHARS = 240
DEFAULT_PAGE_CHARS = 6000
DEFAULT_PREVIEW_CHARS = 600
MARKDOWN_SUFFIXES = {".md", ".markdown"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _display(value: str, limit: int = MAX_DISPLAY_CHARS) -> str:
    if len(value) <= limit:
        return value
    return value[:limit - 1] + "…"


def _validate_source_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    candidate = value.strip()
    try:
        parsed = parse.urlsplit(candidate)
    except ValueError:
        raise ValueError("source_url_invalid") from None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("source_url_invalid")
    return candidate


def _read_markdown(path_value: str) -> tuple[Path, bytes, str]:
    path = Path(path_value).expanduser()
    if not path.is_file():
        raise ValueError("input_file_missing")
    if path.suffix.casefold() not in MARKDOWN_SUFFIXES:
        raise ValueError("input_file_must_be_markdown")
    try:
        raw = path.read_bytes()
    except OSError:
        raise ValueError("input_file_unreadable") from None
    if len(raw) > MAX_BYTES:
        raise ValueError("report_too_large")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("input_file_must_be_utf8") from None
    return path.resolve(), raw, text


def _outline(text: str) -> tuple[str, list[dict[str, Any]], int]:
    """Extract a bounded heading outline without interpreting Markdown."""

    title = "Untitled report"
    headings: list[dict[str, Any]] = []
    heading_count = 0
    in_fence = False
    fence_marker = ""
    display_text = text.lstrip("\ufeff")
    for line_number, line in enumerate(display_text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
            continue
        if in_fence:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        level = len(match.group(1))
        heading = match.group(2).strip()
        if not heading:
            continue
        if title == "Untitled report":
            title = _display(heading)
        heading_count += 1
        if len(headings) < MAX_OUTLINE:
            headings.append({"level": level, "text": _display(heading), "line": line_number})
    return title, headings, heading_count


def _metadata(raw: bytes, text: str, title: str, headings: list[dict[str, Any]],
              heading_count: int, source_url: str | None, method: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ok",
        "imported_at": _now(),
        "source": {
            "url": source_url,
            "acquisition_method": method,
            "format": "text/markdown",
        },
        "report": {
            "path": "report.md",
            "sha256": _sha256(raw),
            "byte_length": len(raw),
            "character_count": len(text),
            "line_count": len(text.splitlines()),
            "title": title,
            "heading_count": heading_count,
        },
        "integrity": {
            "status": "unverified",
            "link_completeness": "unknown",
            "fact_verification": "not_performed",
            "notes": [
                "The Markdown body was copied locally; import is not factual verification.",
                "A recorded source URL is metadata only and does not prove citation completeness.",
            ],
        },
    }


def _paths(directory: str) -> tuple[Path, Path, Path]:
    root = Path(directory).expanduser().resolve()
    return root, root / "report.md", root / "metadata.json"


def _load_metadata(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("destination_metadata_invalid") from None
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("destination_metadata_invalid")
    report = value.get("report")
    if not isinstance(report, dict) or not isinstance(report.get("sha256"), str):
        raise ValueError("destination_metadata_invalid")
    return value


def _summary(root: Path, report_path: Path, metadata_path: Path,
             metadata: dict[str, Any], text: str, headings: list[dict[str, Any]],
             heading_count: int,
             status: str, preview_chars: int) -> dict[str, Any]:
    report = metadata.get("report") or {}
    source = metadata.get("source") or {}
    preview = text.lstrip("\ufeff")[:preview_chars]
    return {
        "status": status,
        "report_dir": str(root),
        "report_file": str(report_path),
        "metadata_file": str(metadata_path),
        "title": _display(str(report.get("title") or "Untitled report")),
        "heading_count": heading_count,
        "line_count": report.get("line_count", len(text.splitlines())),
        "byte_length": report.get("byte_length", len(text.encode("utf-8"))),
        "sha256": report.get("sha256"),
        "source_url": source.get("url"),
        "acquisition_method": source.get("acquisition_method"),
        "integrity_status": (metadata.get("integrity") or {}).get("status", "unverified"),
        "outline": headings[:20],
        "outline_truncated": heading_count > len(headings[:20]),
        "preview": preview,
        "preview_truncated": len(text.lstrip("\ufeff")) > preview_chars,
        "network_used": False,
        "untrusted_source_data": True,
    }


def import_report(input_path: str, out_dir: str, source_url: str | None,
                  method: str, preview_chars: int) -> dict[str, Any]:
    source_path, raw, text = _read_markdown(input_path)
    source_url = _validate_source_url(source_url)
    title, headings, heading_count = _outline(text)
    metadata = _metadata(raw, text, title, headings, heading_count, source_url, method)
    root, report_path, metadata_path = _paths(out_dir)
    root.mkdir(parents=True, exist_ok=True)

    if report_path.exists():
        try:
            existing_raw = report_path.read_bytes()
        except OSError:
            raise ValueError("destination_report_unreadable") from None
        if existing_raw != raw:
            raise ValueError("destination_exists_with_different_content")
        if not metadata_path.is_file():
            raise ValueError("destination_metadata_missing")
        existing_metadata = _load_metadata(metadata_path)
        existing_report = existing_metadata.get("report") or {}
        if existing_report.get("sha256") != _sha256(existing_raw):
            raise ValueError("destination_metadata_hash_mismatch")
        return _summary(root, report_path, metadata_path, existing_metadata, text, headings,
                        heading_count,
                        "reused", preview_chars)
    if metadata_path.exists():
        raise ValueError("destination_metadata_exists_without_report")

    try:
        with report_path.open("xb") as handle:
            handle.write(raw)
        with metadata_path.open("x", encoding="utf-8") as handle:
            json.dump(metadata, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except FileExistsError:
        raise ValueError("destination_changed_during_import") from None
    except OSError:
        raise ValueError("destination_write_failed") from None
    return _summary(root, report_path, metadata_path, metadata, text, headings,
                    heading_count,
                    "imported", preview_chars)


def _resolve_report(target: str) -> tuple[Path, Path, Path, dict[str, Any], str]:
    candidate = Path(target).expanduser()
    if candidate.is_file() and candidate.name.casefold() == "report.md":
        root = candidate.parent.resolve()
    elif candidate.is_dir():
        root = candidate.resolve()
    else:
        raise ValueError("report_directory_missing")
    report_path = root / "report.md"
    metadata_path = root / "metadata.json"
    if not report_path.is_file() or not metadata_path.is_file():
        raise ValueError("report_artifacts_missing")
    metadata = _load_metadata(metadata_path)
    try:
        raw = report_path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        raise ValueError("report_body_unreadable") from None
    report = metadata.get("report") or {}
    if _sha256(raw) != report.get("sha256"):
        raise ValueError("report_content_hash_mismatch")
    return root, report_path, metadata_path, metadata, text


def _paginate(text: str, page_chars: int) -> list[str]:
    try:
        from websearch.layer3_agentio.pagination import paginate
        pages = paginate(text, page_size_tokens=page_chars, chars_per_token=1.0)
    except (ImportError, ModuleNotFoundError):
        pages = [text[index:index + page_chars] for index in range(0, len(text), page_chars)]
    return pages or [""]


def open_report(target: str, page: int, page_chars: int) -> dict[str, Any]:
    root, report_path, metadata_path, metadata, text = _resolve_report(target)
    pages = _paginate(text, page_chars)
    if not 1 <= page <= len(pages):
        raise ValueError("page_out_of_range")
    report = metadata.get("report") or {}
    title, headings, heading_count = _outline(text)
    return {
        "status": "ok",
        "report_dir": str(root),
        "report_file": str(report_path),
        "metadata_file": str(metadata_path),
        "title": _display(str(report.get("title") or title)),
        "heading_count": heading_count,
        "integrity_status": (metadata.get("integrity") or {}).get("status", "unverified"),
        "page": page,
        "total_pages": len(pages),
        "has_more": page < len(pages),
        "page_chars": page_chars,
        "text": pages[page - 1],
        "outline": headings[:20],
        "outline_truncated": heading_count > len(headings[:20]),
        "network_used": False,
        "untrusted_source_data": True,
    }


def find_report(target: str, term: str, page_chars: int) -> dict[str, Any]:
    if not term:
        raise ValueError("find_requires_term")
    if len(term) > 200:
        raise ValueError("find_term_too_long")
    root, report_path, metadata_path, metadata, text = _resolve_report(target)
    pages = _paginate(text, page_chars)
    ends: list[int] = []
    end = 0
    for page_text in pages:
        end += len(page_text)
        ends.append(end)
    matches: list[dict[str, Any]] = []
    total = 0
    for match in re.finditer(re.escape(term), text, flags=re.IGNORECASE):
        total += 1
        if len(matches) >= MAX_MATCHES:
            continue
        start = match.start()
        finish = match.end()
        matches.append({
            "page": bisect_right(ends, start) + 1,
            "end_page": bisect_right(ends, max(start, finish - 1)) + 1,
            "excerpt": text[max(0, start - 120):min(len(text), finish + 240)],
        })
    report = metadata.get("report") or {}
    return {
        "status": "ok",
        "report_dir": str(root),
        "report_file": str(report_path),
        "metadata_file": str(metadata_path),
        "title": _display(str(report.get("title") or _outline(text)[0])),
        "integrity_status": (metadata.get("integrity") or {}).get("status", "unverified"),
        "query": term,
        "total_matches": total,
        "matches": matches,
        "matches_truncated": total > len(matches),
        "match_scope": "literal case-insensitive match over the complete local report; first 20 excerpts",
        "page_chars": page_chars,
        "network_used": False,
        "untrusted_source_data": True,
    }


def _print(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="search.py report",
        description="Import and read a local UTF-8 Markdown report without network access",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    importer = commands.add_parser("import", help="copy a local Markdown file into an explicit report directory")
    importer.add_argument("input", help="explicit local UTF-8 .md/.markdown file")
    importer.add_argument("--out-dir", required=True, help="explicit task-local output directory")
    importer.add_argument("--source-url", help="optional source URL recorded as metadata; never fetched")
    importer.add_argument("--method", choices=("copy", "docs_export", "local_file"), default="local_file")
    importer.add_argument("--preview-chars", type=int, default=DEFAULT_PREVIEW_CHARS)
    opener = commands.add_parser("open", help="read one local report page")
    opener.add_argument("target", help="report directory or its report.md")
    opener.add_argument("--page", type=int, default=1)
    opener.add_argument("--page-chars", type=int, default=DEFAULT_PAGE_CHARS)
    finder = commands.add_parser("find", help="find a literal term in a local report")
    finder.add_argument("target", help="report directory or its report.md")
    finder.add_argument("term")
    finder.add_argument("--page-chars", type=int, default=DEFAULT_PAGE_CHARS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "import":
            if not 100 <= args.preview_chars <= 2000:
                raise ValueError("preview_chars_out_of_range")
            result = import_report(args.input, args.out_dir, args.source_url, args.method, args.preview_chars)
        elif args.command == "open":
            if args.page < 1 or not 1000 <= args.page_chars <= 12000:
                raise ValueError("page_or_page_chars_out_of_range")
            result = open_report(args.target, args.page, args.page_chars)
        else:
            if not 1000 <= args.page_chars <= 12000:
                raise ValueError("page_chars_out_of_range")
            result = find_report(args.target, args.term, args.page_chars)
        _print(result)
        return 0
    except (ValueError, OSError) as exc:
        _print({"status": "error", "reason": str(exc), "network_used": False})
        return 2
    except Exception as exc:
        # Do not echo report content or exception payloads from untrusted data.
        _print({"status": "error", "reason": "report_route_error", "error_type": type(exc).__name__, "network_used": False})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
