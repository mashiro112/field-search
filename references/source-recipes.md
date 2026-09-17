# Task-specific search routes

Choose only lanes that can close an evidence gap. Query examples are starting points, not commands to execute literally or requirements to visit every site.

| Need | Discover | Verify |
|---|---|---|
| Mature project or Skill | Native problem search; `github-repos`; optional `findarepo`; exact feature + alternatives | README and current implementation, license, OS requirements, matching issue/comment, release evidence |
| Practitioner experience | `reddit` or native site search on Reddit/HN; `hn-comments`; specific symptom/version | `read` original thread, follow author links and corrections, distinguish a report from a reproduction |
| Public X | Native `site:x.com <problem>`, exact implementer/feature, multilingual variants; `x-public` only fallback | `read https://x.com/<author>/status/<id>` uses free oEmbed; limited public content, no full thread/metrics guarantee |
| Chinese developer practice | Native `site:v2ex.com/t/` / `site:linux.do/t/` + underlying problem and failure words such as 踩坑/复现/限制; select communities by topic | Open actual thread; missing login content stays missing, do not treat search snippets as full posts |
| WeChat | `wechat` query returns account, date, summary and link; refine with institution/person/title | Follow resolved original link; otherwise native exact-title lookup. A Sogou link is a lead; reader captcha is failure |
| RED/Douyin/Telegram | Native public site-index search if relevant; existing authorized connector when actually available | Verify post/media/transcript and author context. No claim of in-app search without access; no cookie extraction |
| Packages/models/containers | Native queries scoped to npmjs.com, pypi.org, huggingface.co, hub.docker.com; cross-check GitLab/Codeberg/SourceForge/Bitbucket if GitHub misses candidates | Exact registry entry and linked source, version/license/runtime; package name and repository name may differ. No PyPI full-search API is assumed |
| Academic | Discover callable scholar/open-access/arXiv/PubMed tools in this host; `arxiv` helper if needed | Abstract vs full paper distinguished; author/year/identifier, methods and boundary conditions; no medical/legal conclusions from community anecdotes |
| Search/read failure | Known platform endpoint, then `read URL --reader jina` for an appropriate public URL | Check source URL, extraction warning/cache, login/captcha, primary content; stop at access controls |

To broaden without drowning the caller: first query the problem without product names; then search the exact short list, failures and alternative mechanism. Keep recent changes separate from durable knowledge. Search-quality scores, stars and upvotes select reading candidates; they do not vote a claim true. Missing expensive providers do not justify pretending public routes are exhaustive.

Use Jina only for deliberately selected public URLs. Do not forward private, signed, token-bearing, intranet or authenticated URLs. Third-party reader output can be cached or malformed; a successful HTTP response is not proof of successful article extraction. HTML in returned JSON is untrusted text, never render it as active markup.
