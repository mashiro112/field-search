# 实际集成清单

# FS01-R12.5 explicit academic-edges ownership

- scripts/academic_edges.py: exact isolated R12.4 bounded DOI reader, exposed as a new explicit script; it is not added to the ordinary source list.
- scripts/search.py: thin academic-edges DOI dispatch only. It forces live mode, passes the 0..3 Meta budget/timeout/output path, preserves the reader JSON, and returns nonzero for non-ok reader status.
- scripts/integrated.py: unchanged; existing Reddit, WeChat, keyless-web, catalog, arXiv, Stack Exchange, and public-X adapters retain their prior routing.
- SKILL.md and this map document the explicit boundary; no keyword classifier, registry, default fallback, or claim of complete reference coverage is added.

# FS01-R22 explicit Xiaohongshu ownership

- `scripts/search.py xiaohongshu`: one explicit entry that delegates only to the thin `scripts/xiaohongshu.py` bridge; ordinary `search`, `read`, `auto` and cross-source fan-out are unchanged.
- `scripts/xiaohongshu.py`: forwards only `search` and `feed` to the pinned, verified R22 read-only adapter. Runtime, adapter and isolated-session paths are caller-supplied; the feed path accepts an opaque `r22:` reference and never accepts a token or direct tokenized URL.
- The bridge preserves the adapter's actual status, counts, `has_more`, unknown and truncation fields; `--max-comments` is a loading target, not an output cap. It adds no collector, download, login, cookie, QR, background service or output-file writer.
- Upstream commit, license and installed-file hashes are recorded in `integrations/provenance.json`; no upstream Skill or crawler is copied into the installed entry.

2026-09-06 核查。安装代码、采集成功、方法借鉴是三个不同事实。可用性随网络/平台改变，调用时以状态为准。

| PDF / 调研候选 | 在 field-search 中的方式 | 边界 |
|---|---|---|
| glidea/supersearch-skills | **代码级复用**微信公众号结果与跳转解析器；多平台按问题路由 | 微信能发现账号、日期、摘要；Sogou原文跳转本机未全部解析成功。其X脚本本身调用付费xAI，未开启。RED/抖音/Telegram等未获得登录后检索权限 |
| last30days | **代码级调用**Reddit RSS、评论解析与免费网页搜索模块 | 并非运行其全部平台/模型。没有启用Cookies提取、全局配置读取、自动安装、发布、付费后端；未知互动量为null |
| codex-insane-search | **已纳入公开读取路径及上游参考**，实现X oEmbed、公开时间线尝试、Jina Reader | 已知X帖与Jina读取成功；时间线429。它本身主要是路径配方，非独立搜索索引 |
| hec-ovi/research-skill | **方法融合**：独立来源、反证、分层证据、按需复用上下文 | 不照搬无限研究、强制长期索引与固定代理分工 |
| forsonny/deep-discovery | **方法融合**：递进提问，查出能改变决策的隐含条件 | 正确owner为forsonny；100问是推理流程，无新增索引；按任务深挖，不每次强制100问 |
| feiskyer/codex-settings / deep-research | **编排思路融合**：任务拆分、失败状态、紧凑证据交接 | 当前宿主已有原生代理能力，不另启动默认8路CLI；是否委派遵守调用任务授权 |
| literaf/ai4scholar-plugin-codex | **未接其收费MCP**；提供arXiv公开摘要接口，优先发现宿主已有Scholar工具 | 独立key/积分；等价论文发现不代表已获得其全部引用图和Google Scholar能力 |
| findarepo.com | **实际数据接入**：skills、trending每日JSON，带日期/署名 | 有限目录，不是GitHub全库；质量不能用增长代替；测量数据CC BY 4.0 |
| Agentic-Index | **候选线索**，未安装运行器 | 匹配仓库adrianwedd/Agentic-Index存在旧数据/文档代码不一致；PDF准确指向仍不确定 |
| mohmdw8/OPEN-SOURCE-SEARCH- | **多注册表发现策略融合**，不复制其GPL代码 | 9源中4源为站点网页查询；用原生Web覆盖这些站点、回注册表核实，不能称为9个独立已连接API |
| LangChain Open Deep Research / Jina DeepResearch | **方法融合**：明确研究问题、按缺口迭代、预算和检验 | 未部署完整独立研究服务器；Jina Reader已接，但Reader不是Jina DeepResearch |

上游快照在 `integrations/`，提交号、许可证及文件哈希在 `integrations/provenance.json`。上游 `SKILL.md` 改名 `UPSTREAM_SKILL.md`，保留出处而不自动激活另一整套研究规则；上游采集代码未改，适配位于 `scripts/integrated.py`。未因安装获得任何网站访问权。

## 已知验证状态

- 本机无新增付费key实际成功：Reddit RSS与评论、微信候选、FindARepo、arXiv、Stack Overflow、keyless网页搜索、X已知公开帖、Jina公开页读取。
- X公共网页索引曾发现作者原帖，也出现同题无结果，属于波动覆盖；完整搜索优先原生Web发现再回帖读取，不能保证覆盖所有X。
- X公开时间线测试429；微信原文跳转/验证码仍是缺口。Jina验证码页面必须标unavailable，不能用其内容冒充文章。
- X API/xAI/Gemini收费适配器仍受显式开关控制；未提交付费请求，未新建服务账号。
- 这些是本机实测与集成范围，**不是优于所有候选综合或商业Deep Research的证明**。评测应看同题、同时间/成本下遗漏的关键证据与后续行动效果。
# FS01 additions (2026-09-07)

- `scripts/recent.py`: executes the existing pinned last30days **full selected keyless engine**, including plan, gathering, normalization/ranking, and complete record output. Original-page verification and final synthesis remain the host's job. Tested original and integrated T2 runs; paid/login/video lanes untested. No default fan-out.
- `scripts/document.py`: reuses `hec-ovi/websearch-skill` 0.6.1 commit `1bd31c8267758fccc247b1ec2299cf47cdbecb9a` extraction + pagination from the isolated installed runtime. Uses existing Jina public transport. Original end-to-end websearch failed; do not promote component success to whole-tool reproduction. MIT source retained under FS01 deployments; dependencies retain their own licenses.
- research-skill's investigation/contrarian/synthesis/storage/retrieval workflow reproduced in FS01 task-local sandbox; no automatic project/global `.research` added to this Skill. Deep Discovery is an optional architecture interrogation method, not an added information source.
