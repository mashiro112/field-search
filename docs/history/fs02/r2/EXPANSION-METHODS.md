> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS02 r2：跨语言映射与检索反馈方法扩展

本批只追两个问题：一是“一个研究概念怎样跨语言、词形和书写系统变成可审计的检索词”，二是“相关反馈、seed-set 迭代和 active learning 是否真的改写检索，而不只是给已有候选集排序”。目标是补方法节点和原始出处，不做排名、整合或推荐。

状态约定：

- **原始方法**：读论文或官方方法说明；未找到可直接运行的实现时，不把它写成工具。
- **代码可追**：固定仓库提交并读了实际源文件；没有安装、运行或登录。
- **相邻方法**：能帮助追踪边界，但主要做候选集筛选、排序或引文扩展，不能替代检索式改写。
- **重复/对照**：主清单已有同一能力族，本批只补区分或不再新增名字。

## 一、跨语言术语映射：从概念到可审计的检索式

### 1.1 社会科学领域词表先提供“概念锚点”

**ELSST（European Language Social Science Thesaurus）** 是本批发现的直接社会科学来源族。其[官方主页](https://elsst.cessda.eu/index.html)说明词表覆盖政治、社会学、经济、教育、法律、犯罪、人口、健康、就业、ICT 和环境等社会科学主题，约 3,400 个概念，提供捷克语、荷兰语、英语、芬兰语、法语、德语、希腊语、匈牙利语、冰岛语、立陶宛语、挪威语、罗马尼亚语、斯洛文尼亚语、西班牙语和瑞典语标签。官方[使用说明](https://elsst.cessda.eu/guide/using-elsst)记录了这些检索行为：

- 大小写和变音符号不敏感，支持前缀及星号截断；
- 非优选词会导向优选词；同一概念可展开到其他语言的等价标签；
- 可沿更宽、更窄、相关概念和上位父概念浏览；
- 版本、弃用关系和 URI 可追踪；
- CESSDA Data Catalogue 可把另一词表中的匹配关键词带入数据目录发现。

这不是论文全文检索 API，而是“研究概念/社会科学元数据词 → 多语标签、层级和目录关键词”的控制词节点。官方[CESSDA API 目录](https://api.tech.cessda.eu/)把 Vocabulary/ELSST 和 Data Catalogue API 分列，适合把词表查询与数据目录查询记录为两个步骤。ELSST 页面注明 CC BY-SA 4.0；调用接口的当前字段、限流和版本号仍需人工核实。

**TheSoz** 是德语社会科学的另一种方法节点。GESIS 的[当前 CV Browser](https://data.gesis.org/cvbrowser/en/)用 Skosmos 展示和下载词表；TheSoz 的[原始 Linked Data 方法论文](https://arxiv.org/abs/1209.5850)将其描述为面向检索和搜索词推荐的 SKOS 数据集，含德语、英语、法语约 12,000 个关键词（优选词和非优选词），覆盖教育学、政治学、经济学及跨学科主题，并与 STW、AGROVOC、DBpedia 等资源交叉链接。方法步骤是把原有词表结构分析为概念、标签和关系，再转换为 SKOS，使用可解析 URI、SPARQL/下载和词间关系支持检索推荐，而不是把机器翻译结果直接当作同义词。

TheSoz 论文记录的是历史版本和 CC BY-NC-ND 3.0；当前浏览器中实际下载包的版本、许可证和更新时间不能由历史论文推断，需人工复核。TheSoz 的“非优选德语词 → 优选描述词 → 英/法标签 → 相关词表映射”可作为德语社会科学检索的概念对齐链，但目前没有证据表明它直接对接中文学术全文库。

**EuroVoc 的多语关键词赋值**提供了与上面查询侧扩展相反的对照方法。[Fujii 等人的原始论文](https://arxiv.org/abs/cs/0609061)把多语 EUROVOC 作为语言无关的控制词：统计文档中的词形与描述词的关联，为一篇文档推荐描述词，再把同一描述词显示成 11 种欧盟语言。它解决的是“文档侧多语概念标引”，不是从用户查询翻译到目标语言；可用于判断一个外语记录是否有跨语言概念标签，不能直接当作查询翻译器。

**社会科学问卷检索的查询扩展**更接近检索行为本身。[GESIS/ZBW 的 Query Expansion for Survey Question Retrieval](https://arxiv.org/abs/1506.05672)在 ALLBUS/SOEP 16,764 个问卷问题和子问题上比较词表扩展、共现扩展和 BM25：把抽象社会构念变成词表词，或从语料共现中扩展词项；共现扩展通常提高前十结果召回，词表扩展的排序质量（nDCG）更好。它是社会科学语料上的原始方法证据，说明“构念 → 词表/语料扩展 → 问卷字段检索”与医学 MeSH 式展开并不等价。论文未提供本批可复用的代码节点。

### 1.2 可以组成概念对齐基础设施的开放实现

这三个实现分别承担“翻译词表”“提供 SKOS 查询”“应用跨词表映射”，不能误写成一个开箱即用的社会科学全文检索系统。

**WOKIE：SKOS 词表的多语翻译流水线（代码可追）**

- 项目：[FelixFrizzy/WOKIE](https://github.com/FelixFrizzy/WOKIE)，固定 HEAD 为 aa68c95ef878cb624c91db80f59523f1ea1033ac；GitHub 页面标为 MIT。
- 实际读过固定提交中的 main.py、config.py、modules/translation_pipeline.py、modules/frequency_confidence_calculator.py、modules/secondary_translation_strategies.py、Argos/OpenAI translator 以及 supported-services.md。
- 真实处理链是：输入 RDF/SKOS → 抽取概念的 prefLabel/上下文 → 对目标 BCP47 语言调用多个 primary translator → 以候选翻译的频次一致性计算置信度 → 低置信时用 individual、batch 或 hierarchy 策略补充描述、父概念链和上下文 → 把缺失语言标签写回 RDF。
- primary service 包括 Argos、Google、Lingvanex、ModernMT、Microsoft、PONS、Reverso、Yandex 等；也可以配置可选的 LLM 二次翻译。Argos 可走本地 HTTP 服务；Google/Microsoft/PONS、LLM 等外部服务需要各自 API key。代码没有“领域金标准”来检验翻译是否符合教育、历史或社会学语境，因此频率一致性不能等同于检索准确率。

WOKIE 的可拆节点是“受控词表翻译与置信度记录”，不是文档召回器。它可以把 ELSST/TheSoz 生成的缺失语言标签写回 SKOS，再交给词表 API 生成检索词，但每一个译词仍需记录来源服务、置信度、上下文和人工修订。未安装、未运行、未请求任何 key。

**Skosmos：SKOS 词表浏览和 REST/Linked Data 接口（代码可追，源码本批未逐文件审）**

- 项目：[NatLibFi/Skosmos](https://github.com/natlibfi/Skosmos)，固定 main 为 b0367e2596946492c1b7d82b879b08ef5812bd13；GitHub README 标为 MIT。
- 官方项目说明是通过 SPARQL/SKOS 提供控制词表网页、REST API、Linked Data 和检索/自动补全；Finto 词表服务以它为基础。
- 可拆节点是：查询语言/主题 → API 返回 prefLabel、altLabel、层级、相关关系、语言标签和 URI → 由本地检索适配器把不同关系转成不同布尔子句。Skosmos 本身不生成译词，也不决定 exact/close/broad 关系应不应该进召回。
- 依赖是本地部署或已有词表服务及 SPARQL 后端；没有必须的商业 API key，但接入远程词表会有服务可用性、版本和权限问题。此次只读 README/API 说明，没有安装或运行源码。

**JSKOS Server：跨词表 mapping 的推断和应用（代码可追，文档/API 读）**

- 项目：[gbv/jskos-server](https://github.com/gbv/jskos-server)，固定 main 为 1f9d00e4b310b875b9e16d722f6a424e99b64b95；GitHub README 标为 MIT。
- README/API 文档中的 /mappings/infer 会沿祖先关系推断 mapping，可按 strict/depth 和 exact、narrow、close、related 等关系控制；/mappings/apply 把映射应用到 from URI 并附加带来源的目标概念；/voc 可按语言、主题、许可证和发布者筛选词表。
- 可拆节点是：源词表 URI → 显式 mapping → 受关系类型与祖先深度限制的推断 → 目标词表 URI/标签及 mapping provenance → 查询扩展或跨目录对照。它比纯机器翻译多了概念 URI、关系类型和来源审计。
- 需要 MongoDB/JSKOS 服务和词表/映射数据；部署可配置认证，公共实例是否允许这些只读端点需现场检查。没有安装、登录或运行。

WOKIE、Skosmos、JSKOS 的组合可形成一条开放实现线：WOKIE 产出多语 SKOS 标签，Skosmos 提供按语言和层级的查询，JSKOS 保留跨词表映射与推断来源。它们仍缺“针对每个学术数据库语法生成 Boolean 字段式并以已知 seed 校验召回”的最后一层。

### 1.3 词形、复合词、音译和上下文歧义的原始方法

跨语言召回的难点不只是把一个字符串翻成另一个字符串。下列原始研究提供了可拆的机制，但其评测多来自旧式技术文献或特定语言，迁移到中文教育/人文资料库尚未验证。

- [Fujii & Ishikawa, Japanese/English CLIR](https://arxiv.org/abs/cs/0206015)：将复合技术词拆为基础词再翻译，用概率方法处理每个词的歧义；对词典外的借词用 transliteration；查询翻译和音译共同改善检索。节点是“复合词分解 → 候选翻译消歧 → OOV 音译补召回”。
- [Fujii & Ishikawa, Cross-Language IR for Technical Documents](https://arxiv.org/abs/cs/9907007)：双语词典与搭配统计共同确定词义，对词典外词保留音译；可作为“词典覆盖不足时的语料回退”原始出处。
- [Seo 等，English–Korean query translation](https://www.sciencedirect.com/science/article/pii/S0306457304000809)：不对每个查询词贪心选一个译词，而是生成目标语言翻译组合，用词对关联分数选择整组组合；这是韩语非英语召回里“组合级歧义消解”的独立节点。
- [Yang 等，Translingual information retrieval](https://www.sciencedirect.com/science/article/pii/S0004370298000630)：从双语语料学习上下文中的术语等价关系，比较 translingual GVSM/LSI、translingual pseudo-relevance feedback 和 example-based translation；其结论对“通用词典翻译不一定保留领域语境”有直接方法意义。
- [Oard, Query and document translation techniques](https://aclanthology.org/1998.amta-papers.41/)：实现并比较六种双语 term-list 查询翻译、机器翻译查询和文档翻译；指出翻译知识的表示方式本身会改变 CLIR 效果，适合用来区分 query-side 与 document-side 设计。

工程层的语言分析器可以承担较低层的形态/书写规范化，但不能替代上述概念对齐：

- [Apache Solr language analysis](https://solr.apache.org/guide/solr/latest/indexing-guide/language-analysis.html)支持按语言配置分析链、decompounder、大小写/Unicode 等处理和多语言字段；
- [Lucene ICU analysis](https://lucene.apache.org/core/8_6_0/analyzers-icu/index.html)提供分词、规范化、大小写和搜索词折叠，以及例如繁体到简体的 transliteration。

本批没有把 Solr/Lucene 作为新“科研搜索工具”计数；它们只是将词表标签变成字段查询前的形态/正字法层。具体中文分词、繁简变体、日语汉字复合词、韩语空格/词素和德语复合词策略，仍需按目标数据库的索引规则验证。

### 1.4 可记录的跨语言搜索节点

不把下面的节点当作推荐方案，它们是后续实验可以逐段替换、审计和比较的接口：

1. 研究构念、原始语言和领域上下文；
2. 选择可解析的词表概念 URI（ELSST、TheSoz 或本地词表），保存版本和许可证；
3. 取得 prefLabel/altLabel、非优选词、层级、相关词及跨词表 mapping；
4. 对缺失语言调用翻译，并保留服务、候选集、置信度和人工修改；
5. 施加语言分析：词形、大小写/变音符号、复合词、繁简/音译和 OOV 规则；
6. 对 exact/close/broad/narrow/related 关系分层，生成目标源的 title/abstract/subject/keyword 字段子句；
7. 每种语言和每个数据库独立运行，记录命中、已知 seed、零命中词和被数据库语法拒绝的子句。

## 二、相关反馈与 seed-set 迭代：真正改写检索的证据

### 2.1 直接针对检索式的反馈和强化学习

**Badami、Benatallah、Baez（2023）自适应 SLR query generation** 是本批找到的最直接的“反馈改写检索”方法。[正式文章](https://doi.org/10.1016/j.is.2023.102231)和[可读 PDF](https://marcosbaez.com/assets/pdf/badami2023adaptive.pdf)描述一条从研究问题或相关摘要 seed 开始的管线：

1. 抽取候选术语；
2. 用通用或领域词向量扩充术语；
3. 组成 Boolean 查询并执行数字图书馆检索；
4. 让研究者对结果提供相关性反馈；
5. 用强化学习/多臂老虎机在迭代中选择添加或删除查询词；
6. 以提高召回、同时减少无必要筛选量为目标，比较 seed 类型、嵌入领域、反馈抽样和迭代次数。

论文在 10 个 SLR 数据集上评估，报告与作者手工查询相近的结果，并把“查询质量”和“筛选负担”放在同一目标里。当前没有找到作者公开、可固定提交的生产代码或各数字图书馆接口实现，因此这里登记为原始方法，不写成可直接调用的工具。需要进一步确认术语动作空间、反馈标签编码、停止规则以及不同 Boolean 语法的适配。

**Automatic Boolean Query Formulation 的 conceptual/objective 对照**见 [Scells 等论文 PDF](https://ielab.io/publications/pdfs/scells2020conceptual.pdf)。conceptual 方法从信息专家或一组已知研究中识别高层概念，再扩展相关关键词；objective 方法以统计显著词排序，并用 seed/留出研究调节 Boolean 子句。它明确把“查询式构建”与“候选文献筛选”分开，是判别后面 SDR/FASTREAD 是否真正扩展检索的重要原始出处。

### 2.2 seed-set 数据和可复现实验资源

[IELab/sysrev-seed-collection](https://github.com/ielab/sysrev-seed-collection) 固定 main 为 3d4e36ee6697cb4825e691c51ff062a9ab88c644，README 标为 MIT。本批读了 README、数据说明和实验说明，未逐个读实验脚本。它不是服务，而是包含系统综述主题、seed studies、included studies、原始 query 和 edited search 的研究集合；experiments/ 下分出 query formulation、SDR document ranking 和 snowballing。

其可复用的方法区分：

- 真实 seed studies 与 pseudo seed studies；
- 用综述标题/初始字符串和 seed 研究优化词项组合的 conceptual formulation；
- 从 seed 和背景语料抽取显著词、在留出 seed 上调节 Boolean 子句的 objective formulation；
- 多轮 query formulation 与另行的 citation snowballing。

这提供了“seed 来源、查询版本、覆盖目标和留出验证”应怎样落盘的证据，也暴露了伪 seed 会高估方法效果。它没有保证目标数据库可直接执行，也没有为中文或人文学科设计词形层。

### 2.3 排序/筛选反馈：相邻而非查询改写

**SDR（Seed-driven Document Ranking）**：[原始方法论文](https://arxiv.org/abs/2112.04090)，代码仓库为 [ielab/sdr](https://github.com/ielab/sdr)，固定 main 为 fd8d662258166ab5558dfd2533d3065f6411d3cd；本批未读源文件，许可证和当前兼容性未知。SDR 接受已有 Boolean 候选集和一个或多个 seed study，使用 seed 相似度、tf-idf/cosine 或 QLM 对候选文档排序，并可从新 seed 更新词权。多 seed 可能提高稳定性，但它仍在已有候选集内排序，不能找回数据库查询式漏掉的文献。故登记为“seed 反馈邻支”，不当作主动检索实现。

**FASTREAD/FAST2（代码可追）**：[仓库](https://github.com/fastread/src)，固定 master 为 f42c6c1d8858ec2a585111740b77a6a5b552a918，GitHub 标为 MIT。本批实际读了固定提交的 src/index.py、src/util/mar.py 和 simulate.py：

- 初始候选来自关键词 BM25；
- 用户给出 relevant/irrelevant/undetermined 标签后，train() 用标题和摘要 TF-IDF 训练线性 SVC，并使用类别平衡、正负样本和伪负样本；
- uncertain() 按决策面附近的不确定性选下一篇，certain() 按相关概率优先展示，另有 recall 曲线估计和 susp() 的可疑标签/概念漂移提示；
- 模拟脚本执行“BM25 候选 → 不确定性/确定性主动学习 → 目标召回停止”的循环。

因此 FASTREAD 是真实的 relevance feedback/active screening 实现，但其反馈只改变候选集中的展示顺序和标签模型，不改写外部数据库 Boolean 查询，也没有多语词表、翻译或跨库适配节点。它可用来验证筛选端反馈接口，不能回答“反馈如何扩大非英语召回”。

**SYMBALS**：[原始论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC8193570/)将 active learning 标题/摘要筛选与 backward snowballing 结合：先用宽数据库查询形成候选集，再用 ASReview 主动学习筛选，最后沿纳入文献的参考文献向后滚雪球。论文报告的案例中，滚雪球找回一批早期文献并降低漏检，但作者把 active learning 定位在筛选阶段；没有查询式重写或目标数据库重发。故它是“候选池扩大/引文补漏”邻支，不是 direct relevance-feedback query engine。

**Simulation-based active learning** 的代码/数据线：[GitHub/Zenodo v3.0](https://github.com/jteijema/Code-for-Simulation-Based-Active-Learning-for-Systematic-Reviews) 和 [Zenodo record](https://zenodo.org/records/13361795)。它支持用模拟数据比较主动学习筛选效率，适合评估标签预算、停止规则和模型差异；方法对象仍是既有候选集，未解决查询词或非英语库的主动扩展。

主清单已有 systematic-review-pipeline。本批不把它新增计数；其 README 已清楚分开 title-term query expansion、实际 citation snowballing、OpenAlex backward/forward 图遍历和去重。它可作为实现层对照：从纳入标题挖词是 query expansion，沿真实引用边走才是 snowballing，二者的证据来源与停止标准不能混写。主清单还已有 query expansion/RobotAnalyst 等条目；本批未重新确认 RobotAnalyst 的身份或代码。

### 2.4 反馈方法的跨语言交叉点

[Yang 等的 translingual IR 方法](https://www.sciencedirect.com/science/article/pii/S0004370298000630)把 translingual pseudo-relevance feedback 和上下文术语等价关系放在同一框架中，是两条分支的交叉节点：第一次检索产生目标语言文档/词项，再把可靠的相关词回投到源查询或下一轮查询。需要留意 pseudo-relevance feedback 把 top-k 当相关的偏差，尤其在中文/英文混杂的人文语料中。

[Boolean versus ranked querying for biomedical systematic reviews](https://link.springer.com/article/10.1186/1472-6947-10-58)提供另一项边界证据：纯 ranked 检索难以保证高召回，但在 Boolean 候选集内排序可帮助交互式查询开发和反馈。它是医学评测，不能直接外推到社会科学；方法上的可迁移节点是“Boolean 负责候选边界，排序/反馈负责人工检查和下一轮改写”。

## 三、与主清单的去重和能力边界

主清单已经覆盖若干查询扩展、引文滚雪球和一个系统综述流水线。本批新增的不是更多数据库名称，而是以下独立方法区分：

| 能力族 | 本批原始/实现证据 | 真实作用 | 与主清单关系 |
|---|---|---|---|
| 多语社会科学概念词表 | ELSST、TheSoz、EuroVoc | URI、优选/非优选标签、语言和层级关系 | 新的非医学领域词表族 |
| 词表翻译和映射基础设施 | WOKIE、Skosmos、JSKOS Server | 翻译候选、SKOS 服务、mapping 推断和 provenance | 新的可拆实现栈，不是单一搜索器 |
| CLIR 词形/复合/OOV | Fujii–Ishikawa、Seo、Yang、Oard | 复合词、歧义组合、音译、上下文等价、PRF | 方法出处补全；多数非社科评测 |
| 直接查询反馈 | Badami；Scells conceptual/objective | 从 seed/相关反馈添加或删除 Boolean 词项 | 重要的新方法节点；公开代码未找到 |
| seed-set 迭代数据 | sysrev-seed-collection | 查询版本、seed provenance、留出覆盖、snowballing 分开 | 代码/数据实验资源，非生产服务 |
| 主动筛选/seed 排序 | FASTREAD、SDR、SYMBALS | 候选池内标签、排序、引文补漏 | 相邻重复能力，不能称为查询改写 |

## 四、接入、许可和人工处理边界

| 资源 | 本批证据状态 | 本地/远程依赖 | 需要人工处理的部分 |
|---|---|---|---|
| WOKIE | 固定提交源文件已读，MIT | 本地 Python；Argos 可本地，其他 translator/LLM 可远程 | API keys、服务条款、译词抽样校正 |
| Skosmos | 固定提交 README/API 读，MIT；源码未审 | 本地部署 + SPARQL/SKOS 后端或已有实例 | 词表导入、版本和远程实例访问 |
| JSKOS Server | 固定提交 API 文档读，MIT；源码未审 | MongoDB/JSKOS 服务，可配置认证 | mapping 数据、关系深度和认证 |
| FASTREAD | 固定提交源文件已读，MIT | 本地旧式 Python/Flask/TF-IDF/SVC | 运行环境修复、标签和目标召回定义 |
| sysrev-seed-collection | 固定提交数据/README/实验说明读，MIT | 本地 JSONL/实验脚本；无服务 key | 数据许可细节、seed 金标准和复现实验 |
| ELSST | 官方词表/API 说明读，CC BY-SA 4.0 | CESSDA Vocabulary/Data Catalogue 远程接口 | 当前 API schema、限流、版本和目录权限 |
| TheSoz | 当前浏览器 + 历史方法论文读 | GESIS CV Browser/SPARQL/下载 | 当前许可证、版本和交叉链接状态 |
| CLIR 论文、Badami、Scells、SYMBALS | 原始论文/开放 PDF 读 | 不依赖本地服务 | 获取代码/数据、确认数据库接口和实验参数 |

OpenAlex 在主清单及相邻流水线中可能出现过 key/接口说明；本批没有把旧 README 当成当前政策，也没有据此断言需要 key。任何 OpenAlex 依赖应单独以当前官方接口状态确认，和本地可运行代码分开登记。

## 五、剩余具体未知

跨语言映射侧：

1. ELSST 当前 API 的查询字段、分页/限流、版本和可否直接返回所有语言 altLabel 尚未用请求验证；Data Catalogue 关键词映射是否能导出为稳定的检索词表也未确认。
2. TheSoz 当前下载版本、许可证、SPARQL 端点、英/法覆盖和与 STW 的最新 mapping 未核验；历史论文不能代表当前服务状态。
3. ELSST、TheSoz、EuroVoc 之间的 exact/close/broad/narrow 对齐是否足以支持中文、韩语或日语检索，尚无可复现实验；控制词存在不代表目标全文库实际索引该标签。
4. WOKIE 的多数翻译服务和 LLM 需要 key，频率置信度没有领域金标准；没有知道每个数据库索引的词形、短语、繁简、空格或复合词规则，WOKIE 也不直接生成数据库 Boolean 语法。
5. Skosmos/JSKOS 只提供标签、关系和映射服务；如何把 close/related/broad 词分层加权、避免伪同义词扩大噪声，尚未有社科中文评测。
6. CLIR 原始研究对日英、英韩和技术文献有证据，但教育、历史、文学、社会学的术语歧义、专名音译和 OCR 变体仍是空白。

反馈和主动搜索侧：

1. Badami 的公开论文给出了 RL/多臂老虎机查询改写思路，但未找到固定可用代码；动作空间、奖励、停止条件、数据库 API 和多数据库语法转换仍未知。
2. seed-set 的来源和可靠性会改变结果：真实纳入研究、专家给出的 seed、伪 seed、top-k pseudo-relevance 各自引入不同偏差；现有实验资源已经提醒伪 seed 会高估效果，但尚未针对中文/人文语料测试。
3. Scells 的 conceptual/objective formulation 和 Badami 的反馈改写之间，是否可加入语言映射置信度、词表关系类型和零命中诊断，尚无开放实现。
4. FASTREAD、SDR、SYMBALS 和 simulation 代码主要在候选池内主动学习、排序或引文补漏；直接让用户反馈触发“重新构造并重发外部 Boolean 查询”的开源实现仍未找到。
5. pseudo-relevance feedback 在跨语言场景可能把错误语言、热门主题或翻译歧义当成相关词；需要记录 top-k 选择、反馈置信度、原语言/目标语言词项及每轮召回变化。
6. sdr 源码/许可证本批未审，SYMBALS 没有定位到官方可复用代码，simulation 资源的实验数据许可和当前依赖也未核对。

## 六、是否仍有重要未探索分支

**仍有，而且是两条方法上的空白，不是“再列更多数据库”的空白。**

第一，已有开放资源把概念词表、机器翻译、SKOS 服务、mapping 推断和语言分析分散在不同组件；没有发现一条可复现的社会科学工作流，能从版本化概念 URI 生成每个非英语数据库的字段级 Boolean 式，并用已知 seed、词形/OOV 日志和每轮召回进行校验。因此“概念对齐 + 形态/音译 + 数据库语法适配”仍需继续追源码或方法实现。

第二，主动学习的公开实现大多在一个已经由宽查询确定的候选池里筛选或排序。Badami 证明了相关反馈可以直接改写查询，但本批未找到相应公开代码；FASTREAD、SDR、SYMBALS 则明确停留在候选集排序、标签或滚雪球。因而“反馈触发跨库、跨语言检索式重写，并可审计召回变化”的实现仍是重要未探索分支。

以上判断只说明证据覆盖和具体未知，不构成整合推荐或优先级结论。
