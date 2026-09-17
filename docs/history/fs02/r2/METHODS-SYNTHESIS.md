> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS02 r2：METHODS-SYNTHESIS

本表只整理已读固定提交和已落盘来源，不把“能拼接”写成“已有全集成”。详细证据见 [TRADITIONAL-NODES.md](TRADITIONAL-NODES.md)、[EXPANSION-METHODS.md](EXPANSION-METHODS.md) 和 [DISCOVERY-CLOSURE-METHODS.md](DISCOVERY-CLOSURE-METHODS.md)。

## 方法关系

|能力族|实际重合|互补节点与限制|
|---|---|---|
|查询 AST：[search-query](https://github.com/CoLRev-Environment/search-query/tree/f6646075c19435a98af36eb4cfe3f34c36d5cc86)、[findpapers](https://github.com/jonatasgrosman/findpapers/tree/3b42b66befa0a64416258e7481201a0253f09e73)、[transmute](https://github.com/hscells/transmute/tree/492a895bec30bc202a169a402da3a8aba6c7bf75)|都做解析、正规化、字段/布尔结构转换|search-query 是带 linter、版本 translator 的通用树；findpapers 再做字段继承、各源 builder、runner；transmute 是 PubMed/Medline 语法↔CQR。三者都没有已验证的 CNKI/Wanfang/KCI/跨语 adapter。三仓库固定许可证均为 MIT。|
|术语候选：[litsearchr](https://github.com/elizagrames/litsearchr/tree/0c108e30f03c773123da2e6fe3f7cb6581d7c523)、[searchbuildR](https://github.com/IQWiG/searchbuildR/tree/482ee4552170b820340bd6b36f332375a7e3389d)|都从文献/词频产生候选词，不能替代最终人工概念分组|litsearchr 用共现图、中心性、closure，人工分组后组内 OR/组间 AND，并可做 title recall；GPL-3，非英语 Google Translate 节点需 key。searchbuildR 侧重 RIS 频率/df、MeSH/限定词、skip-gram CSV，GPL-3，没有 Boolean builder。|
|受控词表：[ELSST](https://elsst.cessda.eu/)、[Skosmos](https://github.com/natlibfi/Skosmos)、[JSKOS](https://github.com/gbv/jskos-server)、[WOKIE](https://github.com/FelixFrizzy/WOKIE)|都能补 label、层级或 mapping，和统计候选互补|ELSST 约 3,400 个社科概念、15 语言，CC BY-SA 4.0；Skosmos/JSKOS/WOKIE 固定仓库为 MIT。TheSoz 当前版本/许可证仍未知。WOKIE 可用本地 Argos，也可调用外部翻译器/LLM；它们不直接生成各库 Boolean，完整“词表→中文库式”未验证。|
|反馈：[SearchRefiner](https://github.com/ielab/searchrefiner/tree/363e7776487b2a7012db8343735d56217c51a89e)、[QueryLens](https://github.com/ielab/querylens/tree/047f5925bbb00b964d80c68d4e67eb8946204258)、[ASReview](https://github.com/asreview/asreview)|都可使用 seed/相关性信号减少人工搜索成本|SearchRefiner 是医学 query visualization、CQR 编辑和关键词建议；QueryLens 是以 seed qrels 生成/评估 PubMed 变体，QuickRank 只到浅层，且固定树无 LICENSE；二者依赖 Entrez/UMLS/MetaMap 等。ASReview 是已取回候选集内的 active-learning 筛选/排序，不改写数据库查询，不能找回漏检文献；它与前两者是串联关系，不是同一反馈器。Badami 的 RL 查询修正目前只有论文证据。|

## 中文、非英语和学科路由

[academic-search](https://github.com/ustc-ai4science/academic-search/tree/b9b692ed1334c858eb42d1f2710ccfcae1a43eb8) 固定许可证 MIT，强项是 RePEc/SSRN/OSF/CNKI 等路由、浏览器/API 编排、OA 下载、provenance 和保守去重；固定 source tree 没有这些站点的 HTTP adapter 或独立 query translator。万方是 PQ/Solr 式中文集合节点，CQVIP 是付费中文节点，KCI 有 REST key 与可先行的 OAI，ERIC 以 descriptor/教育类型过滤，RePEc 以 JEL、IDEAS 布尔式和 OAI/版本链工作；它们的字段、费用、权限和分页不能由通用 AST 自动假定。SSRN 当前适合网页 Fuzzy→Boolean 与 references 手工滚雪球，未确认公开 API。

## 可复用组合节点（按需，不部署）

1. 先用 ELSST/TheSoz/SKOS URI、litsearchr 共现词和 searchbuildR 频率表产生候选；人工定概念块、语言标签、exact/close/broader 关系，再交给 search-query/findpapers AST。
2. 将 AST 分别渲染为 PubMed/WoS/EBSCO 或 findpapers 已有源式；对万方、KCI、ERIC、IDEAS、CQVIP 另保留 source adapter/人工导出边界，记录语法版本、字段、总数和凭据状态。
3. 有 seed 后，先做引用/参考文献滚雪球；医学支路才接 SearchRefiner/QueryLens 做查询变体评估，结果集形成后再用 ASReview 排序筛选。

可复用的是“候选词/受控 URI → 人工概念块 → AST → 源特定式 → provenance/召回核验”的接口思想；已验证的开源项目仍是分段节点，尚未发现一条同时覆盖多语术语映射、中文/机构库执行、相关反馈和灰文去重的完整实现。许可证和服务条款也必须按组件、数据和远程 API 分开复核；固定树无 LICENSE 的 QueryLens/QueryFormulation 不继承 SearchRefiner 的 MIT。
