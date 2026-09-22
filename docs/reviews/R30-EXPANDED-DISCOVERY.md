# R30: wider exploration, site discovery and local materials

Date: 2026-09-23. Status: plan approved through the owner's autonomous-work request;
implementation/acceptance in progress. This is not an accepted-feature claim.

## What was explored

The goal is to improve useful source coverage and low-cost reuse across the whole
FS workflow. Three bounded research lanes used existing FS search routes and
official project/documentation checks. No new Deep Research job was submitted.

| Space | Candidate and evidence | Decision |
|---|---|---|
| Publisher/site navigation | [llms.txt](https://llmstxt.org/), [Sitemaps protocol](https://www.sitemaps.org/protocol.html), HTML feed links | Implement explicit bounded discovery of candidate pages, Markdown documents and feeds. No whole-site crawler. |
| Attachments and local materials | [Microsoft MarkItDown](https://github.com/microsoft/markitdown), MIT, 0.1.8 | Implement a local-file conversion adapter and reuse FS report storage/open/find. Install only required format extras. |
| Static-page extraction | [Trafilatura](https://trafilatura.readthedocs.io/en/latest/corefunctions.html), Apache-2.0 | Already used inside the current document HTML fallback. Do not install another independent static reader in this round. |
| Layout/OCR-heavy documents | [Docling](https://github.com/docling-project/docling), MIT | Keep for a demonstrated layout/scanned-PDF need; its model/runtime requirements are beyond the current lightweight route. |
| Version-specific library docs | [Context7](https://github.com/upstash/context7), MIT client | Conditional candidate. Official docs contain both required-key and keyless-rate-limit wording; do not infer available access from README claims. No account/key is created. |
| Code and implementation discussions | Existing GitHub connector search, issue comments and PR comment tools; grep.app alternatives | Prefer the existing connector. A second connector/wrapper has no demonstrated benefit here. |
| Historical web evidence | [Wayback CDX](https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md) | A bounded public index probe timed out on this host. Useful direction, not a working integrated route. |
| Cross-document reuse and package provenance | [ripgrep](https://github.com/BurntSushi/ripgrep), [deps.dev](https://docs.deps.dev/api/v3/) | Reuse installed rg for explicit task-directory searches. A public deps.dev package-version probe returned HTTP 200 and license/advisory/link metadata; keep the official API available without adding a graph/index subsystem. |

Research statements distinguish official descriptions, installed components,
actual probes and new integration. Lack of a search result is not evidence that
a candidate is absent. No claim of exhaustive discovery or comparative token
savings follows from this sweep.

## Implementation plan

1. `search.py discover URL`: bounded, one-shot reading of publisher entry files.
   Support explicit llms.txt and sitemap URLs, and homepage feed/Markdown links;
   optionally discover likely entry files from a site/path. Return candidate URLs,
   their source and kind, filtering/limits, failures and unvisited work. Only
   follow same-origin discovery documents within the request budget. External
   links can be returned as candidates but are not followed automatically.
2. `search.py convert FILE --out-dir DIR`: use MarkItDown for local text PDFs,
   DOCX, PPTX, XLSX, HTML, TXT and CSV. Preserve Markdown as an FS report, record
   the input hash and converter/version, then reuse report open/find. No URL
   downloading, OCR, LLM enrichment, audio transcription, plugin or Azure setup.
3. Add concise route documentation, isolated runtime configuration and dependency
   pins. Validate real public entry files and representative material formats,
   independently review behavior, then publish source and actual acceptance.

The discovery helper reuses FS's existing bounded HTTPS transport. Its parser is
small format adaptation, not a copied research Skill or a search engine. The
material helper directly reuses the mature converter rather than implementing
Office/PDF extraction. Remote documents remain source data, never instructions.

## Acceptance and cost boundaries

- Discover useful links from real public llms.txt and sitemap files. Preserve
  relative URL resolution, source provenance, de-duplication and explicit
  request/entry limits; malformed/HTML error responses are not valid indexes.
- Demonstrate a feed/Markdown link discovery and bounded sitemap-index behavior.
  Distinguish live inputs from synthetic edge cases. Discovery is not proof of
  completeness, freshness or correctness of the referenced content.
- Convert representative PDF, DOCX, PPTX and XLSX files with known text/table
  content. Verify links/Unicode where supported and read/find in cached Markdown.
  Conversion is lossy; it is not layout, formula or citation-fidelity validation.
- Same-request intact artifacts reuse offline; changed requests/inputs and
  corrupted artifacts cannot silently overwrite or masquerade as valid caches.
- Enforce input/output/time bounds, compact model-facing output and explicit
  unavailable/no-text results. Test important failure paths, not every format
  permutation. Windows UTF-8 handling is part of the actual CLI checks.
- No paid API, new external account, background monitoring, vector database,
  automatic full-site crawl, or repeat Deep Research task is added. MarkItDown
  may use bundled local file-type classification; no generative model is called.

## Results

Pending implementation and independent review. R29 remains the latest completed
source delivery; R28 ChatGPT report transfer and X-native search keep their
separate partial status.
