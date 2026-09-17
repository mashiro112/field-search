# FS03 对话提炼与归档摘要

日期：2026-09-17。归档对象为 FS03 建项与发布对话及其侧栏分区；科研流程本身仍为 planning：规格完成、待真实任务试跑。

## 已确定

- FS03 是当前科研场景唯一默认 SOP，FS01/FS02 既有成果和通用 field-search 能力继续保留，按需支持此流程。
- 主链为问题与用途 → 分库检索式 → PsycINFO/Scopus/WoS 正式召回（教育主题按需 ERIC）→ Elicit 合并/去重/筛选 → 引用与长尾补漏并回筛 → Zotero 原文资料 → Evidence Matrix → 大纲与 Claim–Evidence Map → 审定段落证据包 → 写作 → 原文、逻辑与结论强度审核。
- 机构授权网页需要用户临时打开；订阅不等于 API 权限。保留 study/report/version 和样本关联，避免重复计证；按任务用途调整严格程度。
- 此次没有执行真实文献检索、部署科研流水线或验证科研效果。私人 MCP 仅讨论了可行性与实施路线，没有部署；当前采用 GitHub 发布资料供 GPT 读取，需要本地实时材料时再考虑只读 MCP。
- 用户已要求后续 FS 开发默认同步 GitHub：每次实质进展、交接或本轮结束时发布相关源码、文档、验证与未完成状态，维护 GPT 入口并核对远端。规则已写入工作区与仓库的 AGENTS.md。

## 产物入口

- [GPT 阅读入口](https://github.com/mashiro112/field-search/blob/main/CONTEXT_FOR_GPT.md)
- [FS 全貌导览](https://github.com/mashiro112/field-search/blob/main/docs/FS-OVERVIEW.md)
- [FS03 规格](https://github.com/mashiro112/field-search/blob/main/docs/academic-evidence-to-writing/FS03-WORK-ITEM.md)、[中文 SOP](https://github.com/mashiro112/field-search/blob/main/docs/academic-evidence-to-writing/SOP.md)、[模板](https://github.com/mashiro112/field-search/blob/main/docs/academic-evidence-to-writing/templates.md)
- [28 份历史材料索引](https://github.com/mashiro112/field-search/blob/main/docs/history/INDEX.md)
- [后续开发发布规则](https://github.com/mashiro112/field-search/blob/main/AGENTS.md)

首次资料发布 commit：`466c295a3613cd01d4f80a299bfd7a460a64d4b2`；原 162 份源码保持原 hash，36 个新增/修改文件已远端读回一致。该验证只证明发布文件一致，不代表工具功能或科研效果验证。后续读取以当前分支实际 commit 为准。

## 恢复时的最小下一步

取得一个真实研究问题及用途，先完成阶段 0–1，再在需要正式召回时打开授权库。以现有 SOP 与模板开始，不重做工具选型或历史调研，不自动唤醒其他角色。共享 Skill 变更仍须明确唯一写入者；按新发布规则同步本轮实际进展。

对话归档不改变上述待试跑状态，不删除本地文件、GitHub 材料或历史记录。侧栏分区在归档其唯一对话后移除；不影响 FS01/FS02 分区。
