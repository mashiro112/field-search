> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS02 R2 传统检索、跨语言与机构库扩展发现

批次：2026-09-15，Execution 补充发现分支。  
范围：传统布尔检索式、跨库语法转换、引文前后向追踪、机构库/OAI-PMH 聚合、中文及其他非英语科研入口，兼顾教育、心理、社科、人文。  
方法：首轮执行 4 个分散主题查询，再对返回项目和官方接口做原始 README、项目文档或 API 文档追踪。以下按发现主题分组，不代表优先级，也不构成推荐。  
标记：源码：未读，只表示本批没有进入具体实现文件；原始材料已读，表示至少核对了原始 README、项目文档、官方 API 文档或方法论文入口。

## 1. 布尔检索式与跨数据库语法

### CoLRev search-query

- URL：<https://github.com/CoLRev-Environment/search-query>；方法论文：<https://joss.theoj.org/papers/10.21105/joss.08775>
- 用途/可拆节点：把学术检索式解析为 AST，构建 AND、OR、括号和字段节点；对查询做 lint；在 PubMed、EBSCOHost、Web of Science 之间翻译 Title/Abstract 字段；保存 SearchFile；接入 pre-commit/CI；可扩展新解析器和目标数据库。
- 读取：源码未读；原始 README、docs、JOSS 摘要已读。
- 人工接入：Python/CLI 或 Search Query Studio；现有目标库语法有限，EBSCO/WoS 仍需人工核对；不需要检索 API key 才能解析/翻译。
- 扩展线索：追踪 parser、translator 和 query lint 规则；补充 CNKI、Wanfang、JSTOR、CiNii 等目标语法适配器；把每次转换后的原生查询写入检索日志。

### litsearchr

- URL：<https://github.com/elizagrames/litsearchr>；方法出处：<https://doi.org/10.1111/2041-210X.13268>；文档：<https://elizagrames.github.io/litsearchr/>
- 用途/可拆节点：从标题/摘要样本、作者词和数据库词提取候选词；形成词共现网络；按概念组生成 Boolean 检索式；支持最多 53 种语言（英语词干化和语言处理的覆盖程度需按语言人工核验）；用已知相关文献做 recall 检查；提供 Shiny GUI。
- 读取：源码未读；原始 README、pkgdown、vignette、API 文档和方法论文入口已读。
- 人工接入：R/RStudio；研究者要审查候选词、概念分组、翻译和误召回；GUI 标为开发中；没有外部 API key 要求。
- 扩展线索：教育/心理概念词可拆为构念、对象、情境、方法四组；比较其生成式与 search-query AST/数据库翻译的衔接；补做中文、日文、德文词形和同义词人工回查。

### findpapers

- URL：<https://github.com/jonatasgrosman/findpapers>；数据库文档：<https://github.com/jonatasgrosman/findpapers/blob/master/docs/databases.md>；查询语法：<https://github.com/jonatasgrosman/findpapers/blob/master/docs/query-syntax.md>
- 用途/可拆节点：一条 Boolean 表达式拆成多数据库查询；覆盖 arXiv、Crossref、IEEE Xplore、OpenAlex、PubMed、Scopus、Semantic Scholar、Web of Science；并行检索、合并去重、补元数据/摘要/关键词/引文、解析合法 PDF；支持保存/载入检索、相似文献和 snowball。
- 读取：源码未读；原始 README、docs/databases.md、query-syntax 及 snowball 文档入口已读。
- 人工接入：IEEE、Scopus、WoS 需要各自 key/机构权限；OpenAlex/S2 key 可选且有速率约束；Crossref 无检索库但可补 DOI/参考文献；Unpaywall/邮件和各库 polite access 需维护。每个后端的 Boolean 能力并不等价。
- 扩展线索：检查数据库 adapter 的字段退化规则、每库命中数和原生查询归档；加入 HAL、CiNii、OpenAIRE、中文入口时先做字段映射和空结果测试。

### scimesh

