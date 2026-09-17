> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS02 r2：方法空白的有界反证追踪

本批是对两条待确认空白的最后一轮定向反证：是否已有开源 interactive query refinement / Boolean feedback 系列，以及是否已有“controlled vocabulary → multilingual literature-search Boolean”转换器。查询空间限制为 4 个问题导向查询，再沿原始论文、作者主页和仓库链接追踪；“未找到组合”只表示本轮证据缺口，不表示全网不存在。

分类：

- **子方法源码**：固定提交并读了实际代码路径，可描述真实输入、输出和依赖。
- **仅论文/方法**：有原始方法出处，但本轮没有定位到可固定的实现。
- **组合未发现/未验证**：找到了组成部件，尚未找到一个公开实现把它们连成目标组合。

## 一、四个定向查询及结果

| 查询 | 原始结果 | 本轮判断 |
|---|---|---|
| open source interactive query refinement systematic review search refinement Boolean feedback GitHub | [searchrefiner 2018 原论文](https://scells.me/pdf/cikm2018_searchrefiner.pdf)、[searchrefiner 官方页](https://ielab.io/searchrefiner/)、[ielab/searchrefiner](https://github.com/ielab/searchrefiner) | 找到源码：交互式可视化、seed 验证和 PubMed/Medline Boolean 编辑；不是多语跨库 |
| systematic review searchrefiner Boolean relevance feedback query refinement open source | [Automatic Boolean Query Refinement 2019](https://bevankoopman.github.io/papers/scells2019refining.pdf)、[searchrefiner docs/tools](https://github.com/ielab/searchrefiner/blob/363e7776487b2a7012db8343735d56217c51a89e/docs/tools.md) | 找到方法论文和作者链接的 QueryLens/QueryFormulation；均是医学实现 |
| Scells automatic query formulation systematic review linked code GitHub dependencies conceptual objective | [Objective search-strategy 方法论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC7148214/)、[searchbuildR 论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC11795901/)、[IQWiG/searchbuildR](https://github.com/IQWiG/searchbuildR) | 找到 objective term-analysis 源码；它输出术语表/CSV，不负责多语或数据库 Boolean 生成 |
| multilingual controlled vocabulary to Boolean query translator SKOS literature search GitHub | [Skosmos](https://github.com/natlibfi/skosmos)、[JSKOS Server](https://github.com/gbv/jskos-server)、searchbuildR 和 SearchRefiner 的 MeSH 相关部件 | 找到词表浏览/mapping 与医学语法转换的分散组件；本轮未发现通用多语 SKOS→目标数据库 Boolean 转换器 |

查询结果中出现的 Bango 等以模型生成数据库字符串为主的工具，没有 controlled-vocabulary mapping 或可审计反馈链，故不作为本批方法证据。前一批已记录 ELSST、TheSoz、WOKIE、Skosmos 和 JSKOS 的领域词表/映射能力，本文件只补它们与 Boolean/feedback 组合的反证边界。

## 二、Scells/ielab 线：实际存在的源码子方法

### 2.1 SearchRefiner 主仓库：交互编辑、seed 验证、词项建议

原始论文 [searchrefiner: A Query Visualisation and Understanding Tool for Systematic Reviews](https://scells.me/pdf/cikm2018_searchrefiner.pdf)把工具定位为系统综述 Boolean query 的形成、可视化和理解界面。论文明确支持用 validation citations 检查已知相关引用、拖放式编辑 Boolean clause、按 clause 查看召回数量，并称当时支持 Ovid MEDLINE 和 PubMed。

仓库 [ielab/searchrefiner](https://github.com/ielab/searchrefiner) 的固定 master 提交是 363e7776487b2a7012db8343735d56217c51a89e；主仓库 LICENSE 是 MIT。本批读了固定提交的：

- api.go：/api/query2cqr 解析 PubMed/Medline 到 Common Query Representation，/api/cqr2query 反向编译；/api/keywordSuggestor 组合词项建议；ApiScroll 重新编译查询后走 Entrez 检索。
- plugin/queryvis/main.go：handleTree 把 raw query 用 transmute 转成 CQR，再以 combinator.NewShallowLogicalTree(..., relevant) 构建树；每个 atom 显示检索数和 seed 命中数，并把 query、语言和相关 PMIDs 记入历史。
- plugin/queryvis/tree.go：递归遍历 Boolean/atom 节点，把字段名称映射为 Title、Title/Abstract、MeSH Terms、Transliterated Title 等可读标签。
- web/query.html 和 plugin/queryvis/index.html：前端拖拽结构编辑器调用 /api/query2cqr、/api/cqr2query、/plugin/queryvis?tree=y；用户修改结构或字段后再重构 query。
- docs/tools.md：明确把 QueryVis、KeywordSuggest、AutoFormulate、QueryLens、AutoDoc 列为独立工具；它还给出作者的 linked repositories。

这个实现的“反馈”是 seed/相关 PMIDs 的可视化和用户重写反馈，不是自动学习一个下一轮外部数据库查询。ApiKeywordSuggestor 的两个实际来源也很具体：

1. getESWordRanking 从 Elasticsearch 的 PubMed 索引取 top pool，使用 RAKE 抽标题/摘要候选词、合并 MeSH headings，再用共现的 PMI/NPMI 排序；
2. getCUIWordRanking 先调用 MetaMap 找 CUI，再从 cui2vec 预计算相似概念取映射字符串；两个来源可 min-max 合并。

因此它是“检索结果统计/医学概念建议 → 用户选择 → CQR 结构编辑”的子方法，不能移植为任意语言的 controlled vocabulary translator。页面和 README 还注明即使本地运行也要建立本地 account，在线 demo 需要获批用户；配置需要 Entrez email/API key、PubMed/UMLS Elasticsearch、MetaMap/QuickUMLS 和本地资源。未登录、未运行。

固定依赖的原始代码链如下：

- [searchrefiner/go.mod](https://raw.githubusercontent.com/ielab/searchrefiner/363e7776487b2a7012db8343735d56217c51a89e/go.mod)：固定依赖包括 cqr、transmute、cui2vec、groove、guru、metawrap、quickumlsrest、toolexchange、Elasticsearch 等。
- [transmute 固定提交](https://github.com/hscells/transmute/tree/492a895bec30bc202a169a402da3a8aba6c7bf75)，commit 492a895bec30bc202a169a402da3a8aba6c7bf75；[README](https://raw.githubusercontent.com/hscells/transmute/492a895bec30bc202a169a402da3a8aba6c7bf75/README.md)将其定义为 PubMed/Medline query transpiler。实际读了 [parser/pubmed.go](https://raw.githubusercontent.com/hscells/transmute/492a895bec30bc202a169a402da3a8aba6c7bf75/parser/pubmed.go)、[parser/medline.go](https://raw.githubusercontent.com/hscells/transmute/492a895bec30bc202a169a402da3a8aba6c7bf75/parser/medline.go)、[backend/pubmed.go](https://raw.githubusercontent.com/hscells/transmute/492a895bec30bc202a169a402da3a8aba6c7bf75/backend/pubmed.go) 和 [backend/medline.go](https://raw.githubusercontent.com/hscells/transmute/492a895bec30bc202a169a402da3a8aba6c7bf75/backend/medline.go)。它把字段、MeSH explosion/noexp、通配符和 Boolean 结构映射到 PubMed/Medline 字符串，输入前提已经是这些语法之一，不接受 SKOS concept URI 或任意多语标签。
- [cqr 固定提交](https://github.com/hscells/cqr/tree/345896d4b48b9a067c2611c19ecdd487c4d87b78)，commit 345896d4b48b9a067c2611c19ecdd487c4d87b78；[commonqueryrepresentation.go](https://raw.githubusercontent.com/hscells/cqr/345896d4b48b9a067c2611c19ecdd487c4d87b78/commonqueryrepresentation.go)只有 Keyword、BooleanQuery、fields/options 等中间表示，LICENSE 是 MIT。它是语法数据模型，不是术语词表或翻译器。
- [cui2vec 固定提交](https://github.com/hscells/cui2vec/tree/d05e62281087231ca9244e0d9e13a3b095292902)，commit d05e62281087231ca9244e0d9e13a3b095292902；实际读了 [similarity.go](https://raw.githubusercontent.com/hscells/cui2vec/d05e62281087231ca9244e0d9e13a3b095292902/similarity.go)、[mapping.go](https://raw.githubusercontent.com/hscells/cui2vec/d05e62281087231ca9244e0d9e13a3b095292902/mapping.go)、[precomputed.go](https://raw.githubusercontent.com/hscells/cui2vec/d05e62281087231ca9244e0d9e13a3b095292902/precomputed.go)。它计算 CUI cosine/similar 并读取 CUI→常用字符串 CSV，MIT；知识域是 UMLS/医学概念。
- [groove 固定提交](https://github.com/hscells/groove/tree/4d808c22d939)，commit 4d808c22d939；README 称其为 query-analysis pipeline framework，LICENSE 是 MIT。QueryLens 和 QueryFormulation 的真正算法主要来自这里。

### 2.2 QueryLens：seed qrels 驱动的候选 query variation

[QueryLens 仓库](https://github.com/ielab/querylens)作者主页链接的固定 master 提交是 047f5925bbb00b964d80c68d4e67eb8946204258；固定树没有 README 或 LICENSE 文件，不能把仓库自身许可证假定为 MIT。实际读了 [main.go](https://raw.githubusercontent.com/ielab/querylens/047f5925bbb00b964d80c68d4e67eb8946204258/main.go)：

- wsEvent 接收 PubMed/Medline query，调用 transmute 转 CQR；
- 用用户 settings 中的 Relevant PMIDs 构建全部 score=1 的 qrels；
- 通过 groove 生成变体：logical operator replacement、adjacency range、MeSH explosion、field restrictions、MeSH parent、clause removal 和 cui2vec expansion；
- 对每个变体编译回 PubMed/Medline，用 Entrez/combinator.NewShallowLogicalTree 检索，计算 precision、recall、F1、NumRet；
- 用 QuickRankQueryCandidateSelector 和 plugin/querylens/balanced.xml 选择候选；主仓库代码把 selector 深度设为 1，最后把变体按 F1 排序返回。

这是真实的“seed set → 查询变体 → 目标语法重编译 → seed qrels 评估”的源码节点，比单纯筛选排序更接近 query refinement。但它仍是医学 MeSH、PubMed/Medline 和一轮候选改写；没有人文学科词表、翻译、跨语言字段适配，也没有把每轮用户相关性标签作为下一次外部库检索的长期状态。groove 中的 ReinforcementQueryCandidateSelector 在固定提交仍是 panic("implement me")，QueryLens 实际使用 QuickRank，不应误称为已实现 RL。

### 2.3 QueryFormulation：相关 PMIDs 到 objective Boolean query

[QueryFormulation 仓库](https://github.com/ielab/queryformulation)固定 master 提交是 5e7ca6d3c3efb88cba36e24a600d32c7ec42687b；固定树只有 README、index.html、main.go，没有 LICENSE 文件。实际读了 [main.go](https://raw.githubusercontent.com/ielab/queryformulation/5e7ca6d3c3efb88cba36e24a600d32c7ec42687b/main.go)：

1. 读取用户设置的 Relevant PMIDs，将其全部写成 score=1 qrels；
2. 建立 formulation.NewPubMedSet，用 Entrez 统计 title/abstract document frequency；
3. 建立 UMLS Elasticsearch client，调用 formulation.NewObjectiveFormulator，固定 F1 优化、最小文档数 30，并对 dev/population/MeSH 参数网格搜索；
4. ObjectiveFormulator.Derive 在 development/validation/unseen 切分上统计词频，按背景集合频率截断，映射到 UMLS CUI/语义类型，按 conditions/treatments/studyTypes 分类，再用相关文档覆盖位集过滤词项；
5. 构造 AND of OR category clauses，分别返回带 MeSH 和不带 MeSH 的两个 CQR query，再由 transmute 编译成 PubMed 或 Medline 字符串。

groove 的固定 [formulation/objective.go](https://raw.githubusercontent.com/hscells/groove/4d808c22d939/formulation/objective.go) 和 [formulation/formulator.go](https://raw.githubusercontent.com/hscells/groove/4d808c22d939/formulation/formulator.go)实际实现了 dev/validation/unseen、DF 过滤、MeSH k 的网格、qrels 评估和 query construction；[formulation/keywordmapper.go](https://raw.githubusercontent.com/hscells/groove/4d808c22d939/formulation/keywordmapper.go)把 CUI/MetaMap/UMLS 词映射成 CQR keyword。该线是“seed/已知相关文献 → objective Boolean query”的源码子方法，但依赖 Entrez、UMLS Elasticsearch、MetaMap/MeSH 和医学字段，不能作为跨语言通用转换器。

### 2.4 QueryLens/QueryFormulation 的算法出处是论文链而非一个统一包

- [Automatic Boolean Query Refinement 2019](https://bevankoopman.github.io/papers/scells2019refining.pdf)提出 Query Transformation Chain：对原始 Boolean query 反复应用候选变换，再由 candidate selector 选择改写。论文列出的六类变换包括 logical operator replacement、field restrictions、MeSH explosion、MeSH parents、clause removal 和 cui2vec expansion；这些在 QueryLens source wiring 中得到对应。
- [A Computational Approach for Objectively Derived Systematic Review Search Strategies](https://pmc.ncbi.nlm.nih.gov/articles/PMC7148214/)给出用一组 relevant studies 自动推导 query 的 objective 方法，并在 PubMed/40 个主题上评估；QueryFormulation 通过 groove 的 ObjectiveFormulator 复现这一家族，但把外部服务和 qrels 接入写进插件。
- [Systematic Review Automation Tools for End-to-End Query Formulation](https://ielab.io/publications/li-2020-sigir-autotool.html)把 AutoFormulate、QueryLens、QueryVis、AutoDoc 等放进 SearchRefiner 生态；其“end-to-end”是工具生态内的链接，不等于一个可跨语言、跨数据库的统一检索执行器。

### 2.5 其他 linked repo 的边界

SearchRefiner 的官方 docs/tools.md 还链接：

- [ielab/wordsuggestion](https://github.com/ielab/wordsuggestion)，固定 master 为 bec3bb8073210829bdffdfbb56be0a7cd5139ca9；[main.go](https://raw.githubusercontent.com/ielab/wordsuggestion/bec3bb8073210829bdffdfbb56be0a7cd5139ca9/main.go)只是把界面挂到 SearchRefiner，实际建议逻辑在主仓库 API 的 Elasticsearch RAKE/PMI 和 CUI2Vec 分支，没有独立多语实现。
- [ielab/autodoc](https://github.com/ielab/autodoc)，固定 master 为 92382709dc81f17da94c552010452b9ffe816abc；[main.go](https://raw.githubusercontent.com/ielab/autodoc/92382709dc81f17da94c552010452b9ffe816abc/main.go)解析 PubMed/Medline query，检查 field dictionary、keyword dictionary 和 CQR，返回拼写/字段错误。它做验证与报告，不做 vocabulary mapping 或 feedback。

这两个 plugin 仓库固定树同样没有 LICENSE 文件。主 SearchRefiner MIT 不能自动替代各分仓库的许可证审查；本批只记录源码行为，不安装或运行。

## 三、searchbuildR：源码存在，但只是 objective term analysis

[IQWiG/searchbuildR](https://github.com/IQWiG/searchbuildR)固定 main 为 482ee4552170b820340bd6b36f332375a7e3389d；README/仓库标为 GPL-3.0，DESCRIPTION 是版本 2.1。本批读了 [README](https://raw.githubusercontent.com/IQWiG/searchbuildR/482ee4552170b820340bd6b36f332375a7e3389d/README.md)、[DESCRIPTION](https://raw.githubusercontent.com/IQWiG/searchbuildR/482ee4552170b820340bd6b36f332375a7e3389d/DESCRIPTION)、[R/app_server.R](https://raw.githubusercontent.com/IQWiG/searchbuildR/482ee4552170b820340bd6b36f332375a7e3389d/R/app_server.R)、[R/prepare_freq_table.R](https://raw.githubusercontent.com/IQWiG/searchbuildR/482ee4552170b820340bd6b36f332375a7e3389d/R/prepare_freq_table.R)、[R/prepare_MeSH_table.R](https://raw.githubusercontent.com/IQWiG/searchbuildR/482ee4552170b820340bd6b36f332375a7e3389d/R/prepare_MeSH_table.R) 和 [R/adjacency.R](https://raw.githubusercontent.com/IQWiG/searchbuildR/482ee4552170b820340bd6b36f332375a7e3389d/R/adjacency.R)。

真实节点是：

- 从 EndNote/PubMed RIS 读入相关 references；
- 对 title/abstract 做 quanteda tokenisation、去标点/符号/数字，统计 term frequency、document frequency、coverage 和 z-score；
- 解析 MeSH、qualifier、starred MeSH，生成 MeSH/qualifier 的频率表；
- 用 adjacency 提取英文 stopword 过滤后的 skip-grams，供用户选择 proximity 词组；
- Shiny 表格让用户查看词在全文上下文，下载 freetext、MeSH、qualifier 和 keyword CSV。

app_server.R 的下载处理明确写 CSV；源代码没有把候选词自动拼成 database-ready Boolean query，也没有调用跨语言词表或把 MeSH 映射到非 PubMed 词表。它是新的源码子方法（“相关文献 → 客观高频/高 z 术语和词组 → 人工布尔式”），同时是对“controlled vocabulary→Boolean translator”组合未发现的正证边界。

## 四、controlled vocabulary 到 Boolean 的部件核对

本轮没有找到一个仓库能同时接受任意版本化、多语言 controlled vocabulary/SKOS concept，完成术语关系分层、词形/翻译变体生成，并输出 PubMed、Scopus、ERIC、CNKI、Wanfang/CQVIP 等各自字段语法。找到的部件各自停在不同层：

| 部件 | 固定/原始证据 | 已实现什么 | 没实现什么 |
|---|---|---|---|
| Skosmos | [固定 main b0367e2596946492c1b7d82b879b08ef5812bd13](https://github.com/natlibfi/Skosmos/tree/b0367e2596946492c1b7d82b879b08ef5812bd13)；MIT；README/API | SPARQL/SKOS 浏览、REST、Linked Data、语言/层级标签 | 不生成译词，不决定词表关系如何变成库语法 |
| JSKOS Server | [固定 main 1f9d00e4b310b875b9e16d722f6a424e99b64b95](https://github.com/gbv/jskos-server/tree/1f9d00e4b310b875b9e16d722f6a424e99b64b95)；MIT；README/API | concept/mapping 存取、infer/apply、mapping provenance | 不输出具体数据库字段、邻接、截词和布尔语法 |
| WOKIE | [固定 HEAD aa68c95ef878cb624c91db80f59523f1ea1033ac](https://github.com/FelixFrizzy/WOKIE/tree/aa68c95ef878cb624c91db80f59523f1ea1033ac)；MIT；前批已读源文件 | RDF/SKOS prefLabel 多服务翻译、置信度和层级上下文 | 不执行数据库检索，不按库语法输出 Boolean，不保证领域译词 |
| transmute | [固定 492a895bec30bc202a169a402da3a8aba6c7bf75](https://github.com/hscells/transmute/tree/492a895bec30bc202a169a402da3a8aba6c7bf75)；MIT；源文件已读 | PubMed/Medline query ↔ CQR ↔ 目标编译 | 输入必须是 PubMed/Medline query，不读取 SKOS/多语 URI |
| searchbuildR | [固定 482ee4552170b820340bd6b36f332375a7e3389d](https://github.com/IQWiG/searchbuildR/tree/482ee4552170b820340bd6b36f332375a7e3389d)；GPL-3.0；源文件已读 | MeSH/自由词/skip-gram 统计表和 CSV | 不做多语词表对齐或 Boolean 字符串 |
| SearchRefiner/QueryLens | [固定 363e777...](https://github.com/ielab/searchrefiner/tree/363e7776487b2a7012db8343735d56217c51a89e)；MIT；主 repo/plugin 源文件已读 | 医学 query visualization、seed 评估、MeSH/CUI2Vec 变体与 PubMed/Medline 编译 | 不接受任意 SKOS，不覆盖非英语数据库 |

其中 transmute 可被误看作“controlled vocabulary to Boolean translator”，但实际是已写好的 PubMed/Medline 语法转译器；SearchRefiner 的 MeSH/CUI2Vec 是医学知识库扩展，而非多语 SKOS 映射。Skosmos/JSKOS 是词表服务/映射服务，而非文献库查询适配层。四个查询中没有出现可把这些部件按上述顺序连起来、同时保存词表版本和每库 query provenance 的公开组合。

## 五、源码/论文/组合的最终分类

### 子方法源码

- SearchRefiner：可视化 Boolean clause、seed 命中统计、query2cqr/cqr2query、医学词项建议。
- QueryLens：seed qrels 下的 query transformation candidates、QuickRank 选择、PubMed/Medline F1/precision/recall 评估。
- QueryFormulation：Relevant PMIDs → objective term/semantic type/coverage filtering → CQR → PubMed/Medline Boolean。
- searchbuildR：relevant RIS → free-text/MeSH/qualifier/skip-gram 表 → CSV。
- transmute/cqr/cui2vec/groove：上面插件所依赖的语法中间表示、编译、医学概念相似度和 query-analysis/learning 基础库。

### 仅论文/方法

- SearchRefiner 2018 论文：交互式 query visualization、validation citations 和 training/feedback 设计出处。
- Automatic Boolean Query Refinement 2019：semantic/syntactic transformation chain、candidate generation/selection 和六类医学 query transformation。
- Objective formulation 2020：从 relevant studies 自动推导 Boolean search strategy 的研究评估。
- searchbuildR 论文：Shiny objective term-analysis 的方法和用户界面评估。
- Badami 2023（前批已记）：RL/多臂老虎机用研究者相关反馈增删 query terms；本轮仍未找到作者可固定的公开生产代码。

### 组合未发现/未验证

本轮没有证据证明存在一个公开实现同时完成：

1. 版本化多语 controlled vocabulary/SKOS concept 与领域 mapping；
2. 翻译、词形、复合词、音译和关系类型的可审计扩展；
3. 研究者相关反馈或 seed-set 迭代；
4. 针对多个非英语和英语学术数据库的字段级 Boolean 生成、执行和召回回写。

这不是说四个子方法不能被工程组合，而是本轮定向原始链接追踪没有找到“已经组合完成”的仓库；其中最接近的组合仍是医学专用的 SearchRefiner 生态，输入/输出语言、词表和远程服务都受限。

## 六、接入与验证边界

- SearchRefiner 主仓库和 transmute/cqr/cui2vec/groove 的许可证能从固定仓库读到；QueryFormulation、QueryLens、WordSuggestion、AutoDoc 分仓库固定树没有 LICENSE 文件，插件代码可追不代表重用条款已确认。
- SearchRefiner 的 Entrez、PubMed/UMLS Elasticsearch、MetaMap/QuickUMLS、QuickRank、CUI2Vec 资源和本地 account 是运行依赖；QueryFormulation 另需 UMLS Elasticsearch、MetaMap URL 和相关 PMIDs；这些是人工接入/权限事项。
- searchbuildR 的 GPL-3.0 与 quanteda、Shiny、revtools、R 运行时依赖已在 DESCRIPTION/README 看到；未安装。
- Skosmos/JSKOS 需要词表/SPARQL/MongoDB 服务，WOKIE 的多翻译器/LLM 可能需要 key；本轮仅读原始文档和代码，未登录、未安装、未运行。
- 本轮没有重新把 OpenAlex README 的旧 key 描述当成当前政策，也没有因缺 key 排除任何部件。

## 七、收口判断

本轮反证改变了“是否存在子方法”的结论：**子方法确实存在且有源码**，尤其 SearchRefiner/QueryLens/QueryFormulation 已实现医学领域的 query visualization、seed 评估和 Boolean 变体/生成；searchbuildR 已实现 objective term analysis。**组合是否存在仍只能记为本轮未发现/未验证**：没有找到任意多语 controlled vocabulary 到多数据库 Boolean 的完整开源实现，也没有找到把跨语言 mapping、直接 relevance feedback 和每库 query execution/recall logging 连起来的公开仓库。该结论是定向搜索后的证据边界，不是全网穷尽声明。
