> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS02 R2 基线：当前 field-search 的科研搜索边界

更新时间：2026-09-15。本文只描述当前已安装 Skill、其方法指令、宿主 Scholar 接口和本轮可复查状态；不把候选项目源码阅读或公开 API probe 写成 field-search 已具备的运行能力。

## 1. 三层基线

|层|当前可用/已确认内容|证据与状态|
|---|---|---|
|Skill 指令|以决策和证据缺口为入口；先 native web/read，再按问题选 GitHub、社区、学术或集成 collector；要求保存 query/source/date/condition、区分发现片段与原文、源码/文档/上游运行/本机运行，并在支持、限制、质疑和未知间停止。|`installed-field-search/SKILL.md` 的 Start from the decision、Choose available routes、Search/discriminate/deepen、Stop and hand off；指令已读。|
|Skill 代码|`scripts/search.py` 普通入口覆盖 GitHub repos/issues、HN、集成 SOURCES，并将 `recent`、`document`、`academic-edges` 分到显式子命令；`scripts/integrated.py` 的集成源为 Reddit、WeChat、keyless-web、FindARepo、arXiv、Stack Exchange、public X，reader 为 Reddit/X/Jina；`document.py` 通过 Jina/Crawl4AI 取得公共长文，保存可复用 snapshot/hash 并离线 find/open；`academic_edges.py` 是显式 DOI→OpenCitations Index→最多三次 Meta，非一般学术搜索。|代码已读；未把本轮候选安装或接入。关键入口：`search.py` L21、L358-L461；`integrated.py` L16-L44、L88-L261；`academic_edges.py` L2-L12、L32-L36；`document.py` L56-L125、L134-L248。|
|宿主接口|ALL_TOOLS 中有 Sider Scholar：OpenAlex works search/advanced、单作详情、引文/参考、arXiv/PubMed 专门入口、Google Scholar、targeted files/knowledge-base RAG；工具说明还区分简单 OpenAlex 查询与需模型解析的复杂查询。|接口描述已发现；实际调用返回 `UNAUTHORIZED: reauthentication required (oauth_refresh_token_missing)`，未重新认证、未把宿主描述当作运行成功。|

## 2. 当前科研相关能力

- **发现入口**：可用 native web/GitHub 和通用公共 collector 找项目、论文摘要、问题/issue 与公开长文；arXiv 是集成源。结果保留来源级失败和截断语义，但没有通用学术索引 fan-out。
- **学术引用边**：`academic_edges.py` 只接受显式 DOI，固定请求 OpenCitations Index，再按明确预算请求 Meta；它保留原始响应、解析状态、身份歧义与部分失败。它不把 DOI 变成搜索词，不做 PDF 匹配、全文读取、支持/相关性推断或完整引用覆盖。
- **全文读取**：`document.py` 适合公共网页/长文的 Jina/Crawl4AI extraction、分页、snapshot、hash 与离线文字定位；它不是学术 OA resolver，也没有 PDF→TEI/page/bbox/citation-context 管线。
- **证据判断**：Skill 指令与 `references/evidence.md` 提供按需读取、出处/条件/未知、研究与资源关系分开、支持/限制/质疑、未运行不称复现等方法；这是推理约束，不是新的索引或学术 API。
- **缺口**：当前 Skill 代码没有已核实的通用 OpenAlex/S2/Crossref/PubMed/Europe PMC 多源搜索器、领域字段路由、查询式翻译/术语扩展、研究对象版本/数据/软件关系、可持续屏幕 ledger、PDF 引文上下文/坐标或学术全文内检索/排序器。宿主描述的 Sider 能力不改变这些共享代码缺口。

## 3. 状态、hash 与公开 probe

共享文件只读基线 hash：

- `SKILL.md` SHA256：`3A84677E15A8652F60F37C7C543163F4A5998F3A66CE29869AFE38B65DE856F4`
- `references/evidence.md` SHA256：`87B24ACB8BCA9B66D13A947C05DEABB6160D26C8767AE1AE99EEB098B55D19FC`
- `scripts/search.py` SHA256：`300BCB3119FA75D53167E8FFC272600956EAB0688C2044906499AC5CB86F84CD`
- `scripts/integrated.py` SHA256：`F338F9B1664F87287162D4818F2E512D0C3D85E532EFD16407430165DBD4DE04`
- `scripts/academic_edges.py` SHA256：`28F87385091976DE07B8594757374B1B092589F97ACB76D6C80B82BD6ECFD985`
- `scripts/document.py` SHA256：`1AB7F080735ECF7252D2DF39139DECE3CDFBF07D4B6B2967C2B7157B99B61EF7`

本轮小规模只读 probe 保存在 `probes/api-policy-probe-2026-09-15.json`（本地历史引用，未随本批发布：`probes/api-policy-probe-2026-09-15.json`），不等同运行候选项目：OpenAlex、Crossref、NCBI、Europe PMC、CORE、OpenCitations 返回 200；Semantic Scholar 与 arXiv 返回 429；Sider 宿主接口为认证错误。没有使用 key、登录、安装或外部写入。

## 4. 与候选比较时的基线规则

候选的“源码确认”只说明固定提交包含该节点；README、论文、Skill 指令、上游运行记录和本机 probe 分开记。未审源码用 `?`，源码明确没有的路径才用 `0`；API 200 不等于完整工作流成功，429 不等于必须 key。以下 R2 inventory 采用 12 个节点定义，query planning 与 metadata/domain filters 分开，全文定位与文内检索分开，去重与研究关系在同一维度内以备注拆开。

本文件不做候选重合排名或选型；传统/非英语/领域分支的已读节点见 [`TRADITIONAL-NODES.md`](TRADITIONAL-NODES.md)，首批代表源码见 [`SOURCE-NODES.md`](SOURCE-NODES.md)，访问事实见 `ACCESS-QUEUE.md`（本地历史引用，未随本批发布：`ACCESS-QUEUE.md`）。
