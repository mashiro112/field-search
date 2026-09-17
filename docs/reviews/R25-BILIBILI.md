# R25：Bilibili 字幕接入

2026-09-17。已安装并通过限定范围的独立验收。公开源码清单共 170 个文件，不含会话、二维码和完整测试字幕。

## 功能

现有 `search.py video` 接受 Bilibili 完整视频链接及 BV/AV 号，获取字幕文字、起止时间、语言与人工/AI 类型，支持关键词查找、保存后的有限预览及任务内 batch 复用。指定 `?p=N` 选择该页；未指定时读取 P1 并明确标记，不展开整个合集。`doctor --source bilibili` 检查本机配置。参数见 [R25 路由说明](../../references/r25-routes.md)。

用户已扫码确认登录；会话保存在本机，配置只保存其路径。正常使用不需要复制 Cookie。

## 复用与自建

复用 [bilibili-ai-subtitle 的请求与协议结构](https://github.com/ccBilly-aipm/bilibili-ai-subtitle/blob/main/src/bilibili_ai_subtitle/extractor.py)及其 [Protobuf 轨道结构](https://github.com/ccBilly-aipm/bilibili-ai-subtitle/blob/main/src/bilibili_ai_subtitle/protobuf.py)。FS 自建统一入口、会话路径配置、输出格式及失败处理，使用 Python 标准库读取 WBI/Protobuf 索引与字幕 JSON。没有安装整套上游工具或采用浏览器 Cookie 提取。最终移除了无收益的 yt-dlp 依赖和重复提取链。

字幕 CDN 不接收登录 Cookie；携凭据的 API 请求限定主机并禁止重定向。没有媒体下载、弹幕读取、ASR 或付费转写。

## 验收结果

| 项目 | 实际结果 |
|---|---|
| 字幕与来源 | `BV1BbKw6XEWq`，CID `40065631429`，轨道 `2065388298645511424`，`ai-zh/auto`，1790 段，末 3950.94 秒/视频 3951 秒 |
| 一致性 | 最终配置三次记录的轨道、路径摘要、正文摘要和首尾时间一致；独立两次 WBI 请求也指向同一轨道 |
| 查找与保存 | “的”命中 764 段；文件保存受数量上限约束的结果，终端仅给有限预览 |
| 分 P | 两页 CID 不同；冻结代码补测 P1 时长 126 秒、28 段、末 117.12 秒、`ok`；P2 已存探测为 `no_subtitles` |
| 兼容与复用 | YouTube 英文人工字幕仍为 61 段；Bili/YouTube 两项第二轮 `executed=0/reused=2`，键与输出一致、语言/类型参数隔离 |
| 失败及安全 | 独立离线反例覆盖三级 Protobuf 截断、空正文、网络错误、无 Cookie 的 CDN 请求、重定向/域边界、URL 脱敏、Thai 类型；语法和 Skill 结构检查通过 |

独立验收绑定 `scripts/bilibili.py` SHA-256 `a4de5e9c4d01cac5ca2ffed1480dce66140248ff419a04e42569d04f13d96e7d`。其余哈希见 [SOURCE_MANIFEST.json](../../SOURCE_MANIFEST.json)。真实样本、离线反例及字段修复分别验证；较早网络证据不冒充最终版本重新联网测试。P1 的冻结版本补测由发布方另行完成。

初版使用 `/x/player/v2` 与不同请求配置，曾将同视频关联到 705、235、267 段的不同正文。这三份结果已撤回，不能作为接通证据。按上游实际源码改用 `/x/player/wbi/v2`、精确视频 Referer 和上游 UA 后，得到一致结果；未把偏差原因武断归到单一参数。

## 限制

- 只读平台已有且当前账号可访问的字幕；AI 字幕可能有识别错误，会话过期后需重新扫码。
- 暂不自动解析 `b23.tv` 短链接，请提供完整链接或 BV 号。
- `--max-segments` 截断或明显早于视频结束的字幕标记 `partial`，batch 会重试。平台缺少分 P 时长时可能回退到总时长；该元数据限制不等于正文错误。
- 验收范围为所列样本与反例，不承诺所有视频/语言均可用或固定的用量节约比例。
