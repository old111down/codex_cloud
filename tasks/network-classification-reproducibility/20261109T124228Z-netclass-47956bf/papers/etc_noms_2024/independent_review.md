> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# ETC_NOMS_2024 独立审查

审查日期：2026-11-09 UTC。审查者为独立候选目录代理，未参与本试点环境、模型运行或补丁实现。审查基线为 `nds-group/ETC_NOMS_2024@52de99ad76d9eff2f64a0fa28df0500e423b58b2`。本次阅读原论文、矩阵、最终报告、补丁、源码及既有运行日志，另作静态 AST/投票枚举检查；没有重新训练模型或执行任何交换机程序。

结论：**在所声明范围内通过独立审查。** R2 仅表示作者附带真实 NIMS 样本上的核心训练/压缩算法已运行；不表示论文整体、三数据集完整实验或 P4 部署复现。最终报告保留了这些边界，没有发现以表项生成或容量数字冒充硬件验证的结论。

## 全文与用例覆盖

核对九页作者接受稿及 38 行 `coverage_matrix.csv`：Fig.1 的解析、流状态、特征、表项/投票和控制器路径分别列项；Fig.2 和 Fig.3 均有 NIMS IMA、Netflow QUIC、ISCX VPN 三数据集；Fig.4 的总览和三张混淆矩阵分别列项。Algorithm 1 及最终 12 折协议、Table I 的三个数据集 × RF/XGBoost/P4、Table II 的三数据集资源结果，以及时延、背景负载和共部署声明均有对应项。取得的论文没有 Appendix；未发现可据此补写的附录实验。

静态“部分覆盖”与运行“已验证”分别使用，后者仅用于两项有实际日志的审计动作。QUIC/VPN 的 P4 模型、配置与硬件结果缺失没有被 NIMS 演示替代。仓库额外数据集也没有被算作 NOMS 原文已复现用例。

## 执行证据与等级

已核查 `readme_pcap2csv`、`readme_pkts2flows`、`notebook_subset`、`model_generation`、`table_validation` 和 `table_validation_v2` 的 JSON/原始日志。README 数据准备两次尝试分别因 `tshark` 和占位路径失败，报告未将失败改写为成功。初次表项比较失败也保留，最终通过记录另存为 v2。

核心结果来自原 notebook 的选定单元；输入 CSV 的实际 1867 行可独立计数，报告列明过滤后 1714、1285/429 划分及跳过的搜索、保存和硬件后处理单元。91.6084% accuracy 是该样本 Python 离线路径的结果，报告明确不能与论文硬件 89.74% 直接比较。原始 PCAP、全量 12 折、全部三用例、资源和性能仍为 Unknown。仅一次固定 seed，也没有被描述为稳定性或训练时间基准。另核对 cell6 的 shuffle/split、cell12 的未压缩 RF，以及 cell1 `RF_evaluation` 中最终压缩 RF，均明确设置 `random_state=42`；不是只固定划分而遗漏模型随机种子。

上游 `git status --short` 为空。环境清单、数据/模型来源及哈希存在，旧 sklearn pickle 在使用前的静态审阅及其局限也有记录。环境组合被描述为本轮兼容选择，没有冒称作者原始完整环境。

## 投票语义补丁

独立读取随附 `Switch/table_entries.py` 的 AST，并枚举全部 `6^5=7776` 个五树类别组合：随附票表为 5256 项，非唯一众数组合为 2520；缺失项按 P4 `set_default_result` 使用 `class0`。这一行为与显式唯一众数策略的有效输出差异为 0。现代 `statistics.mode` 的有效输出与随附表有 360 个组合不同。补丁后生成的票表为 5256 项，和随附表的有效投票差异为 0。

因此 `0001-unique-voting-mode.patch` 的“恢复随附表语义”有证据支持。这里并不推断原作者运行时一定使用了哪个 Python 版本，也不将离散硬投票等同于 sklearn RF 的类别概率平均预测。P4 源码 `size=5256` 是声明容量，不能当作编译后 SRAM/TCAM 使用率或成功装表结果。

## 位宽补丁与剩余语义边界

对补丁后的**所有** feature range 项作静态检查，而非只检查末端值：

| 表 | P4 键位宽 | 项数 | 完整区间 | `0 <= start <= end <= max` | 排序后间隙/重叠 |
|---|---:|---:|---|---|---|
| feature0 | 15 | 64 | [0,32767] | 全部通过 | 无 |
| feature1 | 16 | 159 | [0,65535] | 全部通过 | 无 |
| feature2 | 8 | 111 | [0,255] | 全部通过 | 无 |
| feature3 | 16 | 244 | [0,65535] | 全部通过 | 无 |

原样输出的 feature0/2 末区间越过相应键域。既有最终验证还对全部 feature/code/voting/target-flow `add_with_` 参数集合与随附表作了精确对照，exit 0；端口配置差异明确保留。该证据支持固定模型的编码修正，**不支持“完整部署已修复”**。

Notebook `extractKBits` 在共同非负整数 32 位域中，取高 15/8 位与 P4 `[31:17]` / `[31:24]` 静态相符；当前固定模型阈值生成的全部区间已满足上述位宽。补丁 0002 仅改末区间上界，未为任意未来模型提供阈值缩放、截断或越界拒绝策略。P4 32 位时间戳和 16 位总长度的溢出、原始包单位/帧长度与 IP 长度口径、长 IAT、包截断、寄存器碰撞、控制器清理时序及硬投票与软件概率预测等价性，均没有包级或真实硬件证据，继续为 Unknown。

## 独立检查记录

执行命令（审计根目录）：

```bash
python scripts/run_logged.py --log logs/etc_noms_2024/independent_review --timeout 30 -- python papers/etc_noms_2024/independent_checks.py
```

结果 exit 0。精确 argv、UTC 时间及 stdout/stderr 在 `logs/etc_noms_2024/independent_review.{json,log}`；结构化结果在 `independent_review_checks.json`。检查脚本只解析源码/已生成文本并枚举投票输入，不调用 BFRT、不编译 P4、不做交换机软件仿真；这些动作没有改变试点复现等级。
