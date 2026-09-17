> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS02 r2：传统检索、非英语、馆藏与灰色文献节点补充

- 批次：2026-09-15；这是对 DISCOVERY-MAP.md 的独立增量，按能力族记录，不排名、不推荐、不声称穷尽。
- 范围：中文/韩文/日文/西语及其他非英语来源，教育/社科/人文检索，布尔式、引文/参考文献滚雪球、机构知识库和学位论文，外加四个固定 commit 的源码核查。
- 方法：没有安装、登录、付费或运行候选；固定 commit 的源码由 raw GitHub 文件阅读，官方服务只读文档/页面。源码已读、README/文档已读、未读代码分开写，API/机构/订阅权归用户手工接入。

## 一、四个固定 commit：可拆出的实际查询节点

### 1. CoLRev-Environment/search-query

- 地址：[仓库](https://github.com/CoLRev-Environment/search-query)，固定 commit f6646075c19435a98af36eb4cfe3f34c36d5cc86。
- 许可证：[固定 commit 的 LICENSE](https://raw.githubusercontent.com/CoLRev-Environment/search-query/f6646075c19435a98af36eb4cfe3f34c36d5cc86/LICENSE) 为 MIT，版权归 Gerit Wagner（2021）。
- 源码已读：search_query/query.py、parser.py、registry.py、serializer_structured.py；pubmed/translator.py、pubmed/v_1/translator.py；wos/translator.py、wos/v_1/translator.py；ebscohost/translator.py、ebscohost/v_1/translator.py；query_and.py、query_or.py、query_not.py、query_near.py 等。
- 实际节点：Query.create 将 AND、OR、NOT、NEAR/WITHIN、RANGE 和 term 建为类型化树；parser 按平台和版本解析，registry 动态登记 parser/list-parser、serializer/list-serializer、translator、linter 并选择最新版本；平台 linter 在解析后检查约束。PubMed、WoS、EBSCO translator 把通用字段移到平台字段，展开 title/abstract 等组合字段，压平或链和近邻结构，并能从特定语法回到 generic syntax；structured serializer 可将树保留为可检查的结构化查询。
- 可拆搜索节点：原始检索式 → 平台无关 AST → 平台约束检查 → 版本化语法转换 → 可复现的字符串/结构化输出；另有 list 解析和 generic/specific 双向转换。这适合在同一逻辑式上生成 PubMed/WoS/EBSCO 版本，也可仿照新增 CNKI/Wanfang/KCI 适配器。
- 本地/人工：解析与转换本身不要求 API；新增中文库适配器要实现对应字段、邻近/截断规则、serializer、translator、linter 并注册版本。当前仓库没有现成的 Wanfang/CQVIP/KCI translator，不能把通用 AST 误写成这些库已支持。

### 2. elizagrames/litsearchr

- 地址：[仓库](https://github.com/elizagrames/litsearchr)，固定 commit 0c108e30f03c773123da2e6fe3f7cb6581d7c523。
- 许可证：固定 commit 没有根目录 LICENSE；[DESCRIPTION](https://github.com/elizagrames/litsearchr/blob/0c108e30f03c773123da2e6fe3f7cb6581d7c523/DESCRIPTION) 明示 GPL-3，不能按缺失 LICENSE 推断为 MIT。
- 源码已读：R/term_selection.R、R/write_scrape_test_searches.R、R/generic_text_functions.R、R/import_and_clean_data.R，以及 vignette 中的完整工作流。
- 实际节点：extract_terms 从初步检索文本中抽取 fakerake/tagged 词和 n-gram；create_dfm/create_network 生成文档-词矩阵和加权共现 igraph；make_importance 支持 strength、eigen centrality、alpha、betweenness、hub、power 等中心性；find_cutoff/get_keywords/reduce_graph 缩减候选词图。人工把候选词分进概念组后，write_search 在组内 OR、组间 AND，处理精确短语和 closure（left/right/full/none），可输出各语言式并用 gold-standard title recall 检查召回。
- 非英语节点：get_languages 从 Ulrich 数据库得到期刊语言；非英语组调用 Google Translate API 的 translate_search，需要 API_key，英语词可用 SnowballC stemming。英文/非英文翻译、短语加引号、冗余词删除、检索式生成是分开的节点，不应写成“无 key 的多语搜索”。
- 灰色文献节点：scrape_hits 分派 scrape_oatd、scrape_ndltd、scrape_openthesis，属于旧式 HTML 抓取器，维护状态、站点条款与当前页面兼容性均未验证；import_results 读取 Bib/RIS，remove_duplicates 走 synthesisr 的精确/字符串/模糊去重。
- 本地/人工：R 包、词网和字符串生成可在本地做；Google Translate key、Ulrich 数据和旧 ETD 页面访问由用户判断。没有运行 scraper，也没有把旧站点当成当前 API。扩展可接 SPIDER/PEO 概念组、韩文/日文词形工具，或将 thesis scraper 替换成 EThOS/NDLTD/机构 OAI。

### 3. ustc-ai4science/academic-search

- 地址：[仓库](https://github.com/ustc-ai4science/academic-search)，固定 commit b9b692ed1334c858eb42d1f2710ccfcae1a43eb8。
- 许可证：[固定 commit 的 LICENSE](https://raw.githubusercontent.com/ustc-ai4science/academic-search/b9b692ed1334c858eb42d1f2710ccfcae1a43eb8/LICENSE) 为 MIT，版权信息为 Chengmingyue（2026）。
- 源码/文档已读：固定 commit 的 SKILL.md、references/disciplines/economics-social-science.md、references/disciplines/humanities-law.md、references/site-patterns/cnki.net.md、references/workflows/systematic-review.md、scripts/academic-records.mjs、scripts/oa-pdf-download.mjs。
- 实际节点：SKILL 按学科路由 RePEc/NBER/SSRN/OSF、学术搜索/馆藏/领域库、CNKI，再以 OpenAlex/Crossref 补元数据；要求保留原始 query、字段、时间窗、条数和失败原因。academic-records.mjs 规范 DOI、arXiv、PMID，校验 citation sources/field_sources/provenance；dedupeRecords 用 DOI/base arXiv/PMID 连通分量合并，标题相似只标为 possible duplicate，不自动合并，并记录版本、冲突和来源索引。流程文档要求每个数据库写自己的语法，提供 dry-run、去重和人工 include/exclude/maybe 审计。
- 重要边界：固定 commit 的 source tree 没有 OpenAlex/CNKI/SSRN 等 HTTP search adapter，也没有独立 query translator；它是宿主路由、浏览器/API 编排、下载验证和保守去重节点。不能仅凭 SKILL.md 把它当作已实现的中文或经济学 API 客户端。
- 本地/人工：记录校验、去重和 OA PDF 链接处理可本地运行；API、Chrome/CDP 动态页面、机构订阅、CNKI/WoS/Scopus 导出需要人工接入。它明确禁止绕过 paywall，未验证站点 pattern 要重新检查。

### 4. jonatasgrosman/findpapers

- 地址：[仓库](https://github.com/jonatasgrosman/findpapers)，固定 commit 3b42b66befa0a64416258e7481201a0253f09e73。
- 许可证：[固定 commit 的 LICENSE](https://raw.githubusercontent.com/jonatasgrosman/findpapers/3b42b66befa0a64416258e7481201a0253f09e73/LICENSE) 为 MIT，版权归 Jonatas Grosman（2020）。
- 源码已读：core/query.py、query/parser.py、query/normalizer.py、query/propagator.py、query/validator.py、query/builder.py；builders/arxiv.py、ieee.py、openalex.py、pubmed.py、scopus.py、semantic_scholar.py、wos.py；runners/search_runner.py。
- 实际节点：输入先把宽松的裸词/引号词正规化为 [term] 形式，再验证括号、空词、过滤码、连接词、NOT 位置和通配符最小长度；解析器构建 ROOT/TERM/CONNECTOR/GROUP 树。ti、abs、key、au、src、aff、tiabs、tiabskey 等过滤字段由 propagator 向子节点传递，内层显式字段优先；builder 再把树展开为执行计划。OpenAlex builder 把 title/abstract/author/affiliation/tiabs 映射到 filter 字段，OR 可展开 DNF，AND NOT 保持分组以避免错误分配；PubMed/Scopus/WoS 各自输出平台标签和连接词。runner 将 API keys、email、日期后过滤、DOI/标题年份去重和 enrichment 分开。
- 可拆搜索节点：统一过滤式 → 规范化/校验 → 字段继承 → 数据库-specific conversion → 多数据库执行计划 → DOI/题名年份去重。支持 arXiv、IEEE、OpenAlex、PubMed、Scopus、Semantic Scholar、WoS；没有 CNKI/Wanfang/KCI/SSRN/ERIC builder。
- 本地/人工：query parser/builders 可本地使用；IEEE、Scopus、PubMed、OpenAlex、S2、WoS 的 key/email 和服务条款按 runner 参数由用户手工接入。OpenAlex 参数名不能当成当前政策证据，见第六节。

## 二、中文、韩文、教育与经济学来源

### 1. 万方：官方 wfdata-open-skills（地图已有名称，本批补 API/query 细节）

- 地址：[wanfangdata/wfdata-open-skills](https://github.com/wanfangdata/wfdata-open-skills)，本批固定 HEAD bc254b2f9c70bc3fc0ada58e6b1ed583a2c2cf04；本批读了 wfdata-search/SKILL.md、references/api-catalog.md、README，未读 scripts/wf_data_query.py 和 wf_data_vector_search.py。
- 实际节点：POST JSON 到 <https://api.wanfangdata.com.cn>；核心 openwanfang/getQuery 接收 PQ/Solr 式 query、collection、fq 类过滤、returned_fields、排序和 start/rows。示例是 (人工智能 AND 医学) AND PublishYear:[2020 TO *]。资源族不仅期刊/学位/会议/专利，还包括法规、科技成果、标准、报告、地方志等集合；getDoc 通过 collection/id 回取详情。vectorsearch/query 是可选的 SentenceVec 自然语言向量入口，和传统 Boolean query 分开。
- 可拆搜索节点：中文词/字段式 → collection/type 选择 → fq 年份/文献类型/机构 → 排序分页 → getDoc 详情/全文路径；学位、会议、报告和地方志可作为人文/教育灰文支路。
- 人工/本地：SKILL 明示 X-Ca-AppKey 与 Authorization: APPCODE，应用 key/APPCODE 必须由用户申请；本地只是 HTTP JSON 调用。根目录固定 commit 未见可确认开源 LICENSE，README 仅有“Copyright © 万方数据”，按版权/服务条款处理，不假定可再许可。

### 2. CQVIP：literature-search-mcp

- 地址：[xusenlin/literature-search-mcp](https://github.com/xusenlin/literature-search-mcp)，固定 HEAD 4bf5994a710df4818cef3c57846331121d12e0fb；本批读 README，未读 Go 源码；README 未呈现可确认的 LICENSE。
- 实际节点：Go stdio MCP 暴露 search_cqvip（query、language=zh、固定 50 条可下载记录、CQVIP native ID）、search_pubmed、search_semantic_scholar、search_arxiv、search_all、get_paper_detail。search_all 特意不含 CQVIP，因为 CQVIP 按调用收费；CQVIP 使用 Bearer key 和 adv-search-jkhh endpoint。
- 可拆搜索节点：中文 query → CQVIP 结果/原生 ID → 详情回取；把付费中文库作为独立 source，和免费 PubMed/S2/arXiv 并行，避免总聚合器一次次触发费用。
- 人工/本地：CQVIP_API_KEY、付费/额度和服务条款必须用户处理；本地 Go 1.24+ 只是运行时。未运行，不把 README 的“支持”当成字段/限额已验证。

### 3. KCI：REST Open API + OAI-PMH MCP

- 官方入口：[KCI Open API](https://www.kci.go.kr/kciportal/po/openapi/openApiConnSearch.kci)；社区实现：[rubatoyd/KCI_openAPI](https://github.com/rubatoyd/KCI_openAPI)，固定 HEAD cc6aafbbabb1057e60545de6125d90d4f045c47f，README 明示 MIT。
- 本批读了固定 HEAD README/接口文档，未读实现代码。REST 搜索字段包含 title、author、journal、institution、affiliation、keyword、abstract、dateFrom/dateTo、DOI、year/years、displayCount（最大 100）和 sort；REST key 由用户申请。OAI endpoint 是 …/po/openapi/openApiSearch.kci 与 …/oai/request 两条分支，后者可按 set/date range harvest，不需 REST key。
- MCP/CLI 工具：kci_status、kci_search、kci_detail、kci_references、kci_journal_citation、kci_harvest、kci_collect。collect 在有/无 key 时路由 REST/OAI；title/keyword 轴取并集并保留各轴 totals。articleSearch 不给完整 keyword/ISSN/UCI，要按 paper id 逐篇 detail；referenceSearch 单次最多 100，需排序 sweep 并记录 total_mismatch/truncated。OAI 引文图只覆盖有 arti_id 的 KCI 索引引用，书籍、报告、外文参考可能无 ID。
- 可拆搜索节点：韩文题名/关键词轴并集 → REST 字段/年份排序 → OAI 增量 harvest → detail 补全 → references/citation journal 网络；适合韩国教育/人文文献和非英语引文滚雪球。
- 人工/本地：REST KCI_API_KEY/配额是人工依赖；OAI 可能先用无 key 的元数据 harvest。端点和条款仍需实测，未登录或运行。

### 4. ERIC：受控词表 + 教育灰文献

- 官方资料：[ERIC/IES 入口](https://ies.ed.gov/use-work/education-research-database-eric)、[Thesaurus](https://eric.ed.gov/default.aspx?ti=0)、[API 示例 PDF](https://eric.ed.gov/pdf/Using_ERIC_API_for_Research_Topics.pdf)。官方库自 1966 年起收录教育期刊与非期刊记录，包括书籍、综述、报告和政策材料；Thesaurus 提供 descriptors、synonyms、dead terms。
- MCP 候选：[SMABoundless/eric-mcp-server](https://github.com/SMABoundless/eric-mcp-server)，固定 HEAD 2c09881bb000e06fdd4d801765e5770ed98c136b，README 明示 MIT；本批读 README，未读 server.py。工具 eric_search 支持 keyword/title/author/descriptor/source 及 peer-reviewed、education-level、publication-type 等过滤；eric_get_record、eric_thesaurus_search、eric_author_search 和 RIS/BibTeX 导出形成补充节点。
- 实际查询思路：subject:autism AND subject:"teaching methods" AND publicationdateyear:2019 一类字段式；先 Thesaurus descriptor，再把 free text、peer-review、教育阶段、出版物类型和年份组合。灰文可按报告/政策/非期刊类型单独保留。
- 人工/本地：项目 README 声称无需 key，但 ERIC 当前 API endpoint、速率和条款未由本批代码实测；把“无需 key”标为候选说明，需用户或后续探测确认。MCP 本地运行时和 ERIC 服务访问分别记录。

### 5. RePEc/IDEAS：JEL/工作论文/元数据 OAI

- 官方：[IDEAS search syntax](https://ideas.repec.org/search.html)、[RePEc API 说明](https://ideas.repec.org/api.html)、[RePEc OAI gateway](https://oai.repec.org/)；本批没有读代码，仅读官方文档。
- 实际节点：IDEAS 支持 + 表示 AND、| 表示 OR、~ 表示 NOT、括号和引号短语，并提供自动同义词/stemming；可从 JEL code、series、journal、作者和 working-paper 系列浏览。RePEc API 不是开放即用的搜索 API，申请需提交身份、用途、数据、IP、频率和结束日期，且有节流与有限 access code；官方更建议对规则性数据使用 OAI、rsync 或 datasets。OAI/归档元数据可按日期/set 增量收集。
- 可拆搜索节点：自然语言问题 → JEL/主题词扩展 → IDEAS Boolean 浏览找 seed → RePEc series/author 追踪 → OAI/rsync 增量元数据 → DOI/工作论文版本合并。适合经济学、教育经济学和政策研究，不等同于全文数据库。
- 人工/本地：IDEAS 网页探索可能直接使用；RePEc API 申请、IP/频率和大规模数据权限由用户处理；OAI harvester 可本地实现。未声称 RePEc 有一个可匿名调用的“搜索 API”。

### 6. SSRN：Fuzzy → Boolean 两阶段网页检索

- 官方入口：[SSRN](https://papers.ssrn.com/)，功能说明：[2026 Advanced Search](https://blog.ssrn.com/2026/03/16/ssrns-new-advanced-search-makes-finding-papers-easier-and-faster/)；本批未发现可确认的公开 SSRN API，也未读代码。
- 实际节点：Advanced Search 可在 title、abstract、keywords、full text 选择范围，并独立限制 author/date；2026 更新加入 Fuzzy Search 与 Boolean Search。Boolean 使用 AND/OR/NOT/括号，推荐先用模糊搜索探索词形，再用 Boolean 在 title 或 title+abstract+keywords/full text 上收窄；摘要页的 references/citations 可作为手工滚雪球入口。
- 人工/本地：基础网页发现不等于有可编程接口；提交、保存和机构功能的账号依赖要另行判断。当前没有把 SSRN 当成可直接由本地 runner 批量抓取的后端，后续需追官方 API/导出政策和引用链接访问。

## 三、SPIDER、定性筛选与灰色/学位注册库

### 1. SPIDER 实施现状

- 方法出处：[Cochrane qualitative searching](https://training.cochrane.org/resource/question-formulation-and-searching-qualitative-evidence) 讨论 SPIDER、SPICE、PerSPEcTiF、RETREAT 等问题框架；Cooke、Smith、Booth 的 SPIDER 论文 DOI 为 [10.1111/j.1471-1842.2012.01193.x](https://doi.org/10.1111/j.1471-1842.2012.01193.x)，字段是 Sample、Phenomenon of Interest、Design、Evaluation、Research type。
- 开源实现：[Kishaz/systematic-literature-review](https://github.com/Kishaz/systematic-literature-review)，固定 HEAD 3fa3b5b7076215a0185f2e1441c03b33fad54e7f；README 与固定 commit LICENSE（MIT）已读，代码未读。README 明示 framework: SPIDER，并将概念块按组内 OR、组间 AND 生成；protocol.yaml 为每个 source 保存不同语法的 query，slr search --dry-run 可查看将发送的式子，slr run 做多库检索、缓存、去重和审计，screen/report 生成人工筛选与 PRISMA 流程。
- 现有缺口：Kishaz 提供框架校验、按数据库写式、dry-run、去重和筛选审计，但没有发现专门的 SPIDER synonym/qualitative-design 词库或可替代信息专家的字段展开器；搜索块仍需人工填写。litsearchr 的 term network 可补候选词，CoLRev/findpapers 可补语法转换，这三者是可组合的独立节点。

### 2. EThOS（英国学位）

- 官方：[British Library EThOS](https://www.bl.uk/collection/ethos)。当前平台恢复，保存超过 650,000 条英国博士论文元数据，超过 400,000 条含开放下载链接；平台通常链接回大学 repository，不要求用户登录，并提供可下载的 CSV 书目数据。
- 可拆搜索节点：题名/作者/机构/年份检索 → 论文 metadata → repository/OA link → CSV 批量分析；适合教育、人文、社会科学学位灰文。没有代码阅读；全文开放状态、链接可用性和版权仍按记录判断。

### 3. NDLTD：新 Union Archive 与旧 Global Search 状态分开

- 当前档案：[NDLTD Union Archive](https://ndltdunion.cs.uct.ac.za/portal/)，页面显示持续收集世界各机构 ETD 元数据并提供给 service providers；[ETD Guide](https://etdguide.ndltd.org/) 说明以 OAI-PMH、ETD-MS 和 repository registration 参与 harvest。
- 状态校正：2026 年 6 月 NDLTD 讨论明确称旧的 union.ndltd.org/search.ndltd.org Global ETD Search 因安全、稳定性和基础设施问题下线；不能沿用旧地址“可搜索”结论。当前 archive portal 仍显示近期提交和机构统计；最终搜索应走各提供商（如 OATD、BASE、CORE、LA Referencia）或直接机构 OAI。
- 可拆节点：机构 OAI-PMH endpoint/ETD-MS → 增量 harvest → provider/union archive → 学位题名、语言、机构和年份过滤 → OA link。没有代码阅读；机构 OAI 配置及大规模 harvest 需后续验证。

### 4. OSF Registrations、REES、OpenDOAR 与 OpenGrey

- [OSF API](https://developer.osf.io/) 是 JSON:API REST，支持 pagination/filter/sparse fieldsets；[Registrations](https://help.osf.io/article/330-welcome-to-registrations) 是带时间戳、只读、可公开发现并可分配 DOI 的预注册/协议实体。地图已有 OSF；本批补出其作为研究计划、未发表研究和灰文注册节点。公开读取与私有 OAuth 权限分开。
- [REES](https://www.icpsr.umich.edu/sites/rees/home) 是教育/社会科学 efficacy/effectiveness studies registry，覆盖 randomized、quasi-experimental、RD、single-case，记录问题、设计、样本、结局和分析计划，支持搜索/导出；[user guide](https://sreereg.icpsr.umich.edu/sreereg/userguide) 显示安全操作需要免费的 ICPSR Researcher Passport。本批未发现公开 API。
- [OpenDOAR developers](https://opendoar.ac.uk/help/developers) 的新 API 需 active API key；页面曾有截至 2026 年 7 月暂停发新 key 的通知，当前 2026-09 状态未确认。它更适合发现机构 repository/OAI endpoint，不应当写成无 key 的全文搜索 API。
- OpenGrey 已关闭并仅保留历史 archive 入口；灰色文献没有单一稳定总库，仍需机构库、学位库、会议和项目/政策页面分源搜索。本批不把旧 OpenGrey URL 当可运行节点。

## 四、人文馆藏、机构 OAI 与多语书目

### 1. CORE、BASE、LA Referencia（地图已有 CORE/BASE；补接口/区域细节）

- [CORE API](https://core.ac.uk/services/api) 聚合机构/学科 repository、预印本和 OA/hybrid journal 的 metadata/full text，并有 OAI resolver（https://oai.core.ac.uk/<oai-identifier>）；免费低速访问与注册 key/更高额度分开，服务条款和全文 license 不能从 OA 标记推断。地图已有 CORE，本批补出 OAI identifier→repository resolver、repository discovery、metadata/full-text 双层节点。
- [BASE OAI interface](https://oai.base-search.net/) 收集 3,000+ document servers，base_dc 含 language、OA、rights、DDC、collection 等字段，可按 set:oa:1、rightsnorm:CC-BY 等过滤。OAI 接口 IP restricted，非商业项目需申请并登记 IP；网页端可浏览不等于机器接口开放。地图已有 BASE，本批补出 OAI harvest、rights/language/document-type 过滤。
- [LA Referencia](https://www.lareferencia.info/en/) 覆盖拉丁美洲与西班牙开放科学节点，首页明确有 article/report/doctoral thesis/master thesis 和国家节点；其开源 [lareferencia-platform](https://github.com/lareferencia/lareferencia-platform) README 描述 OAI-PMH harvesting、metadata validation/transformation、实体 REST、thesis contexts 和多语言界面。本批读官方/README，未读代码或固定 release；可作为西语/葡语机构库和学位检索扩展。
- 可拆节点：OAI endpoint registry → incremental harvest → language/type/rights/subject facets → repository/record resolver → DOI/OAI identifier dedupe；对人文馆藏可保留无 DOI 的书、章节、学位和档案记录。

### 2. WorldCat/OCLC 书目匹配

- 代码候选：[OCLC-Developer-Network/pyMetadataAPIRecordFind](https://github.com/OCLC-Developer-Network/pyMetadataAPIRecordFind)，README 已读，代码未读；输入 MARC/Excel/CSV/TSV，优先 ISBN，缺失时按 title/author/publisher/date 回退，format 映射 itemType/itemSubType，并可选 LCSH、MARCXML 和 full bibliographic record。README 声明 Apache 2.0，但本批未独立核对 LICENSE 文件。
- 实际节点：本地书目规范化 → WorldCat Metadata API brief-bibs 匹配 → OCLC number → 详情/MARCXML/LCSH 回取 → 题名/作者/出版年冲突保留。适合人文图书、章节和多语馆藏，不是论文全文搜索器。
- 人工/本地：OCLC API key/secret、OAuth2 和速率延时由用户处理；本地匹配脚本可单独运行。不能把 WorldCat 的机构可见性、借阅权限当成开放全文。
- 相关 R 工具：[NYPL/libbib](https://github.com/NYPL/libbib) 用 WorldCat API，并含书目代码/索书号到主题处理；本批仅发现，未读代码/固定提交。

### 3. HathiTrust、DPLA、Europeana、Gallica、NDL Search

- [HathiTrust Volume API](https://github.com/hathitrust/catalog/wiki/Volume-API) 支持 brief/full JSON，按 htid、OCLC、ISBN、ISSN、LCCN、recordnumber 等字段查询；多个值可用 | 表示 OR，不同字段用 ; 表示 AND，full 可给 MARC-XML。其 [hathifiles](https://github.com/hathitrust/hathifiles) 可作为批量 metadata extract；本批未读代码，访问/版权字段需逐记录判断。
- [DPLA developer resources](https://pro.dp.la/developers) 提供编程搜索和馆藏 metadata；API key/使用条款需按当前开发者页面申请，地图未展开其馆藏字段。适合美国地方档案、图像、书籍等人文长尾。
- [Europeana API](https://api.europeana.eu/en) 覆盖欧洲文化遗产 metadata/search/import，要求免费 Europeana account 获取 key；把 item metadata、IIIF/thumbnail 和 rights 作为分离字段。
- [Gallica IIIF API](https://www.data.gouv.fr/dataservices/api-gallica-iiif) 提供 BnF Gallica 的 IIIF Presentation/Image、metadata 与图像/OCR 访问；描述 metadata 使用法国开放许可，但数字对象与重用限制仍按记录核对。适合法语人文和原始材料，不是一般论文索引。
- [NDL Search API](https://ndlsearch.ndl.go.jp/en/help/api/)（日本国立国会图书馆）支持 SRU、OpenSearch、OpenURL 与 OAI-PMH harvest；非营利使用在遵守 metadata 条款时可能无需申请，商业/持续高量访问可能需要申请，且有并发限制。它是日文图书、期刊、学位和人文学术馆藏的入口。

## 五、API/机构依赖与普通本地环境分离

| 依赖类型 | 本批候选 | 用户人工处理项 | 普通本地可先做的部分 |
|---|---|---|---|
| 应用 key/付费 | 万方 X-Ca-AppKey/APPCODE；CQVIP_API_KEY（按调用收费）；KCI REST key | 申请、额度、合同、条款 | 查询式构建、分页计划、结果 schema |
| 账户/key/速率 | OpenAlex、CORE、DPLA、Europeana、WorldCat/OCLC、RePEc API、BASE OAI IP | 账户、免费 key、IP 白名单、机构 OAuth/订阅 | parser、OAI/JSON 客户端、缓存、去重和审计 |
| 机构订阅或导出 | WoS/Scopus/Embase/CINAHL、CNKI 当前页面、部分 WorldCat/SSRN 功能 | 机构登录、人工导出和使用许可 | 导入 RIS/Bib/CSV、字段转换和 provenance |
| 公开/较低门槛 | KCI OAI、EThOS、NDL Search、OSF public registrations、Gallica IIIF | 仍需遵守 robots/metadata/版权/频率 | OAI harvest、SRU、IIIF manifest、记录链接 |
| 当前未知 | SSRN 公开 API、ERIC 当前 API 端点/配额、OpenDOAR key 发放、Wanfang/CQVIP 字段/ToS、LA Referencia 公共查询接口 | 后续人工或最小探测 | 先设计 source adapter，不把未知接口写成已通 |

### OpenAlex 当前政策校正

- [当前 authentication 帮助](https://help.openalex.org/api/authentication/)与[pricing](https://help.openalex.org/access/pricing/)说明基础/少量查询可无 key，免费账户/key 提高预算和限额，超过免费额度才进入付费；大规模/生产使用应有账户/key。官方 blog 的措辞更偏向生产请求需要 key，页面之间有表述差异。
- 因此 findpapers 的 openalex_api_key 参数、academic-search 的 contact email/配置和旧 README 不能单独证明“当前必须 key”或“永远无 key”。本地 Python/R/Go/Node/parser 环境和远程访问权限必须分栏；探索量可先无 key，生产规模由用户处理账户、速率和费用。

## 六、能力族、未知项与下一批

### 本批新增或补实的独立能力族

1. 平台无关 Boolean AST、字段继承、近邻和 generic/specific 双向转换（CoLRev）。
2. 从 seed 文本到 n-gram 共现图、中心性截断、多语 Boolean 组装、gold-standard recall（litsearchr）。
3. 规范化过滤树到多数据库执行计划，以及 DOI/题名年份连通分量去重（findpapers）。
4. 中文资源型 PQ/Solr query（万方）、韩文 REST+keyless OAI 双轨及 detail/reference/citation 补全（KCI）、教育 descriptor+灰文过滤（ERIC）。
5. RePEc 的 JEL/series/working-paper→OAI/rsync 元数据路线与 SSRN Fuzzy→Boolean 两阶段检索。
6. SPIDER 作为配置/筛选框架而非一键词表，机构 OAI/ETD harvest，REES/OSF 研究注册和 BASE/CORE/LA Referencia 区域聚合。
7. WorldCat MARC/ISBN 匹配、Hathi 书目/标识字段、DPLA/Europeana 聚合、Gallica IIIF、NDL SRU/OAI 的人文书目与原始材料节点。

### 仍未知或只到文档层

- Wanfang/CQVIP/KCI/ERIC 当前字段、分页、速率和错误响应尚未运行确认；CQVIP 费用、KCI key quota、万方版权和 fulltext 许可需人工核查。
- SSRN 是否有公开、可批量使用且允许系统综述的 API/导出接口未找到；引用页的可编程性也未验证。
- BASE OAI 的 IP 开通、CORE API 当前免费速率、DPLA/Europeana/WorldCat key、OpenDOAR 当前 key 状态尚未接入。
- Kishaz、ERIC MCP、CQVIP MCP、Wanfang scripts、LA Referencia、Hathi/WorldCat 工具未做源码运行；当前记录的“源码已读”只对明确列出的固定文件生效。
- SPIDER/PEO 的定性设计词库、非英语词形/主题词映射、机构 OAI endpoint 质量和跨语言去重仍缺少固定实现与小样本验证。
- DART-Europe 已于 2025-02 永久关闭，应继续查其替代聚合器；NDLTD 旧 Global Search 已下线，但新 Union Archive/服务提供商的分发边界仍需核对。

### 下一批仍可能产生新方向

仍有新方向，建议优先追：大学/国家 OAI endpoint 与 DSpace/EPrints harvest 实现；KCI/Wanfang/CQVIP/ERIC 的可公开字段式与导出格式；日文 J-STAGE/NDL、韩文 RISS、法语 HAL/Gallica、西语/葡语 LA Referencia/SciELO；定性 PEO/SPIDER 的可复用词表和过滤器；以及 RePEc/SSRN/OSF/REES 的版本、注册、引用关系。下一批应继续固定 commit/许可证并读实际 adapter，减少只报名字。


