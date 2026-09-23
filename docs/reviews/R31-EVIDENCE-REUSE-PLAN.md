# R31: durable reuse, feed freshness and evidence retrieval

Date: 2026-09-23. Status: implementation planned; no R31 acceptance claim yet.

The owner asked Codex to execute the 14-branch Goal described in the linked
ChatGPT conversation. The conversation text is available; its separate sandbox
download is not attached to this task. This plan uses the stated branches and
acceptance intent, and will record actual tests before claiming delivery.

## Decision

Reduce repeated work on a real FS task: a stopped batch should keep completed
items; a feed reader should distinguish an offline snapshot from a check for
updates; prior materials should be retrievable with source and location. Keep
the source's date, the retrieval/check time and the saved snapshot distinct.

| Branch | Provisional disposition and deciding test |
|---|---|
| A1 Batch interruption and multiple entries | Reproduce lost progress; fix with an incremental, recoverable task-local manifest. Add existing entries only where item identity and artifact reuse are sound. |
| A2 Feed freshness | Add an explicit check against a previous valid snapshot. Use ETag/Last-Modified when supplied; treat 304 as unchanged and preserve the previous immutable file. |
| A3 Skill entry length | Measure loaded entry and remove duplicate route details only if references retain route/permission boundaries. |
| A4 ChatGPT complete report | One bounded host-capability check. Existing R28 report retrieval remains partial unless a real full export path appears; do not regenerate a research job. |
| B1 Cross-material retrieval | Trial installed `rg` and current report/document find against actual saved artifacts. Add a thin task-local route only for a demonstrated usability gap; no vector database. |
| B2 Original location and provenance | Reuse saved report/document metadata and exact text offsets or page references. Distinguish byte-identical artifacts from the larger question of whether reports describe the same study. |
| B3 Distinct search perspectives | Retain as a small planning method: alternative mechanism, context and failure condition each need a decision-changing question. No STORM deployment without evidence of a missed source. |
| B4 Effect comparison | Record pre/post task behavior: completed work retained, network requests or mock requests, original location, time and manual recovery. Avoid source-count or fixed token-savings claims. |
| C1 Version-specific docs | Context7 library search worked previously; full version-matched document retrieval remains unproven. Official version docs and Git refs stay the baseline. |
| C2 Academic handoff | Preserve FS03's PsycINFO/Scopus/WoS formal recall and the existing Elicit/Zotero roles. Crossref/OpenAlex/Zotero are conditional identity and handoff tools. |
| C3 Complex documents | Defer Docling until an actual MarkItDown order/table/scanned-material failure changes a decision. |
| C4 Historical change | Use two immutable snapshots and a bounded local change summary first. Wayback CDX remains conditional after a previous timeout. |
| C5 In-site evidence | Existing public X and browser routes have known limits. Test a specific missed, decision-relevant source before installing OpenCLI or claiming logged-in X search. |
| C6 Dependency checks | Keep targeted doctor/official metadata checks for components actually used. No blanket upgrade or audit service. |

## Planned acceptance

1. Show a controlled interruption after one successful batch item. Resume from
   the saved checkpoint without re-running it; preserve the original input and
   distinguish partial/error items. Confirm write failure before execution.
2. For a feed: demonstrate initial 200, conditional 304, changed 200, and an
   error. Preserve prior snapshots; record the update-check time, source date,
   validators and bounded changes. Use a real public feed where supported.
3. In an actual task-local saved-material set, retrieve a prior source and
   exact passage offline. Compare with current `rg`/find before adding code.
4. Independently inspect important boundaries, document the disposition of all
   14 branches, then update source manifests and publication context.

Primary references: [feedparser conditional HTTP](https://feedparser.readthedocs.io/en/stable/http-etag.html),
[RFC 9110 conditional requests and 304](https://www.rfc-editor.org/rfc/rfc9110.html),
[W3C Web Annotation selectors](https://www.w3.org/TR/annotation-model/).
These are design references, not evidence that the new routes passed locally.
