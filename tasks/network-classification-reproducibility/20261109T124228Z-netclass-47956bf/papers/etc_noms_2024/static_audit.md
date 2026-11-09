> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# ETC_NOMS_2024 静态覆盖审计

审计对象为 NOMS 2024 会议版本，DOI `10.1109/NOMS59830.2024.10575394`。作者接受稿九页已读取：III 方法（pp.3–5）、IV 实现/实验设置（pp.5–7）、V 评估（pp.7–8）；p.9 为参考文献，未见 Appendix。2025 IJNM 扩展版不在本次全文审计范围。

论文 p.1 脚注直接指向 `nds-group/ETC_NOMS_2024`，上游 README:3,11,31–39 反向引用论文及 DOI，关联已核实。固定 `main@52de99ad76d9eff2f64a0fa28df0500e423b58b2`；提交时间 `2025-06-18T23:40:55Z`。GitHub API 的 pushed_at 为 `2026-02-02T23:37:02Z`、updated_at 为 `2026-10-13T09:04:25Z`，这些仓库级字段不等于当前分支最后源码变更时间。未发现 LICENSE/COPYING，API license=null，许可证为 Unknown。

## 覆盖边界

`coverage_matrix.csv` 按原文 Fig.1–4、Algorithm 1、Table I–II 及三种用例分别列项，共 38 行（包括两项审计运行验证）。表格中的“部分覆盖”表示找到了相关实现，不表示论文实验已执行；“已验证”仅用于本次有日志的明确审计动作。

| 用例 | 离线源码 | P4/编码/控制器 | 数据 | 原论文评估覆盖 |
|---|---|---|---|---|
| NIMS IMA，6类，前8包 | `Offline_ETC/noms2023_ima_only_traffic_classifier.py`；共享基类；模型准备 notebook | 有固定4特征/5树的 NIMS 实现 | 一天的1867行派生样本、429行test、一个RF pickle；原PCAP未获取 | 样本核心测试通过；完整12折、硬件混淆矩阵和资源/时延 Unknown |
| Netflow QUIC，5类，前4包 | `Offline_ETC/netflow_quic_traffic_classifier.py` | 无独立用例的 P4、RF权重、编码配置或硬件结果CSV | 外部链接；未获取 | 静态离线路径部分覆盖，P4用例关键产物缺失 |
| ISCX VPN，7类，前8包 | `Offline_ETC/iscxvpn2016-vpn-classifier.py` | 无独立用例的 P4、RF权重、编码配置或硬件结果CSV | 外部链接；未获取 | 静态离线路径部分覆盖，P4用例关键产物缺失 |

README:20–26 列出全部三个用例，同时明确只提供 NIMS IMA 的 Python/P4 示例，不能由“相同方法适用”推导全部论文实验可执行。仓库额外包含 UC Davis QUIC、CSTNET-TLS1.3 和10类NIMS脚本；Offline_ETC/README.md 明确前3数据集才保留在会议论文，因此不把额外脚本算成 NOMS 原文评估。

## 方法与实现差距

- **Algorithm 1 与 notebook 评估协议不同。** 原文 III-A 声明最终模型12折交叉验证；共享类 `_generate_data_folds`（147–192）提供分层K折，离线CLI默认12折。附带 notebook cell6 使用一次75/25分层切分，cell8/13 在同一测试集上选择模型/压缩参数。不能把运行该 notebook 的测试分数称为原文12折结果。
- **原始数据抽取存在两套口径。** `Offline_ETC/data_preparation/pcap2csv.sh:4` 导出 `frame.len`、`frame.time_delta`；离线类逐流汇总这些 IAT。`In_switch_ETC/.../pre-processing/extract_pkts.sh:4` 导出 `ip.len` 和时间戳，`extract_flows_from_txt.py:73–106` 再计算逐流时间差并转纳秒。P4 使用IP长度和逐流时间信息。两个流程的特征等价性 Unknown，原PCAP/完整中间产物未获取。
- **离线 min_iat 静态缺陷。** NIMS IMA脚本:259、ISCX脚本:228 从整个CSV `df_new` 而非当前流的前n包取最小正IAT；NIMS脚本:157还对全流而非截断前n包取值。Netflow脚本:239则用当前截断流。此处只记录静态问题，未在本轮修复，也没有将其影响量化为论文准确率偏差。
- **离线 RF 返回值接口不一致。** 共享 `RF_predict:1109` 返回3项，NIMS IMA调用点:801、ISCX调用点:784及其他脚本部分调用仍解包4项，后续还访问已注释的 `y_test_isolated_flows`。完整数据缺失，未运行到该分支；属于静态确定的接口风险，不声称其是本轮完整实验的已观测异常。
- **P4 编码固定配置。** generator 固定4特征、5树、6类和 `bfrt.noms_20_5_4`；P4:584固定第8包触发，不能不改配置直接覆盖论文QUIC第4包/1树情况。其模型规模、位宽和投票表容量需同步生成/审查。

## 已运行验证的编码问题

1. 原样 generator 在Python3.8.20/scikit-learn0.23.2下退出0，但产生7776个票表项；随附P4:501–511容量为5256。Python3.8起 `statistics.mode` 在并列众数时选择先出现者，generator:312–319依赖旧版抛异常的行为。2520种非唯一众数输入应由随附P4 `class0` 默认动作处理；现代mode在其中360种输入上改变最终有效类别。独立兼容性补丁 `0001-unique-voting-mode.patch` 显式恢复唯一众数规则。
2. 只修复投票后，首次全表项对照仍失败，日志 `table_validation.log` 保留原始断言。generator 给所有特征末区间使用65535，但 P4:433、445分别匹配15位和8位压缩IAT；随附表的末值是32767、255。`0002-feature-range-domains.patch` 按固定P4配置给出15/16/8/16位域上界。
3. 两补丁后，所有生成的 feature/code/voting/target-flow 表项的参数集合与随附 `Switch/table_entries.py` 精确相同；7776种树输出组合的有效投票决策全部一致。该验证不包含BFRT调用、P4编译或包级仿真，也没有证明P4硬投票与scikit-learn RF的概率平均预测等价。

生成脚本仍只配置QSFP cages1、5；随附交换机表项脚本配置1、5、9。该部署差异没有静默修复。最终输出不是整个部署脚本字节相同，只有已比较的表项参数集合一致。

## 部署与指标限制

P4程序依赖TNA、Intel SDE9.7.0/BFRT；控制器启动时读取 `SDE_INSTALL`，并导入专有接口。仓库没有BMv2移植、软件交换机拓扑或集成测试。当前主机没有 `bf-p4c`、`p4c`、`simple_switch` 和Tofino硬件；没有安装或取得专有SDK。

Table II 中SRAM/TCAM/Xbar/VLIW等所有资源比例、383–398ns延迟、与 `switch.p4` 共部署增加25%资源、40Gbps背景负载和线速推理均未复现。原文IV-A明确仅目标流量参与分类，40Gbps是背景流量注入速率，不能写成已测分类吞吐。

代码、论文、数据和模型的来源/校验值见 `metadata.json`、`evidence/etc_noms_2024/upstream_files.csv`、`data_model_sources.json`；命令、环境、补丁效果和原始日志见 `reproduction_report.md`。
