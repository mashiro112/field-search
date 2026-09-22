# R29: repository content and RSS/Atom routes

Date: 2026-09-23. Status: delivered; accepted for the real cases and limits below.

## Goal and decision

Add two directly usable reading capabilities to FS by reusing mature upstream
components. Existing GitHub search discovers repository metadata; it does not
provide a local, searchable source snapshot. Existing web search does not provide
an explicit general RSS/Atom feed reader. These are complementary gaps with
public inputs, no account setup and no additional model service.

The round uses FS's own GitHub repository search, followed by upstream source,
package, license and relevant failure checks. It selects two routes, without
turning every search into a research workflow or adding another framework.

| Candidate | Decision and reason |
|---|---|
| [Repomix](https://github.com/yamadashy/repomix), MIT, pinned 1.18.1 | Reuse the CLI's repository packing, plus the official [repomix-explorer Skill](https://github.com/yamadashy/repomix/blob/v1.18.1/skills/repomix-explorer/SKILL.md) approach of packing once and reading selected sections. Do not activate the entire upstream Skill or adopt its instructions as authority. |
| [feedparser](https://feedparser.readthedocs.io/en/latest/introduction/), BSD-2-Clause, pinned 6.0.14 | Reuse the parser for RSS/Atom. The [Agent-Reach RSS channel](https://github.com/Panniantong/Agent-Reach/blob/main/agent_reach/channels/rss.py) shows that a thin adapter is sufficient; do not install its full framework. |
| [GitIngest](https://github.com/coderamp-labs/gitingest), MIT, PyPI 0.3.1 | Credible alternative; this round keeps one repository backend. Repomix has a directly relevant official Skill and fits the existing Node runtime. This is a fit decision, not a comparative performance claim. |
| [OpenCLI](https://github.com/jackwener/OpenCLI) | Local 1.8.7 is already installed, but its ChatGPT/X routes still need browser/session integration. [Issue 2435](https://github.com/jackwener/OpenCLI/issues/2435) reports a relevant Windows/ChatGPT failure in that version. Keep it as a candidate; do not duplicate installation or infer universal failure. |

## Small implementation plan

1. Add `repo fetch/open/find` through a thin Repomix CLI adapter. Default to a
   small documentation/manifest selection; allow explicit include/exclude and ref
   options. Preserve the resulting Markdown, provenance and content hash. Reuse
   FS's existing local report pagination/search.
2. Add `feed` through a thin feedparser adapter. Fetch a public HTTPS feed once
   with byte/time/redirect limits; return bounded titles, dates, links and
   summaries. Keep unknown dates and partial results explicit.
3. Register both commands in the existing FS entry point, document portable
   runtime setup and routing, then run real inputs plus focused counterexamples.
   Publish the accepted source and evidence together.

## Acceptance

- A real public repository can be fetched with an explicit file selection and
  read/searched offline through FS. Preserve source URL, selected ref/options,
  upstream version and body hash; do not infer an immutable commit from a moving
  branch.
- A real RSS and a real Atom feed produce useful bounded entries. HTML or bad
  XML is not silently accepted as a valid feed. Unknown dates do not become
  invented dates or silently satisfy a date filter.
- Identical requests with valid cached artifacts reuse them without fetching;
  changed requests and corrupted artifacts are refused instead of overwritten.
- Missing runtimes, invalid inputs and unavailable upstreams have useful failure
  states. Normal stdout contains summaries, not entire repositories or feeds.
- An independent behavioral review uses the actual FS commands and checks the
  documented limits. Claims apply only to tested cases.

## Cost and scope

Use local upstream libraries, one-shot public retrieval, bounded output and
task-local reuse. No paid API, model call, background watcher, global index,
credential import or new Deep Research task is part of these routes. Defaults
limit model-facing content; repository include filters do not bound Git clone
traffic or peak disk use. No fixed token-saving percentage has been measured.

R28's ChatGPT full report transfer and logged-in X-native search remain separate
unfinished capabilities. Adding these two routes does not resolve those gaps.

## Result

Implementation, real-input checks and independent behavioral review are complete.
The review found a Windows Unicode output defect; the fix passed a fresh RSS
retrieval and offline reuse through the normal FS entry point. Repomix runs
locally with Node 22.18.0; feedparser runs in an isolated
Python 3.12.14 environment. Runtime paths remain local. Reproducible dependencies
are in [the npm package and lock](../runtime/r29-repomix/package.json),
[the exact dependency lock](../runtime/r29-repomix/package-lock.json), and
[the Python pins](../runtime/r29-feed-requirements.txt).

| Check | Observed result |
|---|---|
| Public repository | `octocat/Hello-World`: one included file, 1,706-byte Markdown. Local open/find, same-request reuse, different-request conflict and damaged artifact rejection passed. |
| Independent repository review | `coderamp-labs/gitingest`, with `src/gitingest/__main__.py` added and `docs/**` excluded: 27,778-byte Markdown. The selected source file is present alongside default documentation files. Offline open/find, reuse and request conflict passed. |
| Empty repository selection | Excluding all files reports `no_results`, `files_count: 0`; an empty pack is not presented as useful source content. |
| Real RSS | [Wikipedia recent changes RSS](https://en.wikipedia.org/w/index.php?title=Special:RecentChanges&feed=rss): parser identifies `rss20`, 50 entries available in this response, one returned under the requested limit. |
| Real Atom | [FS commit feed](https://github.com/mashiro112/field-search/commits/main.atom): parser identifies `atom10`, 18 entries in the tested response, one returned. Feed sizes change over time. |
| Parser and date counterexamples | Malformed XML and HTML are rejected; valid embedded XHTML is accepted. Unknown dates are included without a cutoff and excluded/countable with `--since`. Oversize links are omitted with truncation metadata instead of returned as broken URLs. |
| Feed caching | Same-request cached output is reused without fetching; a changed limit conflicts without overwriting. Successful snapshots preserve their original UTC fetch time and result hash. |
| Independent feed review and final retest | Real Atom reading, cache reuse and damaged-hash rejection passed. After the Unicode fix, the main reviewer retrieved Wikipedia RSS through its feedrecentchanges endpoint with ordinary Python, then reused it with an intentionally unavailable parser runtime. Hash/time stayed identical and `network_used=false`; no external UTF-8 flag was needed. |
| Focused local checks | Repository adapter compile and three targeted tests passed. Feed parser fixtures and cache checks passed. Skill frontmatter validation passed. These are route checks, not a whole-project regression claim. |

## Findings fixed and remaining limits

- The initial feed DNS check mistook this host's transparent proxy addresses for
  private destinations. The final route reuses FS's established URL policy,
  requires HTTPS, rejects credentials/literal nonpublic IPs/reserved host names
  and validates each redirect. It leaves hostname resolution to the configured
  transport; it does not promise network isolation against DNS rebinding.
- Searching feed contents for HTML markers incorrectly rejected legitimate
  embedded markup. Document-root checking replaces that heuristic. Entry fields
  expose truncation; overly long URLs are omitted rather than cut into links.
- Isolated Python on Windows ignored the UTF-8 environment flag and failed on
  an actual RSS entry containing Unicode symbols. Explicit interpreter UTF-8
  mode and stream encoding fixed the output path; a Chinese/emoji fixture and
  a new live RSS request passed. The source byte/file cache remains UTF-8.
- Repository failures after starting the upstream process report network use
  as unknown, instead of incorrectly claiming no request was made. Input/cache
  rejection and offline reuse retain the definite no-network state.
- `hnrss.org/frontpage` timed out in this environment and the BBC RSS response
  was rejected by parsing. Neither is relabeled as a successful empty feed.
  Verified RSS/Atom support does not imply every publisher response will parse.
- Feed output follows publisher order and its current window. It does not
  download full articles, establish coverage of a historical period, or monitor
  changes. Unknown-date count refers to the fetched response.
- Repository defaults are `README*`, `SKILL.md`, `package.json`, `pyproject.toml`
  and `LICENSE*`; `--include` adds patterns. Upstream ignore/security exclusions
  remain active. Exact original repository completeness is not asserted.
- Fetch caches do not check upstream freshness. Use a new output path for a new
  retrieval; source refs, timestamps and hashes make the old snapshot explicit.

See [the installed route instructions](../../references/r29-routes.md) and
[integration ownership](../../references/integration-map.md) for actual commands
and the division between reused upstream components and FS adaptation.
