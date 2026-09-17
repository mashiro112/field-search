# Google Deep Research 接入路线比较

2026-09-17。此文保留最初的接入选型背景。当前状态已推进至 [R27](R27-GEMINI-DEEP-RESEARCH.md)：单个真实任务已自动完成网页提交、计划启动、等待、官方导出和回答取回；后段复用已验收的 [R26 本地报告入口](R26-GEMINI-REPORT-IMPORT.md)。下文的原始建议及尚未实测描述属于形成选型时的记录，当前能力与验证边界以 R27 为准。既有 R25 验收状态不变。

目标是给 FS 增加真正的 Gemini Deep Research，并优先使用已有网页订阅额度。当前 FS 的 Gemini grounded-search 适配器只是模型加 Google Search，不是完整 Deep Research 产品。

| 路线 | 核实结果 | 建议 |
|---|---|---|
| Gemini 网页 | 官方提供 Deep Research 模式、研究计划、Start research、结果打开/复制/导出 Docs；订阅用户有相应使用额度 | 当前首选，需验证本机登录与完整交互 |
| Antigravity CLI | 官方支持代理、网页搜索和后台研究任务；内置 research 子代理主要面向代码库。查阅的文档未证明它直接调用 Gemini Apps 的 Deep Research 作业 | 可另作编程/普通调查执行器，不作为本次产品接入的默认替代 |
| 官方 Deep Research API | Interactions API 可异步启动真正的研究 agent，返回作业 ID，支持状态查询、流式输出及研究计划；仍为 preview，按模型和工具用量计费 | 自动化需求更高且接受独立 API 账单时再考虑，不能默认抵扣网页 Deep Research 额度 |

建议的最小组合：FS 准备目标/范围/验收要点 → 已登录 Gemini 网页选择真正的 Deep Research → 核对研究计划并启动 → 保存会话标识、低频查状态 → 读取完成的报告及引用 → FS 核查影响行动的关键出处。避免把完整主对话送入每次研究，避免等待时反复让高成本模型读同一页面。

读取先采用页面可用的正文/复制能力；长报告若读取不全，官方 Export to Docs 是可用的产品能力，现有 Google Drive 连接器可作为后续读取候选。网页发起、文档读取这一组合的维护收益是工程判断，尚未本机验证；需核对正文、引用链接及表格完整性，不预先声称比直接读取网页稳定。

最小验收：一次真实 Deep Research 从启动到完成；能辨认计划阶段/进行中/完成/失败，保存会话链接避免重复提交；完整取回正文及引用，超长时如实标出遗漏；复用已完成报告；登录或额度问题有明确提示。先完成这一闭环，不新建多代理研究框架或默认批量并发。

官方依据：

- [Gemini Apps Deep Research 帮助](https://support.google.com/gemini/answer/15719111)：启动、计划、额度与导出。
- [Antigravity CLI features](https://antigravity.google/docs/cli/features)、[Subagents](https://antigravity.google/docs/subagents)：CLI 的代理与 research 定位；搜索/研究能力不自动证明等同特定 Deep Research 服务。
- [Gemini Deep Research API](https://ai.google.dev/gemini-api/docs/deep-research)：独立 agent、Interactions API、异步运行、preview 与按量计费。未做网页/API 报告质量或真实成本的同题比较。