- URL：<https://github.com/gabfssilva/scimesh>
- 用途/可拆节点：对 arXiv、OpenAlex、Scopus、Semantic Scholar 并行查询；使用 Scopus 风格语法和 Python 运算符组合；统一元数据、DOI/标题年份去重；输出 BibTeX、RIS、CSV、JSON 和 Workspace；用 Unpaywall 解析合法 OA；可建引文图，并把本地 PDF 导入 FTS5 全文检索。
- 读取：源码未读；原始 README 和仓库文件列表已读。
- 人工接入：Scopus key 必需；S2 key、OpenAlex mailto、Unpaywall 邮箱可选/建议；Python/uv；仅使用合法 OA 路径。README 中的 Sci-Hub 选项登记为不纳入本工作流。
- 扩展线索：看 provider 结果的字段保真度、分页/速率和本地缓存；把中文检索词先在目标库验证后再转换为统一语法；比较其引文图和 citracer/CitationChaser 的用途边界。

### Bango

- URL：<https://github.com/Bilal-S/Bango>
- 用途/可拆节点：从研究问题和 PICO 概念生成同义词组；生成 PubMed、Scopus、WoS、Cochrane、EBSCOhost、JSTOR、ScienceDirect、arXiv 的数据库原生 Boolean 字符串；提供每库语法提示、警告和可复制检索式；另有引文前后向、SQLite 记录和全文节点。
- 读取：源码未读；原始 README 和功能说明已读。
- 人工接入：桌面应用；检索式生成需配置 LLM/API（具体提供商和额度待核）；用户须把字符串粘贴到各库并人工测试；JSTOR/EBSCO/Scopus/WoS 常需机构访问。
- 扩展线索：把“研究问题—概念—同义词—字段—数据库字符串—命中数”拆成可审计节点；核查版本和许可证；观察其对人文主题词、中文字段、非 PICO 问题的适配。

### scitech-librarian

- URL：<https://github.com/fabiocampolim-design/scitech-librarian>
- 用途/可拆节点：一次编写结构化查询，渲染为九个数据库的原生语法；覆盖 OpenAlex、NASA ADS、arXiv、INSPIRE-HEP、Scopus、Semantic Scholar、Crossref、CORE、Web of Science；并行执行后保存原始记录、RIS、每后端精确查询和命中数；可摄入 Zotero/Mendeley/WoS/RIS/参考文献表，生成 PRISMA2020、PRISMA-S、时间线和“此次检索新增了什么”的报告；根目录含 Claude Code 的 SKILL.md。
- 读取：源码未读；原始 README、仓库文件清单、内置 SKILL 提及和自测/CI 说明已读。
- 人工接入：标准库 Python 脚本即可运行；Scopus/WoS 需要机构/API，其他 API 也有速率/邮件要求；WoS 无 API 时通过 wos_manual.py 准备原生式并人工导入 RIS；只走 Unpaywall 合法 OA。
- 扩展线索：进一步读 backends/query/parser 和 SKILL.md；把每后端查询、raw response、hit count 接入 FS02 的 provenance；补上 HAL、CiNii、J-STAGE 和中文库的字段/分页适配。

## 2. 引文滚雪球、概念邻域与证据筛选

### snowball-slr

- URL：<https://github.com/rjglasse/snowball>
- 用途/可拆节点：以 PDF/DOI 为种子，做 backward、forward 或双向 snowball；默认从 PDF 抽参考文献，也可切换 GROBID；通过 OpenAlex 和 Semantic Scholar 找引用；支持审查/过滤/状态、元数据增强、DOI 浏览、坏元数据修复、补 PDF 后再次滚雪球；提供 Textual CLI/TUI 和 Python 包。
- 读取：源码未读；原始 README、pyproject 已读（包名 snowball-slr，Python >=3.9）。
- 人工接入：本地 GROBID 服务；默认/可选 OpenAI-compatible LLM 解析需要 key；Semantic Scholar key 建议配置；API 礼貌访问需要邮箱；PDF、DOI 和边界年份由研究者确认。
- 扩展线索：追踪引用解析失败、S2/OpenAlex 分页和去重规则；记录 seed、方向、深度、排除理由；在人文书目和中文参考文献上测试 GROBID/LLM 的误读边界。

### ProfOlaf

- URL：<https://github.com/sr-lab/ProfOlaf>
- 用途/可拆节点：从标题种子 txt/JSON 启动迭代；向前/向后收集引文；Semantic Scholar 可同时提供两方向，Google Scholar 主要提供向前引文；修复断引文；标题相似度约 0.8 去重；输出 BibTeX；抓 venue rank；按语言、年份、下载和元数据筛选；交互式人工标题/全文筛选和评级者分歧处理。
- 读取：源码未读；原始 README、配置和工作流说明已读。
- 人工接入：Python 3.10（README 明示版本冲突）；Google Scholar 可能需代理 key，且网页/CLI 能力不一致；S2、DBLP 受公开接口速率限制；LLM 可选（OpenAI/Gemini/Anthropic）；需要研究者处理边界样本。
- 扩展线索：验证其 CLI 与 Web 应用的功能差异、筛选表结构和去重阈值；观察教育/人文的 venue rank 是否误导；不把可选 LLM 当成必要依赖。

