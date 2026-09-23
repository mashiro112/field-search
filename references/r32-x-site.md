# R32: read-only X site search through OpenCLI

Use this route when X's own search or a post's replies could change the decision and an already authorized OpenCLI browser bridge is connected. The tested upstream is [`@jackwener/opencli` 1.8.7](https://github.com/jackwener/opencli) (Apache-2.0); FS calls its CLI directly and does not copy its adapter or manage login. Check `opencli doctor` and `opencli twitter search --help -f yaml` on the current host before use. An unavailable bridge means this optional route is unavailable; continue native `site:x.com` discovery and the public post reader.

```text
opencli twitter search 'specific query' --product live --limit 5 -f json --window background --site-session ephemeral
opencli twitter thread <post-id-or-url> --limit 10 -f json --window background --site-session ephemeral
```

Only run `search` and `thread` for this FS route. Save the JSON to a task-local file when the result matters, and cite the returned post URLs. Keep the logged-in account, cookies, browser trace and raw account exports out of public artifacts. A search result is a bounded sample, not an exhaustive X index.

**Completeness boundary:** OpenCLI 1.8.7's thread adapter internally stops after at most five cursor pages, then slices to `--limit`. Its JSON array has no total-count, `has_more` or truncation receipt. If the returned count equals the limit, truncation is possible; a smaller count still does not prove all replies were accessible. Inspect follow-up posts or a narrower query for a decision that depends on corrections or exhaustive context. Report reply completeness as unknown unless independently checked.

R32 local trials: one `Docling OCR` search returned five posts in 19.0 s; its selected thread returned the original plus two replies in 7.4 s, whereas the FS public oEmbed read showed only the original. An independent `faster whisper hallucination` search returned five posts in 8.6 s; a selected thread returned exactly the ten requested posts in 8.1 s, illustrating the limit boundary. The second search was topically loose. These tests verify access and added context, not search precision, thread exhaustiveness or factual truth of posts. Ordinary FS search remains unchanged and no paid X API was called.
