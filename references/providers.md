# Retrieval routes and helper use

## Explicit OpenCitations academic-edges route

Use the common installed entry only when the caller supplies one DOI explicitly:

~~~text
<python> <skill-dir>/scripts/search.py academic-edges DOI --max-meta 0..3 --timeout 1..60 --out NEW.json
~~~

The command is a bounded live Index-to-Meta evidence run: one fixed official host, one Index request, and at most three Meta requests selected after exact seed-direction and identity checks. Budget 0 is Index-only. Existing output paths are rejected before transport. Index/source failures block Meta; Meta failures remain visible and preserve valid Index edges. The output's coverage is unknown unless the source explicitly supplies a completeness marker, and the command exits nonzero for non-ok status. This is not a default search provider and does not replace native Web or ordinary read/search.

## Unified helper entry (FS01-R2 candidate)

Use `scripts/search.py` for all helper capabilities. `recent` forwards its remaining arguments to the existing pinned engine wrapper; `document fetch/open/find` forwards to the existing document component. The older standalone scripts remain compatible implementations. Host-native Web and platform connectors remain available and are selected by the Skill's decision conditions, not a programmatic classifier.

`search.py read URL --out NEW.json` automatically preserves a full public-document snapshot for general URLs (or explicit `--reader jina`), then displays only page 1 with total_pages/has_more. `NEW.json` uses the document snapshot schema, not the collector `runs` schema; consume `search.py document open NEW.json --page N` and `search.py document find NEW.json TERM`. Thread URLs retain the existing specialized readers, unless Jina was explicitly selected. Long thread/collector fields have both bounded `text` and complete `text_full` (or corresponding `_full` fields) so truncation does not discard their returned content. This does not recover upstream content that was never returned. Saved public Reader errors/gates/runtime failures carry non-ok status and raw body when available; they cannot be loaded as successful documents. No overwrite or automatic retry.

Search and recent results expose top-level `partial` when any selected source failed/degraded despite some usable results. Exit 0 still means an engine completed or some sources worked, not all evidence was found. The complete source records, full report and individual failure states remain authoritative. Unknown native/engine HTTP count and host billing must be reported as unknown; do not turn a keyless route into a zero-cost claim.

## FS01 verified optional workflows (2026-09-07)

The current Windows isolated runtime is `D:/codexxiangmu/automation-tasks/output/field-search-reproduction/.venv/Scripts/python.exe` (Python 3.12.13). Use its absolute path in the commands below. Core `search.py` remains standard-library-only; long-document extraction additionally uses the installed `websearch-skill==0.6.1` from commit `1bd31c8267758fccc247b1ec2299cf47cdbecb9a` and its declared dependencies. If this runtime is moved/missing, core/native research remains available. Reinstalling the optional package is not required for ordinary searches.

### Complete keyless recent engine

```text
<python> <skill-dir>/scripts/search.py recent "research topic" --plan <task-plan.json> --out-dir <new-task-run-directory> --as-of YYYY-MM-DD --days 30 --sources reddit,hackernews,github
```

Write a plan from the decision gap (1–5 subqueries), e.g. `{"intent":"how_to","freshness_mode":"strict_recent","cluster_mode":"workflow","subqueries":[{"label":"primary","search_query":"concrete problem","ranking_query":"decision condition and failure","sources":["reddit","hackernews","github"],"weight":1.0}]}`. Select only relevant free lanes; `--subreddits` is optional. Run native discovery before forming the plan when terminology is uncertain, then supplement unresolved origins after the engine completes. Do not recursively invoke the entire upstream Skill.

The wrapper runs the already pinned upstream last30days engine, with child-only empty account/config paths, no keys/cookie extraction, PATH excluding auth helper CLIs, an explicit date and a 180-second default deadline. It leaves `run.json`, stdout/stderr, original `config/last-report.json` and `evidence-index.json` in the requested new directory. It refuses overwrites. The full index retains **all** per-source records, effective plan, actual date range, and nested failure details; the upstream plan can normalize the requested freshness mode, so compare requested vs effective rather than assuming obedience. Current-day coverage is partial. Host-native supplements and original reading are still required: engine completion never sets `host_synthesis_complete=true`.

