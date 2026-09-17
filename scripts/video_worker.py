"""Isolated youtube-transcript-api worker used by scripts/video.py.

The worker accepts only JSON on stdin and returns one JSON object.  It fetches
caption text and timing metadata; it never downloads audio/video, uses ASR, or
reads cookies and browser profiles.
"""
from __future__ import annotations

import json
import re
import sys
from importlib import metadata
from typing import Any


def _emit(value: dict[str, Any]) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def _clean_text(value: Any) -> str:
    text = str(value or "")
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def _failure(reason: str, *, error_type: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "unavailable",
        "records": [],
        "reason": reason,
        "scope": "captions_only; no_media_download; no_asr",
    }
    if error_type:
        result["failure"] = {"kind": error_type}
    return result


def _error_kind(exc: BaseException) -> str:
    name = type(exc).__name__
    lowered = name.casefold()
    if "transcriptsdisabled" in lowered:
        return "no_subtitles"
    if "notranscriptfound" in lowered:
        return "no_subtitles_for_language"
    if "videounavailable" in lowered:
        return "video_unavailable"
    if "ipblocked" in lowered or "requestblocked" in lowered:
        return "access_blocked"
    if "couldnotretrievetranscript" in lowered:
        return "transcript_fetch_failed"
    if "too_many_requests" in lowered or "ratelimit" in lowered:
        return "rate_limited"
    return "transcript_provider_error"


def _language_match(item: Any, requested: list[str]) -> tuple[int, bool]:
    code = str(getattr(item, "language_code", "")).casefold()
    label = str(getattr(item, "language", "")).casefold()
    for index, wanted in enumerate(requested):
        wanted = wanted.casefold()
        if code == wanted or label == wanted:
            return index, True
        if code.replace("_", "-") == wanted.replace("_", "-"):
            return index, True
    return len(requested), False


def _select(items: list[Any], requested: list[str], subtitle_type: str) -> Any | None:
    candidates = []
    for item in items:
        language_rank, matched = _language_match(item, requested)
        if matched:
            generated = bool(getattr(item, "is_generated", False))
            if subtitle_type == "manual" and generated:
                continue
            if subtitle_type == "auto" and not generated:
                continue
            # For "any", manually created captions win when language is equal.
            generated_rank = 1 if generated else 0
            candidates.append((language_rank, generated_rank, item))
    if not candidates:
        return None
    candidates.sort(key=lambda value: (value[0], value[1]))
    return candidates[0][2]


def _available(items: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "language": str(getattr(item, "language", "")),
            "language_code": str(getattr(item, "language_code", "")),
            "subtitle_type": "auto" if getattr(item, "is_generated", False) else "manual",
            "is_generated": bool(getattr(item, "is_generated", False)),
        }
        for item in items
    ]


def main() -> int:
    try:
        request = json.load(sys.stdin)
        video_id = str(request["video_id"])
        languages = [str(value) for value in request.get("languages", ["en"]) if str(value).strip()]
        subtitle_type = str(request.get("subtitle_type", "any"))
        find_text = str(request.get("find", "") or "")
        max_segments = int(request.get("max_segments", 5000))
        if not video_id or not 1 <= max_segments <= 10000:
            raise ValueError("invalid_worker_request")
        if subtitle_type not in {"any", "manual", "auto"}:
            raise ValueError("invalid_subtitle_type")
        if not languages:
            raise ValueError("language_required")
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        _emit(_failure("invalid_worker_request", error_type="invalid_request"))
        return 2

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        api = YouTubeTranscriptApi()
        transcripts = list(api.list(video_id))
        selected = _select(transcripts, languages, subtitle_type)
        if selected is None:
            result = _failure("no_subtitles_for_requested_language", error_type="no_matching_caption")
            result["available_languages"] = _available(transcripts)
            return _emit(result) or 0
        fetched = selected.fetch()
        raw = fetched.to_raw_data()
    except ModuleNotFoundError:
        _emit(_failure("runtime_dependency_missing", error_type="dependency_missing"))
        return 2
    except Exception as exc:  # Provider exceptions vary by version; map by class only.
        _emit(_failure(_error_kind(exc), error_type=type(exc).__name__))
        return 2

    all_segments: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        try:
            start = float(item.get("start", 0.0))
            duration = max(0.0, float(item.get("duration", 0.0)))
        except (TypeError, ValueError):
            start, duration = 0.0, 0.0
        all_segments.append(
            {
                "index": index,
                "start_seconds": round(start, 3),
                "duration_seconds": round(duration, 3),
                "end_seconds": round(start + duration, 3),
                "text": _clean_text(item.get("text", "")),
            }
        )
    needle = find_text.casefold()
    segments = all_segments[:max_segments]
    # Keep the text-match output bounded by the returned segment window. A
    # caller that needs a later match can raise --max-segments explicitly.
    matches = [segment for segment in segments if needle and needle in segment["text"].casefold()]
    truncated = len(all_segments) > len(segments)
    result = {
        "status": "partial" if truncated else "ok",
        "records": segments,
        "matches": matches,
        "match_count": len(matches),
        "matches_scope": "returned_segments",
        "video_id": video_id,
        "language": str(getattr(fetched, "language", "")),
        "language_code": str(getattr(fetched, "language_code", "")),
        "subtitle_type": "auto" if getattr(fetched, "is_generated", False) else "manual",
        "is_generated": bool(getattr(fetched, "is_generated", False)),
        "segment_count": len(all_segments),
        "returned_segment_count": len(segments),
        "segments_truncated": truncated,
        "available_languages": _available(transcripts),
        "scope": "captions_only; no_media_download; no_asr",
        "provider_version": metadata.version("youtube-transcript-api"),
    }
    if truncated:
        result["partial_reason"] = "max_segments"
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
