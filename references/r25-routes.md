# R25 Bilibili subtitle route

This is an explicit `video` route. It is selected only when the positional
argument is a Bilibili video URL or a BV/AV identifier; YouTube behavior is
unchanged.

```text
<python> <skill-dir>/scripts/search.py video \
  "https://www.bilibili.com/video/BVxxxxxxxxxx" \
  --config <local-config.json> --language ai-zh --subtitle-type auto \
  --find "term" --out <new-result.json>
```

The adapter reads metadata from Bilibili's public metadata endpoint, then
uses the authorized legacy WBI subtitle endpoint and the official web
subtitle Protobuf endpoint. The legacy request uses the exact video Referer;
the modern request uses `preferred_language=ai-zh` for the Chinese AI track.
The signed subtitle URL is fetched without forwarding login cookies. The
implementation is metadata/caption-only: it does not download media,
danmaku, playlists, or run ASR. The protocol shape follows the current
[Bilibili AI subtitle extractor](https://github.com/ccBilly-aipm/bilibili-ai-subtitle/blob/main/src/bilibili_ai_subtitle/extractor.py)
and its [web-subtitle Protobuf parser](https://github.com/ccBilly-aipm/bilibili-ai-subtitle/blob/main/src/bilibili_ai_subtitle/protobuf.py);
the browser-cookie code in that project is not used here.

## Input and output

Normal Bilibili video URLs are canonicalized to the video path. Only `p` is
retained from the query. A multi-part URL without `p` reads page 1 and sets
`page_defaulted_to_first=true`; an explicit `?p=N` is preserved and resolved
to that page's CID. Bilibili `b23.tv` short links are not followed: they return
`short_link_requires_verified_resolution` until a verified canonical URL is
provided.

Each caption record contains `index`, `start_seconds`,
`duration_seconds`, `end_seconds`, and `text`. The result also preserves
`aid`, `cid`, `duration_seconds`, selected language/type, `available_subtitles`,
and a non-secret `selected_subtitle` identity: provider route, public track ID
when supplied, CDN host, query-key names, and a hash of the URL path. Signed
query values are never emitted.

With `--out`, the complete bounded result is saved to a new file and stdout
contains only a small preview with up to five matches. Existing output files
are never overwritten. `--max-segments` caps the returned records; a caption
whose final timestamp is materially earlier than the video duration is also
marked `partial` with `partial_reason=caption_ends_before_video`.

## Session and failure semantics

The optional local config stores only a session-file path:

```json
{
  "schema_version": 1,
  "runtimes": {
    "youtube_transcript_python": "C:/path/to/youtube-runtime/Scripts/python.exe"
  },
  "readers": {
    "bilibili": {
      "session_path": "C:/path/to/qr-session.json"
    }
  }
}
```

The session must come from an explicit Bilibili QR login flow. The adapter
does not read browser profiles or browser-cookie stores, and only sends the
selected Bilibili session cookies to `api.bilibili.com`. Do not put cookie
values, QR URLs, or session contents into the config file or evidence notes.

Important unavailable reasons remain distinct: `login_required` means the
metadata endpoint says the subtitle needs authorization; `no_subtitles` means
the selected page returned no subtitle tracks without that login signal;
`access_blocked` covers HTTP access/risk responses; `network_error_or_timeout`
and `protobuf_invalid` preserve transport/protocol failures; and
`video_metadata_unavailable`/`bilibili_page_not_found` preserve missing or
invalid video/page metadata. An empty subtitle body is
`subtitle_empty`, not automatically `no_subtitles`.

`search.py doctor --source bilibili` performs only a local route/config check;
it does not contact Bilibili or read the session file.

## Batch use

`batch` accepts Bilibili items as `kind=video` using the same `language`,
`subtitle_type`, `find`, `max_segments`, `timeout`, `config`, and
`session_path` options. Request keys include the item kind, target, options,
and config fingerprint, so successful Bilibili results can be reused while
unavailable/error results are retried. YouTube items remain isolated from the
Bilibili session and provider parameters.
