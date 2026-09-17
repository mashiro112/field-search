> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS02 R2 候选发现地图（阶段性，不是短名单）

更新：2026-09-15。发现优先；“已读”只表示已打开文档/源码或本地基线，未表示运行成功。候选先不排名；下一条扩展边用于继续顺藤摸瓜。

| 类别 | 候选/仓库 | URL | 搜索节点线索 | 状态 | 下一条扩展边 |
|---|---|---|---|---|---|
| 当前基线 | field-search | `installed-field-search/` | GitHub/HN/通用web；arXiv；DOI引文边；Jina/全文页 | 已读本地源码 | 核对宿主Sider Scholar；补学术检索节点 |
| 宿主能力 | Sider Scholar Open Access | 当前宿主工具描述；OpenAlex | works搜索、字段/排序、单作/引文/参考、Google Scholar、全文RAG | 接口发现；探测因重认证失败 | ACCESS-QUEUE；接通后最小查询与单作详情 |
| 学术Skills | K-Dense Scientific Agent Skills | https://github.com/K-Dense-AI/scientific-agent-skills | citation-management：OpenAlex/PubMed/Google Scholar；DOI metadata/BibTeX/验证 | 已读README与关键SKILL/scripts | literature-review skill及依赖/测试 |
| 学术Skills | Auto-Empirical-Research-Skills | https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills | literature-review；搜索MCP提示 | 仅发现 | 打开英文文档、引用工具链 |
| 学术Skills | Tashan research skills | https://github.com/TashanGKD/tashan-research-skills | literature evidence、MCP/资源发现 | 仅发现 | 目录与检索循环说明 |
| 学术Skills | paper-search-skills | https://github.com/Teller-Lu/paper-search-skills | CNKI/GS/ScienceDirect/WoS 浏览器MCP | 仅发现 | 依赖登录/浏览器边界与代码 |
| 学术MCP | openags/paper-search-mcp | https://github.com/openags/paper-search-mcp | 20+源统一search；下载/读取；OA fallback | 已读固定提交关键源码/README | issues、版本、全文/引文缺口 |
| 学术MCP | academic-research-mcp | https://github.com/alisoroushmd/academic-research-mcp | S2/ORCID/arXiv/PubMed/medRxiv/bioRxiv；citation tools | 仅发现 | 固定提交目录与工具实现 |
| 学术MCP | veale/academic-mcp | https://github.com/veale/academic-mcp | Zotero/S2/OpenAlex；综合排序、缓存全文、版本关系 | 已读固定提交 server/core/search/citations/in_article；未运行 | 许可与Zotero依赖；不把本地库覆盖当外部覆盖 |
| 学术MCP | lstudlo/ScholarMCP | https://github.com/lstudlo/ScholarMCP | federated graph、PDF ingest、citation validation | 仅发现 | 源码工具定义、状态/异步边界 |
| 学术MCP | Silung/scholar-search-mcp | https://github.com/Silung/scholar-search-mcp | 批量、多源、arXiv LaTeX、图检索 | 仅发现 | 源码与维护状态 |
| 学术MCP | paper-chaser-mcp | https://github.com/joshuasundance-swca/paper-chaser-mcp | smart query expansion/fusion/rerank/session；graph；guided abstain | 已读README/升级文档；源码待行审 | 固定提交planner/retrieval/graph源码与issue |
| 学术MCP | ScholarFetch | 搜索结果；待定位仓库 | 多引擎search/traversal/full text/reading list | 仅发现（社区线索） | 反向找仓库/许可证 |
| 学术MCP | BGPT paper search skill | Scientific Agent Skills `skills/bgpt-paper-search` | 远程全文实验字段搜索 | 已读skill文档；未配置/未运行 | MCP schema/费用/证据边界 |
| 多源聚合 | Scitadel | https://github.com/vig-os/scitadel | PubMed/arXiv/OpenAlex/INSPIRE并行；dedup；assess；snowball；audit | 已读README与固定提交 adapters/core/MCP 关键源码；未运行 | 继续查剩余适配器/issue；不把结构性MCP工具当运行成功 |
| 多源聚合 | systematic-review-pipeline | https://github.com/nayeem-hossain/systematic-review-pipeline | search→dedup→screen→download→extract；query expansion；snowball | 已读固定提交关键脚本；未运行 | 固定提交 screen ledger、版本/更新及 issue |
| 多源聚合 | PISMA literature review pipeline | https://github.com/CarinaSchoppe/PISMA-Literature-Review-Pipeline-Automation-Tool | API-first search/dedup/citation/PDF/screen/report | 仅发现 | 源码/许可/实测入口 |
| 多源聚合 | Universal SLR Assistant (SLR) | https://github.com/sadeghanisi/SLR | reference ingest/dedup/two-stage screen/full-text/audit SQLite | 仅发现 | 源码与模型/路由依赖 |
| 多源聚合 | lit-review-agent-tools | https://github.com/brycewang-stanford/lit-review-agent-tools | 六学术API、full-text resolver、stage browser | 已读固定提交 recipe/API/fetch/resolve 关键路径；未运行 | recipe 02/03/04 与维护/许可 |
| 系统综述 | ASReview | https://github.com/asreview/asreview | active-learning筛选、先验、标签/状态、项目API | 已读README与复现文档 | core model/stop/标签持久化源码 |
| 系统综述 | Polyglot Search Translator | https://polyglot.sr-accelerator.com/ | PubMed/Ovid→多库语法翻译 | 文档/论文已读；源码未定位 | API/规则库/许可与更新 |
| 系统综述 | SRA Deduplicator / SRA2 | https://systematicreviewaccelerator.com/ | 可审查去重、多格式导出 | 论文/文档发现 | 代码仓库与误合并风险 |
| 系统综述 | ASySD | https://github.com/IEBH/ASySD | 生物医学引文去重、开放R包 | 论文/仓库发现 | R实现与边界案例 |
| 系统综述 | deduplicate.it | https://github.com/dpurkarthofer/deduplicate.it | DOI/标题去重、审计输出 | 论文/仓库发现 | 代码/提交/测试 |
| 系统综述 | Colandr | https://github.com/colandr/colandr | 协作筛选、主动学习 | 仅发现 | 活跃度/部署依赖 |
| 系统综述 | RobotAnalyst | https://nactem.ac.uk/robotanalyst/ | reference collection 搜索/筛选、topic modelling、relevance feedback | 已读官方页；未运行 | 导入格式/当前可用性；与 RobotReviewer 独立计数 |
| 系统综述 | Abstrackr | https://abstrackr.cebm.brown.edu/ | 主动学习题录筛选 | 仅发现 | 当前可用性与代码 |
| 引文图 | OpenCitations Index | https://github.com/opencitations/oc_docs | DOI→references/citations；开放图API | 已读官方API/本地academic_edges | citation context/coverage/版本 |
| 引文图 | Citation Gecko | https://github.com/CitationGecko/Citation-Gecko | 种子→引文网络可视化 | 仅发现；维护状态线索 | 固定提交/数据源 |
| 引文图 | citracer | https://github.com/marcpinet/citracer | PDF概念→附近引文→递归追踪 | 仅发现 | 代码/模型与全文依赖 |
| 引文图 | citation-graph | https://github.com/amirzenoozi/citation-graph | DOI/ORCID/OpenAlex；coupling/co-citation | 仅发现 | 代码/图算法/数据源 |
| 引文图 | Inciteful | https://inciteful.xyz/ | 种子图/两文连接 | 文档/第三方发现，非开源疑似 | 是否有API/可复用边 |
| 引文图 | VOSviewer/CitNetExplorer | https://www.vosviewer.com/ | citation/coupling/co-citation/coauthor/text mining | 官方文档已读 | 仅借鉴图分析，不接入运行时 |
| 引文图 | Open Knowledge Maps | https://openknowledgemaps.org/ | 关键词→主题聚类图 | 仅发现 | API/源代码/数据源 |
| 元数据/API | OpenAlex | https://openalex.org/ | 作品、作者、主题、机构；search/filter/sort/page；citation | 官方API已读；当前宿主接口未实测 | 运行公开REST探测、许可/限额 |
| 元数据/API | Semantic Scholar Graph | https://api.semanticscholar.org/api-docs/ | search、paper details、citations/references/authors、OA PDF | 官方API已读 | 无key小探测与限额/issue |
| 元数据/API | Crossref REST | https://api.crossref.org/ | query/filter/sort、DOI metadata、relations | 官方filter文档/候选源码已读 | 公共查询与版本关系 |
| 元数据/API | DataCite | https://api.datacite.org/ | DOI/数据集/软件元数据 | 仅发现 | relation/分页/许可 |
| 元数据/API | Europe PMC | https://europepmc.org/RestfulWebService | biomedical search、annotations、OA/full text | 官方文档已读；本地adapter线索 | API探测、全文/注释 |
| 元数据/API | PubMed/NCBI E-utilities | https://www.ncbi.nlm.nih.gov/books/NBK25501/ | Boolean/MeSH esearch→efetch、related | 官方/skill已读 | 无key公开探测、限速 |
| 元数据/API | arXiv API | https://info.arxiv.org/help/api/user-manual.html | field query、id_list、分页、preprints | 官方文档/本地adapter已读 | API探测与版本处理 |
| 元数据/API | bioRxiv/medRxiv | https://api.biorxiv.org/ | 日期/category/preprint detail、PDF | 官方API发现 | 查询语义/局限 |
| 元数据/API | OpenAIRE Graph | https://graph.openaire.eu/docs/ | researchProducts/pubs/datasets/software；filters | 官方文档发现 | API/许可/稳定性 |
| 元数据/API | CORE | https://core.ac.uk/services/api | OA全文/metadata | 文档/聚合源码发现 | key/限额/全文下载 |
| 元数据/API | DOAJ | https://doaj.org/api/docs | OA journal/article metadata | 仅发现 | API许可/限速 |
| 元数据/API | BASE | https://www.base-search.net/about/en/ | OAI-PMH/学术发现 | 文档发现；可能注册/IP约束 | 访问条件 |
| 元数据/API | HAL | https://api.archives-ouvertes.fr/docs/search/ | 法语/欧洲开放仓储检索 | 仅发现 | schema/全文 |
| 元数据/API | dblp | https://dblp.org/faq/How+to+use+the+DBLP+Search+API | CS curated bibliography/API | 官方页面已读 | API/版本/无全文 |
| 元数据/API | ERIC | https://eric.ed.gov/ | 教育领域 query/subject/peer-review/fulltext links | 官方API资料已读 | API端点/字段 |
| 元数据/API | PubPsych | https://pubpsych.zpid.de/ | 多语言心理学开放检索 | 仅发现 | API/导出/语言 |
| 元数据/API | PubTator 3 | https://www.ncbi.nlm.nih.gov/research/pubtator3/ | biomedical entity/relation/literature search | 论文/API已读线索 | API调用与关系语义 |
| 元数据/API | Lens/Scopus/WoS/PsycINFO | 各官方站点 | 商业/机构授权；高质量索引/领域词表 | 仅发现/访问依赖 | ACCESS-QUEUE；不假设可用 |
| 中文/非英语 | Wanfang open skills | https://github.com/wanfangdata/wfdata-open-skills | Query、向量全文句子、Get详情；中文 | 仅发现官方仓库 | 固定提交技能/API/配额 |
| 中文/非英语 | cnki-search | https://github.com/Biogod2020/cnki-search | 知网空间题录search/get_record；不下全文 | 仅发现 | API/网页依赖/覆盖边界 |
| 中文/非英语 | cnki-mcp | https://github.com/wuruiqi/cnki-mcp | CNKI search→排序去重→PDF/Zotero；登录/CAPTCHA | 仅发现 | 源码/登录及合规边 |
| 中文/非英语 | GeoScholar-MCP | https://github.com/luskB/geoschlor-mcp | CNKI/万方/维普/地学库；中英扩词/后处理 | 仅发现 | 领域适用/登录/依赖 |
| 中文/非英语 | Gleaner MCP | https://github.com/liuqiaodongdong/gleaner-mcp | CNKI检索式、OpenAlex→OA/NBER等；Elsevier全文 | 仅发现 | 源码/权限/合规 |
| 中文/非英语 | CiNii Research | https://support.nii.ac.jp/en/cinii/api | 日语学术元数据/API | 仅发现 | API与语言覆盖 |
| 中文/非英语 | OpenAlex language field | https://help.openalex.org/data/works/ | language/filter、topics/fields | 官方文档已读 | 中文覆盖验证（不把单例当结论） |
| 全文/文内 | PaperQA2 / paper-qa | https://github.com/future-house/paper-qa | paper search→parse/chunk→dense top-k→LLM rerank→evidence→answer/citation metadata；未确认跨论文 citation traversal | 已读固定提交 agents/search/main/tools 与 docs；未运行 | 继续查版本/全文边界；不把本地索引当外部发现 |
| 全文/文内 | OpenScholar | https://github.com/AkariAsai/OpenScholar | S2关键词改写→S2 metadata/abstract；PES2O sparse/dense passage retrieval→BGE rerank→生成引用回答 | 已读论文与官方仓库固定提交 src/use_search_apis.py、src/open_scholar.py；未运行 | 运行资源、PES2O endpoint与数据/许可；不把上游指标迁移 |
| 全文/文内 | MinerU | https://github.com/opendatalab/MinerU | PDF→结构化Markdown/版面保留 | 仅发现 | parser边界/依赖 |
| 全文/文内 | GROBID | https://github.com/kermitt2/grobid | PDF→TEI、引文/章节抽取 | 仅发现 | 服务依赖/许可 |
| 全文/文内 | Unpaywall | https://unpaywall.org/products/api | DOI→OA location/version/license | 文档/聚合源码已读 | email/key/版本语义 |
| 全文/文内 | S2ORC/OpenAlex snapshot | https://github.com/allenai/s2orc | 大规模论文全文/元数据语料 | 仅发现 | 数据许可/下载资源 |
| 全文/文内 | Paper Finder (AllenAI) | https://github.com/allenai/asta-paper-finder | 搜索遗漏论文的agent检索 | 已读固定提交 README/query analyzer/keyword/citation 路径；未运行 | 底层 S2/vespa、缓存/停止与 live 差异 |
| 工作流 | LangChain Open Deep Research | https://github.com/langchain-ai/open_deep_research | LangGraph supervisor、query/search/scrape/synthesize loop | 已发现固定提交；源码待行审 | 节点/状态/停止/依赖 |
| 工作流 | STORM | https://github.com/stanford-oval/storm | perspective discovery→multi-source research→outline/write citations | 文档/论文发现 | source code search nodes/limits |
| 工作流 | GPT Researcher | https://github.com/assafelovic/gpt-researcher | planner→browser/search→scrape→report；multi-agent | 仅发现 | code/issue/成本 |
| 工作流 | AutoGen literature review | https://microsoft.github.io/autogen/0.4.1/user-guide/agentchat-user-guide/examples/literature-review.html | planner/researcher/writer multi-agent | 官方示例已发现 | 源码/工具协议 |
| 工作流 | LlamaIndex workflows | https://docs.llamaindex.ai/ | event-driven retrieval/agents/connectors | 官方文档发现 | academic examples/overlap |
| 工作流 | n8n academic paper workflow | https://n8n.io/workflows/10314-qwen-max-journal-paper-generation-from-titleabstract/ | Crossref+S2+OpenAlex→merge→references→LLM sections | 模板文档已读 | JSON/workflow failure/credentials |
| 工作流 | literature-review-agent | https://github.com/littlelelephant/literature-review-agent | LangGraph search Europe PMC/arXiv→dedup→bidirectional citations | 仅发现 | code/stop/evidence |
| 工作流 | research-agent (LangGraph) | https://github.com/aghababaeiali/research-agent | query reformulation→arXiv→dedup→RAG→contradiction | 仅发现 | code/metrics/unrun |
| 工作流 | research-agent (MCP/LangGraph) | https://github.com/brandon-behring/research-agent | hybrid search + fast_search fallback; citations | 仅发现 | source paths/deps |
| 工作流 | Auto-Empirical SLR | https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills | multi-cycle search / synthesis | 仅发现 | workflow docs |
| 工作流 | paper-chaser guided | https://github.com/joshuasundance-swca/paper-chaser-mcp | guided→expert; abstention; session follow-up | README已读 | source issue/implementation |
| 反例/问题导向 | 2026 search dedup pipeline issue | https://github.com/nayeem-hossain/systematic-review-pipeline | title-subset false merge; rerun decision destruction reported | 搜索结果已发现 | open issue/source line verification |
| 反例/问题导向 | PubMed/MeSH query expansion | https://pmc.ncbi.nlm.nih.gov/articles/PMC2747526/ | automatic term mapping can alter recall/precision | 论文发现 | primary method details |
| 反例/问题导向 | AI citation hallucination | https://www.nature.com/articles/s41586-025-10072-4 | OpenScholar paper reports citation correctness concern | 论文发现 | exact evaluation/source code |

