> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS01 复现与优化结果

2026-09-07。Home：[internal-id-omitted]。契约与canonical为唯一规格和状态入口。

**已交付 FS01-v4.1，独立验收通过，限于下述已运行能力与任务条件。** 安装位于 `installed-field-search/`；157个安装文件与release-manifest逐项SHA一致，未闭合必修项为零。独立结论见[evidence/independent-review.md](evidence/independent-review.md)，调用和恢复见RUNBOOK.md（本地历史引用，未随本批发布：`RUNBOOK.md`），便携文件包见field-search-FS01-v4.1.zip（本地历史引用，未随本批发布：`field-search-FS01-v4.1.zip`）。包不含本机隔离运行环境，迁移要求见调用说明。

**FS01-R2-v2.1 已按限定范围 conditional pass（2026-09-08）。** C1 独立Verdict见runs/r2/critic/FS01-R2-v2.1/VERDICT-PACK.md（本地历史引用，未随本批发布：`runs/r2/critic/FS01-R2-v2.1/VERDICT-PACK.md`）。本次采用统一 `search.py` native-first入口与 native-sufficient stop、recent 一次已运行引擎的完整记录/低排名/partial保全、document 明确选用时的全文快照/失败保留/离线分页/find，以及已核验的平台/资源/超时/取消指导。候选代码与v2相同：`candidate-manifest-v2.1.json` SHA256 `c249e54450c6b13548019652f9132f2eb886af30ab88836c504d40c0735554b6`；Result Pack SHA256 `2633160071aa6d1150d39605c4d608a9a7484a8050ba0432173795fe88946cd1`；`final-evidence-manifest-v2.1.json` SHA256 `02395ed6329a3b6b1740d8931ca85435ea99e64804e49ef51efac382a85566df`；`final-verification-v2.1.json` SHA256 `ee7349cff262f1433150c84d0dfd3c26dfb04da06020f627a13e2cc1058cf203`。这些SHA标签已按C1报告更正。

该限定发布不证明宿主自动发现或自然调用 document helper；B2仍是长期未验证缺口。也不宣称所有URL自动路由、收费/登录/完整websearch或独立研究服务复现、速度/因果优势、全面胜过成熟工具或完整网页语义。v1/v2 return、失败首答、v4.1基线和未运行候选均保留；真实 native gap 出现且已有helper适用时再按方法复查，不强造任务。

## 做了什么

读取原始Grok报告全部4页扫描图；PDF推荐的“跨社区搜索、research持久化、100问、访问补充、项目目录”属于不同能力层，不能混成一个已复現工具。首轮真实选择research-skill、last30days、Deep Discovery作为方法/引擎代表，Supersearch和新发现websearch实部署并查明可运行边界，其余按增量与依赖处置。所有原源码、许可、SHA与日志位于deployments/evidence；未买服务、未转换订阅凭据或突破访问控制。

## 原方案运行账本

| 对象 | 实际运行 | 结论边界 |
|---|---|---|
| hec-ovi research-skill 1095897 | T1与H1分解/多源搜读/反例/综合，均已完成Home存储与二次取回；另完成逐调用存档的T1独立复跑及存储取回 | 同宿主方法移植；Opus不可用，最早T1索引初次落盘顺序偏差公开。非作者同模型复现 |
| last30days 3.23.0 / 56ba5ac | 预研计划→Reddit/HN/GitHub采集与原排序→全报告核验→原文综合，48.154秒引擎 | 完整selected keyless workflow；未复现收费/登录/视频分支；包含约20分钟部署/候选并行工作，不与另一臂纯检索秒数直接比赛 |
| Deep Discovery ad261d3 | 完整100问100答、10问题/10强项/修正结论，492秒+少量前读 | 结构自审已复现；未证明额外信息召回或比简短审视更有收益，不默认整合100问 |
| Supersearch a3d3829 | 10 Skill隔离链接部署、56 Node+6 Python原测试、微信实搜5条；4 xAI分支实际报告无key | 未完整复现聚合器；缺授权账号部分不能靠更多微信结果补齐 |
| websearch 0.6.1 / 1bd31c8 | 隔离安装36依赖；init→search失败→doctor→针对检索仍失败；fetch被保留地址DNS安全检查拒绝 | 完整原始搜索栈未复现；未关闭检查。Jina公开响应作为输入的原extract/paginate已运行，六页无损拼回，仅复用组件 |
| 其余候选 | 见evidence/candidate-disposition.md | LangChain/Jina自主引擎缺独立LLM/API条件；AI4Scholar无key；目录/重叠编排未伪称运行。不能宣称超越 |

## 冻结同题比较

