# R24 optional routes

These routes are explicit additions to the common `scripts/search.py` entry.
They are not selected by ordinary `search`, `read`, `auto`, or source fan-out.

## Video captions

Use an isolated Python runtime containing [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api):

```text
<python> <skill-dir>/scripts/search.py video "https://www.youtube.com/watch?v=<id>" \
  --config <local-config.json> --language en --find "term" --out <new-result.json>
```

The accepted input is a YouTube watch/shorts/embed URL or an 11-character
video ID. `--language` is a comma-separated preference list. `--subtitle-type`
is `any` (manual first, then automatic), `manual`, or `auto`. Returned records
contain `start_seconds`, `duration_seconds`, `end_seconds`, `index`, and text;
`matches` contains the segments matching `--find`. The result also preserves
language, generated/manual type, available-language metadata, segment counts,
and the provider version.

This route only requests captions. It does not download audio/video, use
cookies, invoke ASR, use a proxy supplied by the route, or call a paid
transcription service. `no_subtitles`, `no_subtitles_for_language`,
`video_unavailable`, `access_blocked`, and provider/runtime failures remain
unavailable/error states. A segment cap produces `partial` and an explicit
`max_segments` reason. With `--out`, complete segments are saved to the new
file while stdout contains only bounded metadata and up to five match previews;
use the saved file for later locating rather than refetching.

## Discourse topics

Use a public HTTPS topic URL:

```text
<python> <skill-dir>/scripts/search.py discourse \
  "https://forum.example.org/t/topic-slug/123" \
  --post-limit 50 --request-budget 6 --batch-size 20 --timeout 20 \
  --out <new-topic.json>
```

The first topic JSON response is not treated as the complete thread. The
adapter follows the public `post_stream.stream` IDs with bounded
`/t/<id>/posts.json?post_ids[]=...` requests. Each record retains a public post
URL, topic/post IDs, floor number, author, creation/update time, cleaned text,
and available `reply_to_post_number`/`reply_to_post_id` fields.

`--post-limit` bounds returned posts, `--request-budget` includes the initial
topic request, and `--batch-size` bounds IDs in each follow-up. A budget limit,
missing stream, incomplete post batch, 401/403/429, or another access/network
failure is preserved in `read.incomplete_reasons`/`failure`; records are not
promoted to complete evidence. Long post text may include the existing
`text_full` companion when the bounded display text is clipped; `post_limit`
is a post-count bound, not a promise that the entire JSON file is small. With
`--out`, stdout contains only topic/read statistics and a file reference; the
complete posts remain in the new local file. The route is public/read-only: it
does not log in, read cookies, or infer private access. See the [Discourse API documentation](https://docs.discourse.org/).

## Runtime configuration and doctor

The optional local JSON configuration contains only path references. The
default location is a user-local `field-search/config.json`; pass `--config`
to use another file. A portable shape is:

```json
{
  "schema_version": 1,
  "runtimes": {
    "youtube_transcript_python": "C:/path/to/isolated/Scripts/python.exe"
  },
  "readers": {
    "xiaohongshu": {
      "session_root": "C:/authorized/isolated/session",
      "adapter_path": "C:/authorized/isolated/readonly_adapter.py",
      "python_path": "C:/authorized/isolated/.venv/Scripts/python.exe"
    }
  }
}
```

Do not put tokens, cookies, passwords, browser data, QR files, or session
contents in this file. The R22 session path is only a reference; the config
loader and doctor never read its contents.

```text
<python> <skill-dir>/scripts/search.py doctor --source youtube --config <local-config.json>
<python> <skill-dir>/scripts/search.py doctor --source xiaohongshu --config <local-config.json>
<python> <skill-dir>/scripts/search.py doctor --source xiaohongshu --probe-session --config <local-config.json>
```

Default checks are local: configured/path-exists, optional package import, and
route-file presence are reported separately. `--probe-session` is the only
targeted network check and performs one bounded read-only R22 adapter search;
`path_exists` never implies `session_authorized`.

## Task-local batch reuse

Create a small manifest; each item owns its target and options:

```json
{
  "items": [
    {"id": "page", "kind": "read", "target": "https://example.org/a", "options": {"reader": "jina"}},
    {"id": "captions", "kind": "video", "target": "https://www.youtube.com/watch?v=<id>", "options": {"language": "en", "find": "term"}},
    {"id": "forum", "kind": "discourse", "target": "https://forum.example.org/t/topic/123", "options": {"post_limit": 20}}
  ]
}
```

```text
<python> <skill-dir>/scripts/search.py batch create <items.json> --out <new-manifest.json>
<python> <skill-dir>/scripts/search.py batch run <manifest.json> --out <new-result.json>
<python> <skill-dir>/scripts/search.py batch run <result.json> --out <new-retry.json>
<python> <skill-dir>/scripts/search.py batch run <result.json> --refresh-id captions --out <new-refresh.json>
<python> <skill-dir>/scripts/search.py batch status <result.json>
```

The request key includes `kind`, target, and item options. Only `ok` and
`no_results` items with the same key are reused; partial/error/unavailable
items are attempted again. `--refresh` re-reads every item and
`--refresh-id` re-reads selected items. The original manifest is never
overwritten. With `--out`, stdout is a bounded run summary; the saved result
manifest contains child outputs needed for reuse and can be inspected on
demand. The batch runner uses separate child invocations and does not
share mutable parameters between items or create a global index.
