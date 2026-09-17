# R27 Gemini Deep Research route

Status: one real R27 end-to-end sample is verified through the native browser:
Deep Research plan, start, completion, official Google Docs export, Drive
metadata/export, controlled Markdown download, and R26 local import/open/find.
This validates the workflow path for one sample, not factual or citation
completeness, Copy Contents, or all future account/UI states.

## When to use it

If the user explicitly names Gemini Deep Research or Google Deep Research, go directly to
this route. Otherwise let field-search choose it only when the research span
and unresolved evidence gap justify the added wait, and state the expected
time. Ordinary web search, a search-enabled chat, or an API result is not
completed Deep Research.

## Shortest executable workflow

1. Take the user's research purpose and write a minimal brief: decision,
   constraints, evidence already checked, missing evidence, deadline, and
   required original URLs or counterexamples.
2. In the existing native logged-in browser, select the actual **Deep
   Research** product, not ordinary search or a normal conversation. Submit the
   brief and inspect the generated plan for scope. When the user has already
   authorized the research, start it yourself; do not ask the user to click
   **Start** again.
3. Immediately save the observed session URL and status in the current task
   directory, for example `gemini-deep-research-session.json`:

   ```json
   {
     "schema": "field-search-r27-gemini-dr-session-v1",
     "research_product": "Gemini Deep Research",
     "status": "submitted",
     "session_url": "<observed browser URL>",
     "saved_at": "<timestamp>",
     "last_checked_at": "<timestamp>"
   }
   ```

   Store no cookies, tokens, account details, or research body in this status
   file or in public evidence.
4. While it runs, check the same browser session infrequently using a
   deterministic wait. Do not continuously reason, reread the full report, or
   create a second submission. A timeout or unknown state requires inspecting
   the existing session; it never authorizes resubmission.
5. When the UI shows completion, use one official **Copy Contents** or
   **Docs → Markdown** export. On this host the verified default is the
   Docs+Drive path: create the official Google Doc, confirm native-Doc metadata,
   call `export_file` with `text/markdown`, then materialize the returned
   authenticated `file_uri` through the controlled download path. Do not try
   both forms for every report; if Copy becomes available, use one fidelity
   check to decide whether it is suitable. Existing Docs are only a
   post-research shortcut; they do not move planning, start, or waiting onto
   the user.
6. Save the returned Markdown bytes to the explicit task directory and hand
   them to `scripts/search.py report import ... --method copy|docs_export`.
   Read the result first with R26 `report open`; use `report find` or later
   pages only when needed. The user-facing delivery must include the
   substantive answer to the original research question, the key sources and
   conditions supporting it, and the local report path—not only paths or
   metadata. State the evidence boundaries instead of claiming factual or
   citation verification.

## Human handoff and limits

Pause only at an actual login, 2FA, CAPTCHA, quota, unexpected payment/upgrade,
or another account decision requiring the user. Do not call another search/API
route “completed Google Deep Research”, do not use an unsupported browser
`content.export` capability, do not publish a private report, and do not add a
scraper, database, daemon, or multi-agent orchestration layer for this route.
This is a Codex native-browser operation flow, not an independent headless CLI
or background service.
