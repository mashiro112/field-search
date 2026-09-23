# R32 phase 1: reproduction checkpoint (in progress)

Date: 2026-09-23. This is an **in-progress experiment checkpoint**, not final
acceptance or a claim that nine integrations are complete. Start from the
[R32 goal](R32-GOAL-PROMPT.md) and [candidate research](R32-EXPANSION-RESEARCH.md).
No FS source changed at this checkpoint; the 184-file source manifest still
describes R31. Local inputs, isolated runtimes and raw outputs remain outside
the public repository.

| Branch | Actual reproduction so far | Decision at this checkpoint |
|---|---|---|
| A QMD 2.8.3 | Installed in an isolated Windows directory (about 850 MiB unpacked). Indexed nine public FS Markdown documents in an isolated index. BM25 returned an exact English hit in about 0.3 s/query but no hit for two Chinese paraphrases. Its default 333 MB embedding model downloaded; after about 3.7 minutes of CPU work the nine documents still had zero vectors, so the run was stopped as a resource bound. | Keyword mode adds little to existing `rg`/`locate`; semantic quality is **unmeasured**, not a negative result. Investigate a smaller multilingual route only if a real task still has a paraphrase miss. No default QMD dependency. |
| B Crawl4AI 0.9.3 | Existing isolated runtime has BFS/BestFirst. A four-page, depth-one best-first run on Python's official asyncio docs took 5.61 s and found `create_subprocess_exec` on the subprocess subpage, absent from the start page. FS `discover` made four attempts and returned no candidates; FS `read` retained the target link but did not follow it. Crawl also spent a slot on an irrelevant `improve-page` URL and left other links unvisited. An earlier run during QMD memory pressure failed with an explicit resource error; the serial rerun succeeded. | Real automatic-follow gain, but extra requests and URL-filter leakage. Tighten path/budget and test an independent site before deciding on an opt-in route. No superiority claim from unequal request budgets. |
| C Context7 | Next.js `/vercel/next.js` gave version-specific v13.5.11 and v15.1.8 snippets with tagged GitHub `codeId` links; a nonexistent v14.2.0 returned `404 version_not_found`. In a separate React test, a v18.2.0 request returned React 19 `ref` advice with a `main` source URL, essentially the same top hit as v19.2.7. Official React guidance says ref-as-prop starts in React 19. | **Version pin alone is unsafe.** Treat Context7 as candidate discovery only where every decisive snippet links to the requested version; otherwise use official version docs or a fixed Git ref. No claim of reliable anonymous service; the API guide documents low unauthenticated limits. |
| D Docling 2.130.0 | On pages 6–8 of the public *Attention Is All You Need* PDF, MarkItDown 0.1.8 flattened Table 1 while Docling recovered two tables with page numbers. Docling took 86.5 s after model setup, versus 4.8 s for MarkItDown's whole PDF. Docling duplicated a Table 2 training-cost value into a visually blank adjacent cell and left a formula undecoded. On a public-domain historical vertical Chinese scan, MarkItDown reported no extractable text and Docling with RapidOCR returned only an image marker despite SUCCESS. On a modern public-domain Chinese scanned page with an existing text layer, Docling improved reading order over MarkItDown, but this does not prove OCR-only accuracy. | Useful optional layout aid, **not automatically trustworthy for decisive table numbers or difficult OCR**. Need a narrow FS handoff that retains original page association and explicitly requires visual check; test an independent structured document. No default replacement of MarkItDown. |
| E ast-grep 0.45.3 | Isolated CLI matched real multi-line Python call shapes in the fixed FS repository and returned file/line/AST metadata. | Continue one counterexample comparison with `rg`; avoid a wrapper if the native CLI suffices. |
| G OpenCLI 1.8.7 | Found an already installed CLI and connected browser bridge. A read-only X site search returned five public posts in about 19 s. A selected thread returned its original plus two replies in about 7.4 s; FS's current public oEmbed returned only the original. The chosen thread had no observed correction, and the CLI array did not state total reply count or truncation. | The non-API site-search path is **actually reachable in this host**, with a material context gain. Verify an independent thread and completeness/authorization boundaries before an FS route. No account/session data is published. |
| H SearXNG | Docker and Podman are absent and WSL reports no installed distribution. | No light isolated deployment here; retain a conditional activation test rather than altering the OS to install a redundant default search service. |

F (short-audio ASR) and I (one-off page-change explanation) have not yet been
tested. The first adopted route, if any, must pass a separate holdout and a
Critic check. A successful conversion/search command is not factual acceptance.

Public primary references: [QMD](https://github.com/tobi/qmd),
[Crawl4AI deep crawling](https://docs.crawl4ai.com/core/deep-crawling/),
[Context7 API guide](https://context7.com/docs/api-guide),
[Next.js v15 source](https://github.com/vercel/next.js/blob/v15.1.8/docs/01-app/02-building-your-application/11-upgrading/03-version-15.mdx),
[React 19 ref change](https://react.dev/blog/2024/12/05/react-19),
[Docling installation](https://docling-project.github.io/docling/getting_started/installation/),
[Attention Is All You Need](https://arxiv.org/abs/1706.03762),
[public-domain Chinese scan](https://commons.wikimedia.org/wiki/File:SSID-11242066_中國報紙社論文字_第1輯_國風報敘例.pdf),
[modern public-domain Chinese source](https://commons.wikimedia.org/wiki/File:陕西省测绘条例.pdf),
[ast-grep CLI](https://ast-grep.github.io/reference/cli), and
[OpenCLI](https://github.com/jackwener/opencli).
