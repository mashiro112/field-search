"""Find literal evidence across an explicit task-local list of saved FS artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Sequence

import document
import report


MAX_MANIFEST_BYTES = 1024 * 1024
MAX_ARTIFACTS = 30
MAX_MATCHES = 20
MAX_PER_ARTIFACT = 3
MAX_TERM_CHARS = 200
MAX_SCAN_BYTES = 64 * 1024 * 1024
MAX_COUNTED_MATCHES = 10000


def _manifest(path_value: str) -> list[dict[str, str]]:
    path = Path(path_value).expanduser().resolve()
    if path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError("manifest_too_large")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    artifacts = value.get("artifacts") if isinstance(value, dict) else None
    if not isinstance(artifacts, list) or not 1 <= len(artifacts) <= MAX_ARTIFACTS:
        raise ValueError("artifacts_must_be_1_to_30_items")
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for item in artifacts:
        if not isinstance(item, dict) or set(item) != {"id", "kind", "path"}:
            raise ValueError("artifact_fields_must_be_id_kind_path")
        artifact_id, kind, raw_path = item["id"], item["kind"], item["path"]
        if not isinstance(artifact_id, str) or not artifact_id.strip() or len(artifact_id) > 80 or artifact_id in seen:
            raise ValueError("artifact_ids_must_be_unique_and_bounded")
        if kind not in {"document", "report"} or not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError("artifact_kind_or_path_invalid")
        target = Path(raw_path).expanduser()
        if not target.is_absolute():
            target = path.parent / target
        seen.add(artifact_id)
        result.append({"id": artifact_id, "kind": kind, "path": str(target.resolve())})
    return result


def _load_artifact(item: dict[str, str]) -> tuple[str, dict[str, Any]]:
    if item["kind"] == "document":
        doc = document.load_document(item["path"])
        return doc["content"], {
            "url": doc.get("url"), "version_sha256": doc["content_sha256"],
            "snapshot_at": doc.get("fetched_at"), "version_kind": "extracted_document_text",
            "extraction": doc.get("extraction"),
        }
    _root, _report_path, _metadata_path, metadata, text = report._resolve_report(item["path"])
    source = metadata.get("source") or {}
    info = metadata.get("report") or {}
    return text, {
        "url": source.get("url"), "ref": source.get("ref"),
        "title": info.get("title"), "version_sha256": info.get("sha256"),
        "snapshot_at": metadata.get("imported_at"), "version_kind": "stored_report_markdown",
        "integrity_status": (metadata.get("integrity") or {}).get("status", "unknown"),
    }


def find(manifest_path: str, term: str) -> dict[str, Any]:
    if not term or len(term) > MAX_TERM_CHARS or any(ord(char) < 32 for char in term):
        raise ValueError("term_must_be_1_to_200_printable_characters")
    artifacts = _manifest(manifest_path)
    matches: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    total = valid = 0
    scanned_bytes = 0
    count_limited = False
    seen_hashes: dict[str, str] = {}
    for item in artifacts:
        if count_limited:
            failures.append({"id": item["id"], "reason": "match_count_budget_exceeded"})
            continue
        try:
            text, provenance = _load_artifact(item)
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            failures.append({"id": item["id"], "reason": "artifact_missing_damaged_or_invalid"})
            continue
        encoded = text.encode("utf-8")
        if scanned_bytes + len(encoded) > MAX_SCAN_BYTES:
            failures.append({"id": item["id"], "reason": "text_scan_budget_exceeded"})
            continue
        scanned_bytes += len(encoded)
        valid += 1
        digest = hashlib.sha256(encoded).hexdigest()
        same_content_as = seen_hashes.get(digest)
        seen_hashes.setdefault(digest, item["id"])
        local_count = 0
        for match in re.finditer(re.escape(term), text, flags=re.IGNORECASE):
            if total >= MAX_COUNTED_MATCHES:
                count_limited = True
                break
            total += 1
            if local_count >= MAX_PER_ARTIFACT or len(matches) >= MAX_MATCHES:
                continue
            start, end = match.span()
            matches.append({
                "artifact_id": item["id"], "kind": item["kind"], "artifact_path": item["path"],
                "source": provenance, "same_content_as": same_content_as,
                "char_start": start, "char_end": end,
                "line": text.count("\n", 0, start) + 1,
                "exact": text[start:end],
                "excerpt": text[max(0, start - 100):min(len(text), end + 160)],
            })
            local_count += 1
    if not valid:
        status = "error"
    elif failures or total > len(matches) or count_limited:
        status = "partial"
    else:
        status = "ok" if total else "no_results"
    return {
        "status": status, "query": term, "artifacts": len(artifacts),
        "valid_artifacts": valid, "total_matches": total,
        "total_matches_exact": not count_limited,
        "returned_matches": len(matches), "matches_truncated": total > len(matches) or count_limited,
        "matches": matches, "failures": failures,
        "scanned_bytes": scanned_bytes, "scan_budget_bytes": MAX_SCAN_BYTES,
        "scope": "literal search over explicitly listed saved extracted text; no live source verification",
        "network_used": False, "untrusted_source_data": True,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="task-local JSON list of report directories or document snapshots")
    parser.add_argument("term", help="literal term to find offline")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        result = find(args.manifest, args.term)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        result = {"status": "error", "reason": "invalid_manifest_or_query", "matches": [], "network_used": False}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in {"ok", "no_results", "partial"} else 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