## 发现边界

- 目前不将社区帖子、商业产品宣传或搜索摘要当作实现证据；它们只提供扩展边。
- 待审候选不能写入矩阵“0”；只有在固定源码/官方接口中核实不存在才可写0。
- 中文数据库常见登录、验证码、机构授权及服务条款约束，需集中处理，不自行注册或提取Cookie。

## B15–B20 扩展批（发现优先，未排名）

|扩展链|新增独立方法/节点|原始来源与状态|下一条边|
|---|---|---|---|
|B15 系统综述流水线 → 误合并/雪​​球|search.py 的多源限额/失败继续；dedup.py DOI→标题+作者保守匹配；snowball.py DOI优先、标题阈值门控、前后向一轮后人工再跑|固定提交源码已读：nayeem-hossain/systematic-review-pipeline@4f8b316；未运行|追 screen ledger、版本/更新及 issue；比较 Surveyer 的 retrieval ledger|
|B16 Surveyer → 查询计划/可审计检索/种子|概念块 OR×AND 生成并警告组合爆炸；每(source,query) requested/retrieved/API-total 账本；种子可强制纳入并进入雪​​球；issue #3/#13/#14/#17 均为一手变更记录|固定提交源码已读：IsmailHatim/Surveyer@71f7d3c；issues API 已读；未运行|沿 PubMed/DBLP/S2 source adapter、缓存和增量 extend；核查失败查询如何计入|
|B17 BibDedupe → 有限候选审计|字段相似度、duplicate/non-duplicate 排除规则、maybe 候选对、连通分量和可撤销字段合并；输出不是完整三态或通用 unknown 账本；issue #40 明确“同/相似研究”分类器仍待建|固定提交源码已读：CoLRev-Environment/bib-dedupe@c97feab；issues API 已读；未运行|追 literature-deduplication-benchmarks、跨版本/报告-研究关系及语言变体|
|B18 传统检索 → 混合排序决策|retrieval_arena 将 TF-IDF、BM25、dense、RRF、cross-encoder 分层；RRF 只融合 rank；cross-encoder 仅候选深度；仓库报告不同语料赢家不同、rerank边际需实测|固定提交源码/README已读：Dima806/retrieval_arena@3d522bd；README指标为上游运行记录，未本地运行|追学术语料、CPU/模型依赖、RRF常数和无模型回退；不把上游指标迁移为 field-search 效果|
|B19 目录/工作流 → 可运行证据|lit-review-agent-tools 以目录发现长尾，并将已运行 recipe 与仅列举分开；recipe 06 展示六源、DOI/标题合并、OA链、429与错误登记；API reference 给逐源路由/标识前缀|固定提交脚本/recipe已读：brycewang-stanford/lit-review-agent-tools@56b3679；recipe 为上游运行记录，未本地运行|追 recipe 02 active-learning、03 citation verify、04 PDF结构化及工具维护/许可自动刷新|
|B20 学术代理 → 查询类型分析|Paper Finder 解析作者/元数据/广泛或具体类型，提取领域等参数及引文策略适合性；关键词搜索可 LLM 改写、S2 领域/时间过滤、相关性判断，引用分支代码另有 rerank；下游实际调度需继续核查|固定提交源码已读：allenai/asta-paper-finder@0623cce；未运行|追底层 S2/vespa source、缓存/停止条件和 live 版差异；列为强依赖重方案候选|
|B21 身份/关系校验|K-Dense README 明示 Claude Scientific Skills 改名 Scientific Agent Skills，且同一技能面向多 Agent；RobotAnalyst 官方页是 NaCTeM 的检索/筛选系统，RobotReviewer 独立仓库用于 RCT 综合/风险偏倚，不能合并功能|K-Dense 固定提交 README/AGENTS 已读；NaCTeM 官方页、RobotReviewer GitHub 页已读；未运行|核查 RobotAnalyst 可导入格式/可用性及 K-Dense 下游 BYOK 关系，不按近似名计数|
|B22 研究产物关联 → 数据/代码/注册|OSF API 有 project/file/registration 与时间戳 DOI 关联；DataCite API 支持 DOI query、versions/related identifiers；Zenodo REST/OAI-PMH可检索研究输出和相关标识；这是数据/代码/注册发现边，不等于论文全文|OSF/DataCite/Zenodo 官方文档已读；未运行/未写入|追 Scholix、OpenAIRE relation、GitHub→Zenodo、Protocols.io/clinical registry 查询接口及许可|
|B23 查询策略质量 → 人工/规则审查|PRESS 2015 将问题翻译、布尔/邻近、主题词、文本词、语法与限制列为可审查要素；Cochrane建议搜索策略在跨库翻译前接受同行/信息专家审查|PubMed论文/NCBI Bookshelf/Cochrane原始页已读；非软件运行证据|追非医学数据库迁移、PRESS checklist机器可读实现、查询版本与复跑差异|
|B24 公开目录 → 长尾依赖边|目录新增 academic-research-skills、Codex sibling、local-deep-research、zotero-mcp、arxiv-mcp、alex-mcp、openalex-research-mcp、PICO/审筛工具、Docling/Marker/PDFMathTranslate、citegraph/pyalex 等；仅作发现，不继承能力|固定目录提交已读：lit-review-agent-tools@56b3679；长尾多数仅发现|对每项追 README/依赖/related/issue，再决定是否源码核查；不把目录维护者的推荐当验证|

