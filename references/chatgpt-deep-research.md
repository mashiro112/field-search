# ChatGPT web Deep Research

Status (R28, 2026-09-18): actual web product selection, prompt submission,
plan inspection and Start are verified on this Windows host. Report completion
and retrieval are still under validation. Do not call this an accepted end-to-end
route until an actual report has been retrieved.

## Use and cost

Use when the user names ChatGPT web Deep Research, or a remaining broad evidence
gap warrants the wait. State the expected added time before submission. Reuse the
authorized browser subscription; do not substitute a paid API, ordinary web
search or a Pro/extra-high reasoning chat. Do not run multiple research products
by default. A short prompt does not guarantee a short job or no quota use.

## Workflow

1. Write a bounded brief from the user's decision, constraints and evidence gap.
   Supply only relevant context and source URLs. Use public web sources unless
   private connected material is explicitly in scope.
2. Use the available native browser. In the observed Chinese UI, the composer
   menu **添加文件等 → 更多 → 深度研究** opens the product. Rediscover controls
   from the current page; do not hardcode accessibility indices. Login,
   verification and actual quota/payment gates may require a user handoff.
3. Submit once. Wait for the saved canonical conversation URL: the temporary
   `/c/WEB:...` identifier is not a valid native `read_thread` conversation.
   Save the canonical URL and observed status to a task-local status file,
   excluding credentials, account data and report body from public records.
4. Inspect the research plan. When it fits the authorized scope, click **开始**
   yourself if offered; do not ask the user to do that step. Verify the research
   component actually entered its running state. Timeout/unknown never means
   permission to submit a duplicate.
5. The ordinary chat and embedded research job have different lifecycles.
   In R28, native `read_thread` returned `idle/completed` plus an acknowledgement
   while the research component still showed its plan/Start control. That is
   NOT report completion. Read the research component's actual visible status
   at low frequency. Avoid repeated full DOM/report output; use compact status
   observations and deterministic waits. Generic chat Stop/thinking indicators
   do not establish research progress. Keep and resume the same conversation.
6. Require an actual completed report, then prefer one official Markdown export
   or Copy contents. Compare body ending, headings/tables and usable source URLs.
   Opaque citation tokens alone are not preserved citations. Native thread reads
   are useful only if they expose the actual report, not just an acknowledgement.
   Do not invent private backend endpoints or extract browser credentials.
7. Save the retrieved text once, then reuse `search.py report import <local.md>
   --out-dir <task-report-dir> --method copy|local_file --source-url <canonical-url>`.
   Use `report open/find` for bounded reads. Keep any source list separately if
   needed and identify missing links honestly. Return the answer to the research
   question, decisive sources, report path and remaining uncertainty. Report
   transfer is not factual validation.

## Reuse assessment

- [andylizf/deep-research-skill](https://github.com/andylizf/deep-research-skill)
  documents the real UI plan/start/export workflow. Its current setup requires
  macOS/web-plane, and its README notes opaque citations in extracted Markdown.
  Reuse the workflow insight, not its platform-specific setup or missing-link
  behavior. No upstream code is vendored here.
- [OpenCLI ChatGPT adapter](https://github.com/jackwener/OpenCLI/blob/main/docs/adapters/browser/chatgpt.md)
  has a `deep-research-result` command; its implementation reads internal
  conversation payloads through an extension/browser bridge. Code inspection is
  not a local acceptance test or proof of the complete submit/start flow. It is
  a candidate if the existing browser path proves insufficient, not a required
  new dependency.
- [Microck/chatgpt-webui-mcp](https://github.com/Microck/chatgpt-webui-mcp)
  is archived and requires a session token plus a separate browser service.
  It is not selected for the current minimal-maintenance route.

The installed `chatgpt-pro-worker` is useful for ordinary web reasoning jobs.
Its native-chat completion rule must not be applied to the independently running
Deep Research component. This route adds neither a daemon nor a background
schedule and does not automatically archive research reports.
