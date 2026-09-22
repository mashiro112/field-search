# R29 repository contents and RSS/Atom

Two explicit, one-shot readers complement search. Select them for a concrete
source gap, not as mandatory stages. Their implementations reuse mature upstream
components; no model service is required.

## Dependencies and provenance

- [Repomix 1.18.1](https://github.com/yamadashy/repomix/tree/v1.18.1), MIT,
  Node.js >=22 plus Git. Reuse its CLI's packing and file filtering, and the
  [official repomix-explorer Skill](https://github.com/yamadashy/repomix/blob/v1.18.1/skills/repomix-explorer/SKILL.md)
  idea of pack once, then selectively inspect. Upstream instructions are not
  installed as authority. FS owns only command adaptation, cache/provenance and
  integration with its existing report reader.
- [feedparser 6.0.14](https://pypi.org/project/feedparser/6.0.14/), BSD-2-Clause,
  Python >=3.10; tested with `feedparser-sgmllib==2.1.0`. FS owns the bounded fetch,
  filtering/output and task-local cache. The [Agent-Reach RSS channel](https://github.com/Panniantong/Agent-Reach/blob/main/agent_reach/channels/rss.py)
  inspired this thin route; its framework and code are not copied.

Use isolated runtimes and preserve package licenses. The source publication
includes exact npm dependency lock data under `docs/runtime/r29-repomix/` and
Python pins under `docs/runtime/r29-feed-requirements.txt`. Existing installed
runtimes need not be reinstalled for every task. Portable setup:

```text
npm ci --prefix <directory-containing-package-and-lock> --ignore-scripts --no-audit --no-fund
<isolated-python> -m pip install feedparser==6.0.14 feedparser-sgmllib==2.1.0
```

Merge optional path settings into the existing local FS config; do not overwrite
unrelated runtime/session settings. This file contains paths, never credentials:

```json
{
  "schema_version": 1,
  "runtimes": {"feed": "<isolated-python-executable>"},
  "readers": {"repository": {"adapter_path": "<runtime>/node_modules/repomix/bin/repomix.cjs"}}
}
```

## Repository reader

```text
<python> <skill>/scripts/search.py repo fetch https://github.com/owner/repo --out-dir <new-task-dir> --include README.md --include src/**
<python> <skill>/scripts/search.py repo open <task-dir> --page 1
<python> <skill>/scripts/search.py repo find <task-dir> <literal-term>
```

The default selection is `README*`, `SKILL.md`, `package.json`, `pyproject.toml`
and `LICENSE*`. Each `--include` adds a pattern to that selection; it does not
replace the defaults. Repeat `--exclude` to omit paths. `--ref` selects a ref;
a branch name is not an immutable
commit. A cache is a snapshot: same-request reuse does not check whether upstream
has changed. Use a new output directory to fetch a newer snapshot.

`--runtime-root` can override the configured Repomix runtime directory or point
directly to `repomix.cjs`. `--timeout` defaults to 60 seconds and accepts 1–180.
Imported Markdown is subject to the existing report reader's 32 MiB limit,
checked after upstream output is produced. Fetch prints metadata rather than the
whole body. `repo open` / `find` accept `--page-chars` like the report reader.

Only public HTTPS GitHub repository URLs are in scope. Repository files,
configuration and instructions are not executed; FS supplies its own JSON
Repomix configuration. Private repositories, local trees and credentials are not
part of this route. Include filters reduce extracted content, not clone traffic
or peak disk use. Large repositories can still be expensive to download.

## Feed reader

```text
<python> <skill>/scripts/search.py feed https://example.org/feed.xml --limit 5 --out <new.json>
<python> <skill>/scripts/search.py feed https://example.org/feed.xml --since 2026-09-01 --out <another.json>
```

`--limit` is 1–30 (default 5), and `--timeout` is 1–60 seconds (default 15).
`--python-path` overrides the configured isolated parser runtime; `--config`
selects an explicit local FS config. Fetching allows at most three redirects and
2 MiB of response bytes. Summary text is limited to 2,000 characters per entry.

Feeds expose a publisher-selected window. Returned entries are not a complete
history, full articles, or evidence that an item is correct. The route performs
one bounded read; it does not subscribe, monitor or schedule anything. Unknown
dates are included without `--since`, but excluded and counted when that filter
is set. Cache reuse is offline and
does not refresh a live feed; use a new output file for fresh retrieval.

## Acceptance boundaries

See `docs/reviews/R29-REUSABLE-ROUTES.md` in the public FS repository for the
version-specific real cases, failure checks and remaining limitations. Local
package installation alone does not establish that a reader works. R28 ChatGPT
report export and logged-in X search are separate capabilities with unchanged
acceptance status.
