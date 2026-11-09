> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# ET-BERT 独立复核

复核对象：`linwhitehat/ET-BERT main@d59470624acd11405f9e88da650cf3bf65521e9a`；本轮69行矩阵、静态/运行报告、原始源码、既有日志与公开arXiv v2的相关方法、全部编号实验对象和AppendixA.1。该复核不重复运行大模型，也不验证原真实数据指标。

## 结论

**范围内通过，未发现遗留的实质性复现成功夸大。** 当前证据支持R1 CPU合成功能测试，不支持R2/R3或论文结果成功复现。原样失败、显式兼容环境、隔离运行补丁和未执行项目有清楚区分。原始上游checkout干净。

## 证据覆盖核查

- 全部Fig1–5、Table1–5、五种任务/七个表格数据集变体已映射。每个数据集区分packet/flow版本；11个基线、Table4七行、五密码各15随机性测试、三个few-shot比例、Fig3密码分布、AppendixA.1六方法t-SNE均有覆盖项。没有把第一个README分类器当成完整实验。
- 文件/证据路径检查69行全部通过。矩阵SHA256见 `independent_review_checks.json`；核查时为`496533fc5089f9aa7f8b97b9c7c4fde70717c1c0d5bb56be22f031c74381879b`。非可执行比较/解释性实验保留缺失/部分覆盖与Unknown。
- 原base网络的12层/12头/768宽度有实际CPU前向日志；只有随机权重、2×16 token、两个人工标签。tiny预训练只有两步，分类使用8/4/4人工样本。报告明确这些不是512-token全量预训练、真实网络分类精度或可比较推理基准。

## 方法差异和版本边界

1. **精确损失probe通过独立验证。** 原 `BertTrainer.forward_propagation`第179行为`loss_mlm/10+loss_sp`。独立执行同一AST函数，输入MLM7/SP3、accumulation2，实际1.8500000238，梯度0.0500000007/0.5；与先前10/2、accum1的3和0.1/1一致。它确认对已归约loss的额外相对系数0.1，不验证Eq2/3完整sum/mean定义，更不能证明原论文实际运行代码。原函数probe耗时1.17秒，无模型重训。
2. **六历史SHA已逐个`git show`核查。** 2022-04-01快照已经有0.1系数，2024和2025有改动/回滚。当前blame到2025不能用来断言问题始于2025；也不能仅凭2022公开快照断言它就是发表实验代码。报告保留这一Unknown边界。
3. **dropout差异可核验。** `uer/opts.py`默认0.5；`load_hyperparam`的`args_dict.update(param)`被base JSON0.1覆盖。原base probe输入CLI0.5、有效0.1，符合源码。报告没有悄悄修改目标权重/dropout后声称追平论文。
4. **预处理与split probe边界准确。** 合成PCAP只在方向提取处mock；确认指定BURST helper保留MAC前缀。split probe用20会话/160人工packet，确认原packet行拆分不保证会话分离。两者都没有被写成“实际论文数据已泄漏”或确定的精度影响。
5. **few-shot歧义已保留。** 论文§4.5正文为VPN-Service，Fig4题注为VPN-App；没有替作者选择数据集后声称复现。

## 原样/补丁核查

原README分类/预训练导入失败、补PYTHONPATH后的缺数据/无GPU、原tiny训练末尾固定confusion路径失败均有日志。两项运行补丁只改输出位置及Classifier模块导入。现有对照显示同seed两次训练的41个state_dict张量完全相同；保存文件字节hash不同没有被误判为参数差异。此结论只适用于该合成案例。

原Scapy2.4.4导入失败、显式2.5.0兼容调整、一次审计harness父目录遗漏失败都被区分并保留。建议将PYTHONPATH等显式执行环境按run_id补入归档，以便汇总CSV能恢复完整命令；已通知执行代理，无需重跑。

复核入口：`papers/et_bert/independent_checks.py`；原始命令/exit0/输出为 `logs/et_bert/independent_review.{json,log}`。仍未验证：原data/checkpoint/实验commit、全部真实AC/PR/RC/F1、预训练/推理成本、baseline/ablation/randomness/t-SNE结果和原始session隔离。
