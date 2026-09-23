# R31: task-local recovery, freshness and original passages

These explicit commands reuse existing FS batch, feed, report and document
artifacts. No account, scheduled monitor, global index or model service is
required.

## Recover a small mixed batch

```text
<python> <skill>/scripts/search.py batch create <items.json> --out <new-manifest.json>
<python> <skill>/scripts/search.py batch run <manifest.json> --out <new-checkpoint.json>
<python> <skill>/scripts/search.py batch status <checkpoint.json>
<python> <skill>/scripts/search.py batch run <checkpoint.json> --out <new-resumed.json>
```

`--out` creates the output before child work and updates it atomically after
each item. A stopped process leaves an `in_progress` manifest of completed
items. Resume with that file as input and a *new* output path; earlier files
remain unchanged. A stop between child completion and checkpoint writing may
rerun that one item. Without `--out`, there is no durable checkpoint. Explicit
refresh removes selected old results from the initial checkpoint so an
interrupted refresh remains pending.

`read`, `video` and `discourse` retain their contract. `feed`, `discover` and
`convert` are now accepted. A convert item needs `options.out_dir`; its
request key includes local input bytes so a changed file is not silently
reused. Normal success reuses offline. Partial/unavailable/error items retry.
A feed update check is separate; batch reuse is not a freshness check.

```json
{"items":[
  {"id":"announcements","kind":"feed","target":"https://example.org/feed.xml","options":{"limit":5}},
  {"id":"site-links","kind":"discover","target":"https://example.org/","options":{"request_budget":2}},
  {"id":"attachment","kind":"convert","target":"C:/task/source.pdf","options":{"out_dir":"C:/task/pdf-report"}}
]}
```

## Check whether a saved feed changed

```text
<python> <skill>/scripts/search.py feed <URL> --limit 5 --out <first.json>
<python> <skill>/scripts/search.py feed <same-URL> --limit 5 --check-from <first.json> --out <new-check.json>
```

The previous snapshot must pass its hash check and match URL, limit and since
options. The new path must not exist. Previous files are never overwritten.
The check sends saved ETag and/or Last-Modified validators when present. HTTP
304 retains previous entries and `fetched_at`, adds a new `checked_at` and
`change_status=not_modified`, and saves a new valid snapshot. A new HTTP 200
saves parsed entries and a change summary over the *returned entry window
only*. HTTP 200 with the same bounded window does not prove the whole feed is
unchanged. An error creates no accepted snapshot. Entry `date` is source
publication time; `fetched_at` and `checked_at` are local observation times.
If a feed's previous final URL differed from the requested URL after a
redirect, the next check uses an ordinary GET rather than applying a validator
to a potentially different representation.

An ordinary call with an existing valid `--out` still reuses that file
offline. Use `--check-from` when freshness matters. This is a one-shot read,
not a subscription. Conditional requests follow [feedparser's HTTP guidance](https://feedparser.readthedocs.io/en/stable/http-etag.html)
and [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html).

## Locate prior original passages

List only saved artifacts relevant to the current task. Relative paths are
resolved from the manifest file:

```json
{"artifacts":[
  {"id":"page","kind":"document","path":"docs/page-snapshot.json"},
  {"id":"report","kind":"report","path":"reports/converted-pdf"}
]}
```

```text
<python> <skill>/scripts/search.py locate <task-materials.json> <literal-term>
```

`locate` checks at most 30 explicitly listed document snapshots or FS report
directories. It reuses their integrity checks, then returns source URL when
known, stored text hash/version, snapshot time, a small exact quote, line and
character offsets in the saved extraction. At most 20 matches are shown, at
most three per artifact. It scans at most 64 MiB of validated text and counts
at most 10,000 hits; `total_matches_exact` and failures expose any cap. Total
matches and display truncation remain explicit.
Matching bytes are flagged as the same extracted content, not the same study,
publisher or independent evidence. Damaged artifacts are reported as failures.
The command never refetches a source. Offsets refer to saved extracted text;
use `document find/open` or `report find/open` for full local context. They
are not live-webpage positions or factual validation. The quote/position
approach is adapted from [W3C Web Annotation selectors](https://www.w3.org/TR/annotation-model/),
without an annotation server or knowledge graph.
