#!/usr/bin/env python3
"""Minimal explicit OpenCitations DOI edge reader.

This module deliberately has two bounded modes:

* replay: parse an already captured Index response and explicitly supplied Meta
  snapshots without network access;
* live-index: make one fixed-host Index GET followed by at most three
  fixed-host Meta GETs selected from that Index response, with no retries,
  redirects, recursion, seed changes, or search.

It is not a general citation crawler, PDF matcher, full-text reader, or default
field-search route. All returned rows and response bytes remain traceable.
"""

from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib import error, parse, request


API_HOST = "api.opencitations.net"
INDEX_PREFIX = "https://api.opencitations.net/index/v2/references/doi:"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_META_PER_RUN = 3
DOI_RE = re.compile(r"^10\.[^\s?#]+$", re.IGNORECASE)


class ReaderError(ValueError):
    """A user-visible bounded-reader error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalize_doi(value: str) -> str:
    if not isinstance(value, str):
        raise ReaderError("doi_must_be_text")
    value = value.strip()
    if value.lower().startswith("doi:"):
        value = value[4:]
    if not DOI_RE.fullmatch(value):
        raise ReaderError("invalid_doi")
    return value


def doi_equal(left: str, right: str) -> bool:
    """Compare complete DOI PID values, never a substring."""

    return left.casefold() == right.casefold()


def pid_tokens(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    return [token for token in value.split() if token]


def doi_pids(value: Any) -> list[str]:
    result: list[str] = []
    for token in pid_tokens(value):
        if token.casefold().startswith("doi:") and len(token) > 4:
            doi = token[4:]
            if doi not in result:
                result.append(doi)
    return result


def exact_doi_in_pids(value: Any, requested_doi: str) -> bool:
    return any(doi_equal(doi, requested_doi) for doi in doi_pids(value))


def unique_casefold(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            result.append(value)
            seen.add(key)
    return result


def decode_snapshot(path: Path) -> tuple[bytes, str]:
    """Load a raw body or the lossless Base64 snapshot used by R12."""

    try:
        encoded = path.read_bytes()
    except OSError as exc:
        raise ReaderError("snapshot_unreadable") from exc
    if path.name.endswith(".body.b64") or path.suffix.lower() == ".b64":
        try:
            return base64.b64decode(b"".join(encoded.split()), validate=True), "base64"
        except (binascii.Error, ValueError) as exc:
            raise ReaderError("snapshot_base64_invalid") from exc
    return encoded, "raw_bytes"


def _basename(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return Path(value.replace("/", "\\")).name


def load_request_log(path: Path | None) -> dict[str, list[dict[str, Any]]]:
    """Index calls by raw snapshot basename and retain duplicate bindings."""

    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReaderError("request_log_invalid") from exc
    result: dict[str, list[dict[str, Any]]] = {}
    for call in data.get("calls", []) if isinstance(data, dict) else []:
        if not isinstance(call, dict):
            continue
        raw = call.get("raw_body_snapshot")
        name = _basename(raw.get("path") if isinstance(raw, dict) else None)
        if name:
            result.setdefault(name, []).append(call)
    return result


def expected_api_url(kind: str, identifier: str) -> str:
    encoded = parse.quote(identifier, safe="/:")
    if kind == "index":
        return INDEX_PREFIX + encoded
    if kind == "meta":
        return "https://api.opencitations.net/meta/v1/metadata/doi:" + encoded
    raise ReaderError("unknown_api_trace_kind")


def response_trace(path: Path, raw: bytes, encoding: str,
                   request_log: dict[str, list[dict[str, Any]]],
                   expected_url: str | None = None) -> dict[str, Any]:
    calls = request_log.get(path.name, [])
    trace: dict[str, Any] = {
        "snapshot_path": str(path.resolve()),
        "raw_encoding": encoding,
        "byte_count": len(raw),
        "sha256": sha256_bytes(raw),
        "raw_bytes_preserved": True,
    }
    if not calls:
        trace["provenance_status"] = "unverified_local"
        trace["verification_errors"] = ["request_log_missing"]
        trace["request"] = {"observation": "snapshot_replay_without_request_log"}
        return trace
    if len(calls) != 1:
        trace["provenance_status"] = "invalid"
        trace["verification_errors"] = ["request_log_binding_not_unique"]
        trace["request"] = {"observation": "multiple_request_records_for_snapshot_basename"}
        return trace

    call = calls[0]
    trace["request"] = {
            key: call.get(key)
            for key in (
                "call_id", "observed_at_utc_start", "observed_at_utc_end",
                "requested_url", "final_url", "status", "reason", "response_headers",
            )
            if key in call
        }
    errors: list[str] = []
    declared_hash = call.get("sha256")
    declared_bytes = call.get("byte_count")
    snapshot_declared = call.get("raw_body_snapshot")
    if not isinstance(declared_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", declared_hash):
        errors.append("manifest_sha256_missing_or_invalid")
    elif declared_hash.casefold() != trace["sha256"].casefold():
        errors.append("manifest_sha256_mismatch")
    if not isinstance(declared_bytes, int) or declared_bytes != len(raw):
        errors.append("manifest_byte_count_mismatch")
    if isinstance(snapshot_declared, dict):
        declared_snapshot_bytes = snapshot_declared.get("decoded_byte_count")
        if isinstance(declared_snapshot_bytes, int) and declared_snapshot_bytes != len(raw):
            errors.append("manifest_snapshot_byte_count_mismatch")
        if _basename(snapshot_declared.get("path")) != path.name:
            errors.append("manifest_snapshot_path_mismatch")
    else:
        errors.append("manifest_raw_snapshot_missing")
    status_code = call.get("status")
    if not isinstance(status_code, int) or not 200 <= status_code < 300:
        errors.append("manifest_http_status_not_success")
    if expected_url is not None:
        if call.get("requested_url") != expected_url:
            errors.append("manifest_requested_url_mismatch")
        if call.get("final_url") != expected_url:
            errors.append("manifest_final_url_mismatch")
    trace["provenance_status"] = "verified" if not errors else "invalid"
    trace["verification_errors"] = errors
    trace["manifest"] = {
        "declared_sha256": declared_hash,
        "declared_byte_count": declared_bytes,
        "declared_status": status_code,
        "expected_url": expected_url,
    }
    return trace


def parse_index_body(raw: bytes, seed_doi: str) -> dict[str, Any]:
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            "status": "error",
            "reason": "index_json_invalid",
            "raw_rows": [],
            "parse_error": str(exc),
        }
    if not isinstance(decoded, list):
        return {
            "status": "error",
            "reason": "index_response_not_array",
            "raw_rows": decoded,
            "parse_error": "expected_json_array",
        }
    if not decoded:
        return {
            "status": "empty",
            "reason": "no_returned_records_this_request",
            "raw_rows": [],
            "edges": [],
            "unresolved_edges": [],
        }

    edges: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for position, raw_row in enumerate(decoded):
        if not isinstance(raw_row, dict):
            unresolved.append({
                "position": position,
                "status": "unresolved",
                "reason": "index_row_not_object",
                "raw": raw_row,
            })
            continue
        citing = raw_row.get("citing")
        cited = raw_row.get("cited")
        citing_pids = pid_tokens(citing)
        cited_pids = pid_tokens(cited)
        cited_dois = unique_casefold(doi_pids(cited))
        citing_matches_seed = exact_doi_in_pids(citing, seed_doi)
        reasons: list[str] = []
        if not raw_row.get("oci"):
            reasons.append("missing_oci")
        if not citing_matches_seed:
            reasons.append("citing_seed_exact_match_failed")
        if not cited_dois:
            reasons.append("cited_doi_missing")
        if len(cited_dois) > 1:
            reasons.append("cited_multiple_dois_ambiguous")
        edge = {
            "position": position,
            "status": "valid" if not reasons else "unresolved",
            "oci": raw_row.get("oci"),
            "citing": citing,
            "cited": cited,
            "citing_pids": citing_pids,
            "cited_pids": cited_pids,
            "cited_doi_candidates": cited_dois,
            "citing_seed_exact_match": citing_matches_seed,
            "unresolved_reasons": reasons,
            "raw": raw_row,
        }
        if len(cited_dois) == 1:
            edge["cited_doi"] = cited_dois[0]
        else:
            edge["cited_doi"] = None
        edges.append(edge)
        if reasons:
            unresolved.append(edge)

    return {
        "status": "ok",
        "reason": None,
        "raw_rows": decoded,
        "edges": edges,
        "unresolved_edges": unresolved,
    }


def parse_meta_body(raw: bytes, requested_doi: str) -> dict[str, Any]:
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            "status": "error",
            "reason": "meta_json_invalid",
            "raw_records": [],
            "parse_error": str(exc),
        }
    if not isinstance(decoded, list):
        return {
            "status": "error",
            "reason": "meta_response_not_array",
            "raw_records": decoded,
            "metadata": None,
            "parse_error": "expected_json_array",
        }
    if not decoded:
        return {
            "status": "unresolved",
            "reason": "meta_empty_response",
            "raw_records": [],
            "metadata": None,
        }
    if len(decoded) != 1 or not isinstance(decoded[0], dict):
        return {
            "status": "ambiguous",
            "reason": "meta_multiple_or_non_object_entities",
            "raw_records": decoded,
            "metadata": None,
        }

    record = decoded[0]
    identifiers = pid_tokens(record.get("id"))
    record_dois = unique_casefold(doi_pids(record.get("id")))
    matching = [doi for doi in record_dois if doi_equal(doi, requested_doi)]
    reasons: list[str] = []
    if not matching:
        reasons.append("meta_requested_doi_identity_mismatch")
    if len(record_dois) > 1:
        reasons.append("meta_multiple_dois_ambiguous")
    missing_fields = [
        field for field in ("id", "title", "pub_date", "author", "venue")
        if not record.get(field)
    ]
    if missing_fields:
        reasons.append("meta_missing_fields")
    if any("ambiguous" in reason or "mismatch" in reason for reason in reasons):
        result_status = "ambiguous"
    elif reasons:
        result_status = "partial"
    else:
        result_status = "ok"
    result = {
        "status": result_status,
        "reason": None if not reasons else ";".join(reasons),
        "requested_doi": requested_doi,
        "identifiers": identifiers,
        "doi_candidates": record_dois,
        "requested_doi_exact_match": bool(matching),
        "missing_fields": missing_fields,
        "metadata": {
            "id": record.get("id"),
            "title": record.get("title"),
            "author": record.get("author"),
            "pub_date": record.get("pub_date"),
            "venue": record.get("venue"),
            "type": record.get("type"),
            "page": record.get("page"),
            "issue": record.get("issue"),
            "volume": record.get("volume"),
            "publisher": record.get("publisher"),
            "editor": record.get("editor"),
        },
        "raw_records": decoded,
    }
    return result


def _meta_assignment(value: str) -> tuple[str, Path]:
    doi, separator, path = value.partition("=")
    if not separator or not path:
        raise ReaderError("meta_snapshot_expected_doi_equals_path")
    return normalize_doi(doi), Path(path)


def _failure_meta(requested_doi: str, reason: str, path: Path | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "unresolved",
        "requested_doi": requested_doi,
        "reason": reason,
        "raw_records": [],
        "metadata": None,
        "provenance_status": "not_supplied",
    }
    if path is not None:
        result["snapshot_path"] = str(path.resolve())
    return result


def _finish_live_response(trace: dict[str, Any], received: bytes) -> tuple[dict[str, Any], bytes]:
    """Retain the prefix when the bounded read proves the body is too large."""

    truncated = len(received) > MAX_RESPONSE_BYTES
    stored = received[:MAX_RESPONSE_BYTES] if truncated else received
    trace["received_byte_count"] = len(received)
    trace["stored_byte_count"] = len(stored)
    trace["response_limit_bytes"] = MAX_RESPONSE_BYTES
    trace["truncated"] = truncated
    trace["response_body_complete"] = not truncated
    trace["raw_integrity"] = "prefix_only" if truncated else "complete_response_body"
    trace["raw_bytes_preserved"] = not truncated
    trace["byte_count"] = len(stored)
    trace["sha256"] = sha256_bytes(stored)
    trace["raw_body_base64"] = base64.b64encode(stored).decode("ascii")
    if truncated:
        trace["error"] = "response_too_large"
        trace["full_response_size"] = "unknown_after_limit_probe"
    expected_url = trace.get("requested_url")
    status = trace.get("status")
    errors: list[str] = []
    if trace.get("final_url") != expected_url:
        errors.append("live_final_url_mismatch")
    if not isinstance(status, int) or not 200 <= status < 300:
        errors.append("live_http_status_not_success")
    trace["provenance_status"] = "live_observed" if not errors else "invalid"
    trace["verification_errors"] = errors
    return trace, stored


def _load_meta(requested_doi: str, path: Path | None,
               request_log: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    if path is None:
        return _failure_meta(requested_doi, "meta_snapshot_not_supplied")
    try:
        raw, encoding = decode_snapshot(path)
    except ReaderError as exc:
        return _failure_meta(requested_doi, str(exc), path)
    result = parse_meta_body(raw, requested_doi)
    result["snapshot_path"] = str(path.resolve())
    result["raw_encoding"] = encoding
    result["byte_count"] = len(raw)
    result["sha256"] = sha256_bytes(raw)
    result["raw_bytes_preserved"] = True
    trace = response_trace(
        path,
        raw,
        encoding,
        request_log,
        expected_api_url("meta", requested_doi),
    )
    result["request"] = trace.get("request")
    result["provenance_status"] = trace.get("provenance_status")
    result["source_verification"] = trace
    if trace.get("provenance_status") == "invalid":
        result["source_parse_status"] = result.get("status")
        if result.get("status") == "ok":
            result["status"] = "unverified"
        result["reason"] = ";".join(
            value for value in (result.get("reason"), "meta_source_manifest_invalid") if value
        )
    elif trace.get("provenance_status") == "unverified_local":
        result["source_parse_status"] = result.get("status")
        if result.get("status") == "ok":
            result["status"] = "unverified"
        result["reason"] = ";".join(
            value for value in (result.get("reason"), "meta_source_unverified_local") if value
        )
    return result


def _live_request_once(kind: str, identifier: str, timeout: float) -> dict[str, Any]:
    """Make one fixed-host GET with no retries and no redirects."""

    url = expected_api_url(kind, identifier)
    started = utc_now()
    req = request.Request(
        url,
        headers={
            "User-Agent": "field-search-r12.4-explicit-reader/1.0",
            "Accept": "application/json",
        },
    )

    class NoRedirect(request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    trace: dict[str, Any] = {
        "requested_url": url,
        "request_kind": kind,
        "requested_identifier": identifier,
        "observed_at_utc_start": started,
        "auto_retry": False,
        "redirects_followed": False,
        "host": API_HOST,
        "read_limit_bytes": MAX_RESPONSE_BYTES + 1,
    }
    try:
        opener = request.build_opener(NoRedirect())
        with opener.open(req, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            trace.update(
                final_url=response.geturl(),
                status=getattr(response, "status", None),
                reason=getattr(response, "reason", None),
                response_headers=dict(response.headers.items()),
            )
    except error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES + 1)
        trace.update(
            final_url=exc.geturl(),
            status=exc.code,
            reason=str(exc.reason),
            response_headers=dict(exc.headers.items()) if exc.headers else {},
            error="http_error",
        )
    except (error.URLError, TimeoutError, OSError) as exc:
        trace.update(
            final_url=None,
            status=None,
            reason=None,
            response_headers={},
            error="network_error_or_timeout",
            error_detail=str(exc),
            observed_at_utc_end=utc_now(),
            received_byte_count=0,
            stored_byte_count=0,
            response_limit_bytes=MAX_RESPONSE_BYTES,
            truncated=False,
            response_body_complete=False,
            raw_integrity="not_available",
            raw_bytes_preserved=False,
            byte_count=0,
            sha256=None,
            raw_body_base64=None,
            provenance_status="invalid",
            verification_errors=["live_transport_failed"],
        )
        return {"trace": trace, "raw": b"", "encoding": "none"}

    trace["observed_at_utc_end"] = utc_now()
    trace, stored = _finish_live_response(trace, raw)
    return {"trace": trace, "raw": stored, "encoding": "live_response_bytes"}


def _live_index_once(seed_doi: str, timeout: float) -> dict[str, Any]:
    return _live_request_once("index", seed_doi, timeout)


def _live_meta_once(requested_doi: str, timeout: float) -> dict[str, Any]:
    return _live_request_once("meta", requested_doi, timeout)


def _live_meta_result(requested_doi: str, timeout: float,
                      index_parse_status: str | None,
                      index_source_usable: bool) -> dict[str, Any]:
    """Parse one live Meta response while retaining its complete trace."""

    response = _live_meta_once(requested_doi, timeout)
    raw = response["raw"]
    trace = response["trace"]
    parsed = parse_meta_body(raw, requested_doi)
    parse_status = parsed.get("status")
    result = dict(parsed)
    result.update(
        raw_encoding=response["encoding"],
        byte_count=len(raw),
        sha256=sha256_bytes(raw),
        raw_bytes_preserved=bool(trace.get("raw_bytes_preserved")),
        request={
            key: trace.get(key)
            for key in (
                "requested_url", "final_url", "observed_at_utc_start",
                "observed_at_utc_end", "status", "reason", "response_headers",
            )
        },
        source_verification=trace,
        provenance_status=trace.get("provenance_status"),
        source_parse_status=parse_status,
        source_usable=False,
        index_source_parse_status=index_parse_status,
        index_source_usable=index_source_usable,
    )

    status_code = trace.get("status")
    if trace.get("error") == "response_too_large":
        result["status"] = "unavailable"
        result["reason"] = "meta_response_not_fully_captured"
    elif not isinstance(status_code, int) or not 200 <= status_code < 300:
        result["status"] = "unavailable"
        result["reason"] = "meta_http_not_success"
    elif trace.get("provenance_status") != "live_observed":
        result["status"] = "unverified" if parse_status == "ok" else parse_status
        result["reason"] = "meta_live_source_invalid"
    else:
        result["source_usable"] = parse_status == "ok"
    return result


def run_reader(seed_doi: str, *, index_snapshot: Path | None = None,
               meta_snapshots: dict[str, Path] | None = None,
               request_log_path: Path | None = None, max_meta: int = 3,
               live_index: bool = False, timeout: float = 15.0) -> dict[str, Any]:
    """Run the bounded reader and return a traceable JSON-compatible result."""

    seed_doi = normalize_doi(seed_doi)
    if not 0 <= max_meta <= MAX_META_PER_RUN:
        raise ReaderError("max_meta_must_be_between_0_and_3")
    if not 1 <= timeout <= 60:
        raise ReaderError("timeout_must_be_between_1_and_60")
    if live_index and index_snapshot is not None:
        raise ReaderError("choose_live_index_or_index_snapshot")
    if not live_index and index_snapshot is None:
        raise ReaderError("index_snapshot_required_for_replay")

    meta_snapshots = meta_snapshots or {}
    request_log = load_request_log(request_log_path)
    if live_index:
        response = _live_index_once(seed_doi, timeout)
        raw = response["raw"]
        index_trace = response["trace"]
        index_encoding = response["encoding"]
        network_index_calls = 1
    else:
        assert index_snapshot is not None
        raw, index_encoding = decode_snapshot(index_snapshot)
        index_trace = response_trace(
            index_snapshot,
            raw,
            index_encoding,
            request_log,
            expected_api_url("index", seed_doi),
        )
        network_index_calls = 0

    parsed_index = parse_index_body(raw, seed_doi)
    index_status = parsed_index.get("status")
    index_parse_status = parsed_index.get("status")
    if live_index and index_trace.get("error") == "response_too_large":
        index_status = "unavailable"
        parsed_index["reason"] = "index_response_not_fully_captured"
    elif live_index and (
        index_trace.get("provenance_status") != "live_observed"
        or not isinstance(index_trace.get("status"), int)
        or not 200 <= index_trace["status"] < 300
    ):
        if isinstance(index_trace.get("status"), int) and not 200 <= index_trace["status"] < 300:
            index_status = "unavailable"
            parsed_index["reason"] = "index_http_not_success"
        else:
            index_status = "error"
            parsed_index["reason"] = "index_live_source_invalid"
    elif not live_index and index_trace.get("provenance_status") == "invalid":
        verification_errors = set(index_trace.get("verification_errors") or [])
        if "manifest_http_status_not_success" in verification_errors:
            index_status = "unavailable"
            parsed_index["reason"] = "index_source_http_failure"
        else:
            index_status = "error"
            parsed_index["reason"] = "index_source_invalid"

    edges = parsed_index.get("edges", []) if isinstance(parsed_index.get("edges"), list) else []
    parsed_valid_edges = [edge for edge in edges if edge.get("status") == "valid"]
    candidates: list[str] = []
    for edge in parsed_valid_edges:
        doi = edge.get("cited_doi")
        if isinstance(doi, str) and not any(doi_equal(doi, previous) for previous in candidates):
            candidates.append(doi)

    index_source_issue = index_trace.get("provenance_status") not in ("verified", "live_observed")
    index_source_usable = (
        index_status not in ("error", "unavailable")
        and index_trace.get("provenance_status") in ("verified", "live_observed")
    )
    index_direction_usable = bool(parsed_valid_edges)
    live_meta_blocked_by_source = live_index and bool(candidates) and not index_source_usable
    live_meta_blocked_by_direction = live_index and bool(edges) and not index_direction_usable
    selection_allowed = not live_index or index_source_usable
    selected = candidates[:max_meta] if selection_allowed else []
    truncated = selection_allowed and len(candidates) > len(selected)
    meta_results: list[dict[str, Any]] = []
    actual_meta_network_calls = 0
    for doi in selected:
        if live_index:
            meta_results.append(
                _live_meta_result(
                    doi,
                    timeout,
                    index_parse_status,
                    index_source_usable,
                )
            )
            actual_meta_network_calls += 1
        else:
            path = next(
                (path for supplied_doi, path in meta_snapshots.items() if doi_equal(supplied_doi, doi)),
                None,
            )
            result = _load_meta(doi, path, request_log)
            result["index_source_parse_status"] = index_parse_status
            result["index_source_usable"] = index_source_usable
            meta_results.append(result)

    meta_failures = [item for item in meta_results if item.get("status") != "ok"]
    index_unresolved = parsed_index.get("unresolved_edges") or []
    meta_source_issue = any(
        item.get("provenance_status") not in ("verified", "live_observed")
        for item in meta_results
    )
    source_issue = index_source_issue or meta_source_issue
    usable_edges = parsed_valid_edges if index_source_usable else []
    if index_status in ("error", "unavailable"):
        status = index_status
    elif index_status == "empty":
        status = "unverified" if index_trace.get("provenance_status") == "unverified_local" else "empty"
    elif index_unresolved or meta_failures or truncated:
        status = "partial"
    elif source_issue:
        only_local_unverified = all(
            provenance in ("unverified_local", "not_supplied")
            for provenance in [
                index_trace.get("provenance_status"),
                *[item.get("provenance_status") for item in meta_results],
            ]
            if provenance is not None
        )
        status = "unverified" if only_local_unverified else "partial"
    else:
        status = "ok"

    warnings = [
        "This reader preserves citation edges only; a citation is not a support, relevance, quality, or full-text claim.",
        "The API response has no completeness marker usable here; overall coverage remains unknown.",
        "Native PDF matching is not performed by this reader.",
    ]
    if index_status == "empty":
        warnings.append("An empty Index response means no records were returned by this request; it does not mean the paper has no references.")
    if truncated:
        warnings.append("Meta selection was capped by the explicit per-run budget; unselected candidates were not requested.")
    if meta_failures:
        warnings.append("Meta failures or identity ambiguities were retained alongside any valid edges.")
    if live_meta_blocked_by_source:
        warnings.append("Index source was not usable; Meta requests were not sent for parsed candidates.")
    if live_meta_blocked_by_direction:
        warnings.append("No Index edge passed the exact seed-direction checks; Meta requests were not sent.")
    if source_issue:
        warnings.append("Source provenance is not fully verified; parsed local data is not presented as an official successful response.")
    if index_status in ("error", "unavailable") and edges:
        warnings.append("Index rows and parse candidates are retained for audit, but no parsed edge is counted as an officially usable citation edge.")

    meta_not_requested_due_to_budget = (
        max(0, len(candidates) - len(selected))
        if selection_allowed
        else 0
    )
    meta_not_requested_due_to_index_source = len(candidates) if live_meta_blocked_by_source else 0
    meta_not_requested_due_to_direction = len(edges) if live_meta_blocked_by_direction else 0

    return {
        "schema_version": 1,
        "reader": "open-citations-explicit-reader",
        "reader_version": "r12.4",
        "status": status,
        "mode": "live-index" if live_index else "replay",
        "network_used": bool(live_index or actual_meta_network_calls),
        "seed_doi": seed_doi,
        "index": {
            "status": index_status,
            "source_parse_status": index_parse_status,
            "source_usable": index_source_usable,
            "direction_usable": index_direction_usable,
            "reason": parsed_index.get("reason"),
            "trace": index_trace,
            "raw_rows": parsed_index.get("raw_rows", []),
            "raw_row_count": len(parsed_index.get("raw_rows", [])) if isinstance(parsed_index.get("raw_rows"), list) else None,
            "edges": edges,
            "unresolved_edges": index_unresolved,
            "raw_response_preserved": bool(index_trace.get("raw_bytes_preserved")),
        },
        "meta": meta_results,
        "limits": {
            "max_meta_per_run": MAX_META_PER_RUN,
            "requested_meta_limit": max_meta,
            "meta_candidates_seen": len(candidates),
            "meta_selected": len(selected),
            "meta_not_requested_due_to_budget": meta_not_requested_due_to_budget,
            "meta_not_requested_due_to_index_source": meta_not_requested_due_to_index_source,
            "meta_not_requested_due_to_direction": meta_not_requested_due_to_direction,
            "max_index_network_calls": 1,
            "max_total_network_calls": 1 + max_meta,
            "actual_index_network_calls": network_index_calls,
            "actual_meta_network_calls": actual_meta_network_calls,
            "actual_network_calls": network_index_calls + actual_meta_network_calls,
            "recursion": False,
            "automatic_retry": False,
            "redirects_followed": False,
        },
        "coverage": {
            "index_returned_rows": len(parsed_index.get("raw_rows", [])) if isinstance(parsed_index.get("raw_rows"), list) else None,
            "index_valid_edges": len(parsed_valid_edges),
            "index_usable_edges": len(usable_edges),
            "index_unresolved_edges": len(index_unresolved),
            "meta_resolved": len([item for item in meta_results if item.get("status") == "ok"]),
            "meta_failed_or_ambiguous": len(meta_failures),
            "meta_parse_errors": len([
                item for item in meta_results
                if item.get("source_parse_status") == "error"
            ]),
            "meta_not_requested_due_to_budget": meta_not_requested_due_to_budget,
            "meta_not_requested_due_to_index_source": meta_not_requested_due_to_index_source,
            "meta_not_requested_due_to_direction": meta_not_requested_due_to_direction,
            "meta_budget_truncated": truncated,
            "overall": "unknown",
            "server_completeness": "unknown",
        },
        "warnings": warnings,
    }


def write_new_json(path: Path, result: dict[str, Any]) -> None:
    if path.exists():
        raise ReaderError("output_exists_choose_new_path")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except FileExistsError as exc:
        raise ReaderError("output_exists_choose_new_path") from exc


def preflight_output(path: Path) -> None:
    """Reject an unusable/existing target before any optional network call."""

    if path.exists():
        raise ReaderError("output_exists_choose_new_path")
    parent = path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ReaderError("output_parent_unavailable") from exc
    if not parent.is_dir() or not os.access(parent, os.W_OK):
        raise ReaderError("output_parent_not_writable")
    if path.exists():
        raise ReaderError("output_exists_choose_new_path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, help="Explicit DOI, with or without a leading doi: prefix")
    parser.add_argument("--index-snapshot", type=Path, help="Existing raw or .body.b64 Index response for replay")
    parser.add_argument("--meta-snapshot", action="append", default=[], metavar="DOI=PATH",
                        help="Explicit offline Meta snapshot mapping; repeat at most three times")
    parser.add_argument("--request-log", type=Path, help="Optional request log used to attach URL/status/time")
    parser.add_argument("--max-meta", type=int, default=3, help="Meta lookup budget, 0..3 (default 3)")
    parser.add_argument(
        "--live", "--live-index", dest="live_index", action="store_true",
        help="Make one bounded fixed-host live Index-to-Meta run",
    )
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--out", type=Path, required=True, help="New output JSON path; existing files are never overwritten")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        preflight_output(args.out)
        mappings = [_meta_assignment(value) for value in args.meta_snapshot]
        if len(mappings) > MAX_META_PER_RUN:
            raise ReaderError("at_most_three_meta_snapshots_allowed")
        meta_snapshots: dict[str, Path] = {}
        for doi, path in mappings:
            if any(doi_equal(doi, existing) for existing in meta_snapshots):
                raise ReaderError("duplicate_meta_doi_mapping")
            meta_snapshots[doi] = path
        result = run_reader(
            args.seed,
            index_snapshot=args.index_snapshot,
            meta_snapshots=meta_snapshots,
            request_log_path=args.request_log,
            max_meta=args.max_meta,
            live_index=args.live_index,
            timeout=args.timeout,
        )
        write_new_json(args.out, result)
        result["output_path"] = str(args.out.resolve())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] in ("ok", "partial", "empty") else 2
    except ReaderError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
