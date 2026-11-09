> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Mousika 独立论文—矩阵复核

复核日期：2026-11-09 UTC。本复核者独立取得并通读 INFOCOM 2022 原文（10 页）和 ToN 扩展作者稿（14 页），建立 `evidence/mousika/access_research/infocom_inventory.md` 与 `ton_inventory.md` 后，对照 `coverage_matrix.csv`。复核快照、矩阵 SHA256、行数和状态统计见 `independent_review.json`。

**结论：当前矩阵的论文对象与用例清单完整，版本边界正确；这不表示论文实验已经复现。** 82 行中唯一“已验证”记录是限定范围的审计 Smoke Test，论文实验行均未写为完整执行。全量精度、时间、性能、资源和物理硬件结果仍未验证。

## 逐项清单

| 论文对象 | 对应 claim_id | 独立核对结果 |
|---|---|---|
| INFOCOM Fig.1、2 | I-F01、I-F02 | 架构图与完整框架分开；概念图不适用，端到端路径仅部分覆盖。 |
| INFOCOM Algorithm1 | I-ALG1 | BDT Gini/递归/终止条件单列；组件测试不当作完整方程/全数据等价验证。 |
| INFOCOM Table I、Listings1–2 | I-T1、I-L1、I-L2 | 编码、初始化表、分类表分别列出；未宣称 P4 构建或转发已成功。 |
| INFOCOM Fig.3–5 | I-F03/04/05-{flow,traffic,malware} | 三个任务各自展开；三位教师 RF/GRU/LSTM、精度、训练时间、规则数覆盖。原仓库缺 LSTM 与两种非 UNIV 数据路径明确记录。 |
| INFOCOM Fig.6–10 | I-F06/07/08/09/10-{flow,traffic,malware} | 三任务各自记录吞吐/零丢包、阶段/表/表项、TCAM/SRAM、crossbar/VLIW、40/100Gbps 延迟。缺硬件与测量代码均明确。 |
| INFOCOM 划分协议、附录 | I-DATA-SPLIT、I-APPENDIX | 日期与五元组无交叠划分单列；已得全文无附录正文，另行补充材料 Unknown。 |
| ToN Fig.1–3、Algorithm1 | T-F01/02/03 | 概念、框架、位 BDT 与 Gini 算法分开；Algorithm1 在 T-F03 的 paper_section 明示。 |
| ToN Table I、Listings1–2 | T-T1、T-L1、T-L2 | 与 INFOCOM 对象编号及版本分开；v2 到 main P4 的依赖明确。 |
| ToN Fig.4–11 | T-F04/05/06/07/08/09/10/11-{flow,traffic,malware} | 三任务分别展开，涵盖混合参数、五教师、accuracy/F1/precision/recall、时间/规则数及其增量。RF/GBDT/MLP 参数别名仍调用 RF、NN 默认 GRU 的实际代码缺口没有被隐藏。 |
| ToN Fig.12–14 | T-F12/13/14-{flow,traffic,malware} | Fig.12 是 Python 与 H3C P4 精度一致性；Fig.13–14 才是三个物理交换机吞吐与延迟。构建、仿真、硬件没有被编码测试替代。 |
| ToN Fig.15 | T-F15 | H3C 恶意检测资源与 IIsy/Planter/pForest 对比单列；缺基线/编译器资源报告/硬件。 |
| ToN Fig.16 | T-F16-{flow,traffic,malware} | 三任务基线精度对比分开；pForest 仅部署 RF 的 4/10 棵树的设置已记录。 |
| ToN Fig.17、18 | T-F17、T-F18 | BDT 规模扫描与 Deep Packet/SAM 教师比较均单列为缺失，没有遗漏 README 之外的实验。 |
| ToN 外层五折、网格搜索 | T-OUTER5FOLD、T-GRID | 与内部 KFold(2) 软标签生成区分。论文五折评价和搜索流程无完整代码，标缺失。 |
| ToN 混合部署建议、附录 | T-HYBRID、T-APPENDIX | 混合 switch/server 是 VII-F p12 的讨论建议，未当作已实现/评估结果；无附录正文，另行补充材料 Unknown。 |

## 版本与执行边界

INFOCOM 只评估 RF、GRU、LSTM 三位教师，使用日期/五元组划分和直接软标签蒸馏；ToN 加入 GBDT、MLP、硬/软标签混合及五折评估。当前矩阵将 `I-` 与 `T-` 前缀分离，未将后版条件套用于原论文。

三个用例均有独立行：UNIV1 elephant/mice、ISCX 六应用、Bot-IoT 合法/恶意。UNIV 流大小预测样本的组件 Smoke Test 不能验证 ISCX 应用分类。已读取 scoped Smoke Test 日志：Tree/SoftTree 预测均通过；Tree 的原始浮点标签导出到整数 converter 失败另留证；SoftTree 规则转换和五份作者规则转换通过。它们只验证这些输入上的 CPU 组件行为。

复核中提出的三项矩阵定位修正已在最终读取的快照解决：ToN 混合建议章节为 VII-F p12；四处 UNIV 数据路径添加 main checkout 前缀；Fig.12 仅使用 H3C 的准确范围。未修改被审计代理的静态报告、运行报告或矩阵。

仍需保留的限制：矩阵“部分覆盖”表示可定位到相关组件，不能读成已运行完整实验；原始抓包处理/划分、完整标签与参数、各教师和基线、外层评估、P4 构建/软件仿真/物理测量仍有缺口。算法修复的微小反例不能证明与作者实验等价。没有发现可以提高 R1 Smoke Test 上限、或将应用分类从 R0 提升的论文指标证据。
