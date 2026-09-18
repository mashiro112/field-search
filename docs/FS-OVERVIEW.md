# FS Skill 全貌导览

更新：2026-09-18。此页连接当前源码、历史证据与新科研流程；状态以各层的实际证据范围区分。

当前部分接入：[R28 ChatGPT 网页 Deep Research 与非付费 X 搜索](reviews/R28-CHATGPT-WEB-RESEARCH.md)。已实测研究入口、计划、自动开始、完成及页面正文读取；Markdown 下载未返回文件，复制返回空内容，本地完整归档尚未验收；已重跑 X 网页索引发现和 oEmbed 读取，长帖仍截断。新增路线明确标注部分可用，当前源码清单为 174 文件。

最近完整交付：[R27 自动发起并取回 Gemini Deep Research](reviews/R27-GEMINI-DEEP-RESEARCH.md)。单个真实任务已由代理完成提交、计划核对与启动、等待、官方 Docs 导出、Drive 取回和本地读取。新增的是 FS 的原生浏览器工作流，复用 R26 后段；173 文件源码/指令清单同步。用户无需负责点击开始或手工导出，登录验证和额度等实际节点仍可能需人工处理。

后段基础：[R26 读取现成 Gemini Deep Research 报告](reviews/R26-GEMINI-REPORT-IMPORT.md)。真实 Docs→Markdown 导出已成功并与网页对照正文及表格；本地原样导入、限量预览、离线分页/查找及复用已安装并完成必要验证，独立审查的输出长度与目录计数问题已修正。R26 自身不负责启动研究，R27 已接上浏览器执行流程；grounded search 仍不是 Deep Research。[路线比较](reviews/GOOGLE-DEEP-RESEARCH-OPTIONS.md)保留为选型背景。

此前已交付：[R25 Bilibili 字幕能力已安装并通过独立验收](reviews/R25-BILIBILI.md)，在已有 video 入口增加 B 站字幕、分 P、时间定位、关键词查找及批量复用。会话和完整测试字幕不公开。科研 FS03 状态保持独立。

[R24 已验收能力](reviews/R24-RESULTS.md)包括 YouTube、Discourse、本机运行配置/诊断及任务内批量复用/刷新。R25 在此基础上扩展；最终 B 站正例为来源一致的 1790 段字幕，初版 705/235/267 段错配结果已撤回，不作为验收证据。短链与元数据限制见 R25 结果说明。

设计依据：[ROI 审查](reviews/2026-09-17-feature-roi.md) 与 [R24 实施范围](reviews/R24-IMPLEMENTATION.md)。前者的“尚未实施”描述属于审查时的历史状态；当前状态以 R24 最终结果为准。批量复用只跳过完整成功项，部分结果仍会重读；没有建立论坛游标续取器或证明固定 token 节约比例。

| 层次 | 内容与状态 | 从哪里读 |
|---|---|---|
| 通用 field-search | 寻找成熟方案、一手经验、反例与决定性原文；根据真实缺口选择路线，已有源码快照 | [Skill](../SKILL.md)、[完整指令](INSTRUCTIONS_FULL.md)、[集成地图](../references/integration-map.md) |
| FS01 演进与验证 | 包含已运行并限定验收的能力、失败和不采用的候选；不代表普遍胜过其他搜索工具 | [历史路线图](history/fs01/ROADMAP.md)、[初期实验](history/fs01/EXPERIMENT.md)、[结果](history/fs01/RESULTS.md) |
| FS02 科研增强 | R1 四句研究关系说明已采用；R2 深度调研与整合设计经限定验收，候选并未全部部署 | [R1 摘要](history/fs02/r1/SUMMARY.md)、[R2 摘要](history/fs02/r2/SUMMARY.md)、[完整方案](history/fs02/r2/REPORT.md) |
| FS03 证据到写作 | 当前科研场景唯一默认 SOP；规格完成，待真实任务试跑 | [规格](academic-evidence-to-writing/FS03-WORK-ITEM.md)、[SOP](academic-evidence-to-writing/SOP.md)、[模板](academic-evidence-to-writing/templates.md) |

## 能力是怎样形成的

1. 初期比较发现近期社区召回互补，因此保留并接入选定的 last30days 工作流；全文快照、分页与跨页查找解决一类已观察到的截断缺口。留出题未证明新增脚本自然触发，也没有速度或普遍优势结论。[初期独立验收](history/fs01/evidence/independent-review.md)
2. 后续对代码检索、社区读取与引用关系逐项验证，分别保留已安装能力、受限候选与负结果；路线图记录了为何不把所有候选装入主流程。[演进记录](history/fs01/ROADMAP.md)
3. 显式 Crawl4AI 路径增加动态 CSS 等待与页内链接/可能附件列表；附件仍未获取，普通 auto 路径不因此改变。[R21 结果](history/fs01/runs/r21/RESULT.md)
4. 小红书显式只读入口在固定环境验收，依赖独立 runtime、adapter 和授权会话；评论加载目标不是完整采集保证。[R22 结果](history/fs01/runs/r22/INSTALLED-RESULT.md)、[最终验收](history/fs01/runs/r22/critic/INSTALLED-VERDICT-v2.md)
5. FS02 从学术搜索节点、查询转换、引用图、去重、全文与反馈方法展开，给出设计及代码范围重合比较。重合指数不代表效果排名；科研当前默认路线已由用户在 FS03 选定。[比较与边界](history/fs02/r2/REPORT.md)

## 让 GPT 读取

先读本页及当前 SOP，再按问题读取历史报告和对应源码。需要实现全貌时使用 [完整原始源码索引](COMPLETE_SOURCE_INDEX.md)，当前数量和 hash 见 SOURCE_MANIFEST.json；需要演进与设计依据时使用 [28 份历史资料索引](history/INDEX.md)。代码源清单与新增文档清单分别维护，原始源码 hash 不因文档发布而改变。

文件以 UTF-8 Markdown 与 JSON 发布；JSON 矩阵有可读 Markdown 配套。大文件应分段读取并报告未读范围。能访问 GitHub 不意味着已读完全部文件，不能从摘要推断已独立复核原始实验。

可直接给 GPT：

> 请读取 mashiro112/field-search 仓库的 CONTEXT_FOR_GPT.md 和 docs/FS-OVERVIEW.md，记录实际读取的 commit。再按需展开历史索引、FS03 三份文档与相关源码，区分已实现/已运行/设计候选/待试跑；科研讨论以 FS03 为当前默认。请先列出实际读到的文件和无法访问的部分，再与我讨论。

用户已确定后续 FS 开发以 GitHub 同步为交付步骤：每次实质进展、交接或本轮结束时更新相关源码、文档、验证及未完成状态，并核对远端版本。具体见 [开发发布规则](../AGENTS.md)。GitHub 保存最新成功发布的阶段；ChatGPT 按需读取，不会因 push 自动更新所有旧对话。[OpenAI GitHub 说明](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt)

FS03 本次建项、SOP/模板固定与资料发布已结束，讨论结论保留于本仓库。科研流程仍为规格完成、待真实任务试跑；后续从真实研究问题与用途开始，不因对话归档变成已运行验证。

[FS03 closure summary / 对话归档摘要](academic-evidence-to-writing/CLOSURE-SUMMARY.md) preserves the decisions, artifacts, and next step.