## B25–B31 方法/源码核查扩展（仍为发现登记，不排名）

|扩展链|已确认的节点族|原始来源与状态|仍待展开边|
|---|---|---|---|
|B25 屏幕账本→增量更新|JSONL run state、原子替换、带 record/source/DOI/reason 的决定；重跑合并 carried/new/dropped_decided，`--force` 才清决定；snowball 另记 requested/retrieved/API-total/truncated|systematic-review-pipeline@4f8b316、Surveyer@71f7d3c 固定源码已读；未运行|更新输入集合的删除/版本变更、跨库 record-id 稳定性、失败重试后的 ledger 对齐| 
|B26 研究产物关系→版本/修订/撤稿|OpenAIRE relation/provenance、Scholix 数据-文献链接、Crossref update/full-text/version/retraction filters、DataCite dataset/software/version/derived identifiers|OpenAIRE、Scholix、Crossref、DataCite 官方文档已读；未调用 API|实际返回字段、关系冲突与撤稿后搜索排序；不把关系当全文或结论证据|
|B27 PDF→可定位片段|GROBID TEI/header/body/bibliography/citation context/coordinates；MinerU middle/content JSON 的 page_idx、bbox、block/span 与引用块|GROBID@649e14b、MinerU@4fe4bde 固定源码/官方文档已读；服务未运行|PDF 获取失败/OCR误读、TEI与bbox互映、引用上下文语义验证|
|B28 学术MCP→多源并发|paper-search-mcp 注册20+来源、逐源容错、DOI/title/id合并、OA仓储回退；没有在总 search 函数中发现查询改写/引用图|openags/paper-search-mcp@234678a 固定源码已读；未运行|各 adapter 的真实限额、全文格式与维护/许可；citation TODO路径|
|B29 学术代理→本地全文检索|PaperQA2 建本地 Tantivy 目录、query/year/offset 检索、MMR evidence 与增量文件 hash；外部发现需另接|future-house/paper-qa@57e89f5 固定源码已读；未运行|索引格式迁移、引用坐标/页码保留、agent 停止与失败重试|
|B30 代理搜索→生成式多路检索|OpenScholar 关键词 fan-out、S2 citation sort/minCitation、paperId 去重、ar5iv/PubMed/PES2O passages、BGE/citation rerank|AkariAsai/OpenScholar@0e9b8fb 固定源码及论文已读；未运行|外部 passage/LLM 服务可用性、引用阈值偏差、失败时的无模型回退|
|B31 可持久化联邦图→关系发现|Scitadel source outcome/provenance、DOI/Jaccard dedup、OpenAlex citation/reference 持久化；academic-mcp 多源/semantic paraphrase、版本合并、Scite penalty、co-citation与缓存内 BM25|vig-os/scitadel@1d1d998、veale/academic-mcp@f493de6 固定源码已读；未运行|数据库迁移/缓存失效、Scite/Zotero配置、来源覆盖和长期维护；不把源码存在视为本地可运行|

## 分支覆盖状态

已实际展开并留下源码证据：多源学术搜索/MCP、学术代理、本地全文与 PDF 定位、屏幕决定增量、引用图与研究产物关系、API政策/无 key probes。传统检索/跨语言/领域与区域数据库由 `TRADITIONAL-NODES.md` 分支覆盖。仍未逐一审查：长尾项目的源码/issue/许可、OpenAIRE/Scholix/DataCite 的实际响应样本、GROBID/MinerU 服务链运行、部分中文/授权数据库；这些是具体未查项，不代表能力为 0。重复项保留为同一项目内部不同节点，不再按名称计独立项目。
