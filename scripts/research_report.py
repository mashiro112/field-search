"""Archive a DOM-captured Deep Research report and index it with report.py.

Input is an explicit JSON capture with ``html``, ``sources``, ``counts``,
``source_url`` and ``method`` fields. No network access or browser control.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    from report import import_report, _resolve_report
except ImportError:  # package import
    from .report import import_report, _resolve_report


MAX_CAPTURE_BYTES = 2 * 1024 * 1024


class _Text(HTMLParser):
    """Small semantic HTML-to-Markdown renderer; keeps table structure."""
    BLOCKS = {"p", "div", "section", "article", "ul", "ol", "li", "blockquote", "tr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.table = False
        self.row: list[str] = []
        self.table_rows = 0
        self.cell = ""
        self.citations: list[str] = []
        self.links: list[str] = []
        self.list_stack: list[tuple[str, int]] = []
        self.suppress_sup = 0
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag in {"script", "style", "svg", "button", "nav"}:
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "table":
            self.table = True
            self.table_rows = 0
            self.parts.append("\n")
        elif tag == "tr":
            self.row = []
        elif tag in {"th", "td"} and self.table:
            self.cell = ""
        elif tag == "sup" and "data-citation-index" in a:
            idx = a["data-citation-index"] or ""
            if idx:
                self.citations.append(idx)
                self._append(f"[source {idx}]")
                self.suppress_sup += 1
        elif tag == "sup":
            self._append("^")
        elif tag == "sub":
            self._append("~")
        elif tag in {"ul", "ol"}:
            self.list_stack.append((tag, 0))
        elif tag == "li":
            if self.list_stack:
                kind, number = self.list_stack[-1]
                number += 1
                self.list_stack[-1] = (kind, number)
                self._append("\n" + (f"{number}. " if kind == "ol" else "- "))
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._append("\n" + "#" * int(tag[1]) + " ")
        elif tag == "br":
            self._append("\n")
        elif tag == "a" and a.get("href"):
            self._append("[")
            self.links.append(a["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg", "button", "nav"} and self.skip:
            self.skip -= 1
            return
        if self.skip:
            return
        if tag == "sup" and self.suppress_sup:
            self.suppress_sup -= 1
            return
        if tag == "sub" or tag == "sup":
            self._append("")
        elif tag in {"ul", "ol"} and self.list_stack:
            self.list_stack.pop()
        elif tag in {"th", "td"} and self.table:
            self.row.append(re.sub(r"\s+", " ", self.cell).strip().replace("|", "\\|"))
            self.cell = ""
        elif tag == "tr" and self.table and self.row:
            self.parts.append("| " + " | ".join(self.row) + " |\n")
            if self.table_rows == 0:
                self.parts.append("| " + " | ".join("---" for _ in self.row) + " |\n")
            self.table_rows += 1
            self.row = []
        elif tag == "table":
            self.table = False
            self.parts.append("\n")
        elif tag == "a" and self.links:
            self._append(f"]({self.links.pop()})")
        elif tag in self.BLOCKS or tag.startswith("h") and len(tag) == 2:
            self._append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip or self.suppress_sup or not data:
            return
        if self.table and self.cell is not None:
            self.cell += data
        else:
            self._append(data)

    def _append(self, value: str) -> None:
        if self.table and self.cell is not None:
            self.cell += value
        else:
            self.parts.append(value)

    def markdown(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


def _convert(capture: dict[str, Any]) -> tuple[str, list[str]]:
    if not isinstance(capture.get("html"), str):
        raise ValueError("capture_html_missing")
    sources = capture.get("sources")
    if not isinstance(sources, list):
        raise ValueError("capture_sources_missing")
    parser = _Text()
    parser.feed(capture["html"])
    body = parser.markdown()
    by_index: dict[str, dict[str, Any]] = {}
    for src in sources:
        if not isinstance(src, dict) or src.get("index") is None or not isinstance(src.get("url"), str):
            raise ValueError("capture_source_invalid")
        key = str(src["index"])
        if key in by_index:
            raise ValueError("capture_duplicate_source_index")
        by_index[key] = src
    missing = sorted(set(parser.citations) - set(by_index))
    source_block = ["", "## Captured source links", ""]
    for key in sorted(by_index, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x)):
        src = by_index[key]
        label = str(src.get("label") or src.get("title") or f"Source {key}").replace("\n", " ")
        source_block.append(f"- [{key}] {label}: {src['url']}")
    if missing:
        source_block += ["", "Unmapped citation indexes: " + ", ".join(missing)]
    return body + "\n".join(source_block) + "\n", parser.citations


def _measure(html: str) -> dict[str, int]:
    parser = _Text()
    parser.feed(html)
    # Parse the original semantic fragment, independently of rendered Markdown.
    from html.parser import HTMLParser

    class Counts(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.headings = self.tables = self.cells = self.citations = 0

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            self.headings += int(tag in {"h1", "h2", "h3", "h4", "h5", "h6"})
            self.tables += int(tag == "table")
            self.cells += int(tag in {"th", "td"})
            if tag == "sup" and "data-citation-index" in dict(attrs):
                self.citations += 1

    counts = Counts()
    counts.feed(html)
    return {"headings": counts.headings, "tables": counts.tables,
            "table_cells": counts.cells, "citation_occurrences": counts.citations}


def _checked_counts(capture: dict[str, Any]) -> dict[str, Any]:
    declared = capture.get("counts")
    if not isinstance(declared, dict):
        raise ValueError("capture_counts_missing")
    measured = _measure(capture["html"])
    checks = {key: {"declared": declared.get(key), "measured": value,
                    "match": declared.get(key) == value}
              for key, value in measured.items()}
    return {"measured": measured, "checks": checks,
            "all_match": all(x["match"] for x in checks.values())}


def _source_warnings(sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{"index": str(src["index"]),
             "warning": "source_url_contains_title_like_encoding_and_ellipsis; preserved_verbatim; destination_unverified"}
            for src in sources if "%20" in src["url"] and "..." in src["url"]]


def archive(input_path: str, out_dir: str) -> dict[str, Any]:
    source = Path(input_path).resolve()
    if source.stat().st_size > MAX_CAPTURE_BYTES:
        raise ValueError("capture_too_large")
    raw = source.read_bytes()
    if len(raw) > MAX_CAPTURE_BYTES:
        raise ValueError("capture_too_large")
    capture = json.loads(raw.decode("utf-8"))
    if not isinstance(capture, dict):
        raise ValueError("capture_root_invalid")
    if not isinstance(capture.get("html"), str):
        raise ValueError("capture_html_missing")
    count_check = _checked_counts(capture)
    markdown, citations = _convert(capture)
    source_indexes = {str(s["index"]) for s in capture["sources"]}
    unmapped = sorted(set(citations) - source_indexes)
    source_warnings = _source_warnings(capture["sources"])
    expected_status = "ok" if count_check["all_match"] and not unmapped else "partial"
    expected_receipt = {
        "status": expected_status, "source_url": capture.get("source_url"),
        "declared_counts": capture.get("counts"), "count_check": count_check,
        "captured_citation_occurrences": len(citations),
        "unique_citation_indexes": len(set(citations)), "source_records": len(capture["sources"]),
        "unmapped_citation_indexes": unmapped, "source_url_warnings": source_warnings,
        "fact_verification": "not_performed",
    }
    root = Path(out_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    raw_path = root / "research_report_capture.json"
    receipt_path = root / "research_report_archive.json"
    md_input = root / "research_report_import.md"
    if raw_path.exists() and raw_path.read_bytes() != raw:
        raise ValueError("capture_exists_with_different_content")
    if receipt_path.exists():
        try:
            old = json.loads(receipt_path.read_text(encoding="utf-8"))
            old_md = md_input.read_bytes()
            _, report_path, _, report_meta, report_text = _resolve_report(str(root / "report"))
            report_raw = report_path.read_bytes()
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            raise ValueError("existing_archive_integrity_check_failed") from None
        if (not raw_path.is_file() or hashlib.sha256(raw_path.read_bytes()).hexdigest() != old.get("capture_sha256")
                or hashlib.sha256(old_md).hexdigest() != old.get("markdown_sha256")
                or hashlib.sha256(report_raw).hexdigest() != old.get("markdown_sha256")
                or hashlib.sha256(report_text.encode("utf-8")).hexdigest() != old.get("markdown_sha256")
                or hashlib.sha256(report_raw).hexdigest() != (report_meta.get("report") or {}).get("sha256")
                or old.get("capture_sha256") != hashlib.sha256(raw).hexdigest()
                or any(old.get(key) != value for key, value in expected_receipt.items())):
            raise ValueError("existing_archive_integrity_check_failed")
        return old
    if not raw_path.exists():
        raw_path.write_bytes(raw)
    if md_input.exists() and md_input.read_text(encoding="utf-8") != markdown:
        raise ValueError("markdown_exists_with_different_content")
    md_input.write_text(markdown, encoding="utf-8", newline="\n")
    imported = import_report(str(md_input), str(root / "report"), capture.get("source_url"),
                             "copy", 600)
    summary = {
        "status": expected_status,
        "capture_sha256": hashlib.sha256(raw).hexdigest(),
        "capture_path": str(raw_path),
        "markdown_path": imported["report_file"],
        "metadata_path": imported["metadata_file"],
        "source_url": capture.get("source_url"),
        "declared_counts": capture.get("counts"),
        "count_check": count_check,
        "captured_citation_occurrences": len(citations),
        "unique_citation_indexes": len(set(citations)),
        "source_records": len(capture["sources"]),
        "unmapped_citation_indexes": unmapped,
        "source_url_warnings": source_warnings,
        "fact_verification": "not_performed",
        "import": {k: imported.get(k) for k in ("status", "title", "heading_count", "line_count", "sha256")},
        "offline_access": "use search.py report open/find against report directory",
        "markdown_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
    }
    receipt_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Archive an explicit DOM-captured research report; no network access")
    parser.add_argument("capture", help="JSON capture with html/sources/counts/source_url/method")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(archive(args.capture, args.out_dir), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False))
        return 2
    except (KeyError, TypeError, AttributeError):
        print(json.dumps({"status": "error", "reason": "invalid_capture_schema"}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
