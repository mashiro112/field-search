# R30 publisher discovery and local material conversion

These routes expand what FS can inspect while keeping retrieval and model-facing
output bounded. Neither starts a research job, background watcher or global index.

## Find publisher entrypoints

```text
<python> <skill>/scripts/search.py discover https://example.org/docs/ --contains authentication --limit 15 --out <new.json>
<python> <skill>/scripts/search.py discover https://example.org/docs/llms.txt --kind llms --limit 10
<python> <skill>/scripts/search.py discover https://example.org/sitemap.xml --kind sitemap --request-budget 4
<python> <skill>/scripts/search.py discover https://example.org/ --kind feeds
```

`--kind` accepts `auto` (default), `llms`, `sitemap` and `feeds`. Auto recognizes
explicit index URLs; for a site/path it inspects the page and conventional entry
files. `--contains` filters candidates by literal text; this is not semantic
search. Select worthwhile returned URLs and use the existing read/feed routes.
The discovery helper does not fetch all referenced pages.

Default limit is 15 and the default fetch-attempt budget is 4. Failed attempts
consume budget. Each attempt uses the existing HTTPS transport, with at most
three redirects and 2 MiB per response; the budget counts documents attempted,
not individual wire requests across redirects. Nested discovery links are
scheduled only for the same origin. External candidates may be returned and
marked, but are not scheduled. Ordinary public HTTPS redirects retain the shared
transport behavior. Inputs and redirects use FS's established URL policy,
including rejection of credentials and literal private/local destinations.

`--limit` accepts 1–100, `--request-budget` 1–8, and `--timeout` 1–60 seconds
(default 15). The timeout is passed to each document fetch; it is not a promised
end-to-end wall-clock deadline across the whole discovery operation.

Inspect `status`, `attempts_count`, `total_matching`, `truncated`, `pending_count`,
`unvisited` and `failures`. The pending list is only a bounded preview. A valid
empty index is different from failure or an unfinished budget. A cached result
is a dated snapshot: matching request/hash reuse is offline; use a new file for
fresh discovery. Changed requests or damaged caches are refused.
Saved failures also retain their failure status/nonzero exit when replayed;
they are not promoted to successful cached discoveries.

Sources and limits:

- [llms.txt](https://llmstxt.org/) is a publisher-curated proposal with uneven
  adoption. The parser supports its inline Markdown list links, including
  bracketed URLs, balanced parentheses and colon notes; it does not implement
  arbitrary Markdown extensions. No instructions in these files are executed.
- [Sitemaps](https://www.sitemaps.org/protocol.html) expose publisher-listed URLs.
  The helper reads bounded XML `urlset`/`sitemapindex` documents; DTD and invalid
  roots are rejected. A sitemap is not proof of completeness or freshness.
- HTML RSS/Atom/Markdown link discovery identifies candidates, not a verified
  live subscription. JavaScript-only navigation requires an existing browser
  route if warranted. No browser or third-party crawler is installed here.

The helper is small FS format adaptation on standard parsers and the existing
bounded fetcher. It is not advertised as an imported third-party search engine.

## Convert a local material to an FS report

```text
<python> <skill>/scripts/search.py convert <local.pdf> --out-dir <new-report-dir>
<python> <skill>/scripts/search.py convert <local.docx> --out-dir <new-report-dir> --source-url https://example.org/source
<python> <skill>/scripts/search.py report open <report-dir> --page 1
<python> <skill>/scripts/search.py report find <report-dir> <literal-term>
```

The input is a local file already obtained in the authorized task. Supported
formats are PDF with extractable text, DOCX, PPTX, XLSX, HTML/HTM, TXT and CSV.
`--source-url` is provenance only; it is never fetched. Input bytes are hashed,
the converter output is stored as UTF-8 Markdown, and existing report open/find
provide offline reading. Same-request valid output reuses without conversion;
changed input/request and damaged artifacts cannot silently overwrite it.

Maximum input size is 25 MiB and accepted converted Markdown is limited to
32 MiB. `--timeout` defaults to 60 seconds (range 1–180) for the converter
subprocess. These byte checks do not guarantee an upper bound on parser peak
memory; Office container size is checked separately before conversion.

This is lossy text conversion. It does not validate page layout, merged cells,
equations, formulas, complete citations or image content. A scanned PDF without
usable text needs the existing PDF/OCR tools when that is actually required.
The route adds no OCR, audio transcription, cloud document intelligence,
generative model client, macro execution or external plugin.

## Runtime reuse and installation

The converter directly uses [Microsoft MarkItDown 0.1.8](https://github.com/microsoft/markitdown)
(MIT), with only `pdf,docx,pptx,xlsx` extras. Its own dependencies retain their
licenses. The tested isolated Windows runtime uses Python 3.12.14. The public FS
repository provides the requested extras and exact tested dependency versions in
`docs/runtime/r30-material/requirements.in` and `requirements.lock.txt`; the
Windows package set is not a universal platform lock.

```text
uv venv <runtime> --python <supported-python>
uv pip install --python <runtime-python> -r <requirements.lock.txt>
```

Merge this non-secret setting with the existing FS config rather than replacing
unrelated runtime/session settings:

```json
{"schema_version":1,"runtimes":{"material":"<runtime-python-executable>"}}
```

`--python-path` and `--config` allow an explicit override. Source files are not
uploaded to a new service. MarkItDown may use a bundled local file-type classifier;
that is distinct from calling a generative model. Parser output remains untrusted
source data. Exact acceptance and known limits are recorded in the public
`docs/reviews/R30-EXPANDED-DISCOVERY.md`.

To follow discovered pages through FS's existing full-document reader, configure
`runtimes.document` with its existing isolated `websearch-skill==0.6.1` Python.
The common `read` and `document` entries use that dependency environment even
when started with ordinary Python. This reuses the current Jina backend and
pagination; it does not change the separate explicit Crawl4AI setup. See
[providers.md](providers.md) for that reader's existing provenance and limits.
