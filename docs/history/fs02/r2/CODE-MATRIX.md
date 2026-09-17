> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# 严格代码能力矩阵

仅已审代码范围；各格详细出处、限制见 JSON。

| 编号 | 能力 |
|---|---|
| D1 | 代码生成、改写、释义或扩展多个检索查询；仅清洗输入不计。 |
| D2 | 代码把通用查询/AST编译为平台特定检索语法；仅调度不计。 |
| D3 | 已审代码实际调用至少两个学术索引、仓储或馆藏取得候选；同源wrapper不计。 |
| D4 | 已审代码按学科、主题、venue、机构、语言等领域条件过滤；年份 alone 不计。 |
| D5 | 已审代码规范 DOI、PMID、arXiv 等标识并用于匹配/保留。 |
| D6 | 已审代码沿 references、citations、co-citation 或 snowball 关系产生候选。 |
| D7 | 已审代码从记录/标识解析到 OA/全文 URL 或文件；仅 OA flag、已给 URL 或下载校验不计。 |
| D8 | 已审代码保留页、section、bbox、字符 offset 或引文上下文等可复查定位；无位置的文本不计。 |
| D9 | 已审代码在已取得的全文或文档 corpus 内检索。 |
| D10 | 已审代码对书目记录去重、聚类或合并。 |
| D11 | 已审代码显式链接研究、版本、补充、派生、数据、软件、撤稿等产物关系；引用边单独计 citation_expansion。 |
| D12 | 已审代码按相关性/分数排序或以标签、active learning 做筛选。 |
| D13 | 已审代码把 source、query、revision、条件、错误或位置与输出关联保存。 |
| D14 | 已审代码有跨轮继续/停止、预算、截断或更新规则；单次分页/top_n 不计。 |
| D15 | 已审代码提供有界 CLI、API、MCP 或 library 节点。 |

| 候选 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 | D11 | D12 | D13 | D14 | D15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 当前 field-search（代码基线） | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 1 |
| K-Dense Scientific Agent Skills | 0 | 0 | 1 | ? | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | ? | 0 | 1 |
| openags/paper-search-mcp | 0 | 0 | 1 | ? | 1 | 0 | 1 | 0 | 0 | 1 | 0 | ? | 1 | 0 | 1 |
| vig-os/scitadel | ? | 0 | 1 | ? | 1 | 1 | 0 | 0 | 0 | 1 | ? | 1 | 1 | ? | 1 |
| FutureHouse PaperQA2 | 0 | 0 | 0 | ? | ? | 0 | 0 | 1 | 1 | ? | ? | 1 | 1 | 0 | 1 |
| AkariAsai/OpenScholar | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | 1 | 1 | ? | 1 | ? | 0 | 1 |
| AllenAI Paper Finder | 1 | 0 | ? | 1 | ? | 1 | 0 | 0 | 0 | ? | ? | 1 | ? | ? | ? |
| ustc-ai4science/academic-search | ? | 0 | 0 | ? | 1 | 0 | 0 | 0 | 0 | 1 | 1 | ? | 1 | ? | 1 |
| jonatasgrosman/findpapers | 0 | 1 | 1 | 1 | 1 | ? | 0 | 0 | 0 | 1 | ? | ? | ? | 0 | 1 |
| CoLRev-Environment/search-query | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| elizagrames/litsearchr | 1 | 0 | 1 | ? | ? | 0 | 0 | 0 | 0 | 1 | 0 | 1 | ? | ? | 1 |
| ASReview | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | 1 | ? | 1 | 1 |
| CoLRev bib-dedupe | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | ? | ? | 1 | 0 | 1 |
| nayeem-hossain/systematic-review-pipeline | ? | 0 | 1 | ? | 1 | 1 | ? | ? | ? | 1 | ? | 1 | 1 | 1 | 1 |
| veale/academic-mcp | 1 | 0 | 1 | 1 | 1 | 1 | ? | 1 | 1 | 1 | 1 | 1 | 1 | ? | 1 |
| LangChain Open Deep Research | ? | 0 | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | 0 | 1 | 1 |

[逐格来源和范围](CAPABILITY-MATRIX-CODE.json)
