> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# FS02 R2 固定提交许可证核查

核查日期：2026-09-15。以下结论来自固定 commit 的许可证文件或包元数据原文；均为“源码已读、项目未运行”，不是对依赖、模型、数据集或服务条款的完整法律判断。链接保留到可复查原文。

| 项目（固定提交） | 原文位置 | 结果与复用边界 |
|---|---|---|
| K-Dense Scientific Agent Skills (`330c8e7`) | [LICENSE.md](https://raw.githubusercontent.com/K-Dense-AI/scientific-agent-skills/330c8e764435a731eff571e3efdda70b363d0792/LICENSE.md) | MIT；脚本依赖/上游 API 条款另审。 |
| openags/paper-search-mcp (`234678a`) | [LICENSE](https://raw.githubusercontent.com/openags/paper-search-mcp/234678ab231074a7977320978ee0496dcdaddd1f/LICENSE) | MIT；各 adapter 与 API 规则不由仓库许可覆盖。 |
| vig-os/scitadel (`1d1d998`) | [Cargo.toml](https://raw.githubusercontent.com/vig-os/scitadel/1d1d9985b148c66def3ec63db6b551d5589d9d61/Cargo.toml) `[workspace.package] license` | `MIT OR Apache-2.0`；本次未找到根 LICENSE，依赖和 provider 另审。 |
| FutureHouse PaperQA2 (`57e89f7`) | [LICENSE](https://raw.githubusercontent.com/Future-House/paper-qa/57e89f7223b0960d5ee5ea048c69e3c47e088572/LICENSE) | Apache-2.0；本次只复用节点思想/源码证据，未运行。 |
| AkariAsai/OpenScholar (`0e9b8fb`) | [LICENSE](https://raw.githubusercontent.com/AkariAsai/OpenScholar/0e9b8fb912273d3dae39e593da86e4f6d3bf8de1/LICENSE) | Apache-2.0；S2/PES2O/ar5iv、模型和论文数据另有服务/数据边界。 |
| AllenAI Paper Finder (`0623cce`) | [LICENSE](https://raw.githubusercontent.com/allenai/asta-paper-finder/0623cce6ff61b0a1a637c78d352c4f4d431d0364/LICENSE) | Apache-2.0；S2/Cohere/OpenAI/Vespa 配置不随仓库许可取得。 |
| ustc-ai4science/academic-search (`b9b692e`) | [LICENSE](https://raw.githubusercontent.com/ustc-ai4science/academic-search/b9b692ed1334c858eb42d1f2710ccfcae1a43eb8/LICENSE) | MIT；目标站点/机构访问与脚本依赖另审。 |
| jonatasgrosman/findpapers (`3b42b66`) | [LICENSE](https://raw.githubusercontent.com/jonatasgrosman/findpapers/3b42b66befa0a64416258e7481201a0253f09e73/LICENSE) | MIT；Scopus/WoS/IEEE 等服务权限另审。 |
| CoLRev search-query (`f664607`) | [LICENSE](https://raw.githubusercontent.com/CoLRev-Environment/search-query/f6646075c19435a98af36eb4cfe3f34c36d5cc86/LICENSE) | MIT；它是查询 AST/翻译器，不带学术数据许可。 |
| elizagrames/litsearchr (`0c108e3`) | [DESCRIPTION](https://github.com/elizagrames/litsearchr/blob/0c108e30f03c773123da2e6fe3f7cb6581d7c523/DESCRIPTION) | GPL-3；若复制代码进不同许可组件，需单独处理 copyleft 兼容性。 |
| ASReview (`79d5682`) | [LICENSE](https://raw.githubusercontent.com/asreview/asreview/79d568212b2b0a78f9fd7be3c5117dfb890489f9/LICENSE) | Apache-2.0；模型、输入文献和部署依赖另审。 |
| CoLRev bib-dedupe (`c97feab`) | [LICENSE](https://raw.githubusercontent.com/CoLRev-Environment/bib-dedupe/c97feab2e66095a6ff8e20ac9a6381f155b993b7/LICENSE) | MIT；只审匹配节点，benchmark/输入数据不随之授权。 |
| systematic-review-pipeline (`4f8b316`) | [LICENSE](https://raw.githubusercontent.com/nayeem-hossain/systematic-review-pipeline/4f8b3166aeb6d96e06c1943fb59159a40f277cda/LICENSE) | MIT；搜索源 key、服务和数据条款另审。 |
| veale/academic-mcp (`f493de6`) | [LICENSE](https://raw.githubusercontent.com/veale/academic-mcp/f493de604eb672fdd7eb49edbc7a233c771c5a5a/LICENSE) | MIT；Zotero/S2/OpenAlex/Scite 的数据与登录边界另审。 |
| LangChain Open Deep Research (`1b7d2e8`) | [LICENSE](https://raw.githubusercontent.com/langchain-ai/open_deep_research/1b7d2e80db9faa586165c60e09096dbbfd483a64/LICENSE) | MIT；LangChain/LangGraph、模型和搜索 provider 依赖另审。 |
| GROBID (`649e14b`) | [LICENSE](https://raw.githubusercontent.com/kermitt2/grobid/649e14b1c0a18fdaef2d0b8c6d39d08c6c1d883d/LICENSE) | Apache-2.0；服务/模型资源与自建部署成本另审。 |
| MinerU (`4fe4bde1`) | [LICENSE.md](https://raw.githubusercontent.com/opendatalab/MinerU/4fe4bde114a23ee5dd637eae99b767f4669bf58c/LICENSE.md) | MinerU Open Source License：Apache-2.0 加 MAU>100m 或月收入>USD20m 时另行商业许可、在线服务需署名等附加条款；不能按纯 Apache-2.0 处理。 |

关键风险是“仓库可复用”与“接入服务可用”是两件事：学术源、全文、模型、可选商业 API 及其数据再分发条件尚未由本表覆盖。所有项目本轮均未安装或完整运行。
