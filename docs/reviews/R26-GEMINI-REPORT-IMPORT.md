# R26：低成本读取现成 Gemini Deep Research 报告

2026-09-17，本地报告入口已安装，真实导出与必要行为验证完成，冻结版本通过独立验收。此阶段落实已完成报告的读取和复用；不把报告导入描述为自动启动、监控并完成 Gemini 研究。

## 采用的路线

目标是完整搬运现成结果，减少重复网页操作和模型输入。复用已有网页订阅生成的报告，读取阶段不再调用研究生成模型。已有 Docs 链接时，直接走现有 Google Drive 工具的官方 `text/markdown` 导出，把返回文件原始字节保存到任务目录，再交给 FS 本地入口。无需新增 API 账单、爬虫或数据库。

原会话有官方“复制内容”入口时，可以先做一次正文、表格和引用映射检查；通过后采用复制路线，否则固定 Docs 导出，不每次双重尝试。公开分享链接只在用户已经提供时读取，不要求为了导入改变分享权限。PDF 是已有材料的兼容路线，不作为默认中间格式。

## 真实样本的已知结果

- 用户提供一份已完成报告及对应 Docs。现有 Drive metadata 与 Markdown 导出成功，下载文件为 28,015 字节；程序直接落盘，没有模型转写。
- 与 Gemini 分享页的 DOM 对照：16 个标题、28 个正文段落、两张表共 80 个单元格，规范化诊断指纹全部匹配。比较忽略 Markdown 加粗/转义、Unicode/空白差异及两处仅含 `&nbsp;` 的间隔；网页引用编号来自可见 DOM 的来源索引。它是结构内容核对，不是逐字节页面归档或研究事实核验。
- 导出末尾保留连续编号 1–45 的来源及各自 HTTPS 链接。初始引用展开显示的 5 个来源网址与导出前 5 项一致；未据此宣称逐条核验了全部来源的内容或所有引用语义。
- Markdown 中引用上标降为紧贴正文的数字，来源列表保留，但原网页的可点击上标结构没有无损保留。机器导入仍标记完整性未独立确认。
- 分享页在当前未登录状态没有“复制内容”按钮，复制路线未实测。本机浏览器 `content.export()` 不受支持。已有 Docs 导出已能满足读取，不为比较路线额外登录或生成研究。
- 一次尝试批量展开网页引用遇到超时，恢复后页面仍可读；此操作没有成为日常导入步骤。后续以已取得的导出文件复用，避免重复 UI 读取。

## 已安装的最小功能与验收

FS 接收明确指定的本地 UTF-8 Markdown，原样保存 `report.md` 和短元数据（来源、获取方式、时间、SHA256、完整性状态）。默认只返回标题、有界目录和小预览；按需分页或查找，均不联网。相同内容复用，不静默覆盖不同内容。

入口为 `scripts/search.py report import/open/find`，由新增的 `scripts/report.py` 实现。获取文档复用现有 Google Drive 连接器，本地原样保存、元数据、离线读取和复用是薄封装；分页复用既有实现，缺少该依赖时有简单本地切片后备。操作说明见 [gemini-report.md](../../references/gemini-report.md)。

合成样本验证保存字节一致、预览截断、尾部定位、复用和冲突不覆盖。真实样本验证导入 SHA256 与官方导出一致，分页重组无损并到达尾部，查找页码与打开页一致。独立检查对网络及外部执行设置 audit hook，验证本地读取不触发这些操作；冲突时两个文件均保持不变。语法编译和 Skill validator 通过。R25 历史验收不计作本轮新代码验证。

独立验收发现并修正了两个与用量有关的问题：超长标题造成大输出，以及标题数超过目录保留上限时的错误计数。现在派生标题和目录项各限 240 字符、返回目录最多 20 项，真实标题总数保留；`outline_truncated` 对照实际返回项数。100,000 字符标题反例的默认输出由 201,411 降为 2,824 字符，原正文不变。这是该反例的输出大小，不是模型 token 节约率。最后两处目录阈值修正经静态逆向替换 hash 核对，确认没有其他代码变化。

验收冻结版本：`report.py` SHA256 `a93111f4e8a50b35a45450559bb352eab27d1d632d6b3bc3689f130d81d1f4f2`。本轮已同步 172 文件源清单与指令合集。导入器会报告 17 个 Markdown 标题，因为导出比网页正文多一个“引用的著作”标题；不能与网页正文的 16 个标题混用。

```text
<python> <skill-dir>/scripts/search.py report import <local-report.md> --out-dir <task-report-dir> --method docs_export
<python> <skill-dir>/scripts/search.py report find <task-report-dir> "keyword"
<python> <skill-dir>/scripts/search.py report open <task-report-dir> --page 2
```

R26 当轮未实测复制路线，也未实现研究任务的自动启动、计划批准或进度监控。后续 [R27](R27-GEMINI-DEEP-RESEARCH.md) 已补上并实测从网页发起到结果取回的完整流程；R26 继续作为本地读取基础。复制保真度仍未实测。

私有报告正文、文档标识、会话、受控下载链接均不进入公共仓库。导出和本地读取不新增 Gemini 研究生成调用；后续模型分析仍消耗输入用量，没有已测得的固定节省比例或全路线速度排名。

官方依据：[Gemini Deep Research 帮助](https://support.google.com/gemini/answer/15719111)、[Google Drive 导出格式](https://developers.google.com/workspace/drive/api/guides/ref-export-formats)、[Google Docs Markdown 导出公告](https://workspaceupdates.googleblog.com/2024/07/import-and-export-markdown-in-google-docs.html)。
