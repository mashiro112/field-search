> 历史文档共享副本 · 发布于 2026-09-17。保留当时的结论、失败、限制和计划；旧授权、自动续接、模型配置与“下一步”不作为当前执行指令。科研默认流程以 FS03 为准。已移除内部任务标识、替换本机路径并调整链接；没有重新运行历史验证。

# 已审代码节点的功能重合

只比较相同代码层及本次审查范围，不推断整个项目缺少未审能力。1=确认具备；0=已审范围不提供；?=未知。等权 Jaccard=双方共有能力数/能力并集数，仅在双方都已判断的维度计算。

同时列已知维数与把未知格补为0/1所得的逻辑上下界。这不是统计置信区间；区间宽时不能排名。两个已审集合都为空时指数不定义。实现粒度、实际来源及依赖另见报告和源码表。

## 与当前 field-search 代码范围比较

| 候选 | 已知格重合（交/并） | 已知维数 | 未知补全范围 |
|---|---:|---:|---:|
| K-Dense Scientific Agent Skills | 25.0% (2/8) | 13/15 | 20.0%–33.3% |
| openags/paper-search-mcp | 33.3% (3/9) | 13/15 | 27.3%–33.3% |
| vig-os/scitadel | 44.4% (4/9) | 11/15 | 30.8%–44.4% |
| FutureHouse PaperQA2 | 66.7% (4/6) | 11/15 | 40.0%–71.4% |
| AkariAsai/OpenScholar | 27.3% (3/11) | 13/15 | 23.1%–33.3% |
| AllenAI Paper Finder | 16.7% (1/6) | 8/15 | 7.7%–44.4% |
| ustc-ai4science/academic-search | 37.5% (3/8) | 11/15 | 25.0%–37.5% |
| jonatasgrosman/findpapers | 25.0% (2/8) | 11/15 | 16.7%–40.0% |
| CoLRev-Environment/search-query | 14.3% (1/7) | 15/15 | 14.3%–14.3% |
| elizagrames/litsearchr | 12.5% (1/8) | 11/15 | 8.3%–30.0% |
| ASReview | 33.3% (1/3) | 3/15 | 6.7%–75.0% |
| CoLRev bib-dedupe | 42.9% (3/7) | 13/15 | 33.3%–42.9% |
| nayeem-hossain/systematic-review-pipeline | 50.0% (4/8) | 9/15 | 28.6%–60.0% |
| veale/academic-mcp | 50.0% (6/12) | 13/15 | 42.9%–50.0% |
| LangChain Open Deep Research | 33.3% (1/3) | 4/15 | 7.1%–71.4% |

## 候选之间

完整两两结果见 [OVERLAP.json](OVERLAP.json)，原始格与出处见 [严格代码矩阵](CAPABILITY-MATRIX-CODE.json)。没有按重合高低推荐整套产品。

## 验证

计算脚本对全部二维三值向量组合做穷举，逐个检查未知补全上下界；JSON维数与唯一ID检查通过。可在本目录运行 `python calculate_overlap.py` 复算。