### CitationChaser

- URL：<https://github.com/nealhaddaway/citationchaser>；方法出处：<https://doi.org/10.1002/JRSM.1563>；Zenodo：<https://zenodo.org/records/4533747>
- 用途/可拆节点：R 包和 Shiny 应用，围绕一组 seed 做 backward/forward citation chasing；通过 Lens.org 及 PubMed/PMC/Crossref/MAG/CORE 数据源获取候选；适合从关键论文扩展证据集并保留追踪过程。
- 读取：源码未读；原始 README、方法论文入口和 Shiny 应用说明已读。
- 人工接入：Lens scholarly API token（免费但可能需申请/有期限）；Shiny 公共应用提供无 API 的人工入口；需要研究者审查 API 覆盖和重复。许可证本批未核实，暂不推断。
- 扩展线索：核查 Lens 现行 API、MAG 退役后的替代路径和结果导出；与 Citation Gecko、citracer 做前向/后向/引文上下文节点拆分。

### citracer

- URL：<https://github.com/marcpinet/citracer>
- 用途/可拆节点：输入本地 PDF、DOI、arXiv 或 URL 与关键词；GROBID 解析全文并定位关键词所在句附近的参考文献；通过 arXiv、Semantic Scholar、OpenReview、合法 OA 和 bioRxiv、medRxiv、ChemRxiv、SSRN、PsyArXiv 等预印本解析论文；递归 BFS 引文图；reverse 模式找“引用源文献且提及概念”的论文；可用 sentence-transformers 做语义过滤；导出 JSON、GraphML、HTML、缓存和可复现 manifest。
- 读取：源码未读；原始 README 已读。
- 人工接入：GROBID Docker；S2 key 建议；OpenAlex 邮箱可用于增强；语义模型约 500MB；全文解析与引用上下文仍需人工核对。README 中的 Sci-Hub 路径登记为不纳入，使用合法 OA。
- 扩展线索：追踪上下文窗口、reverse citation-context 取数和图指标；在人文论文的多语种引用句、书籍引用和中文 PDF 上验证 GROBID/解析器；保留 concept match 证据句。

### snowballing

- URL：<https://github.com/JoaoFelipe/snowballing>；文档：<https://joaofelipe.github.io/snowballing/>
- 用途/可拆节点：Python/Jupyter 工作流与 Chrome 插件；从研究综述种子开始记录 backward/forward 步骤、引文数据库、图和直方图；插件辅助 Google Scholar 添加 BibTeX、保存工作集和前向追踪。
- 读取：源码未读；原始 README、文档和示例入口已读。
- 人工接入：旧版 Python 3.6/3.7 及 Chrome 开发者模式；依赖 Google Scholar 网页交互，无 API key 但易受页面变化、验证码和浏览器环境影响；研究者需手动确认记录。
- 扩展线索：只作为人工滚雪球节点和历史工作流参考；核验当前浏览器可用性、数据导出和重复记录策略。

### Surveyer

- URL：<https://github.com/IsmailHatim/Surveyer>
- 用途/可拆节点：配置驱动的多源综述检索；concept block 做同义词交叉积；独立 filter concept 支持 any/all/min:N；seed 必引；backward/forward/both snowball，OpenAlex 深度 1；自动去重、关键词/LLM 相关性、Excel/BibTeX、PRISMA；ledger 记录 requested/actual/db total，能暴露截断。
- 读取：源码未读；原始 README、配置示例和命令工作流已读；MIT。
- 人工接入：uv/Python；DBLP/OpenAlex 无 key，S2/PubMed 建议 key，Google Scholar 可选但脆弱/关闭风险；Ollama 可本地使用；需要人工确认 concept、截断和相关性阈值。
- 扩展线索：读 sources、ledger、snowball 和 PRISMA 实现；把语言、教育/心理学科路由和机构库入口放入概念/源配置；记录每源失败与降级。

## 3. 机构库、OAI-PMH 与元数据聚合

### metha

