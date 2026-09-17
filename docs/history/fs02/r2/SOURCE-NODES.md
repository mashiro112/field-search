> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS02 R2 SOURCE-NODES（本批追加；源码与上游运行分开）

本文件只登记可复查的节点入口。固定 commit 链接用于源码定位；“未运行”表示本机未安装/未构建/未调用完整项目。上游 README 的“已运行”只作为上游记录。

## systematic-review-pipeline @ 4f8b3166aeb6d96e06c1943fb59159a40f277cda

- [README.md L3-L16](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/README.md#L3-L16)：依赖轻量、7阶段、multi-source search/dedup/screen/OA PDF/citation verify；工作例子可替换但本身不是通用科研验证。已读，未运行。
- [scripts/search.py L14-L58](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/scripts/search.py#L14-L58)：每源上限、keyless/keyed 路由、单源失败记录并继续；输入输出为 candidates.csv。已读，未运行。
- [scripts/search.py L96-L155](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/scripts/search.py#L96-L155)：公开限速/页大小常量与来源分类。已读，未运行。
- [scripts/dedup.py L1-L17](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/scripts/dedup.py#L1-L17)、[L42-L75](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/scripts/dedup.py#L42-L75)、[L99-L124](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/scripts/dedup.py#L99-L124)：DOI先行、标题长度/排序相似度、共享作者姓氏与 maybe/false-merge 防护。已读，未运行。
- [scripts/snowball.py L1-L29](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/scripts/snowball.py#L1-L29)、[L65-L101](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/scripts/snowball.py#L65-L101)、[L118-L180](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/scripts/snowball.py#L118-L180)：OpenAlex DOI/标题解析、阈值门控、前后向引用、每次一轮后人工筛选再迭代。已读，未运行。

## Surveyer @ 71f7d3ca35a5373cbb278b4d14feacb2d8fb66ec

- [README.md L22-L38](https://github.com/IsmailHatim/Surveyer/blob/71f7d3ca35a5373cbb278b4d14feacb2d8fb66ec/README.md#L22-L38)、[L64-L83](https://github.com/IsmailHatim/Surveyer/blob/71f7d3ca35a5373cbb278b4d14feacb2d8fb66ec/README.md#L64-L83)：多源抓取、去重、关键词/LLM筛选、extend/snowball CLI；README依赖 uv/可选 S2/NCBI/OpenAI/Ollama。已读，未运行。
- [config.py L64-L101](https://github.com/IsmailHatim/Surveyer/blob/71f7d3ca35a5373cbb278b4d14feacb2d8fb66ec/src/surveyer/config.py#L64-L101)：概念块的 OR×AND 查询交叉积；只剔除与显式 `terms` 完全相同的生成项，不能据此声称消除所有内部重复；超过100条仅警告。已读，未运行。
- [dedup.py L14-L100](https://github.com/IsmailHatim/Surveyer/blob/71f7d3ca35a5373cbb278b4d14feacb2d8fb66ec/src/surveyer/dedup.py#L14-L100)：弱 DOI 前缀（arXiv/Zenodo）、DOI/标题匹配、合并来源/查询标签并优先正式 DOI。已读，未运行。
- [Issue/PR #3](https://github.com/IsmailHatim/Surveyer/issues/3)、[#13](https://github.com/IsmailHatim/Surveyer/issues/13)、[#14](https://github.com/IsmailHatim/Surveyer/issues/14)、[#17](https://github.com/IsmailHatim/Surveyer/issues/17)：概念扩展、检索完整性账本、前后向引用追踪、must-cite 种子的一手变更记录。已读，未运行。

## BibDedupe @ c97feab2e66095a6ff8e20ac9a6381f155b993b7

- [README.md L17-L30](https://github.com/CoLRev-Environment/bib-dedupe/blob/c97feab2e66095a6ff8e20ac9a6381f155b993b7/README.md#L17-L30)：面向 literature reviews 的 entity resolution；透明 blocking/matching、可验证整合、持续 benchmark。README主张，未运行。
- [match.py L86-L100](https://github.com/CoLRev-Environment/bib-dedupe/blob/c97feab2e66095a6ff8e20ac9a6381f155b993b7/bib_dedupe/match.py#L86-L100)、[L103-L176](https://github.com/CoLRev-Environment/bib-dedupe/blob/c97feab2e66095a6ff8e20ac9a6381f155b993b7/bib_dedupe/match.py#L103-L176)：按导入条件给 duplicate/non-duplicate 排除规则并产生 `maybe` 候选对；输出仅是 duplicate/maybe 相关对与审计标签，不是完整三态或通用 `unknown` 账本。已读，未运行。
- [cluster.py L13-L32](https://github.com/CoLRev-Environment/bib-dedupe/blob/c97feab2e66095a6ff8e20ac9a6381f155b993b7/bib_dedupe/cluster.py#L13-L32)、[L78-L120](https://github.com/CoLRev-Environment/bib-dedupe/blob/c97feab2e66095a6ff8e20ac9a6381f155b993b7/bib_dedupe/cluster.py#L78-L120)：重复边转连通分量，并限制同一 search set 的实体重复。已读，未运行。
- [Issue #40](https://github.com/CoLRev-Environment/bib-dedupe/issues/40)、[Issue #51](https://github.com/CoLRev-Environment/bib-dedupe/pull/51)：相似研究分类器仍是开放工作；标题相似度有 benchmark 调整经验。已读，未运行。

## retrieval_arena @ 3d522bdb543208fc209ad723287e43c07bfed2cc

- [README.md L5-L14](https://github.com/Dima806/retrieval_arena/blob/3d522bdb543208fc209ad723287e43c07bfed2cc/README.md#L5-L14)、[L21-L58](https://github.com/Dima806/retrieval_arena/blob/3d522bdb543208fc209ad723287e43c07bfed2cc/README.md#L21-L58)：TF-IDF/BM25/dense/RRF/cross-encoder 五路比较、不同语料结果不同；指标与运行结果只作上游记录，未本地验证。
- [hybrid.py L1-L59](https://github.com/Dima806/retrieval_arena/blob/3d522bdb543208fc209ad723287e43c07bfed2cc/src/retrievers/hybrid.py#L1-L59)：两个候选列表以 RRF 融合，输入 corpus/query/k，未依赖学术API。已读，未运行。
- [rerank.py L1-L57](https://github.com/Dima806/retrieval_arena/blob/3d522bdb543208fc209ad723287e43c07bfed2cc/src/retrievers/rerank.py#L1-L57)：cross-encoder 只对 base top-depth 评分，模型懒加载 CPU；成本/模型是额外依赖。已读，未运行。

## lit-review-agent-tools @ 56b3679d4f2148f725de0cf6badd3c1c17087650

- [README.md L1-L14](https://github.com/brycewang-stanford/lit-review-agent-tools/blob/56b3679d4f2148f725de0cf6badd3c1c17087650/README.md#L1-L14)：目录标出 maintenance/license 与 verified workflows；目录条目不能替代源码审计。
- [recipes/06-multi-source-search/README.md L1-L24](https://github.com/brycewang-stanford/lit-review-agent-tools/blob/56b3679d4f2148f725de0cf6badd3c1c17087650/recipes/06-multi-source-search/README.md#L1-L24)、[L26-L52](https://github.com/brycewang-stanford/lit-review-agent-tools/blob/56b3679d4f2148f725de0cf6badd3c1c17087650/recipes/06-multi-source-search/README.md#L26-L52)：六源搜索、DOI/标题合并、429 继续、OA与预印本/正式版去重经验；仅是上游一次运行记录，未本地运行。
- [skills/.../reference/apis/README.md L16-L36](https://github.com/brycewang-stanford/lit-review-agent-tools/blob/56b3679d4f2148f725de0cf6badd3c1c17087650/skills/literature-review-tools/reference/apis/README.md#L16-L36)、[L38-L70](https://github.com/brycewang-stanford/lit-review-agent-tools/blob/56b3679d4f2148f725de0cf6badd3c1c17087650/skills/literature-review-tools/reference/apis/README.md#L38-L70)：问题到数据库路由、跨库标识前缀、keyless/限速与缺失报告。已读，未运行。
- [scripts/fetch_papers.py L1-L14](https://github.com/brycewang-stanford/lit-review-agent-tools/blob/56b3679d4f2148f725de0cf6badd3c1c17087650/skills/literature-review-tools/scripts/fetch_papers.py#L1-L14)、[L70-L95](https://github.com/brycewang-stanford/lit-review-agent-tools/blob/56b3679d4f2148f725de0cf6badd3c1c17087650/skills/literature-review-tools/scripts/fetch_papers.py#L70-L95)、[L101-L203](https://github.com/brycewang-stanford/lit-review-agent-tools/blob/56b3679d4f2148f725de0cf6badd3c1c17087650/skills/literature-review-tools/scripts/fetch_papers.py#L101-L203)：统一记录、六源 adapter、API错误保留、DOI规范化/标题去重。已读，未运行。
- [scripts/resolve_oa.py L1-L17](https://github.com/brycewang-stanford/lit-review-agent-tools/blob/56b3679d4f2148f725de0cf6badd3c1c17087650/skills/literature-review-tools/scripts/resolve_oa.py#L1-L17)、[L74-L189](https://github.com/brycewang-stanford/lit-review-agent-tools/blob/56b3679d4f2148f725de0cf6badd3c1c17087650/skills/literature-review-tools/scripts/resolve_oa.py#L74-L189)：magic-byte PDF验证、JATS结构化文本、Unpaywall→OpenAlex→Europe PMC→arXiv→CORE；closed/not-in-Crossref分开。已读，未运行。

## Paper Finder @ 0623cce6ff61b0a1a637c78d352c4f4d431d0364

- [README.md L3-L17](https://github.com/allenai/asta-paper-finder/blob/0623cce6ff61b0a1a637c78d352c4f4d431d0364/README.md#L3-L17)、[L21-L58](https://github.com/allenai/asta-paper-finder/blob/0623cce6ff61b0a1a637c78d352c4f4d431d0364/README.md#L21-L58)：自然语言→结构对象→执行规划→工作流→相关性/排序；快/勤奋两种运行模式与文件缓存；README说明是历史快照且需多钥。
- [query_analyzer.py L118-L211](https://github.com/allenai/asta-paper-finder/blob/0623cce6ff61b0a1a637c78d352c4f4d431d0364/agents/mabool/api/mabool/agents/query_analyzer/query_analyzer.py#L118-L211)：解析作者/元数据/广泛或具体类型，并提取领域等参数及引文策略适合性；本文件片段未证明下游实际调度 citation 分支。已读，未运行。
- [broad_search_by_keyword_agent.py L42-L53](https://github.com/allenai/asta-paper-finder/blob/0623cce6ff61b0a1a637c78d352c4f4d431d0364/agents/mabool/api/mabool/agents/broad_search_by_keyword/broad_search_by_keyword_agent.py#L42-L53)、[L124-L193](https://github.com/allenai/asta-paper-finder/blob/0623cce6ff61b0a1a637c78d352c4f4d431d0364/agents/mabool/api/mabool/agents/broad_search_by_keyword/broad_search_by_keyword_agent.py#L124-L193)：LLM生成检索式，S2搜索/时间/venue/fields-of-study过滤，相关性判断后输出。已读，未运行。
- [broad_by_specific_paper_citation_agent.py L39-L109](https://github.com/allenai/asta-paper-finder/blob/0623cce6ff61b0a1a637c78d352c4f4d431d0364/agents/mabool/api/mabool/agents/by_citing_papers/broad_by_specific_paper_citation_agent.py#L39-L109)、[L112-L202](https://github.com/allenai/asta-paper-finder/blob/0623cce6ff61b0a1a637c78d352c4f4d431d0364/agents/mabool/api/mabool/agents/by_citing_papers/broad_by_specific_paper_citation_agent.py#L112-L202)：S2 citing papers、snippet过滤、Cohere rerank与snippet计数加权。已读，未运行。

## 其他一手来源

- [Scientific Agent Skills README @ 330c8e7 L1-L20](https://github.com/K-Dense-AI/scientific-agent-skills/blob/330c8e764435a731eff571e3efdda70b363d0792/README.md#L1-L20)：明确 Claude Scientific Skills → Scientific Agent Skills 改名；同一技能集合面向兼容 Agent Skills 的多种 agent。已读，未运行。
- [Scientific Agent Skills AGENTS.md @ 330c8e7 L3-L24](https://github.com/K-Dense-AI/scientific-agent-skills/blob/330c8e764435a731eff571e3efdda70b363d0792/AGENTS.md#L3-L24)：窄技能、避免泛编排/第二 provider 的范围约束；关系信息不可当作 field-search 集成。
- [NaCTeM RobotAnalyst](https://nactem.ac.uk/robotanalyst/)：官方描述其为 reference collection 搜索/筛选、topic modelling、relevance feedback；网页已读，未运行。
- [RobotReviewer repo](https://github.com/ijmarshall/robotreviewer)：独立开源项目，定位 RCT 自动综合/风险偏倚；网页/README已读，未运行；不得与 RobotAnalyst 合并。
- [PRESS 2015 PubMed](https://pubmed.ncbi.nlm.nih.gov/27005575/) 与 [NCBI Bookshelf](https://ncbi.nlm.nih.gov/books/NBK98350/?report=reader)：查询式翻译、布尔/邻近、主题词、文本词、语法/限制的审查要素；方法资料，未运行。
- [Cochrane search chapter](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-04)：建议搜索式在跨库翻译前接受同行/信息专家审查；方法资料，未运行。
- [OSF API v2](https://developer.osf.io/)、[DataCite query API](https://support.datacite.org/docs/api-queries)、[Zenodo developers](https://developers.zenodo.org/)：研究项目/注册/版本/related identifiers/数据与代码输出的机器接口边；官方文档已读，未运行。

## openags/paper-search-mcp @ 234678ab231074a7977320978ee0496dcdaddd1f

- [paper_search_mcp/server.py L1-L31](https://github.com/openags/paper-search-mcp/blob/234678ab231074a7977320978ee0496dcdaddd1f/paper_search_mcp/server.py#L1-L31)、[L67-L126](https://github.com/openags/paper-search-mcp/blob/234678ab231074a7977320978ee0496dcdaddd1f/paper_search_mcp/server.py#L67-L126)：导入并注册 arXiv、PubMed、bio/medRxiv、Google Scholar、IACR、Semantic Scholar、Crossref、OpenAlex、PMC、CORE、Europe PMC、DBLP、OpenAIRE、CiteSeerX、DOAJ、BASE、Zenodo、HAL、SSRN、Unpaywall 等 adapter；IEEE/ACM key 为可选配置。源码已读，未运行。
- [server.py L137-L162](https://github.com/openags/paper-search-mcp/blob/234678ab231074a7977320978ee0496dcdaddd1f/paper_search_mcp/server.py#L137-L162)：统一结果的 key 优先 DOI，其次标题+作者，再次 paper_id；这是精确/规范化去重入口，不等同实体解析或版本判断。源码已读，未运行。
- [server.py L172-L239](https://github.com/openags/paper-search-mcp/blob/234678ab231074a7977320978ee0496dcdaddd1f/paper_search_mcp/server.py#L172-L239)：PDF 下载检查 HTTP、content-type 和 magic bytes；OA 仓储 fallback 按 OpenAIRE→CORE→Europe PMC→PMC，按 DOI/标题最多尝试 3 个并逐源容错。源码已读，未运行。
- [server.py L242-L354](https://github.com/openags/paper-search-mcp/blob/234678ab231074a7977320978ee0496dcdaddd1f/paper_search_mcp/server.py#L242-L354)：对选定来源并发调用，`gather(return_exceptions=True)` 保留单源失败，合并后去重并返回来源/错误/原始与唯一计数；该函数没有查询改写，也没有引用图扩展。源码已读，未运行。
- [server.py L359-L422](https://github.com/openags/paper-search-mcp/blob/234678ab231074a7977320978ee0496dcdaddd1f/paper_search_mcp/server.py#L359-L422)、[L605-L730](https://github.com/openags/paper-search-mcp/blob/234678ab231074a7977320978ee0496dcdaddd1f/paper_search_mcp/server.py#L605-L730)：arXiv/PubMed/生物医学时间过滤与 Semantic Scholar、Crossref 专门入口；Crossref 可排序/过滤 DOI，但源码注明不能直接给 PDF。源码已读，未运行。

## future-house/paper-qa @ 57e89f7223b0960d5ee5ea048c69e3c47e088572

- [src/paperqa/agents/tools.py L120-L210](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/agents/tools.py#L120-L210)：`PaperSearch` 接受 query、年份和偏移，对本地目录索引取 top_n；相同 `(query, year)` 最多重复两次并把文本加入 agent state。它搜索本地已索引文档，不是外部学术发现 API。源码已读，未运行。
- [src/paperqa/agents/tools.py L225-L293](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/agents/tools.py#L225-L293)、[src/paperqa/agents/main.py L121-L148](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/agents/main.py#L121-L148)：证据收集走文档检索/MMR；agent 先建目录索引再选择工具，检索结果进入答案上下文。源码已读，未运行。
- [src/paperqa/agents/search.py L399-L435](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/agents/search.py#L399-L435)、[L500-L575](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/agents/search.py#L500-L575)：Tantivy query 清洗/解析、top_n/offset/min_score；新文件 hash/check、解析失败标记和增量建索引。源码已读，未运行。
- [src/paperqa/docs.py L456-L570](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/docs.py#L456-L570)：缓存 embedding 的 MMR 文本召回、并发 evidence summary 与引用元数据；全文内检索强，但外部全文获取和学术多源发现需另接。源码已读，未运行。

## AkariAsai/OpenScholar @ 0e9b8fb912273d3dae39e593da86e4f6d3bf8de1

- [src/use_search_apis.py L96-L119](https://github.com/AkariAsai/OpenScholar/blob/0e9b8fb912273d3dae39e593da86e4f6d3bf8de1/src/use_search_apis.py#L96-L119)：Semantic Scholar `/paper/search` 使用生成 query、`minCitationCount=10`、按 citationCount 降序，并请求 title/year/abstract/authors/citation/externalIds 等字段；错误返回 `None`。源码已读，未运行。
- [src/use_search_apis.py L121-L172](https://github.com/AkariAsai/OpenScholar/blob/0e9b8fb912273d3dae39e593da86e4f6d3bf8de1/src/use_search_apis.py#L121-L172)：最多生成 5 个关键词查询，逐次调用 S2，按 `paperId` 去重；arXiv ID 再取 passages。该 fan-out 依赖模型生成与 S2 限额，不能当无依赖默认路径。源码已读，未运行。
- [src/use_search_apis.py L229-L274](https://github.com/AkariAsai/OpenScholar/blob/0e9b8fb912273d3dae39e593da86e4f6d3bf8de1/src/use_search_apis.py#L229-L274)、[L386-L413](https://github.com/AkariAsai/OpenScholar/blob/0e9b8fb912273d3dae39e593da86e4f6d3bf8de1/src/use_search_apis.py#L386-L413)：ar5iv HTML 段落解析、PubMed 摘要和 PES2O passage 检索；外部 passage 服务/模型是配置边界。源码已读，未运行。
- [src/open_scholar.py L40-L65](https://github.com/AkariAsai/OpenScholar/blob/0e9b8fb912273d3dae39e593da86e4f6d3bf8de1/src/open_scholar.py#L40-L65)、[L100-L170](https://github.com/AkariAsai/OpenScholar/blob/0e9b8fb912273d3dae39e593da86e4f6d3bf8de1/src/open_scholar.py#L100-L170)：BGE cross-encoder 对段落 rerank，可叠加引用数；设置含最小引用数和关键词抽取，默认重型模型/服务。源码已读，未运行。相关论文：[arXiv:2411.14199](https://arxiv.org/abs/2411.14199)。

## vig-os/scitadel @ 1d1d9985b148c66def3ec63db6b551d5589d9d61

- [crates/scitadel-core/src/services/orchestrator.rs L78-L123](https://github.com/vig-os/scitadel/blob/1d1d9985b148c66def3ec63db6b551d5589d9d61/crates/scitadel-core/src/services/orchestrator.rs#L78-L123)：并行调用多个 source adapter；单源失败不终止整次搜索，并记录 source outcome、数量和延迟。源码已读，未运行。
- [crates/scitadel-core/src/services/dedup.rs L7-L78](https://github.com/vig-os/scitadel/blob/1d1d9985b148c66def3ec63db6b551d5589d9d61/crates/scitadel-core/src/services/dedup.rs#L7-L78)、[L80-L180](https://github.com/vig-os/scitadel/blob/1d1d9985b148c66def3ec63db6b551d5589d9d61/crates/scitadel-core/src/services/dedup.rs#L80-L180)：标题规范化/Jaccard、DOI精确匹配再到标题模糊匹配；canonical Paper 保留每个来源 SearchResult provenance。源码已读，未运行。
- [crates/scitadel-mcp/src/tools.rs L25-L140](https://github.com/vig-os/scitadel/blob/1d1d9985b148c66def3ec63db6b551d5589d9d61/crates/scitadel-mcp/src/tools.rs#L25-L140)：MCP search 可接 query 或 question_id/linked terms，构建 adapter、运行搜索、0.85 去重并保存 Paper/Search/SearchResult，返回逐源结果。源码已读，未运行。
- [crates/scitadel-mcp/src/tools.rs L687-L746](https://github.com/vig-os/scitadel/blob/1d1d9985b148c66def3ec63db6b551d5589d9d61/crates/scitadel-mcp/src/tools.rs#L687-L746)、[L752-L891](https://github.com/vig-os/scitadel/blob/1d1d9985b148c66def3ec63db6b551d5589d9d61/crates/scitadel-mcp/src/tools.rs#L752-L891)：references/citations 工具抓 OpenAlex 前后向边，批量持久化 paper/edge；references/citations 有默认和 OpenAlex 上限。源码已读，未运行。
- [crates/scitadel-mcp/src/tools.rs L1415-L1452](https://github.com/vig-os/scitadel/blob/1d1d9985b148c66def3ec63db6b551d5589d9d61/crates/scitadel-mcp/src/tools.rs#L1415-L1452)、[L1537-L1632](https://github.com/vig-os/scitadel/blob/1d1d9985b148c66def3ec63db6b551d5589d9d61/crates/scitadel-mcp/src/tools.rs#L1537-L1632)：存储查询的 BM25 相似搜索、source registry（PubMed/arXiv/OpenAlex/INSPIRE/PatentsView/Lens/EPO 等）和 key/polite-email 配置线索；后者需以各服务当前政策为准。源码已读，未运行。

## veale/academic-mcp @ f493de604eb672fdd7eb49edbc7a233c771c5a5

- [src/academic_mcp/server.py L117-L167](https://github.com/veale/academic-mcp/blob/f493de604eb672fdd7eb49edbc7a233c771c5a5a/src/academic_mcp/server.py#L117-L167)、[L168-L284](https://github.com/veale/academic-mcp/blob/f493de604eb672fdd7eb49edbc7a233c771c5a5a/src/academic_mcp/server.py#L168-L284)：搜索 Zotero/Semantic Scholar/OpenAlex；keyword 与自然语言 semantic_query 分开，semantic_query 可带 2–4 个 paraphrase；schema含 source/year/venue/domain_hint/exclude_local 等。源码已读，未运行。
- [src/academic_mcp/core/search.py L379-L452](https://github.com/veale/academic-mcp/blob/f493de604eb672fdd7eb49edbc7a233c771c5a5a/src/academic_mcp/core/search.py#L379-L452)、[L816-L930](https://github.com/veale/academic-mcp/blob/f493de604eb672fdd7eb49edbc7a233c771c5a5a/src/academic_mcp/core/search.py#L816-L930)：semantic fan-out、reranker overfetch、多源并发与逐源失败诊断；按 DOI/Zotero key/标题合并并追踪 best DOI/superseded。源码已读，未运行。
- [src/academic_mcp/core/search.py L984-L1077](https://github.com/veale/academic-mcp/blob/f493de604eb672fdd7eb49edbc7a233c771c5a5a/src/academic_mcp/core/search.py#L984-L1077)：可选 Zotero preview、Scite enrichment/retraction penalty、diagnostics；Scite 与 Zotero 属于外部配置。源码已读，未运行。
- [src/academic_mcp/core/citations.py L71-L209](https://github.com/veale/academic-mcp/blob/f493de604eb672fdd7eb49edbc7a233c771c5a5a/src/academic_mcp/core/citations.py#L71-L209)、[src/academic_mcp/core/discover.py L1-L239](https://github.com/veale/academic-mcp/blob/f493de604eb672fdd7eb49edbc7a233c771c5a5a/src/academic_mcp/core/discover.py#L1-L239)：OpenAlex 前后向引用树和 shared-reference/co-citation 排序。源码已读，未运行。
- [src/academic_mcp/core/in_article.py L81-L188](https://github.com/veale/academic-mcp/blob/f493de604eb672fdd7eb49edbc7a233c771c5a5a/src/academic_mcp/core/in_article.py#L81-L188)、[src/academic_mcp/core/in_corpus.py L1-L26](https://github.com/veale/academic-mcp/blob/f493de604eb672fdd7eb49edbc7a233c771c5a5a/src/academic_mcp/core/in_corpus.py#L1-L26)：缓存文章上的 BM25、术语窗口/offset/section；corpus 模式不意外抓取，未缓存项显式返回 `not_cached`。源码已读，未运行。
- [src/academic_mcp/server.py L3481-L3529](https://github.com/veale/academic-mcp/blob/f493de604eb672fdd7eb49edbc7a233c771c5a5a/src/academic_mcp/server.py#L3481-L3529)：文内搜索返回 snippet 和 character range，再由 `fetch_fulltext(mode=range)` 定位；这是证据定位节点，不等同全文覆盖。源码已读，未运行。

## kermitt2/grobid @ 649e14b1c0a18fdaef2d0b8c6d39d08c6c1d883d

- [Readme.md L15-L41](https://github.com/kermitt2/grobid/blob/649e14b1c0a18fdaef2d0b8c6d39d08c6c1d883d/Readme.md#L15-L41)、[L43-L73](https://github.com/kermitt2/grobid/blob/649e14b1c0a18fdaef2d0b8c6d39d08c6c1d883d/Readme.md#L43-L73)：PDF→TEI，抽取 header/reference/citation context、结构化全文、坐标、consolidation；服务有 demo quota，严肃批量需自建。源码/文档已读，未运行。
- [doc/Grobid-service.md L135-L173](https://github.com/kermitt2/grobid/blob/649e14b1c0a18fdaef2d0b8c6d39d08c6c1d883d/doc/Grobid-service.md#L135-L173)：TEI 是较完整来源，Markdown/JSON 客户端输出可能丢坐标/书目细节；可选 Crossref/biblio-glutton consolidation。文档已读，未运行。
- [doc/Grobid-service.md L177-L243](https://github.com/kermitt2/grobid/blob/649e14b1c0a18fdaef2d0b8c6d39d08c6c1d883d/doc/Grobid-service.md#L177-L243)：`processHeaderDocument`/`processFulltextDocument` 输出 header/body/bibliography、raw citations、coordinates、sentence IDs 和 page ranges；503 时建议重试。服务未运行。
- [grobid-core/src/main/java/org/grobid/core/engines/CitationParser.java L78-L147](https://github.com/kermitt2/grobid/blob/649e14b1c0a18fdaef2d0b8c6d39d08c6c1d883d/grobid-core/src/main/java/org/grobid/core/engines/CitationParser.java#L78-L147)、[L222-L287](https://github.com/kermitt2/grobid/blob/649e14b1c0a18fdaef2d0b8c6d39d08c6c1d883d/grobid-core/src/main/java/org/grobid/core/engines/CitationParser.java#L222-L287)：citation string/layout token 解析，抽作者/日期/页码并可 consolidation。源码已读，未运行。
- [get-citation-context-from-tei.xq L11-L34](https://github.com/kermitt2/grobid/blob/649e14b1c0a18fdaef2d0b8c6d39d08c6c1d883d/grobid-core/src/main/resources/xq/get-citation-context-from-tei.xq#L11-L34)：从 TEI 取得引用目标、上下文、section、相对位置和坐标；适合把“引文为何支持/质疑”定位为可复查片段。源码已读，未运行。

## opendatalab/MinerU @ 4fe4bde114a23ee5dd637eae99b767f4669bf58c

- [README.md L48-L78](https://github.com/opendatalab/MinerU/blob/4fe4bde114a23ee5dd637eae99b767f4669bf58c/README.md#L48-L78)、[L145-L183](https://github.com/opendatalab/MinerU/blob/4fe4bde114a23ee5dd637eae99b767f4669bf58c/README.md#L145-L183)：PDF/DOCX/PPTX/XLSX/图像/网页到结构化 Markdown/JSON，含 OCR、版面和多语言；有 CLI/FastAPI/异步 task 及 MCP/LangChain/LlamaIndex 集成线索。源码/文档已读，未运行。
- [docs/en/reference/output_files.md L109-L187](https://github.com/opendatalab/MinerU/blob/4fe4bde114a23ee5dd637eae99b767f4669bf58c/docs/en/reference/output_files.md#L109-L187)、[L298-L328](https://github.com/opendatalab/MinerU/blob/4fe4bde114a23ee5dd637eae99b767f4669bf58c/docs/en/reference/output_files.md#L298-L328)：`middle.json`/content_list 保存 page_idx、block/line/span 以及 bbox；content list 用规范化坐标，能回到页面区域。文档已读，未运行。
- [docs/en/reference/output_files.md L472-L520](https://github.com/opendatalab/MinerU/blob/4fe4bde114a23ee5dd637eae99b767f4669bf58c/docs/en/reference/output_files.md#L472-L520)、[L542-L674](https://github.com/opendatalab/MinerU/blob/4fe4bde114a23ee5dd637eae99b767f4669bf58c/docs/en/reference/output_files.md#L542-L674)：VLM 输出包含引用/参考块与 page/bbox，但模型后端的输出格式约束不同；不能把页面坐标自动解释成正确证据关系。文档已读，未运行。
- [mineru/backend/pipeline/pipeline_analyze.py L88-L140](https://github.com/opendatalab/MinerU/blob/4fe4bde114a23ee5dd637eae99b767f4669bf58c/mineru/backend/pipeline/pipeline_analyze.py#L88-L140)、[L157-L212](https://github.com/opendatalab/MinerU/blob/4fe4bde114a23ee5dd637eae99b767f4669bf58c/mineru/backend/pipeline/pipeline_analyze.py#L157-L212)：按页/批处理分析 OCR/版面并生成 middle_json；这是已得到 PDF 后的解析与定位节点，不提供学术发现或引用图。源码已读，未运行。

## 屏幕账本、增量与雪​​球节点

- [systematic-review-pipeline/srp/state.py L1-L5](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/srp/state.py#L1-L5)、[L21-L51](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/srp/state.py#L21-L51)、[L146-L188](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/srp/state.py#L146-L188)：配置/状态/决策 JSONL，原子写临时文件后替换；决策带 timestamp、record id、stage、reason、source、title、DOI，适合复跑与审计。源码已读，未运行。
- [systematic-review-pipeline/scripts/screen.py L1-L17](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/scripts/screen.py#L1-L17)、[L82-L160](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/scripts/screen.py#L82-L160)：重跑时按 record id 合并既有 screening.csv，统计 carried/new/dropped_decided；`--force` 才清空决定，源自过去重跑破坏决定的修复。源码已读，未运行。
- [Surveyer/src/surveyer/snowball.py L37-L157](https://github.com/IsmailHatim/Surveyer/blob/71f7d3ca35a5373cbb278b4d14feacb2d8fb66ec/src/surveyer/snowball.py#L37-L157)、[src/surveyer/models.py L33-L124](https://github.com/IsmailHatim/Surveyer/blob/71f7d3ca35a5373cbb278b4d14feacb2d8fb66ec/src/surveyer/models.py#L33-L124)：以种子取 OpenAlex references/citations，保留 requested/retrieved/API total、truncated/quota 计数；上限触发警告并保留已得候选。源码已读，未运行。
- [systematic-review-pipeline/tests/test_snowball.py L1-L6](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/tests/test_snowball.py#L1-L6)、[tests/test_update_check.py L1-L108](https://github.com/nayeem-hossain/systematic-review-pipeline/blob/4f8b3166aeb6d96e06c1943fb59159a40f277cda/tests/test_update_check.py#L1-L108)：测试把 snowball 与 query expansion 区分，并要求更新检查失败时安静回退；未运行测试。注：仓库名应为 `nayeem-hossain`，上条错误拼写 URL 已于本批扫描前修正待核。

## 研究产物关系与版本/更新边

- [OpenAIRE Graph API](https://graph.openaire.eu/docs/apis/graph-api/)：官方接口按 research-products、projects、persons、organizations 等实体查询，支持分页/cursor；适合把论文、数据、软件、项目作为关系发现层。官方文档已读，未调用 API。
- [OpenAIRE relationship types](https://graph.openaire.eu/docs/data-model/relationships/relationship-types/)：列出 `IsSupplementTo`、`IsRelatedTo`、`IsPartOf`、`IsDocumentedBy`、`IsDerivedFrom`、`IsCitedBy/Cites`、`IsReviewedBy/Reviews` 等及 harvested/inferred/user provenance。关系可扩展检索边，不能单独证明全文可得或关系语义正确。官方文档已读，未调用 API。
- [Scholix How-To v3 PDF](https://www.stm-researchdata.org/wp-content/uploads/2021/09/Scholix-How-To-v3.pdf)：描述数据-文献链接的捕获与发现交换；适合作为论文→数据/数据→论文的关系扩展线索。资料已读，未运行服务。
- [Crossref REST filters](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/)、[relations](https://www.crossref.org/documentation/schema-library/markup-guide-metadata-segments/relationships)：`has-update/is-update`、correction/retraction、full-text/version 过滤与 DOI/PURL/URI、preprint/translation/derived/references/data/software 关系；可单独保存 relation type 与来源。官方文档已读，未调用 API。
- [DataCite connecting to works](https://support.datacite.org/docs/connecting-to-works)：RelatedIdentifier 支持 `Cites/IsCitedBy`、`References/IsReferencedBy`、`IsSupplementTo`、`HasVersion/IsVersionOf`、`IsDerivedFrom` 等；可补足数据集/软件/版本关系。官方文档已读，未调用 API。

## 证据边界

以上固定提交源码均为“源码已读、项目未运行”；官方 API 页面与少量 HTTP probe 分开登记。GROBID/MinerU 能把已取得的 PDF 变成可定位文本/坐标，不能替代发现、实体关系判断或科学结论验证。OpenAIRE/Scholix/Crossref/DataCite 的 relation 是检索扩展证据，需保留 relation type、来源和未解析状态。


## K-Dense-AI/scientific-agent-skills @ 330c8e764435a731eff571e3efdda70b363d0792：脚本入口复核

- [skills/citation-management/scripts/search_openalex.py L57-L145](https://github.com/K-Dense-AI/scientific-agent-skills/blob/330c8e764435a731eff571e3efdda70b363d0792/skills/citation-management/scripts/search_openalex.py#L57-L145)：真实 Python 搜索节点；OpenAlex free-text、年份/type filters、cursor 分页、relevance/citations 排序，返回规范化 DOI/作者/摘要/OA flag。源码已读，未运行。
- [skills/citation-management/scripts/search_pubmed.py L27-L117](https://github.com/K-Dense-AI/scientific-agent-skills/blob/330c8e764435a731eff571e3efdda70b363d0792/skills/citation-management/scripts/search_pubmed.py#L27-L117)：NCBI E-utilities 节点；PubMed query、日期与 publication-type 条件、retmax 上限、key/email 可选及无 key 限速。源码已读，未运行。
- [skills/citation-management/scripts/doi_to_bibtex.py L14-L96](https://github.com/K-Dense-AI/scientific-agent-skills/blob/330c8e764435a731eff571e3efdda70b363d0792/skills/citation-management/scripts/doi_to_bibtex.py#L14-L96)、[validate_citations.py L240-L292](https://github.com/K-Dense-AI/scientific-agent-skills/blob/330c8e764435a731eff571e3efdda70b363d0792/skills/citation-management/scripts/validate_citations.py#L240-L292)：DOI URL 前缀清理、Crossref BibTeX 转换，以及 DOI/key/title 的重复检查；是标识/书目清洁节点，不是版本关系或引文图。源码已读，未运行。

## asreview/asreview @ 79d568212b2b0a78f9fd7be3c5117dfb890489f9：筛选循环入口

- [asreview/learner.py L67-L132](https://github.com/asreview/asreview/blob/79d568212b2b0a78f9fd7be3c5117dfb890489f9/asreview/learner.py#L67-L132)、[L167-L219](https://github.com/asreview/asreview/blob/79d568212b2b0a78f9fd7be3c5117dfb890489f9/asreview/learner.py#L167-L219)：`ActiveLearningCycle` 组合 querier/classifier/balancer/feature extractor/stopper，按标签结果取下一批并输出排序；Python library 节点，源码已读，未运行。
- [asreview/models/queriers.py L55-L82](https://github.com/asreview/asreview/blob/79d568212b2b0a78f9fd7be3c5117dfb890489f9/asreview/models/queriers.py#L55-L82)、[L110-L225](https://github.com/asreview/asreview/blob/79d568212b2b0a78f9fd7be3c5117dfb890489f9/asreview/models/queriers.py#L110-L225)：random/top-down/uncertainty/max 与混合策略；只审筛选排序，不推断学术发现或证据正确。
- [asreview/models/stoppers.py L38-L65](https://github.com/asreview/asreview/blob/79d568212b2b0a78f9fd7be3c5117dfb890489f9/asreview/models/stoppers.py#L38-L65)、[L109-L205](https://github.com/asreview/asreview/blob/79d568212b2b0a78f9fd7be3c5117dfb890489f9/asreview/models/stoppers.py#L109-L205)、[L217-L255](https://github.com/asreview/asreview/blob/79d568212b2b0a78f9fd7be3c5117dfb890489f9/asreview/models/stoppers.py#L217-L255)：安全全量/空集停止、N/quantile/两类/连续无关标签停止条件；停止规则不等于召回完备性证明。源码已读，未运行。

## langchain-ai/open_deep_research @ 1b7d2e80db9faa586165c60e09096dbbfd483a64：通用工作流入口复核

- [src/open_deep_research/deep_researcher.py L118-L175](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/deep_researcher.py#L118-L175)、[L699-L719](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/deep_researcher.py#L699-L719)：消息→research brief→supervisor→final report 的 LangGraph 节点与边；搜索源由配置/工具提供，未审学术适配器。
- [src/open_deep_research/deep_researcher.py L178-L349](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/deep_researcher.py#L178-L349)：supervisor 通过 `ConductResearch` 拆题，限制并行单元、聚合 raw notes、`ResearchComplete`/迭代上限决定退出；异常时结束研究阶段。源码已读，未运行。
- [src/open_deep_research/deep_researcher.py L365-L509](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/deep_researcher.py#L365-L509)、[src/open_deep_research/state.py L15-L95](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/state.py#L15-L95)：研究者取配置 tools/MCP，工具并行执行并安全捕获错误，达到 `max_react_tool_calls` 或完成标记后压缩；状态保留 brief、raw notes、compressed research、final report。源码已读，未运行；不把消息状态等同结构化证据 provenance。

## 语义边界修正

- PaperQA2 的固定源码审计覆盖 `PaperSearch` 的本地 Tantivy directory→MMR evidence 路径；旧发现表中的 “citation traversal” 未在该路径确认，应理解为答案引用元数据/上下文，不是跨论文 references/citations 图扩展。[tools.py L120-L210](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/agents/tools.py#L120-L210)、[search.py L399-L435](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/agents/search.py#L399-L435)。