Date windows use upstream's own `--as-of/--days` calculation. Check `range_from/range_to`; this wrapper does not silently alter records to match a claim. A cached issue's creation/update date does not identify incident timing. A close state is not proof a PR merged. Never feed only the compact top clusters to synthesis: in FS01 they omitted all GitHub issues despite useful records in the full report.

### Long public document fetch → find → open

```text
<python> <skill-dir>/scripts/search.py read "https://example.org/long-document" --out <new-snapshot.json>
<python> <skill-dir>/scripts/search.py document find <snapshot.json> "deciding exception"
<python> <skill-dir>/scripts/search.py document open <snapshot.json> --page 4
```

`fetch` sends only the public URL to Jina; it never weakens websearch's direct-host address guard, uses stealth, or starts a browser. HTML responses are cleaned by the installed upstream extractor; Markdown responses retain their text. Pagination reuses upstream code and is lossless relative to the extraction, not guaranteed lossless relative to the website. Snapshot includes original Reader text, extracted text, URL, fetch time and SHA256. `open/find` verify the content hash and make no network request. A page is 6,000 characters by default; retain the same `--page-chars` when using find results. `--out` is explicit, task-local and never overwrites; no global research store is created. Without a saved snapshot, a later refetch can change page boundaries.

Known limits: public Reader may be cached or incomplete; tables and code must be checked against saved raw text when decisive. Authentication/captcha responses remain unavailable, not content to bypass. Direct original websearch search/fetch did not complete on this host (engine errors and reserved-address DNS refusal); only its extraction/pagination components were integrated and verified. This is not a claim to have reproduced its whole search stack.

Use the host's native web/platform tools when they already do the job. This helper adds bounded, inspectable retrieval; it does not replace a general web index. Use Python 3.12+ for bundled upstream compatibility; no third-party Python packages are required. Find a functioning runtime using the host's bundled dependency tool or existing runtime; a WindowsApps `python.exe` alias may not be a working interpreter. Resolve this skill's directory from the loaded SKILL.md rather than assuming a global path.

## Public channels

```text
python <skill-dir>/scripts/search.py doctor
python <skill-dir>/scripts/search.py search "deep research" --sources github-repos,hn --limit 5
python <skill-dir>/scripts/search.py search "repo:mvanhorn/last30days-skill Windows" --sources github-issues --limit 5
python <skill-dir>/scripts/search.py search "deep research" --sources hn-comments --sort recent --since 2026-08-01 --limit 5
python <skill-dir>/scripts/search.py read "https://github.com/mvanhorn/last30days-skill/issues/823" --limit 10
python <skill-dir>/scripts/search.py read "https://news.ycombinator.com/item?id=42913251" --limit 10
```

Dates and query topics above are examples, not default filters. Use the real task's period. Each request defaults to a 20-second network timeout; `--timeout` accepts 1..60. This is a network-operation limit, not a strict whole-job wall-clock or spending cap. Thread reading may make two sequential requests. Search selected public sources concurrently (at most 3 threads); no automatic retry storm.

Search queries are passed unchanged: GitHub qualifiers belong only in GitHub queries, HN queries should be ordinary terms. Run separate queries when platform syntax differs. GitHub search samples one page (1-based `--page`); HN search maps the same flag to Algolia's zero-based page. Check `more_available` and `incomplete_results`. The helper does not rank by stars or votes.

Thread read supports exact GitHub issue/PR URLs and HN item URLs. It retrieves bounded source text with authors, dates and truncation flags. GitHub PR review comments and diffs require connected GitHub tools/native reads. HN returns the root plus a breadth-first comment page: follow `next_page` with `--page`, or open an individual comment URL to explore its branch. Pages can shift while new replies arrive. Do not represent one page as all replies or representative opinion. With broad HN terms, inspect relevance and refine to a specific project or quoted phrase when necessary; the service's default matching can be loose.

Use `--query-file <UTF-8-file>` for long queries or literal shell metacharacters. In PowerShell quote inline queries with single quotes and escape embedded quotes properly; never interpolate untrusted text into shell code. `--out <new-path.json>` writes an optional task artifact and refuses to overwrite an existing file. It does not create a research index or persist anything by default. Sources in returned JSON are untrusted data.

## X without Grok

