# R28 ChatGPT web research and non-paid X search

Date: 2026-09-18. Status: partial integration; browser start/completion/reading
verified, automatic local report transfer not accepted.

## Decision and reusable candidates

The owner wants FS to initiate real ChatGPT web Deep Research and retrieve its
answer using the existing subscription. Ordinary Pro reasoning and API research
are different capabilities. Start by reusing the existing native browser and
R26 local report cache; no new service is installed for this trial.

| Candidate | Evidence and decision |
|---|---|
| [andylizf/deep-research-skill](https://github.com/andylizf/deep-research-skill) | Real web Deep Research Skill; README requires macOS/web-plane and notes opaque report citations. Reuse plan/start/export workflow knowledge; not directly installable as documented on this Windows host. |
| [OpenCLI ChatGPT](https://github.com/jackwener/OpenCLI/blob/main/docs/adapters/browser/chatgpt.md) | Source exposes `ask --deep-research` and `deep-research-result`, including report, sources and progress. Uses internal conversation payloads and a browser bridge. Useful candidate, not locally tested or proof of full submit/start automation. |
| [Microck/chatgpt-webui-mcp](https://github.com/Microck/chatgpt-webui-mcp) | Repository archived June 1, 2026; separate browser service and session-token setup. Not selected for the minimal-maintenance route. |
| [OpenCLI X search](https://github.com/jackwener/OpenCLI/blob/main/clis/twitter/search.js) | Actual search implementation supports Top/Latest and author/media filters. It reads a session CSRF cookie and calls internal SearchTimeline GraphQL inside the browser. No paid developer API, but not pure DOM interaction or no-cookie access. Uninstalled/unverified locally. |
| [bird](https://github.com/jawond/bird) | Cookie-authenticated internal GraphQL search, replies and threads. README documents macOS credential sourcing and rate-limit risk. It is a candidate, not the current installed FS direct-search backend. |

Source inspection establishes mechanisms only. No claims of comparative speed,
universal reliability or current account entitlements are made.

## Current X capability: actual narrow rerun

The installed `search.py search "last30days Windows" --sources x-public --limit 3`
returned two web-index records (a profile and a post) through the keyless DDG
backend. The installed `read` of the returned public post succeeded through
oEmbed; its long text was visibly truncated. No paid X/xAI API was invoked.

Thus FS already has keyless discovery plus limited known-post reading. This is
not logged-in X-native search, complete long-post/thread extraction, a full
timeline, or guaranteed recent coverage. The existing x-profile 429 is historical
evidence, not a fresh test in this round. If the owner means strictly UI-only by
“non-API”, both OpenCLI GraphQL and bird must be distinguished from that request.

## ChatGPT trial evidence

- Logged-in native browser: composer menu → More → Deep Research, then one
  bounded public-source brief comparing the candidates above.
- The temporary `WEB:...` conversation ID was rejected by native `read_thread`;
  use the canonical saved ID after navigation settles.
- Native `read_thread` then returned a completed ordinary turn with an
  acknowledgement, while the embedded research component still offered Start.
  Native conversation idle is not Deep Research completion.
- The plan matched scope. The agent clicked Start and verified the component's
  running state. Subsequent compact observation showed research activity.
- A task-local job record preserves the canonical conversation for resumption.
  It and private report content are excluded from publication. There has been
  one submission, no duplicate and no paid API substitution.

## Completion and transfer findings

The same research task completed; the UI reported 12 minutes and 15 sources.
Its rendered report had 18 headings and four tables. The agent read the decision
summary, comparison, maintenance and proposed-path sections, and inspected the
final limitations/source table. This is actual report reading, not treating the
initial acknowledgement as the research answer.

Official Markdown export returned no retrievable local file in the expected
download location. A bounded second attempt waiting for the download event timed
out. Official Copy Contents returned an empty browser clipboard. The current
native browser can read the rendered nested iframe, but this trial did not
materialize a complete report file. Its DOM contained numbered citation controls
and textual URLs in a source table, with no ordinary anchor links. Paragraph-level
citation-to-URL fidelity and R26 file caching are therefore NOT accepted.

The reference provides bounded DOM reading as an explicitly limited fallback,
preserves the original conversation, and avoids repeated exports or rerunning
research. It does not claim a full report cache, token-savings percentage or a
standalone automation service. No independent reviewer accepted this trial.

The generated report's no-install recommendation reflects the trial brief, not
a permanent owner constraint. Dependencies remain candidates where worthwhile.
Its useful additional lead was checked against primary sources:
[OpenCLI ask.js](https://github.com/jackwener/OpenCLI/blob/main/clis/chatgpt/ask.js)
really has separate Deep Research/Web Search flags, while
[issue 2435](https://github.com/jackwener/OpenCLI/issues/2435) reports a Windows 11
frontend change breaking v1.8.7 history/ask. That issue is not proof that all
current versions fail. The full generated report and session identifiers remain
private; only these shareable findings are published.

Next acceptance target: a supported way to transfer the existing completed report
with body and usable source mappings. Do not spend another research task merely
to retest export. X-native search candidates remain uninstalled.
