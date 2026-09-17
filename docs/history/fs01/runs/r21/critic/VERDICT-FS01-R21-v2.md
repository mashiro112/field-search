> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS01-R21 v2：限定接受

R21 v1 唯一阻断项已关闭。实际安装代码改从已返回的渲染 HTML 提取 a/area href，不再使用 SDK 已规范化的链接作为目标；原反例中的签名、参数顺序、重复参数、ref、百分号编码及 fragment 均保留。HTML 实体正确解码为属性值，raw_href 指解码后的属性值，不是 HTML 源码字节串。

本次只审查相对 `backup/r21-before-c2/scripts/` 的差异并运行受影响的离线测试。独立脚本 `check_v2.py` 从安装文件 AST 加载实际解析函数，执行 E2 两份测试及补充反例，未导入 SDK、未联网、未更改安装文件。结果见 `checks-v2.json`。

- 签名/重复参数/ref/实体/转义、相对 base、最终 URL、area、缺 HTML 与受控解析失败测试通过。缺 HTML 或解析失败返回 links_status=unavailable，不回退有损 SDK。
- 复用冻结 arXiv 渲染 HTML 得到 65 条链接，PDF 候选仍为 not_fetched。与上一版 SDK 投影的 64 条不同，属于提取来源变化，不是新联网结果。
- 实际接线优先 redirected_url，其次 result.url 和输入 URL。实现使用第一个带 href 的 base，再判断其解析结果是否可用；不是遍历寻找后续有效 base。此处按实际行为解释，不作为本次签名修复阻断项。
- search.py 完全未变；document.py 仅增加 links_base_url/links_error 透传。原抓取失败、空正文失败和异常捕获分支未变，本次未重跑此前通过项。
- SKILL.md 实际哈希为 4fb4f763f606b02ff4da01b6c903963b57ee6d25a2f3e4a9a4df6911d0d176c0；references/evidence.md 为 87b24acb8bca9b66d13a947c05deabb6160d26c8767ae1ae99eeb098b55d19fc，均与保护基线一致。PREFLIGHT-C2 中 SKILL 哈希漏写末尾 0 是记录笔误。

接受范围为本轮链接保真修复及其与 R21 已通过功能的衔接；不扩张为全部网页链接完整性、签名服务可访问性或所有异常路径清理保证。v1 记录的运行依赖与阶段超时限制继续有效。