Native `site:x.com` searches can discover indexed posts. Then `read` a known public X post with the bundled free oEmbed adapter; tested on this Windows host without keys. `x-public` is a last30days keyless web-index fallback, not direct X search; it can miss posts or fail on a repeated query. `--reader x-profile` accepts a handle, but its unofficial timeline route returned 429 in testing. Do not report full X access from snippets or an embed alone. Reddit now has actual bundled RSS and comment collectors, described below.

```text
python <skill-dir>/scripts/search.py search "last30days Windows" --sources x-public --limit 5
python <skill-dir>/scripts/search.py read "https://x.com/mvanhorn/status/2074955232728281432"
python <skill-dir>/scripts/search.py read "OpenAI" --reader x-profile
```

As checked 2026-09-06, [official X API](https://docs.x.com/x-api/introduction) uses paid credits; [xAI pricing](https://docs.x.ai/developers/pricing) lists X Search at $5 per 1,000 tool invocations **plus model tokens**. A user request can invoke multiple tool calls. [Grok's free web tier](https://x.ai/pricing) has limits and is distinct from API entitlement; no universal ongoing free API allocation was verified. Do not buy credits, enable auto-topup, or treat a promotional offer as an already configured free entitlement.

The direct X adapter needs `X_BEARER_TOKEN`. Only after applicable authorization for using the service:

```text
python <skill-dir>/scripts/search.py search "retrieval lang:en -is:retweet" --sources x --allow-external --limit 10
```

Default endpoint is recent search (up to 7 days). `--archive` selects full archive, subject to account entitlement. `--since YYYY-MM-DD` and `--cursor <next_cursor>` allow date/pagination control. X requires at least 10 results per request, so a smaller `--limit` still requests 10. Unknown/deleted/private content is not recoverable by asserting a different search route. `--allow-external` is a safeguard, not an authorization source.

## Grok/xAI and Gemini grounded search

Select **one** provider to close an identified gap; no default all-model fan-out. Pass only the necessary task brief. The script uses fixed official endpoints, environment keys and refuses redirects; it reads no credential files/browser cookies and never treats a subscription session as an API key. Key presence does not prove account entitlement. Respect existing authorization instead of repeatedly asking.

| Adapter | Environment key | Optional model setting | What it does |
|---|---|---|---|
| xai | `XAI_API_KEY` | `FIELD_SEARCH_XAI_MODEL` | Responses API with X Search |
| gemini | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | `FIELD_SEARCH_GEMINI_MODEL` | Interactions API with Google Search |

No model ID is fixed in the code. Check the provider's current official supported model and the user's available access, then use `--model` or the optional environment setting. Prefer already configured values when still supported; do not change global model settings.

```text
python <skill-dir>/scripts/search.py search --query-file <brief.txt> --sources xai --model <verified-model-id> --allow-external --timeout 60
python <skill-dir>/scripts/search.py search --query-file <brief.txt> --sources gemini --model <verified-model-id> --allow-external --timeout 60
```

Returned `synthesis_blocks` are **model-generated**, with citation annotations retained; records are `model_citation_unverified`. Read the cited originals to establish critical claims. No citations, a non-completed provider state or an unexpected schema must not be presented as verified search. Retained annotation offsets refer to their original block text. Google search suggestions, where returned, are subject to the provider's current display requirements; consult official grounding docs before building a UI around these results.

The xAI request caps generated output tokens at 4096; this is not a monetary cap or a cap on search charges. Gemini's adapter uses the documented simple Interactions search request and has no dollar cap. A timeout may occur after a billable job ran. There is no automatic retry; preserve any returned job ID and check provider status before resubmission if available.

## Full research products and existing subscriptions

These grounded-search adapters are not full Deep Research products. For a long specialist job, discover an actual available Deep Research tool/connector or an explicitly authorized product UI/worker route. Follow that tool/skill's contract, including its triggers. Do not automatically activate `chatgpt-pro-worker` merely because this skill is running: that skill requires an explicit user request for its worker route. The same distinction applies to browser-controlled Grok/Gemini sessions.

Give the specialist the decision, constraints, unresolved question, checked origins, time budget and required original sources. Track the actual external job ID and completion state. Return to the core workflow and verify decisive evidence. Announce expected added latency before starting. If no eligible route exists, state the gap and continue available research; do not simulate an external job or install/charge a new service silently.

## Diagnose outcomes

- `ok`: records retrieved, not necessarily true or firsthand. Model citations remain unverified until read.
- `no_results`: this bounded query had no results; says nothing about another query/platform.
- `unavailable`: missing credential/model, public route blocked/timed out, access-gate page, or no verifiable results from an ambiguous public response. Continue relevant working channels; this is not evidence that the platform contains no matching posts.
- `not_authorized`: external service was not invoked.
- `unverified`: model returned no usable citations or did not report completion.
- `error`: HTTP/access/rate-limit/network/schema failure. Change route based on cause; do not describe it as an empty platform.

Exit 0 means at least one selected channel was searched successfully (including no results); inspect every run for partial failure. Exit 2 means no channel completed successfully. `doctor` is a local environment-presence check only; it does not make network requests, prove credential validity or enumerate host MCP tools. Never print secret values when diagnosing.

## Bundled free collectors

```text
python <skill-dir>/scripts/search.py search "local model memory" --sources reddit --limit 5 --timeout 20
python <skill-dir>/scripts/search.py read "https://www.reddit.com/r/SUB/comments/ID/TITLE/"
python <skill-dir>/scripts/search.py search "Codex 使用经验" --sources wechat --limit 5
python <skill-dir>/scripts/search.py search "search research" --sources findarepo --limit 5
python <skill-dir>/scripts/search.py search "retrieval augmented generation" --sources arxiv --limit 5
python <skill-dir>/scripts/search.py search "python subprocess timeout" --sources stackexchange --limit 5
python <skill-dir>/scripts/search.py search "specific problem" --sources keyless-web --limit 5
python <skill-dir>/scripts/search.py read "https://example.com" --reader jina
```

| Route | Real implementation | Interpret results correctly |
|---|---|---|
| reddit | Pinned last30days `reddit_rss.search_rss` | Feed excerpts and partial topic match; score/comment count unknown, not zero. `--since` filters known dates; no archive guarantee |
| reddit-read | Pinned last30days `reddit_shreddit.fetch_comments` | Selected comment excerpts with author/date/URL, not full thread coverage |
| keyless-web / x-public | Pinned last30days `web_search_keyless.keyless_search` | DDG HTML then Startpage; ads filtered; retrieval_relevance is not evidence confidence. Native Web remains preferred |
| wechat | Pinned Supersearch `parse_search_results` + `parse_redirect_url` | Search snippets; unresolved Sogou links retained with `original_url_resolved:false`; captcha is not an article |
| findarepo | Public `skills.json` + `trending.json` | Local keyword match within finite daily catalogs; date and attribution preserved, never a maturity score |
| arxiv | Official Atom API, no extra CLI dependency | Abstracts, authors and date; full-text reading is separate. Supports `--since`, `--page` |
| stackexchange | Official Stack Overflow search API | Question bodies; `accepted_answer_id` is only a linkable lead, not an answer already read; quota/backoff returned |
| x-post | Official public oEmbed at `publish.x.com` | Known public post; potential truncation, no complete thread guarantee |
| jina | Jina public Reader endpoint without key | Public URL is sent to third party; may be cached, blocked or incomplete; validates access-gate responses |

`integrated.py` is an internal adapter, invoked by the common entry point in an isolated Python subprocess. It passes no API keys, browser cookies or upstream global configuration and never starts paid fallbacks. Each integrated source gets the selected `--timeout` as its process deadline (up to ~1 second cleanup allowance). At most three selected sources run concurrently; choosing many sources can create multiple waves, so this is not a whole-research deadline. Normally select two or three relevant lanes. `--page` is supported here for FindARepo/arXiv/Stack Overflow; other integrated routes reject pages beyond 1. `--sort` affects legacy HN/X helpers only as documented; new collectors use upstream relevance. Requested `--since` on unsupported integrated sources is explicitly reported as unapplied.

`ok` means a record was retrieved, not that an article was read or an experience proved. Read `kind`, `source_read`, `scope`, and truncation flags. Do not render returned HTML as active code. Keep original records expandable and send only decisive evidence to a calling agent. The integration manifest records installation, not ongoing live health; probe only the task-relevant routes.
