# R32：从搜索缺口选择成熟组件

日期：2026-09-23。状态：**调研与少量公开接口探测完成，实施和效果验收待 FS01 执行**。
基线：`9bb63d23e86a00e0d6e1b5b5464e292ec744ae75`（R31，184 个源码文件）。
执行入口：[R32 Goal Prompt](R32-GOAL-PROMPT.md)。

## 结论与共同框架

下一阶段最有价值的探索，是找回表达不同的已有证据、深入少量相关页面、获得适用版本的文档，以及恢复复杂文件中的关键信息。已有的 Feed、Repomix、MarkItDown、批次恢复和原文定位继续使用。

用同一条链分析所有候选：**问题与约束 → 发现来源 → 获取内容 → 恢复结构 → 找到相关片段 → 核对条件和反证 → 支持行动**。新项目必须补上其中一个具体缺口，并接回现有来源、版本、位置及缓存记录；不要为了统一接口重新写一套研究平台。

“首选”指本机 Windows、中文/英文材料、低用量、按需调用这些条件下的试验顺序，是基于公开资料的工程判断，尚不是横向性能冠军。成熟度检查包括维护状态、明确许可、可独立使用的接口、依赖和本机条件；星数不作为质量或效果排名。

## 九个探索分支

| 分支与现有缺口 | 首选项目与采用方式 | 对照及为何优先 | 首个可判定的试验 |
|---|---|---|---|
| **A. 任务内语义找回**：`locate` 能找原词，尚无混合语义检索 | **[QMD](https://github.com/tobi/qmd)**，MIT；直接复用其检索接口，仅索引明确提供的任务材料 | 与 `locate`/`rg` 比较；[FastEmbed](https://github.com/qdrant/fastembed) 是 Apache-2.0 的较轻组件备选，但需要自行拼接更多检索逻辑。优先试完整现成检索器 | 中英混合、同义改写、跨语言、精确版本号和一个“材料中没有答案”的问题；从命中结果回到原文与版本。分开测关键词、向量、重排成本 |
| **B. 定向多页深入**：站点入口发现和单页读取之后仍需逐页挑选 | **[Crawl4AI Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/)**，Apache-2.0；在已有隔离运行时中复用 BFS/BestFirst、过滤和流式结果 | 对照当前 `discover → read/batch`；[Firecrawl](https://github.com/firecrawl/firecrawl) 核心 AGPL-3.0，另装服务的迁移成本较高，暂不替换现有运行时 | 一个官方文档站、一个公开经验站，限制域名、页面数、深度及时间；比较是否找到原路径漏掉的关键页。读取失败和边界外链接必须可见 |
| **C. 适用版本的技术文档**：原生网页容易混入最新版本 | **[Context7](https://github.com/upstash/context7)**，MIT 客户端；优先调用现有 CLI/MCP/API 能力，随后核对原始文档 | 对照官方版本站和固定 Git ref 的 Repomix；后两者是无服务依赖的保底路径。Context7 的检索后端并不开源，复制客户端不等于拥有其索引 | 同一个库的新旧版本问题：必须返回适用来源或明确“不支持该版本”。不能把最新文档标签改成指定版本 |
| **D. 复杂 PDF、扫描和表格**：MarkItDown 的轻量转换不承担布局/OCR保真 | **[Docling](https://github.com/docling-project/docling)**，MIT；直接复用本地转换与结构输出，保留页/表定位 | 对照已装 MarkItDown；[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)（Apache-2.0）作为中文扫描识别不达标时的专项备选。优先 Docling 是为了接入统一结构，中文准确率仍需比较 | 一份真实双栏/表格 PDF 和一份可合法使用的中文扫描页，预先确定需要恢复的数字、表头和段落顺序，逐项与页面核对 |
| **E. 从“读仓库”到“找实现”**：文本检索不能表达调用形状 | **[ast-grep](https://github.com/ast-grep/ast-grep)**，MIT；只复用结构搜索，不启用重写 | 与已有 `rg`/Repomix 对照；[Aider repo map](https://github.com/Aider-AI/aider/blob/main/aider/website/docs/repomap.md) 适合结构导览，但为搜索引入完整编码代理收益较低。[Repomix 压缩](https://repomix.com/guide/code-compress) 仍标为实验性，可作导览，不能拿删去函数体的摘要证明实现行为 | 在固定提交的一个真实上游中查某种调用模式，返回文件、代码片段和位置；至少包含跨行调用及一个同名不同用途的反例 |
| **F. 没有字幕的一手语音材料**：现有视频路线仅覆盖字幕 | **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)**，MIT；复用本地 ASR，先试 CPU INT8、时间戳和 VAD | [whisper.cpp](https://github.com/ggml-org/whisper.cpp)（MIT）是独立二进制/不同硬件条件下备选。两者本机速度、中文术语准确率未比较；若已试 Docling 的 ASR 足够，也可避免重复运行时 | 明确提供的短音频或有明确可用许可的公开样本：抽查中英文术语、数字、否定词、静音与时间戳。ASR 结果标为机器转录，不能升级成作者原始字幕 |
| **G. 社区原生搜索与上下文**：X 长帖和登录后搜索仍未验收 | **[OpenCLI](https://github.com/jackwener/opencli)**，Apache-2.0，作为可复用适配器的首要考察对象；先与现有原生浏览器比较，再决定是否安装 | 现有浏览器已能完成的动作不另包服务。补充来源可研究 Bluesky 官方 [atproto](https://github.com/bluesky-social/atproto)（`@atproto/api` 包 MIT），但本轮匿名探测为 403 | 对指定的公开主题，找到原帖、回复及后续修正，核对长文是否截断；会话或桥接扩展不可用就登记具体缺口，继续其他分支，不把公开索引结果冒充站内搜索 |
| **H. 可控多引擎发现**：原生/现有 keyless 路线可能有来源盲区 | **[SearXNG](https://github.com/searxng/searxng)**，AGPL-3.0；有合适本地运行条件时直接部署独立实例，选择少量引擎 | 对照原生 Web 和现有 keyless 引擎；重叠搜索服务不算独立证据。公共实例稳定性和 JSON 开放性不足以作为默认依赖 | 三个实际问题，中英文、社区长尾、版本故障各一；同一查询预算，核对新增且影响判断的原始来源以及引擎错误。没有额外有效来源就不升为默认 |
| **I. 网页证据的时间变化**：Feed 更新检查不是正文变化解释 | **[changedetection.io](https://github.com/dgtlmoon/changedetection.io)**，Apache-2.0；先借鉴目标区域过滤与变化归因，再决定是否复用组件 | 优先当前两个不可变快照的一次性本地差异；[Wayback CDX](https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md) 只在缺历史版本时作为条件来源。默认不装常驻监控服务 | 一份真实版本更新文档，区分内容变动、导航噪声和提取失败；变化摘要必须能指回旧/新原文。只做本次显式比较 |

## 影响取舍的核查结果

### QMD：最值得试，也最需要分层测成本

官方提供关键词、语义和混合模式；完整模式包含本地模型与重排。GitHub API 本轮读到最新 release `v2.8.3`（2026-08-16），该 tag 的包要求 Node >=22。README 列出的默认三个模型合计约 2 GB；它也明确提示默认 embedding 的 CJK 覆盖局限，并提供自定义模型方式。不能从英文演示直接推断中文效果。[项目说明](https://github.com/tobi/qmd)、[release](https://github.com/tobi/qmd/releases/tag/v2.8.3)、[包元数据](https://github.com/tobi/qmd/blob/v2.8.3/package.json)

先固定版本，隔离配置、索引及模型缓存，先关键词，再按真实缺口启用向量/重排。自定义模型需要完整重建并验证维度/指纹；[上游问题 #497](https://github.com/tobi/qmd/issues/497) 曾报告模型维度不一致，关闭状态本身不构成本机验证。当前 README 可能晚于 release，实施时必须以固定版本的接口为准。

### Context7：本轮读到了文档，但没有证明指定版本和长期免费

2026-09-23 的无密钥只读探测：

| 请求 | 结果 | 能说明什么 |
|---|---|---|
| `/api/v2/libs/search?libraryName=fastapi&query=dependency%20injection` | HTTP 200；5 个候选 | 当前主机可以发现库 |
| `/api/v2/context?libraryId=%2Ffastapi%2Ffastapi&query=dependency%20injection&type=json` | HTTP 301 JSON；`library_redirected`，目标库 `/websites/fastapi_tiangolo` | 库 ID 会迁移；该响应不是文档成功 |
| 用上述目标库重新请求同一 context 接口 | HTTP 200；7,979 bytes，`codeSnippets`/`infoSnippets`，含指向 FastAPI 依赖文档的来源链接 | 至少一次真实片段获取成功，超出 R30 只验证 library search 的范围 |

读取的是片段，不是整站全文。尚未实测指定旧版本、配额耗尽、完整引用正确性或稳定匿名访问。README 推荐免费 key，而当前 [API Guide](https://context7.com/docs/api-guide) 说明请求需要鉴权；这与本轮端点的实际匿名成功存在差异，应保留这个差异，不能宣称无密钥长期可用。若遇鉴权/配额问题，回到官方版本资料。未新建账号、key，也未发送付费请求。[客户端与后端边界](https://github.com/upstash/context7)

### 社区：不能把项目列出的平台数当成已接通数

OpenCLI 使用浏览器桥接扩展和本地 daemon；本轮只读了项目说明，没有安装或验证任何账号。它是相对较新的项目（仓库创建于 2026-03），不能与多年稳定的通用组件等同。需证明它相对现有浏览器减少了重复动作或取回了缺失上下文，才值得引入。[官方项目](https://github.com/jackwener/opencli)

Bluesky 请求 `https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=docling&limit=3&sort=latest` 在本机返回 HTTP 403，未返回帖子。本轮没有继续尝试登录或更换身份。官方 [searchPosts 定义](https://github.com/bluesky-social/atproto/blob/main/lexicons/app/bsky/feed/searchPosts.json) 也允许服务实现要求鉴权；因此只保留候选，不记作已连接。API 包的 MIT 许可来自其 [package.json](https://github.com/bluesky-social/atproto/blob/main/packages/api/package.json)，仓库顶层 GitHub license 字段是 NOASSERTION，不能直接推广到全仓所有内容。

### 研究方法与旧项目

[STORM](https://github.com/stanford-oval/storm) 的观点引导提问和有来源的追问可用于检查搜索盲区；R31 已保留这类方法，本轮不再把同一方法包装成新功能。它不提供免费、完整的新索引，也不免除模型运行成本。

[Open Deep Research](https://github.com/langchain-ai/open_deep_research) 已于 2026-08-21 归档，GitHub API 本轮返回 `archived=true`。保留它的实验/编排方法作为历史参考，不把它当成活跃依赖或另起完整研究服务。

所有分支共用一个低成本判断：先问“还缺什么会改变行动的证据”，再选工具；结果按来源条件和矛盾组织，不能因多个站转载同一经验而抬高可信度。知识图谱、自动自我优化、全站抓取和多家 Deep Research 同时调用暂不单独立项；没有现实缺口时不增加系统层级。

## 顺序、成本与重新激活条件

1. **首批主动复现 A/B/C/D**。为每项主动找一个相关公开真实案例，不能因为“暂无用户文件”又只写一轮计划。遇模型下载、长处理或外部访问缺口时先说明具体成本/限制，切换到可独立推进的分支。
2. **第二批 E/F**。实现查找与短音频转录各做一个真实样本，对照现有路线。有实际收益再接入；不为扩展数目多装同类工具。
3. **G/H/I 做有界可行性判定**。G 依赖已有可用且授权的浏览器会话/桥接；H 需先检查本地运行条件，本轮 PATH 未发现 Docker，WSL 命令存在不代表已配置 Linux；I 先用已有快照。访问或资源门槛只阻止对应路径。
4. 高不确定项保留“缺什么、何时重试、下一次最小试验”，不自动定时唤醒、不持续轮询不可用接口。一次失败不证明方案无效，一次成功也不证明长期覆盖。

开放软件通常不收 API 使用费，但模型下载、存储、算力、维护和第三方服务配额仍是成本。复用代码保留上游出处、固定提交和适用许可证；模型权重与依赖的许可单独检查。商业方案可借鉴公开设计，不复制未公开实现。

## 本轮证据边界

已做：读取当前 Skill/集成表、R30/R31 结果与计划、选定实现；检查相关上游 README/官方 API/功能文档、17 个候选仓库的许可与维护元数据；进行上述 Context7 和 Bluesky 探测；核对发布副本 clean 且与远端基线相同。

未做：候选安装、模型下载、检索质量/中文准确率/性能比较、登录后 X 搜索、SearXNG 部署、PDF 或 ASR 保真验收。上表是复现任务单，不是已部署清单。旧的 R28 报告导出缺口、X 边界和 FS03 学术 SOP 状态均未改变。

FS03 仍承担现有正式学术检索到写作流程；新组件提供材料能力，不替换 PsycINFO/Scopus/WoS、Elicit、Zotero 和证据到写作分工。
