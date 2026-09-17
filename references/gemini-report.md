# R26 completed-report handoff

This reference covers a deliberately thin local handoff for a completed Gemini
Deep Research report. The route does not start research, call Gemini, use a
paid API, read credentials, or publish a report. An explicitly authorized
private export may be used for local acceptance, but its body and original URL
stay outside public result records.

## Local import

The caller must provide one explicit local UTF-8 Markdown file and one explicit
task directory:

```text
<python> <skill-dir>/scripts/search.py report import <report.md> \
  --out-dir <task-report-dir> \
  --method copy|docs_export|local_file \
  --source-url <optional-source-url>
```

The importer writes exactly two artifacts:

- `report.md`: the original input bytes, without Markdown normalization;
- `metadata.json`: schema version, import time, acquisition method, optional
  source URL, byte/hash/line counts, title/heading count, and an explicit
  initial integrity state.

`integrity.status` starts as `unverified`; `link_completeness` is `unknown`
and `fact_verification` is `not_performed`. A recorded URL is metadata only:
the importer never fetches it and its existence does not prove citation
completeness. Importing a report does not validate its claims.

Identical bytes imported into the same directory are reported as `reused`.
Different bytes return an error and cannot silently overwrite `report.md` or
`metadata.json`. Choose a new explicit directory for a different report.

When an existing Docs link is available, first read Drive metadata and confirm
the file is a native Google Doc, then call `export_file` with
`mime_type=text/markdown`; materialize its authenticated `file_uri` through
the controlled download/workspace path and pass those exact bytes directly to
`report import --method docs_export`. Do not put the source URL in shell logs
or public results, and do not have the model rewrite the exported body. If the
connector is unavailable, use the same official Docs Markdown-download entry
point.

## Offline reading

```text
<python> <skill-dir>/scripts/search.py report open <task-report-dir> --page 1
<python> <skill-dir>/scripts/search.py report find <task-report-dir> "literal term"
```

Both commands read only the local two-file artifact. `open` returns one bounded
page; `find` scans the complete local body and returns at most 20 excerpts with
page locations. Neither command follows report links or uses the network.

## Copy versus Docs export

For the first real report only, compare the two official acquisition forms if
both are available for the same report:

1. Official **Copy Contents** output.
2. Official **Docs → Markdown** export.

Compare the body, heading structure, Markdown tables, and cited URL strings;
record the comparison as separate evidence rather than changing the importer's
integrity status automatically. If Copy Contents preserves all required body,
table, heading, and citation URL content, prefer `--method copy`. If it loses a
material part, use the Docs export as the fixed method for that source. Do not
force a two-export comparison for every later report.

The R26 authorized comparison evidence is kept under the run's private
directory. It found 16 headings, 28 body paragraphs, and 80 table cells
matching after ignoring Markdown/whitespace differences and two `&nbsp;` blank
lines. The 45 numbered references each had an HTTPS URL, and the first five
URLs matched the webpage expansion. This does not verify all 45 originals or
the semantics of every citation. The share page had no Copy Contents control in
the available logged-out view, so Docs export is the current usable acquisition
path; do not claim that Copy Contents was validated. The browser-side
`content.export` path is not a verified local route. Keep the importer’s
`unverified` integrity state even when this structural comparison passes.