| 决定条件 | 原research-skill T1 | field-search-v3 T1 | 判断 |
|---|---|---|---|
| NTFS/SMB后端选择 | watchdog原生+显式轮询；已有watchfiles可保留 | 相同 | 本题持平 |
| 事件不等于写完 | API/源码与反例，生产者完成协议 | 相同，另读维护者#367及微软重命名案例 | 核心结论持平；额外来源不是通用胜出 |
| 恢复/遗漏 | PollingEmitter OSError停止、补扫/重建 | 相同 | 持平 |
| 可行动/不过度承诺 | 未实跑SMB，明确试验参数 | 相同，更完整试验矩阵 | 持平；没有本地兼容性能实验 |
| 成本/时间 | 搜6/读6，215秒到资料核查，不含输出与Home存储 | 搜5/读7+2匿名GET，343秒含报告 | 计时终点不同，不作速度优胜结论 |

T2：last30days完整keyless工作流找到T3/OpenClaw与WAL复盘；field-search-v3独立检索找到Hermes的旁文件替换、未合并锁方案与后续失败，区分多进程/多连接。两臂都没有找到对方全部具体事故，**召回互补，单独v3不能宣称全面持平原引擎**。因此选择接入原引擎而非替换它。集成后重复运行保留全部36条/19 GitHub、完整嵌套限流、准确as-of窗口，原文综合吸收两路关键证据。原引擎51.687秒，新增包装成本不可从两次直播差异精确拆出。

## 已安装的修改

1. scripts/recent.py：调用已有固定版本完整免费引擎；显式date/plan/新目录，完整原始结果与证据索引保留低排名项目、有效计划和嵌套失败；宿主继续读原文与综合。
2. scripts/document.py：复用已安装websearch的HTML清理与无损分页，沿既有Jina公网读取；显式任务快照、SHA、离线find/open。原始SQLite文档42,257字符，旧入口只给前6,000字符且混有HTML；新提取34,109字符六页，第4页有checkpoint starvation、第5页SQLITE_BUSY、第6页修复版本和近期复现，连接不会因最后一页被截而丢失。无损是相对提取文本；原网页完整性不保证。
3. Skill按真实差距增加按需路由与事故日期/进程拓扑/修复状态判断，保留原轻量核心。未设默认全部工具并发、长期知识库或新全局Harness。

## 验证与恢复

新增行为检查初版8项通过；审查找到跨分页短语漏检，修成在完整提取文本查找再映射起止页，新增第9项回归通过，独立边界复验通过。原采集器9项集成和23项回归通过。首次运行旧回归缺sys.path，用明确脚本目录复用后通过；首次许可证检查发现新增runtime来源未在Skill保留LICENSE，补齐后通过。保存了原失败记录的会话；最终日志见evidence/test-*.txt。

v3全量快照与SHA在baseline/field-search-v3；v4候选冻结在baseline/field-search-v4-candidate（留出前冻结）。H1后跨页find修订仅为独立边界缺陷，不使用H1结果调参。返回安装文件需逐一比对本次hash，保留后续用户修改。

## H1留出结果与审计限制

两臂均推荐ZIP-only标准库逐项读取，加私人暂存、Windows名称拒绝、实际输出与进程资源预算、嵌套默认不递归且递归时全树共享预算。都明确未实跑安全解压器，未把库名字等同安全保证。field臂读到CPython真正_extract_member与libarchive manpage，找到safezip递归重建计数器和Ubuntu-only CI；原方法臂发现stream-unzip/Deflate64兼容路线，但相关原文多未成功显示，仅作待核候选。此题支持核心决策与边界无退化，不证明任何脚本自然触发：field臂明确未调用document.py。

H1预算按预定工具调用批次：field搜索4批11query、读取8批22URL，339秒含报告；原方法搜5批15query、打开10URL（部分失败/仅元信息），143秒到末次资料核查，不含答复/存储。实际URL工作量与计时终点不同，不能据此宣布因果或速度优胜。

原T1第一臂最初未逐次保存完整web对象。后来由原代理导出5份当时确实可见的关键摘录，保留原工具ID、URL、行号和范围时间；它们支持核心条件，但不等同完整历史对象。新增research-auditable-t1是盲于旧答案的后来独立复跑，每调用立即保存完整返回，不能回填为旧日志。11份原始JSON和SHA已经独立核验：5搜索批15query、6读取批19URL尝试/15不同目标，399秒；Home随后完成原方法存储与INDEX→Summary二次取回，未新增网页调用。它再次支持NTFS原生/SMB轮询、完成协议、轮询故障监督与补账等核心结论。不同运行时点、实际访问量和计时终点不支持速度排名。H1原方法仍有原始对象未逐调用落盘的限制，不能当严格盲法大样本实验证明。
