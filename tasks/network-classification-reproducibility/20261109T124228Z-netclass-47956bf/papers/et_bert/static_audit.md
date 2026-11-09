> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# ET-BERT 全静态覆盖审计

本轮阅读公开arXiv:2202.06335v2（2022-02-19）全部11页，含§3方法、§4.1实现/数据、§4.2–4.5评估、§5局限和AppendixA.1。共有Fig1–5、Table1–5；Appendix的Fig5为六方法t-SNE，不是可忽略的附属演示。最终ACM排版未另行完整取得，原论文与此预印本独有差异为Unknown。固定源码main `d59470624acd11405f9e88da650cf3bf65521e9a`（2026-07-23），MIT；论文首页明确给出该作者仓库，关联已核实。

## 已确认事实：核心机制公开，但未覆盖整套论文实验

公开代码包含BURST/相邻字节bigram与词表构建、BERT式mask/SBP样本生成、Transformer、MBM/SBP目标、CPU/GPU预训练、随机/预训练初始化的通用分类器，以及推理入口。它超过单一前向演示的范围。不能据此认定全部论文实验可完整复现。

69行 `coverage_matrix.csv` 逐项涵盖：七个数据集变体（Cross-Platform iOS/Android、USTC-TFC、ISCX-VPN-Service/App、ISCX-Tor、CSTNET-TLS1.3），每个变体的packet/flow两种ET-BERT评估，11个比较方法，Table4全部七行，五种密码×15项随机性测试，Fig3密码分布，Fig4三个few-shot比例及AppendixA.1全部六种t-SNE。

原数据、七数据集的确切样本ID/标签映射/划分、原checkpoint、全部基线驱动、few-shot采样与运行配置、随机性样本/NIST测试、cipher统计和t-SNE脚本没有在固定checkout中形成可重放的完整流程。作者Google Drive数据/权重链接存在，但完整性与实际可获取文件未核实；不把“尚未获取”写成“数据不存在”。目录与符号证据为 `evidence/et_bert/upstream_files.json`、`source_symbols.json`。

## 已确认方法—代码差异

1. **预训练目标权重。** 公开论文§3.3 Eq4为`L=L_MBM+L_SBP`。当前 `uer/trainer.py:BertTrainer.forward_propagation:179` 为 `loss=loss_mlm/10+loss_sp`。原函数精确数值probe输入10与2得到3，而不是12；梯度分别为0.1与1。该probe只验证传入已归约loss张量后的额外0.1系数，不验证Eq2/3整体sum/mean归约的等价性。`loss_history.json` 显示0.1权重已存在于2022-04-01的`cbd7c8af...`；2024-11版本改成不加权sum，2024-12回滚为包含第三个tov项的版本，2025-03又恢复0.1。当前blame到2025不意味着该差异只在2025才出现。原论文实验究竟采用哪个版本仍Unknown，不能据此直接断定发表结果错误。
2. **dropout与序列长度。** §4.1.3称fine-tune dropout0.5，`uer/opts.py`亦默认0.5，但 `load_hyperparam`用base/tiny JSON中的0.1覆盖CLI，即使显式`--dropout0.5`也会被覆盖。原模型probe已实际记录0.5→0.1。论文§3.1 pretrain512 tokens，README/preprocess默认128，缺精确原始配置；这属于需确认的默认配置差异，不证明作者当时未传其他参数。
3. **预处理路径不一致。** `get_feature_packet/get_feature_flow`固定切除前38字节；`vocab_process.preprocess`也切38字节；`data_process.dataset_generation.get_burst_feature`直接截取完整frame前64字节。对合成Ethernet/IPv4/TCP PCAP、仅mock方向提取边界后，原BURST helper首token仍是MAC前缀`aabb`。说明该helper包含头部；实际论文corpus使用何路径Unknown，不能把本probe等同于原数据泄漏证据。
4. **packet split无session保证。** `dataset_extract`对packet行做StratifiedShuffleSplit（41/42），不传session/group。执行原split函数，以20个已知session的160条合成packet为边界输入后，train/test共享11个session。确认此代码不保证会话隔离；实际论文样本是否泄漏、规模和对指标的影响仍Unknown。
5. **few-shot数据集命名。** §4.5正文写ISCX-VPN-Service，Fig4 caption却为ISCX-VPN-App。没有原subset及脚本可消歧，不能替作者选定一个版本后称结果复现。

## 运行观察

README原样分类/预训练缺uer模块路径，inference缺run_classifier模块路径。添加明确PYTHONPATH后，分类进一步因作者数据文件未在本地而停止，8-rank预训练因无GPU而停止。合成tiny分类原代码确实训练完成，但最终evaluate(True)因硬编码绝对confusion输出路径失败。隔离两项运行修复后训练和推理通过，41个权重张量与原样训练完全相同。

原版Scapy2.4.4在本机Python3.8上导入失败（ctypes找`libc`过程中报`liblibc.a`不存在）；显式调整到2.5.0后通过。原始失败和一次审计harness目录遗漏失败均保留，后者属于本审计测试设置失误，未归咎上游。

## 合理推测与未知

MLM相对权重、dropout及预处理分支改变可能影响学习到的表示，因此需要作者实验commit/配置及受控敏感性实验；本轮没有测出它们对论文Accuracy/F1的影响。会话相关性可能导致过于乐观的packet评估，但需要原始session ID和group-disjoint对照才能证实。全部真实数据指标、完整预训练/基线/附录重现、原始GPU成本和时延吞吐均Unknown。本项目没有P4部署用例。
