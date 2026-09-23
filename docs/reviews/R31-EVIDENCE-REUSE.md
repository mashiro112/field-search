# R31: interrupted-work recovery, feed updates and saved evidence

Date: 2026-09-23. Status: delivered with scoped acceptance. The source manifest
contains 184 files. The prior [execution plan](R31-EVIDENCE-REUSE-PLAN.md)
records the 14-branch exploration and its initial conditions.

## Result and measured trial

| Before | After and observed result |
|---|---|
| A batch kept this run's results in memory until the end. A controlled stop after item one left no output. | With `--out`, a valid `in_progress` checkpoint retained item one. Resuming from it executed only item two. A mixed real Feed + site discovery + local PDF conversion batch completed three items; its next run executed zero and reused three. Interrupted refresh, partial retry, occupied output and changed local-file identity were also checked without network. |
| A valid same-path Feed output was an offline cache; there was no explicit update check. | `feed --check-from OLD --out NEW` performs one conditional GET where validators apply. A real HN RSS first read returned HTTP 200 with Last-Modified; the next returned HTTP 304, retaining three entries and their `fetched_at` while recording a later `checked_at`. A real python.org feed with no validators returned another HTTP 200 and an unchanged *returned window*. Controlled 200→304→changed-200→error cases checked version linking, change counts, no accepted artifact on failure and cross-origin validator stripping. |
| `rg -l` could identify saved files, but a mixed JSON document/report set needed manual type selection and a separate find call to recover location. | `locate` searched three explicitly listed existing artifacts offline. “FastHTML” returned the real documentation URL, content hash and character position; a DOCX fixture and a public repo report were likewise located with their saved versions. A damaged artifact was reported rather than skipped, and byte-identical content was labelled without inferring independent evidence. |

The Skill entry was reduced from 22,322 to 20,023 bytes (10.3%) while adding
R31 routing. Mode-specific details remain in linked references. The Skill
validator passed; source AST parsing, final source hashes and selected CLI
paths were checked. These are file-size and behavior measurements, not a claim
of fixed model-token saving or general search superiority.

## Fourteen-branch disposition

| Branch | Outcome |
|---|---|
| A1 Interruption / multi-entry | Implemented incremental batch checkpoint and added Feed, discovery and conversion items. |
| A2 Freshness | Implemented explicit Feed check, HTTP validators and immutable successive snapshots. |
| A3 Skill entry size | Removed duplicate route mechanics, retaining mode selection and permission boundaries; measured 10.3% fewer entry bytes. |
| A4 ChatGPT report | Bounded host check: a small public PDF opened in the in-app browser, but `tab.content.export` reported unsupported. No complete ChatGPT research export was claimed or retried. R28 remains partial. |
| B1 Cross-material retrieval | Added a bounded local manifest + `locate` because file-name-only `rg` did not return provenance and passage across mixed artifacts. No FTS/vector index. |
| B2 Quote and provenance | Added exact saved-text quote, line/character offset, source URL where available, hash/version and snapshot time. Same bytes are distinguished from same study or corroboration. |
| B3 Alternative perspectives | Existing Skill already asks for alternatives, mechanisms and deciding exceptions. No STORM deployment or new prompt framework without a demonstrated critical miss. |
| B4 Effect comparison | Used the controlled before/after interruption, real mixed batch, conditional RSS and actual saved-material task above. No source-count proxy or unmeasured token claim. |
| C1 Version-specific docs | Context7's earlier anonymous library-name lookup did not establish version-matched full text; official version docs/Git refs remain the working route. Conditional candidate. |
| C2 Academic handoff | FS03's formal recall and Elicit/Zotero division remain authoritative. Crossref/OpenAlex/Zotero integration awaits a concrete paper-identity or import/export failure. |
| C3 Complex materials | Docling remains conditional on a real MarkItDown ordering/table/scanned-PDF failure; no default OCR runtime. |
| C4 History/change | The Feed route now compares successive bounded entry windows locally. Wayback remains unintegrated after the earlier bounded timeout. |
| C5 In-site evidence | No decision-changing X example requiring a logged-in site search was supplied. Existing public X route and R28 limits remain; OpenCLI is a comparison candidate, not installed. |
| C6 Dependency state | Existing targeted doctor and actual runtime execution cover this round's dependencies. No blanket audit or package upgrades. |

The accepted commands are documented in [r31-routes.md](../../references/r31-routes.md).
They are one-shot, task-local operations. Batch checkpoints require `--out`;
a stop between child completion and its checkpoint write can rerun that item.
Feed 304 means the representation did not change according to the server's
validator; the bounded entry-window comparison says nothing about full feed
history. Text offsets refer to the saved extraction, not live page coordinates
or verified factual claims. Material and page content remain untrusted data.

Primary protocol/method references: [feedparser conditional HTTP](https://feedparser.readthedocs.io/en/stable/http-etag.html),
[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html),
[W3C Web Annotation selectors](https://www.w3.org/TR/annotation-model/).
