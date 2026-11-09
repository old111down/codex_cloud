> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Flowrest 独立复核

复核日期2026-11-09；复核者为负责YaTC的另一审计agent。已阅读最终静态/运行报告、83行矩阵、核心/原notebook执行harness及关键原单元，对照两版作者稿的用例、表格、评估协议和资源/延迟说明。没有重新训练模型、加载pickle、运行生成BFRT脚本或模拟交换机。

**结论：本轮限定范围内通过。** 没有发现把敏感性结果、完整UNIBS示例或静态P4表项检查冒充完整论文复现的实质夸大；两个真实CSV组件的R2边界正确。完整原论文任务、数据处理、硬件/性能仍Unknown。

## 版本和覆盖

INFOCOM2023作者稿10页：原文§IV-B明确三数据源、UNSW16/26两种难度，合计四用例；图1–7/TableI与矩阵C-*对应。README明确区分conference与full子目录，conference只给UNSW16示例。

2025 ToN作者稿18页：同一Flowrest框架、作者和仓库，新增五数据集与模拟器、模型选择、基线映射和资源/延迟评估；矩阵J-*分别列Fig1–10/TableI–VI、五数据集、packet流长度加权及缺失路径。README直接说明扩展版和full代码，因此按一个family连接两版而不重复统计合理。没有把新增IoT23/ToN-IoT或期刊复杂基线计入INFOCOM的已执行覆盖。

原文TableV UNIBS Python的macro P/R/F1=98.716/99.759/99.203%，UNSW=84.051/82.190/81.010%，与报告参照数值一致；TableVI Flowrest列364.75–436.07ns范围也与报告一致。这些参照不代表已重测。

## 数值与单因素条件

`independent_review_checks.py`用标准库从全部逐样本预测重新计算Accuracy及macro/weighted P/R/F1，不调用作者模型。对照 `core_conference`、`core_conference_time_aligned`、`core_full` 三套JSON，全部指标误差<1e-12，原始复验日志 `logs/flowrest/independent_review.{json,log}` exit0。

- UNSW原样：73249测试行，Accuracy0.645647039550028、MacroF1=0.40269406439541156。
- UNSW对照：同73249行，Accuracy0.9870305396660706、MacroF1=0.9199888480412193。
- UNIBS：19636测试行，Accuracy0.9960786310857609、MacroF1=0.9715531718280608。

原样与对照的训练输入hash、训练/测试行数、标签及行索引、特征、模型参数/seed42、树节点/叶数和执行单元列表完全相同。共用harness中唯一数据处理分支是在原cell20后将X_test的Flow IAT Min/Max/Duration同时乘1000；训练和其他配置未另换。原cell17确实只对训练作上述乘1000，cell20/prepare_test没有对应转换，属于可确认处理不对称。**这支持敏感性观察，不证实哪个条件具有正确物理单位，也不证实对照等价于原论文。** 报告已准确保留这个边界。

## 原notebook、阈值与P4

- 已独立比较UNIBS notebook的codecell清单与实际原始日志：12个codecell（0–11）顺序全部出现，notebook SHA匹配，exit0，包含grid/排序/保存。使用普通Python exec而非IPython rich display的限制已明确；这不等于期刊五用例全流程通过。
- 读取原`get_fewest_features`和调用：函数score是0–1 F1，调用阈值99；既有合成反例证明即使完美F1=1仍不能返回特征子集。报告同时说明返回值某些调用被忽略，没有夸大成所有训练必崩溃。
- 原模型/特征选择多次在X_test/y_test打分，UNIBS grid据test score排序，代码事实成立；没有独立validation或外层CV证据，但实际乐观偏差量与论文最终选择程序仍Unknown。报告没有把这个风险宣布成已证明的数据泄漏。
- 对生成脚本重新做静态AST检查，并与固定P4物理key切片对照：feature1是FlowDuration[31:29]（3位），输出末区间7..65535；feature6是FlowIATMax[31:27]（5位），末区间26..65535。两项确实越域。没有BFRT装载或P4编译证据，报告未声称它们已在硬件上触发特定错误。
- 上游 `13a527cfc0cac523b9f4be9a9366738bcdd3d5db` Git状态为空。本次敏感性是隔离harness条件，无上游修复或PR。

详细复验数据在 `independent_validation.json`。所有检查仅校验本轮证据之间的一致性与边界，不授予论文R3/R4，也不替代原始PCAP、单位、模型选择、历史SDK和真实硬件验证。
