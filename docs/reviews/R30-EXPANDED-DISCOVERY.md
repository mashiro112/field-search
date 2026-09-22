# R30: wider exploration, site discovery and local materials

Date: 2026-09-23. Status: delivered with scoped acceptance. The plan was published
before implementation; the final source snapshot contains 182 files.

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
| Version-specific library docs | [Context7](https://github.com/upstash/context7), MIT client | Conditional candidate. One anonymous official library-search GET returned HTTP 200 and valid results metadata. Full document retrieval, quota and lasting anonymous access were not tested; no account/key was created. |
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

The independent trial also found a concrete handoff defect: ordinary Python could
discover links but could not import the existing document reader's optional
dependency. Reuse the already installed, verified websearch 0.6.1 environment via
`runtimes.document` in the existing local config. This small runtime-dispatch fix
is in scope; it does not add or change a search backend or install another parser.

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

Discovery, material conversion and the document-runtime handoff fix have passed
the scoped real/fixture and independent checks described below.
R28 ChatGPT report transfer and X-native search keep their separate partial status.

| Validation | Evidence and boundary |
|---|---|
| Public site discovery | FastHTML homepage, robots and sitemap returned 8 candidates from 38 with a four-attempt budget; a missing root llms.txt was reported as HTTP 404. Official llmstxt.org llms and sitemap entries were found; literal Python filtering selected its intro Markdown page. |
| HTML feed discovery | One request to python.org found five feed candidates; a limit of three returned PEPs, Jobs and Python Software Foundation feed URLs with explicit partial/external flags. An omitted feeds-mode dispatch was found during this real check, corrected and rerun; earlier empty results are withdrawn. |
| Discovery counterexamples | Failed fetches consume budget; nested pending work and output clipping are explicit. Root URLs without a trailing slash, path-level indexes, relative/parenthesized links, descriptions and non-page sitemap extensions were checked. Invalid roots, HTML masquerading as llms and damaged/conflicting cache requests are not valid indexes. |
| Material formats | Local known-content PDF, DOCX, PPTX, XLSX, HTML, TXT and CSV fixtures were converted. Selected text/table/Unicode/link content was checked; this is not universal layout or formula fidelity. A public W3C dummy PDF was also actually converted. |
| Independent conversion | A separately built DOCX containing English, Chinese and an emoji was converted through MarkItDown 0.1.8, then read and searched offline through FS. Same-request reuse and changed-request rejection passed. |
| Material failures | A blank PDF returned no extractable text; unsupported ZIP input failed. Changed input/source URL and damaged report bodies were rejected without overwriting. Failed conversion leaves no final artifact directory. |
| Discovery-to-reader handoff | The final installed common entry, started with ordinary Python, read the actual FastHTML documentation through the configured existing Jina/websearch runtime and saved a nine-page snapshot. Independent offline open/find then passed (31 FastHTML matches, bounded output). A missing configured interpreter returned a structured unavailable result before networking. Earlier prototype/publication-copy checks are not used as installed-source acceptance. |
| Dependency provenance | MarkItDown 0.1.8 with selected extras runs in isolated Windows Python 3.12.14. [Requested package](../runtime/r30-material/requirements.in) and [42 tested package versions](../runtime/r30-material/requirements.lock.txt) are published. No new OCR, cloud or generative model client was enabled. |

Findings fixed during review include failed attempts escaping the discovery
budget, misleading parse/cache success states, path construction, missing
feeds-mode dispatch, unrelated sitemap extension URLs appearing as document pages,
and a missing document dependency under the common entry's interpreter. The result contains compact
provenance and explicit partial/failure state; neither a source index nor format
conversion independently verifies the source's claims.

The root llms.txt path is not universally present. Compressed sitemaps, arbitrary
Markdown dialects, dynamic navigation, complete historical coverage and visual
document fidelity are outside the accepted cases. Cached error snapshots keep
their failure status and nonzero exit; a new path is needed for a fresh attempt.