- URL：<https://github.com/miku/metha>
- 用途/可拆节点：Go OAI-PMH 客户端/采集器；endpoint info、缓存、增量同步；按 set/metadata prefix 收集机构库；导出压缩 NDJSON；适合作为“端点注册—采集—缓存—规范化—下游索引”的底层节点。
- 读取：源码未读；原始 README、CLI 说明和版本信息已读（GPL-3）。
- 人工接入：不需要账号/API key，但需要维护机构 OAI endpoint、set、metadata prefix 和更新计划；XML/字段映射与重复归并需要人工配置；可用 cron/任务调度。
- 扩展线索：建立中文高校、法语、德语、日语机构库 endpoint 清单；比较 Dublin Core、MARC、JATS/ETD 映射；加入 provenance、deletedRecord 和增量游标审计。

### oai-harvest

- URL：<https://github.com/bloomonkey/oai-harvest>
- 用途/可拆节点：Python OAI-PMH 采集；按 base URL、日期、set、limit 选择性抓取；provider registry 保存 endpoint、目标目录、metadata prefix 和 last harvest；可用 cron 做增量。
- 读取：源码未读；原始 README 已读；项目版权信息显示为较早期（Liverpool，2013–2014），当前维护状态待核。
- 人工接入：无 key；需要 OAI endpoint registry、cron、XML 目标格式和失败重试策略。
- 扩展线索：和 metha 做轻量单库采集对照；检查 OAI-PMH 错误、分页、删除标记和增量日期边界；不把旧维护状态当作现成生产保证。

### oarepo-oaipmh-harvester

- URL：<https://github.com/oarepo/oarepo-oaipmh-harvester>
- 用途/可拆节点：Invenio 体系中的端到端 OAI-PMH harvester；注册/REST/admin/facet；DataStream reader、transformer、writer；持久化记录、错误、原始 XML；Celery/Jobs 定时运行；OpenSearch 索引。
- 读取：源码未读；原始项目说明、架构和依赖入口已读；MIT。
- 人工接入：适合已有 Invenio/OpenSearch/Celery 的机构环境；Python 3.13/3.14、Invenio 14 等依赖较重；需自行维护 endpoint、字段变换、队列和存储。
- 扩展线索：作为“机构库聚合服务节点”而非轻量桌面工具继续核验；考察 harvest errors、facets 和自定义 transformer 是否能承载中文/多语种字段。

## 4. 非英语、区域性与学科机构入口

### PsychPorta / PSYNDEX（替代已下线的 PubPsych）

- URL：<https://psychporta.org/>；字段帮助：<https://www.pubpsych.de/>（旧站公告入口，当前应跳转）；ZPID 词表/图谱线索：<https://www.zpid.de/>
- 用途/可拆节点：心理学元数据 PSYNDEX（德语区心理学）、PsychArchives 国际心理学研究对象、PSYNDEX Tests、作者画像；旧 PubPsych 官方页已公告 2026 年 6 月下线并指向 PsychPorta。PSYNDEX 支持 TI、PY、AU、CM、topic、AGE、PLOC、AB、ISBN/ISSN/JT 等字段，短语、AND/OR/NOT、自动 AND、大小写/连字符/重音处理。
- 读取：源码无公开 repo；官方门户、下线说明、beta/产品说明和字段帮助已读。
- 人工接入：浏览器人工检索；无本批确认的公共 API key；元数据为 CC0，第三方摘要等可能另有许可；需确认当前导出、批量访问和德语/英语字段。
- 扩展线索：把 PSYNDEX 字段查询拆为心理学/教育检索节点；核验 ZPID 词表的 RDF/SKOS/SPARQL 服务和可下载元数据；更新主地图中 PubPsych 的过时状态。

### HAL Search API

- URL：<https://api.hal.science/docs/search>
- 用途/可拆节点：法国 HAL 论文/机构库 Solr 风格查询；q、字段 title_t 等、短语、通配符、模糊、近邻、AND/OR/NOT、fq、时间范围、分页/游标、facet；输出 JSON/XML/XML-TEI/BibTeX/EndNote/RSS/Atom/CSV；适合作为法语和欧洲社科/人文来源。
- 读取：源码无；官方 API 文档已读。
- 人工接入：文档所示搜索端点与参数；是否需要 key、速率和批量上限要按现场 ToS 再核；需要人工做字段映射、语言/全文许可判断。
- 扩展线索：从 q/fq/field/facet 组合形成统一 source adapter；测法语重音、作者机构、学科/文档类型和 CSV/BibTeX 保真度。

