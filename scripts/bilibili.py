"""Read Bilibili captions through the official subtitle APIs.

The route uses Bilibili metadata and subtitle endpoints only.  It never reads
browser cookies, downloads media or danmaku, invokes ASR, or silently follows
a Bilibili short link to another host.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import html
import json
from pathlib import Path
import re
from typing import Any
from urllib import parse
from urllib import error as urlerror
from urllib import request as urlrequest

import runtime_config


BVID_RE = re.compile(r"^BV[0-9A-Za-z]{10}$")
AV_RE = re.compile(r"^av[0-9]+$", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]*>")
DEFAULT_LANGUAGES = [
    "zh-Hans",
    "zh-CN",
    "zh-Hant",
    "zh-TW",
    "zh",
    "ai-zh",
    "en",
    "ai-en",
]
GENERATED_CODES = {"ai-zh", "ai-en", "ai-ja", "ai-ko"}
SUBTITLE_HOST_SUFFIXES = (".bilibili.com", ".hdslb.com", ".bilivideo.com")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
)


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


NO_REDIRECT_OPENER = urlrequest.build_opener(_NoRedirect())


@dataclass(frozen=True)
class BilibiliRef:
    original: str
    target: str
    video_id: str | None
    page: int | None
    short_link: bool = False


def parse_video_ref(value: str) -> BilibiliRef | None:
    """Return a safe Bilibili reference, or None for a YouTube/other URL."""

    raw = str(value or "").strip()
    if BVID_RE.fullmatch(raw) or AV_RE.fullmatch(raw):
        return BilibiliRef(raw, f"https://www.bilibili.com/video/{raw}", raw, None)
    if not raw:
        return None
    try:
        parsed = parse.urlsplit(raw)
    except ValueError:
        return None
    host = (parsed.hostname or "").casefold().rstrip(".")
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        return None
    if host in {"b23.tv", "www.b23.tv"}:
        if not parsed.path.strip("/") or len(parsed.path) > 128:
            return None
        page = _page_number(parsed.query)
        safe_short = f"https://b23.tv{parsed.path}"
        return BilibiliRef(safe_short, safe_short, None, page, short_link=True)
    if host not in {"bilibili.com", "www.bilibili.com", "m.bilibili.com"}:
        return None
    match = re.fullmatch(r"/video/(BV[0-9A-Za-z]{10}|av[0-9]+)(?:/)?", parsed.path, re.IGNORECASE)
    if not match:
        return None
    video_id = match.group(1)
    page = _page_number(parsed.query)
    canonical = f"https://www.bilibili.com/video/{video_id}"
    if page is not None:
        canonical += f"?p={page}"
    return BilibiliRef(canonical, canonical, video_id, page)


def _canonical_bilibili_url(value: Any) -> str | None:
    try:
        parsed = parse.urlsplit(str(value or ""))
    except ValueError:
        return None
    host = (parsed.hostname or "").casefold().rstrip(".")
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        return None
    match = re.fullmatch(r"/video/(BV[0-9A-Za-z]{10}|av[0-9]+)(?:/)?", parsed.path, re.IGNORECASE)
    if host not in {"bilibili.com", "www.bilibili.com", "m.bilibili.com"} or not match:
        return None
    try:
        page = _page_number(parsed.query)
    except ValueError:
        return None
    result = f"https://www.bilibili.com/video/{match.group(1)}"
    return result + (f"?p={page}" if page is not None else "")


def _page_number(query: str) -> int | None:
    values = parse.parse_qs(query, keep_blank_values=True).get("p", [])
    if not values:
        return None
    try:
        page = int(values[-1])
    except (TypeError, ValueError):
        raise ValueError("bilibili_page_must_be_positive_integer") from None
    if page < 1 or page > 10000:
        raise ValueError("bilibili_page_must_be_between_1_and_10000")
    return page


def _session_path(args: Any, config_result: dict[str, Any]) -> tuple[Path | None, str | None]:
    value = getattr(args, "session_path", None) or runtime_config.reader_paths(
        config_result.get("data") or {}, "bilibili"
    ).get("session_path")
    if not value:
        return None, None
    path = Path(value).expanduser()
    if not path.is_file():
        return None, "session_path_missing"
    return path.resolve(), None


def _load_session(path: Path | None) -> tuple[dict[str, str], str | None]:
    if path is None:
        return {}, None
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}, "session_invalid"
    cookies = value.get("cookies") if isinstance(value, dict) else None
    if not isinstance(cookies, dict):
        cookies = value if isinstance(value, dict) else {}
    selected = {
        key: str(cookies[key])
        for key in ("SESSDATA", "bili_jct", "buvid3", "DedeUserID")
        if isinstance(cookies.get(key), str) and cookies.get(key)
    }
    if not selected.get("SESSDATA"):
        return {}, "session_invalid"
    return selected, None


def _cookie_header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{key}={value}" for key, value in cookies.items())


def _safe_https_host(url: str, *, exact: str | None = None, suffixes: tuple[str, ...] = ()) -> bool:
    try:
        parsed = parse.urlsplit(url)
        port = parsed.port
    except ValueError:
        return False
    host = (parsed.hostname or "").casefold().rstrip(".")
    if parsed.scheme != "https" or parsed.username or parsed.password or port not in {None, 443}:
        return False
    if exact is not None and host != exact:
        return False
    return not suffixes or any(host == suffix.lstrip(".") or host.endswith(suffix) for suffix in suffixes)


def _api_json(
    url: str,
    cookies: dict[str, str],
    timeout: float,
    referer: str = "https://www.bilibili.com/",
) -> tuple[dict[str, Any] | None, str | None]:
    if not _safe_https_host(url, exact="api.bilibili.com"):
        return None, "unsafe_api_host"
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": referer,
        "Origin": "https://www.bilibili.com",
    }
    if cookies:
        headers["Cookie"] = _cookie_header(cookies)
    try:
        with NO_REDIRECT_OPENER.open(urlrequest.Request(url, headers=headers), timeout=timeout) as response:
            data = json.loads(response.read(4 * 1024 * 1024).decode("utf-8"))
    except urlerror.HTTPError as exc:
        return None, f"http_{exc.code}"
    except (urlerror.URLError, TimeoutError, OSError):
        return None, "network_error_or_timeout"
    except (UnicodeError, json.JSONDecodeError):
        return None, "invalid_json_response"
    return data if isinstance(data, dict) else None, None


def _subtitle_json(
    url: str,
    timeout: float,
    referer: str,
) -> tuple[list[dict[str, Any]] | None, str | None]:
    parsed = parse.urlsplit(url)
    host = (parsed.hostname or "").casefold().rstrip(".")
    allowed_host = any(host == suffix.lstrip(".") or host.endswith(suffix) for suffix in SUBTITLE_HOST_SUFFIXES)
    if not _safe_https_host(url, suffixes=SUBTITLE_HOST_SUFFIXES) or not allowed_host:
        return None, "unsafe_subtitle_host"
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": referer,
        "Origin": "https://www.bilibili.com",
    }
    # Signed subtitle URLs are the only credential for the CDN request.  Never
    # forward SESSDATA or any other login cookie away from api.bilibili.com.
    try:
        with NO_REDIRECT_OPENER.open(urlrequest.Request(url, headers=headers), timeout=timeout) as response:
            data = json.loads(response.read(16 * 1024 * 1024).decode("utf-8"))
    except urlerror.HTTPError as exc:
        return None, f"http_{exc.code}"
    except (urlerror.URLError, TimeoutError, OSError):
        return None, "network_error_or_timeout"
    except (UnicodeError, json.JSONDecodeError):
        return None, "invalid_json_response"
    body = data.get("body") if isinstance(data, dict) else None
    if not isinstance(body, list):
        return None, "subtitle_body_missing"
    records = []
    for item in body:
        if not isinstance(item, dict):
            continue
        try:
            start = float(item.get("from", item.get("start", 0.0)))
            end = float(item.get("to", item.get("end", start)))
        except (TypeError, ValueError):
            continue
        text = html.unescape(TAG_RE.sub("", str(item.get("content") or item.get("text") or "").strip()))
        if not text:
            continue
        records.append({
            "index": len(records),
            "start_seconds": round(start, 3),
            "duration_seconds": round(max(0.0, end - start), 3),
            "end_seconds": round(max(start, end), 3),
            "text": text,
        })
    if not records:
        return [], "subtitle_empty"
    return records, None


def _read_varint(data: bytes, offset: int) -> tuple[int, int] | None:
    value = 0
    shift = 0
    while offset < len(data) and shift <= 63:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
    return None


def _protobuf_fields_checked(data: bytes) -> tuple[list[tuple[int, int, Any]], bool]:
    fields = []
    offset = 0
    complete = True
    while offset < len(data):
        key = _read_varint(data, offset)
        if key is None:
            complete = False
            break
        raw_key, offset = key
        number, wire_type = raw_key >> 3, raw_key & 7
        if number <= 0:
            complete = False
            break
        if wire_type == 0:
            value = _read_varint(data, offset)
            if value is None:
                complete = False
                break
            raw_value, offset = value
            fields.append((number, wire_type, raw_value))
        elif wire_type == 1:
            if offset + 8 > len(data):
                complete = False
                break
            fields.append((number, wire_type, data[offset : offset + 8]))
            offset += 8
        elif wire_type == 2:
            length = _read_varint(data, offset)
            if length is None:
                complete = False
                break
            size, offset = length
            if size < 0 or offset + size > len(data):
                complete = False
                break
            fields.append((number, wire_type, data[offset : offset + size]))
            offset += size
        elif wire_type == 5:
            if offset + 4 > len(data):
                complete = False
                break
            fields.append((number, wire_type, data[offset : offset + 4]))
            offset += 4
        else:
            complete = False
            break
    return fields, complete and offset == len(data)


def _protobuf_tracks(body: bytes) -> tuple[list[dict[str, Any]], bool]:
    top_fields, complete = _protobuf_fields_checked(body)
    if not complete:
        return [], False
    data_payloads = [value for number, wire, value in top_fields if number == 1 and wire == 2]
    tracks: list[dict[str, Any]] = []
    for data_payload in data_payloads:
        data_fields, data_complete = _protobuf_fields_checked(data_payload)
        if not data_complete:
            return [], False
        for number, wire, value in data_fields:
            if number != 3 or wire != 2:
                continue
            item_fields, item_complete = _protobuf_fields_checked(value)
            if not item_complete:
                return [], False
            text_values: dict[int, str] = {}
            track_id: int | None = None
            track_id_text: str | None = None
            for item_number, item_wire, item_value in item_fields:
                if item_number == 1 and item_wire == 0:
                    track_id = int(item_value)
                elif item_number == 2 and item_wire == 2:
                    try:
                        track_id_text = item_value.decode("utf-8")
                    except UnicodeDecodeError:
                        return [], False
                elif item_number in {3, 4, 5} and item_wire == 2:
                    try:
                        decoded = item_value.decode("utf-8")
                    except UnicodeDecodeError:
                        return [], False
                    if decoded:
                        text_values[item_number] = decoded
            language = text_values.get(3, "")
            subtitle_url = text_values.get(5, "")
            if not language or not subtitle_url:
                continue
            tracks.append(
                {
                    "language_code": language,
                    "language": text_values.get(4) or language,
                    "subtitle_url": subtitle_url,
                    "track_id": track_id_text or (str(track_id) if track_id is not None else None),
                }
            )
    return tracks, True


def _view_state(ref: BilibiliRef, cookies: dict[str, str], timeout: float) -> tuple[dict[str, Any] | None, str | None]:
    video_id = ref.video_id
    if not video_id or not (BVID_RE.fullmatch(video_id) or AV_RE.fullmatch(video_id)):
        return None, "modern_subtitle_requires_bvid_or_av"
    key = "bvid" if BVID_RE.fullmatch(video_id) else "aid"
    api_video_id = video_id[2:] if key == "aid" else video_id
    view, error = _api_json(
        "https://api.bilibili.com/x/web-interface/view?" + parse.urlencode({key: api_video_id}),
        cookies,
        timeout,
        ref.target,
    )
    if error:
        return None, error
    if not view or view.get("code") not in {0, None}:
        return None, "video_metadata_unavailable"
    data = view.get("data") or {}
    pages = data.get("pages") if isinstance(data.get("pages"), list) else []
    page_index = (ref.page or 1) - 1
    if page_index < 0 or page_index >= len(pages):
        return None, "bilibili_page_not_found"
    page_data = pages[page_index] if isinstance(pages[page_index], dict) else {}
    cid = page_data.get("cid")
    aid = data.get("aid")
    if not cid or not aid:
        return None, "video_metadata_missing_cid"
    legacy_url = "https://api.bilibili.com/x/player/wbi/v2?" + parse.urlencode(
        {key: api_video_id, "cid": cid}
    )
    legacy, legacy_error = _api_json(legacy_url, cookies, timeout, ref.target)
    if legacy_error:
        return None, legacy_error
    legacy_data = (legacy or {}).get("data") or {}
    legacy_subtitles = ((legacy_data.get("subtitle") or {}).get("subtitles") or [])
    return {
        "aid": aid,
        "cid": cid,
        "bvid": data.get("bvid") or video_id,
        "title": data.get("title") or "",
        "duration_seconds": page_data.get("duration") or data.get("duration"),
        "page_count": len(pages),
        "need_login_subtitle": bool(legacy_data.get("need_login_subtitle")),
        "legacy_tracks": [item for item in legacy_subtitles if isinstance(item, dict)],
    }, None


def _modern_tracks(
    state: dict[str, Any],
    cookies: dict[str, str],
    timeout: float,
    preferred: str,
    referer: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    params = {
        "oid": state["cid"],
        "pid": state["aid"],
        "context_ext": json.dumps({"video_type": 1}, separators=(",", ":")),
        "type": 1,
        "cur_production_type": 0,
        "preferred_language": preferred,
        "playlist_switch": 0,
    }
    url = "https://api.bilibili.com/x/v2/subtitle/web/view?" + parse.urlencode(params)
    if not _safe_https_host(url, exact="api.bilibili.com"):
        return [], "unsafe_api_host"
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": referer or f"https://www.bilibili.com/video/{state.get('bvid') or state.get('aid')}",
        "Origin": "https://www.bilibili.com",
        "Accept": "application/octet-stream",
    }
    if cookies:
        headers["Cookie"] = _cookie_header(cookies)
    try:
        with NO_REDIRECT_OPENER.open(urlrequest.Request(url, headers=headers), timeout=timeout) as response:
            body = response.read(4 * 1024 * 1024)
    except urlerror.HTTPError as exc:
        return [], f"http_{exc.code}"
    except (urlerror.URLError, TimeoutError, OSError):
        return [], "network_error_or_timeout"
    tracks, complete = _protobuf_tracks(body)
    if not complete:
        return [], "protobuf_invalid"
    return tracks, None


def _track_entries(state: dict[str, Any], modern: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries = []
    for item in state.get("legacy_tracks") or []:
        code = str(item.get("lan") or "")
        url = str(item.get("subtitle_url") or "")
        if url.startswith("//"):
            url = "https:" + url
        if code and url and code.casefold() != "danmaku":
            entries.append({
                "language_code": code,
                "language": str(item.get("lan_doc") or code),
                "subtitle_url": url,
                "subtitle_type": "auto" if _generated(code) else "manual",
                "is_generated": _generated(code),
                "provider_route": "legacy_json",
                "track_id": str(item.get("id_str") or item.get("id") or "") or None,
            })
    for item in modern:
        code = str(item.get("language_code") or "")
        url = str(item.get("subtitle_url") or "")
        if url.startswith("//"):
            url = "https:" + url
        if code and url and code.casefold() != "danmaku" and not any(x["language_code"] == code for x in entries):
            generated = _generated(code, str(item.get("language") or ""))
            entries.append({
                "language_code": code,
                "language": str(item.get("language") or code),
                "subtitle_url": url,
                "subtitle_type": "auto" if generated else "manual",
                "is_generated": generated,
                "provider_route": "protobuf",
                "track_id": item.get("track_id"),
            })
    return entries


def _select_direct_entry(entries: list[dict[str, Any]], requested: list[str], subtitle_type: str) -> dict[str, Any] | None:
    candidates = []
    for entry in entries:
        code = str(entry.get("language_code") or "")
        generated = bool(entry.get("is_generated"))
        rank, matched = _language_rank(code, requested)
        if not matched:
            continue
        if subtitle_type == "manual" and generated:
            continue
        if subtitle_type == "auto" and not generated:
            continue
        candidates.append((rank, 1 if generated else 0, code, entry))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[:3])
    return candidates[0][3]


def _subtitle_identity(entry: dict[str, Any]) -> dict[str, Any]:
    url = str(entry.get("subtitle_url") or "")
    if url.startswith("//"):
        url = "https:" + url
    parsed = parse.urlsplit(url)
    return {
        "language_code": entry.get("language_code"),
        "language": entry.get("language"),
        "subtitle_type": entry.get("subtitle_type"),
        "provider_route": entry.get("provider_route"),
        "track_id": entry.get("track_id"),
        "host": parsed.hostname,
        "path_sha256": hashlib.sha256(parsed.path.encode("utf-8")).hexdigest()[:20],
        "query_keys": sorted(parse.parse_qs(parsed.query)),
    }


def _generated(code: str, label: str = "") -> bool:
    normalized = code.casefold().strip()
    label_is_ai = bool(re.search(r"(?<![a-z])ai(?![a-z])", label.casefold())) or "自动" in label
    return normalized in GENERATED_CODES or normalized.startswith("ai-") or label_is_ai


def _language_rank(code: str, requested: list[str]) -> tuple[int, bool]:
    def aliases(value: str) -> set[str]:
        normalized = value.casefold().replace("_", "-")
        if normalized in {"ai-zh", "zh", "zh-cn", "zh-hans"}:
            return {"ai-zh", "zh", "zh-cn", "zh-hans"}
        if normalized in {"ai-en", "en", "en-us"}:
            return {"ai-en", "en", "en-us"}
        return {normalized}

    code_aliases = aliases(code)
    for index, value in enumerate(requested):
        if code_aliases & aliases(value):
            return index, True
    return len(requested), False


def _failure(reason: str, *, failure: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "unavailable",
        "records": [],
        "reason": reason,
        "scope": "captions_only; no_media_download; no_asr; no_danmaku",
    }
    if failure:
        result["failure"] = {"kind": failure}
    return result


def _emit(result: dict[str, Any], out: str | None) -> None:
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if out:
        path = Path(out)
        if path.exists():
            raise ValueError("--out already exists; choose a new artifact path")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text + "\n")
        matches = result.get("matches") if isinstance(result.get("matches"), list) else []
        preview = {
            "status": result.get("status"),
            "source": "bilibili",
            "url": result.get("url"),
            "original_url": result.get("original_url"),
            "video_id": result.get("video_id"),
            "page": result.get("page"),
            "language_code": result.get("language_code"),
            "subtitle_type": result.get("subtitle_type"),
            "segment_count": result.get("segment_count"),
            "returned_segment_count": result.get("returned_segment_count"),
            "match_count": result.get("match_count"),
            "match_preview": [
                {
                    "index": item.get("index"),
                    "start_seconds": item.get("start_seconds"),
                    "end_seconds": item.get("end_seconds"),
                    "text": str(item.get("text", ""))[:240],
                    "text_truncated": len(str(item.get("text", ""))) > 240,
                }
                for item in matches[:5]
                if isinstance(item, dict)
            ],
            "output_file": str(path),
            "note": "full caption result saved; use the file for further find/location instead of refetching",
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))
    else:
        print(text)


def _requested_languages(value: str | None) -> list[str]:
    if value is None or not str(value).strip():
        return list(DEFAULT_LANGUAGES)
    values = [part.strip() for part in str(value).split(",") if part.strip()]
    if values == ["all"]:
        return list(DEFAULT_LANGUAGES)
    if not values or len(values) > 12 or any(len(part) > 40 for part in values):
        raise ValueError("language_list_invalid")
    return values


def _preferred_language(requested: list[str]) -> str:
    for value in requested:
        normalized = value.casefold().replace("_", "-")
        if normalized in {"ai-zh", "zh", "zh-hans", "zh-cn"}:
            return "ai-zh"
        if normalized in {"ai-en", "en", "en-us"}:
            return "ai-en"
        return value
    return "ai-zh"


def _with_records(result: dict[str, Any], records: list[dict[str, Any]], code: str, generated: bool, args: Any) -> dict[str, Any]:
    if not records:
        result.update(_failure("subtitle_empty", failure="subtitle_empty"))
        return result
    max_segments = int(getattr(args, "max_segments", 5000))
    segments = records[:max_segments]
    find_text = str(getattr(args, "find", "") or "").casefold()
    matches = [item for item in segments if find_text and find_text in item["text"].casefold()]
    coverage_partial = False
    duration = result.get("duration_seconds")
    if isinstance(duration, (int, float)) and duration > 0 and records:
        coverage_partial = float(records[-1].get("end_seconds") or 0.0) < float(duration) * 0.8
    is_partial = len(segments) < len(records) or coverage_partial
    result.update(
        {
            "status": "partial" if is_partial else "ok",
            "records": segments,
            "matches": matches,
            "match_count": len(matches),
            "matches_scope": "returned_segments",
            "language": code,
            "language_code": code,
            "subtitle_type": "auto" if generated else "manual",
            "is_generated": generated,
            "segment_count": len(records),
            "returned_segment_count": len(segments),
            "segments_truncated": len(segments) < len(records),
        }
    )
    partial_reasons = []
    if len(segments) < len(records):
        partial_reasons.append("max_segments")
    if coverage_partial:
        partial_reasons.append("caption_ends_before_video")
    if partial_reasons:
        result["partial_reason"] = ";".join(partial_reasons)
    return result


def _direct_read(
    ref: BilibiliRef,
    requested: list[str],
    subtitle_type: str,
    cookies: dict[str, str],
    timeout: float,
    config: dict[str, Any],
    args: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    """Try the public/authorized Bilibili metadata and subtitle APIs.

    Return a definitive caption or access outcome from the official API route.
    """

    base = {
        "source": "bilibili",
        "original_url": ref.original,
        "url": ref.target,
        "video_id": ref.video_id,
        "page": ref.page or 1,
        "config": config,
        "session_used": bool(cookies),
        "scope": "captions_only; no_media_download; no_asr; no_danmaku",
        "integration": {
            "route": "field-search video",
            "provider": "Bilibili subtitle API",
            "runtime": "standard-library HTTPS + official subtitle endpoints",
            "media_downloaded": False,
            "asr_used": False,
            "danmaku_downloaded": False,
            "browser_cookies_used": False,
            "modern_protobuf_probe": True,
        },
    }
    state, state_error = _view_state(ref, cookies, timeout)
    if state is None:
        if state_error in {"network_error_or_timeout", "invalid_json_response"}:
            result = _failure(state_error, failure="bilibili_api_error")
            result.update(base)
            return result, None
        reason = "access_blocked" if state_error and state_error.startswith("http_") else (state_error or "video_metadata_unavailable")
        result = _failure(reason, failure="bilibili_api_error")
        result.update(base)
        return result, None
    base.update(
        {
            "video_id": state.get("bvid") or ref.video_id,
            "aid": state.get("aid"),
            "cid": state.get("cid"),
            "page": ref.page or 1,
            "page_defaulted_to_first": ref.page is None and int(state.get("page_count") or 1) > 1,
            "page_count": state.get("page_count"),
            "title": str(state.get("title") or ""),
            "duration_seconds": state.get("duration_seconds"),
        }
    )
    preferred = _preferred_language(requested)
    modern_tracks, modern_error = _modern_tracks(state, cookies, timeout, preferred, ref.target)
    if modern_error:
        reason = "access_blocked" if modern_error.startswith("http_") else modern_error
        failure = "subtitle_metadata_blocked" if reason == "access_blocked" else "subtitle_metadata_error"
        result = _failure(reason, failure=failure)
        result.update(base)
        return result, None
    entries = _track_entries(state, modern_tracks)
    base["available_subtitles"] = [
            {
                "language_code": item["language_code"],
                "language": item["language"],
                "subtitle_type": item["subtitle_type"],
                "is_generated": item["is_generated"],
                "provider_route": item["provider_route"],
            }
            for item in entries
        ]
    base["danmaku_filtered"] = True
    selected = _select_direct_entry(entries, requested, subtitle_type)
    if selected is None:
        if state.get("need_login_subtitle") and not entries:
            base.update(_failure("login_required", failure="login_required"))
        elif entries:
            reason = "no_subtitles_for_requested_type" if subtitle_type != "any" else "no_subtitles_for_requested_language"
            base.update(_failure(reason, failure="no_matching_caption"))
        else:
            base.update(_failure("no_subtitles", failure="no_subtitles"))
        return base, None
    base["selected_subtitle"] = _subtitle_identity(selected)
    records, subtitle_error = _subtitle_json(str(selected["subtitle_url"]), timeout, ref.target)
    if records is None:
        reason = "access_blocked" if subtitle_error and subtitle_error.startswith("http_") else (subtitle_error or "subtitle_fetch_failed")
        base.update(_failure(reason, failure="subtitle_fetch_failed"))
        return base, None
    return _with_records(base, records, str(selected["language_code"]), bool(selected["is_generated"]), args), None


def run(args: Any) -> int:
    ref = parse_video_ref(getattr(args, "url_or_id", ""))
    if ref is None:
        return 2
    out = getattr(args, "out", None)
    if out and Path(out).exists():
        raise ValueError("--out already exists; choose a new artifact path")
    config_result = runtime_config.load_config(getattr(args, "config", None))
    config = runtime_config.redacted_config_summary(config_result)
    if ref.short_link:
        result = _failure("short_link_requires_verified_resolution", failure="unsupported_short_link")
        result.update(source="bilibili", original_url=ref.original, url=ref.target, config=config)
        _emit(result, out)
        return 2
    session_file, session_path_reason = _session_path(args, config_result)
    if session_path_reason:
        result = _failure(session_path_reason, failure="session_unavailable")
        result.update(source="bilibili", original_url=ref.original, url=ref.target, config=config)
        _emit(result, out)
        return 2
    cookies, session_reason = _load_session(session_file)
    if session_reason:
        result = _failure(session_reason, failure="session_invalid")
        result.update(source="bilibili", original_url=ref.original, url=ref.target, config=config)
        _emit(result, out)
        return 2
    timeout = float(getattr(args, "timeout", 30.0))
    requested = _requested_languages(getattr(args, "language", None))
    subtitle_type = str(getattr(args, "subtitle_type", "any"))
    direct_result, _unused = _direct_read(
        ref, requested, subtitle_type, cookies, timeout, config, args
    )
    if direct_result is None:
        direct_result = _failure("network_error_or_timeout", failure="bilibili_api_error")
        direct_result.update(
            source="bilibili",
            original_url=ref.original,
            url=ref.target,
            video_id=ref.video_id,
            page=ref.page or 1,
            config=config,
            session_used=bool(cookies),
        )
    result = direct_result
    _emit(result, out)
    return 0 if result.get("status") in {"ok", "partial"} else 2


def main(args: Any) -> int:
    return run(args)
