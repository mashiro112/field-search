---
name: wechat-search
description: Search WeChat Official Account articles for Chinese news, industry perspectives, tutorials, product analysis, and institutional publications through Sogou WeChat Search. Return account names, publication dates, summaries, and original WeChat links.
---

# WeChat Search

Run:

```bash
python3 scripts/search.py "search query"
```

Return five results by default. Answer and cite only fields actually returned in `results`:

- Prefer most-liked sorting when the search surface provides it. Sogou WeChat does not expose like sorting or engagement counts, so use relevance ordering and state the actual sort mode.
- Prefer the original WeChat article in `url`.
- Use `sogou_url` from the same result when `url` cannot be opened.
- Open `url` and read the article when its full position matters. Do not infer it from the summary alone.
- Merge duplicate syndications and distinguish account opinions from verifiable facts.

When the script returns `search_executed: false` and `fallback: browser`, load and follow `$browser:control-in-app-browser`, then search at `https://weixin.sogou.com/`. Ask the user to complete any CAPTCHA. Do not bypass it.

End every response with a `## References` section. Keep links next to supported claims and repeat the used links here, deduplicated and comma-separated on one website line:

```markdown
## References

WeChat: [result title](https://example.com), [result title](https://example.com)
```

List only links actually used in the answer. When none exist, write `No citable sources.` below the heading.