### CiNii Research API

- URL：<https://support.nii.ac.jp/en/cinii/api/api_outline>
- 用途/可拆节点：日本论文、图书和机构记录入口；OpenSearch 文章查询可按 q、title、lang、count、start、format；支持 RDF/JSON-LD；CiNii Books NACSIS-CAT 记录可按 CC-BY 使用；适合日语非英语和人文图书/论文检索。
- 读取：源码无；官方 API outline、OpenSearch、RDF/JSON-LD 和 OpenURL 说明已读。
- 人工接入：需注册申请 application ID；摘要/内容受数据合同限制且不保证提供；每周更新；字段 Boolean 能力按接口/字段确认；UTF-8、日文作者/题名和机构参数需人工测试。
- 扩展线索：做日文字段/语言检索 adapter；同时保留 OpenSearch 与 JSON-LD；把 CiNii Books、Research 和 OpenURL 作为不同节点，不把图书记录混同为文章全文。

### J-STAGE WebAPI

- URL：<https://www.jstage.jst.go.jp/static/pages/JstageServices/TAB3/-char/en>
- 用途/可拆节点：日本期刊/文章/卷期元数据 API；按题名、ISSN、年份、文章题名、作者、关键词检索；期刊查询还可用语言、同行评审、OA 状态；可与 J-GLOBAL、CiNii、NDL 对接；官方页面记录 2026-03-26 发布的新文章检索功能。
- 读取：源码无；官方 WebAPI 页面和使用条款说明已读。
- 人工接入：需接受 API/使用协议；大量下载、商业使用、署名和访问量有限制；key/申请字段按协议现场确认；日文元数据与 OA 状态需人工核验。
- 扩展线索：比较 J-STAGE、CiNii 的 DOI/ISSN/作者归并；为日文社会科学/人文检索保存原始 XML 和语言字段；核验最新文章接口的分页/限流。

### SciELO ArticleMeta / CitedBy

- URL：<https://scielo.readthedocs.io/en/latest/>；检索入口：<https://search.scielo.org/?lang=en>
- 用途/可拆节点：拉丁美洲、葡语/西语期刊元数据；ArticleMeta REST API 覆盖文章、期刊、卷期、collection；CitedBy REST API 提供引用关系；检索字段包含题名、语言代码、机构国家等；可作为区域社科/人文和非英语来源节点。
- 读取：源码无；官方文档、搜索入口和 API 目录已读。
- 人工接入：现场核验 API 版本、端点、速率和许可；使用 pt/es 词形、语言和国家字段；全文/OA 许可逐条确认。
- 扩展线索：增加葡语、西语同义词和题名/摘要字段；比较 ArticleMeta 的引用/期刊规范化和 OpenAlex/Crossref 归并；记录 collection 与国家筛选。

### Dialnet API / OAI-PMH

- URL：<https://fundaciondialnet.unirioja.es/servicios/api-dialnet/>；OAI 说明：<https://soporte.dialnet.unirioja.es/portal/es/kb/articles/instrucciones-de-acceso-por-oai-pmh>
- 用途/可拆节点：西语生产数据库/大学 CRIS 接口；可列机构作者、机构全部成果、详细书目记录、按日期增量；另有 OAI-PMH 2.0 入口可作为机构库采集节点，适合西语社科/人文。
- 读取：源码无；官方 API 服务说明和 OAI-PMH 访问说明已读。
- 人工接入：生产 API 需向 Fundación Dialnet 技术联系人申请信息/权限；OAI endpoint 的 set、metadata prefix、限流和可采字段需现场确认；西语作者/机构消歧需人工。
- 扩展线索：优先核验 OAI-PMH 可公开范围，再评估生产 API；将机构作者列表、日期增量和书目详情拆成独立节点；与 HAL/SciELO 做区域覆盖对照。

### OpenAIRE Graph Search API

