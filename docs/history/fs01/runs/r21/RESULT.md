> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS01-R21 结果

## 已实现

只扩展已存在的显式 `--reader crawl4ai` 路径：

- `search.py read URL --reader crawl4ai --wait-css SELECTOR --wait-timeout SECONDS`：只接受受限 CSS selector，固定传给 Crawl4AI 的 `css:` wait 语义；拒绝 `js:` / `javascript:`，等待上限 30 秒且不能超过页面 `--timeout`。
- `--include-links`：把 Crawl4AI 已返回的 internal/external links 投影到成功快照和分页结果；只保留 HTTP(S)，解析相对链接，去重，保留 `links_truncated=false` 和无效条目计数，不下载任何链接。
- 链接现在来自 Crawl4AI 已返回的渲染 HTML，经标准库 `HTMLParser` 提取原始 `href` 属性；使用实际 `redirected_url` 和首个有效 HTML `<base href>` 解析相对地址，并保留 `raw_href`、重复 query 参数、原始 query 顺序、编码和 fragment。SDK 已规范化的 `result.links` 不再冒充保真来源。
- `possible_attachments`：仅按扩展名或链接元数据作猜测；每项明确 `status=not_fetched`，不声称已下载、读取或完整。
- 若渲染 HTML 缺失或解析不可用，链接投影为 `links_status=unavailable`，不静默回退到有损 SDK href。
- selector 超时、Crawl4AI 失败和空正文仍是显式失败；不会回退到默认路线。

未实现路线 2、ast-grep/MCP、PDF/MHTML、媒体扩展、附件下载、翻页/点击/session、任意 JS、登录/cookie 和默认 `auto` 路由变更。

## 验证

验证使用已记录的 R4 Crawl4AI runtime，并按现有 `references/crawl4ai-runtime-r4.md` 暴露已验证的 `websearch` 依赖路径；没有安装新依赖。

- 三个脚本 AST parse：`AST_OK`。
- `--help`：`search.py` 和 `document.py fetch` 均显示 `--wait-css`、`--wait-timeout`、`--include-links`。
- CSS/参数边界：`js:document.body`、`--reader auto --include-links`、`--wait-timeout 31` 均在 parser 阶段拒绝，退出码 2。
- 动态公开页 `https://quotes.toscrape.com/js-delayed/`：
  - 无等待快照正文 263 字符，未包含 quote 正文。
  - `--wait-css .quote --wait-timeout 15` 成功，正文 1674 字符，包含 `The world as we have created it`；快照记录 `wait_for=css:.quote` 和 15 秒边界。
  - 同一页面的 10 秒等待因页面自身约 10 秒延迟而按边界失败，随后用 15 秒重跑成功；该失败快照保留在 `quotes-wait.json`，说明等待不足不会伪装成成功。
- 失败语义：不存在的 selector 在 1 秒等待后退出码 2，结果为 `status=unavailable`、`reason=crawl4ai_failed`、`failure_state=wait_condition_failed`，并保存失败快照。
- C2 未重新抓取公开页：复用既有 arXiv 渲染 HTML 快照 `installed/arxiv-links-v2.json` 离线重投影，得到 65 条实际 HTML href、`links_source=rendered_html`、`links_status=ok`、`links_truncated=false`，最终 URL/base 可见；保留 `https://arxiv.org/pdf/2408.15232` 为 `not_fetched` 可能附件。旧快照顶层的 64 条 SDK 列表未被当作新保真结果。
- 离线保真反例 `c2/html_link_fidelity_test.py` 覆盖签名样式 URL、重复 query 参数、`ref`/fragment、`%2f`/`+`、HTML `&amp;`、相对 href、`<base href>`、实际 final URL 解析、去重和缺失 HTML 不回退；`c2/saved_snapshot_link_retest.py` 经既有真实渲染 HTML 路径通过。
- 回归：`--reader auto` 的 `https://example.com/` 仍为 `jina_markdown`；成功快照 `document open/find` 均 `network_used=false`，且能命中等待后的正文。
- 进程检查：测试结束无残留 Chromium/Chrome 进程。

证据目录：`installed/quotes-default.json`、`installed/quotes-wait15.json`、`installed/quotes-wait.json`、`installed/wait-failure.json`、`installed/arxiv-links-v2.json`、`installed/static-auto.json`、`c2/html_link_fidelity_result.json`、`c2/saved_snapshot_link_retest_result.json`。

## 文件与完整性

实际修改文件：

- `installed-field-search/scripts\search.py`
- `installed-field-search/scripts\document.py`
- `installed-field-search/scripts\crawl4ai_reader.py`

修改后 SHA256：

- `search.py`: `82A987F9F4D29E401A40C5B1D986C52D9DCC942EB21E1C4E052CC0E7E89B4916`
- `document.py`: `1AB7F080735ECF7252D2DF39139DECE3CDFBF07D4B6B2967C2B7157B99B61EF7`
- `crawl4ai_reader.py`: `037454C95118517F025B5E5E56B2BAEC2599010A2A1CF243D97E3BF812C79C4D`

保护文件哈希保持不变：

- `installed-field-search/SKILL.md`: `4FB4F763F606B02FF4DA01B6C903963B57EE6D25A2F3E4A9A4DF6911D0D176C0`
- `installed-field-search/references\evidence.md`: `87B24ACB8BCA9B66D13A947C05DEABB6160D26C8767AE1AE99EEB098B55D19FC`

## 备份与回滚

R21 初始变更前备份与 pre-state 记录在 `backup/installed/scripts/` 和 `PREFLIGHT.md`；C2 变更前的当前 R21 备份与 pre-state 记录在 `backup/r21-before-c2/scripts/` 和 `PREFLIGHT-C2.md`。如需只撤销 C2，恢复 C2 备份；如需整体撤销 R21，恢复初始备份。本轮未执行回滚。
