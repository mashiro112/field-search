# R35: Bluesky posts and replies through the logged-in browser

Use this route when Bluesky posts/replies address a concrete evidence gap and
the selected Browser Bridge profile is already authorized. It reuses
[OpenCLI](https://github.com/jackwener/opencli) 1.8.7 (Apache-2.0); FS adds
bounded DOM extraction, not another browser framework. OpenCLI's own
`bluesky search` searches accounts, so it cannot replace post search.

Check `opencli profile list` and select the authorized profile. A profile ID
is a routing identifier, not a login credential. Do not guess that a bridge
belongs to a named browser; confirm the selected browser/session against the
actual page. In this trial the user identified Edge, and its connected bridge
exposed the logged-in Bluesky page. Native Codex browser inventory alone did
not expose that tab.

```text
search.py context community-search bluesky "Docling" --browser-profile <authorized-profile> --limit 3 --out <new-search.json>
search.py context community-search bluesky "Docling" --browser-profile <authorized-profile> --sort latest --limit 3 --out <new-latest.json>
search.py context community-thread bluesky https://bsky.app/profile/simon.fedi.simonwillison.net.ap.brid.gy/post/3l7zjl2gnzfq2 --browser-profile <authorized-profile> --limit 4 --out <new-thread.json>
```

Without `--browser-profile`, the pre-existing public API reader is unchanged;
its R34 HTTP 403 is not reclassified as a login success. The browser thread
route accepts only canonical HTTPS `bsky.app/profile/<actor>/post/<id>` URLs,
without query, fragment or extra path components. The API route still accepts
its original AT-URI input.

Browser search accepts 1..10 posts; threads accept 1..10 surrounding records
plus the verified original post. The browser thread default is 10; the old
public thread default remains 20. Search defaults to no scroll, with explicit
`--max-scrolls 0..3` for a remaining gap. Both sorts select the actual search
tab, because the site's URL does not encode that choice. `--page`/`--instance`
are Lemmy options, not Bluesky pagination. Threads read currently rendered
context without a recursive reply crawler. Hidden old screens are excluded.
URLs, author identity, rendered body and external links stay attached to each
record. Thread context can include ancestors or replies; unverified relations
remain unknown. UI counts and displayed date labels do not prove exhaustive coverage
or precise normalized timestamps.

Each call uses a separate owned background session and releases only its own
tab lease; OpenCLI can reuse its managed tab between calls.
It does not bind, navigate or close the user's original tab, export cookies,
read private account storage, call a paid API, or publish/follow/react. Login,
bridge failures and layout failures remain explicit unavailable results;
zero matches require the rendered empty-result message rather than a blank
loading screen. Results
are bounded samples and completeness stays unknown.

Use `--out` for task-local full JSON and short stdout; `--full` is optional.
Existing output paths are rejected before browser work. Follow the retained
source links and read decisive originals; a community post is not factual
verification by itself. Credentials and raw logged-in account state are not
part of the source publication.

Acceptance and observed limits are recorded in the repository's
`docs/reviews/R35-BLUESKY.md`. Linux.do is excluded from the owner's current
expansion scope; its older route remains available but is not pending work.
