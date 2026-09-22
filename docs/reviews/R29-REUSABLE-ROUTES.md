# R29: repository content and RSS/Atom routes

Date: 2026-09-23. Status: implementation and acceptance in progress.

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

Pending. Dependencies have been installed in isolated local runtimes; successful
installation alone is not acceptance. Test results and any final limitations will
replace this paragraph after actual execution and review.