- URL：<https://graph.openaire.eu/docs/apis/search-api/results/>；下一版文档：<https://graph.openaire.eu/docs/next/apis/search-api/>
- 用途/可拆节点：统一查询 publications、datasets、software、other research products；支持结果类型、项目/组织/国家/社区等关系过滤；适合作为欧盟机构库、绿色 OA、数据/软件和论文元数据聚合入口。
- 读取：源码无；官方 Search API、结果类型和限制文档已读。
- 人工接入：搜索 API 的字段、页大小、速率和 key 状态按现场文档核；前 10,000 结果限制意味着大规模全量需另取完整图；语言、OA、项目关系等过滤不可直接假定。
- 扩展线索：把 publication/dataset/software 拆成不同检索节点；保存 API query、分页、relation filters 和结果总数；与 OAI-PMH 原始记录保留来源链。

## 5. 中文科研搜索 Skill 与跨源路由

### ustc-ai4science/academic-search

- URL：<https://github.com/ustc-ai4science/academic-search>
- 用途/可拆节点：面向 Codex/Claude Code 兼容宿主的 API-first 学术检索 Skill；覆盖 arXiv、Semantic Scholar、Crossref、OpenAlex、Unpaywall、Google Scholar、ACM、IEEE、PubMed、Papers with Code、CNKI；按社会科学、经济、教育、人文、法律等学科路由；支持查询扩展、保守验证/去重、引用链、合法 OA PDF manifest、站点模式；README 记载 2026-04-05 增加 CNKI 支持、1.4.0 增加结构化页面读证据。
- 读取：README、版本变更和仓库目录已读；源码：具体 SKILL.md、academic-records.mjs、oa-pdf-download.mjs、cdp-proxy.mjs 及 site-pattern 文件未读；未安装。
- 人工接入：宿主需支持 Skill；API key/额度按源配置；Node 22+ 脚本；浏览器模式需 Chrome/CDP 专用 profile；CNKI/Google Scholar 可能出现登录、验证码或页面变化，本批未登录；不绕过付费墙。
- 扩展线索：优先读 CNKI site pattern、字段映射、验证/去重和 evidence manifest；确认 CNKI/Wanfang/CQVIP 的访问边界；把“API 检索—浏览器补充—OA 解析—人工核验”拆成独立可替换节点。

## 6. 人工接入与缺口集中登记

本批未安装、未登录、未购买、未申请新账号，也未执行真实数据库抓取。缺口集中如下：

- 账号/API：Semantic Scholar、OpenAlex、Unpaywall、IEEE、Scopus、WoS、Lens；CiNii application ID；可能的 Google Scholar 代理；Dialnet 生产 API 访问。
- 机构/协议：Scopus/WoS/EBSCO/JSTOR/ScienceDirect 等机构订阅；J-STAGE 使用协议；各门户批量下载、署名和速率条款。
- 本地运行：Python/R/Go/Node 版本；GROBID 服务；可选 Ollama/LLM；Chrome/CDP 专用 profile。
- 数据维护：机构 OAI endpoint/set/prefix 清单；中文库和非英语库字段、分页、语言、作者消歧；合法 OA 与第三方摘要许可。
- 统一审计：保存原始查询、每库翻译后的查询、请求时间、命中数、截断/错误、去重合并证据、人工排除理由和复现 manifest。

## 7. 原始方法与后续扩展线索

- 检索式：search-query JOSS 论文 <https://doi.org/10.21105/joss.08775>；litsearchr 方法论文 <https://doi.org/10.1111/2041-210X.13268>。
- 引文追踪：CitationChaser 方法论文 <https://doi.org/10.1002/JRSM.1563>；snowball-slr、citracer、ProfOlaf、JoaoFelipe/snowballing 的原始 README。
- 非英语门户：PsychPorta <https://psychporta.org/>、HAL <https://api.hal.science/docs/search>、CiNii <https://support.nii.ac.jp/en/cinii/api/api_outline>、J-STAGE <https://www.jstage.jst.go.jp/static/pages/JstageServices/TAB3/-char/en>、SciELO <https://scielo.readthedocs.io/en/latest/>、Dialnet <https://fundaciondialnet.unirioja.es/servicios/api-dialnet/>。
- 下一批优先展开的发现面：中文 Wanfang/CQVIP 与高校机构库的 OAI/开放接口；韩文 KCI、日文/法文/西文人文期刊和图书目录；WorldCat、HathiTrust、DPLA/Europeana、Gallica 等人文书目/数字馆藏；Kishaz systematic-literature-review 与其他跨数据库查询策略项目；上述候选的 adapter、字段翻译、许可证和维护状态。
- 尚未做的工作：没有源码级审查、安装执行、性能/覆盖率实验或候选排序；需要下一批再逐项补证。

