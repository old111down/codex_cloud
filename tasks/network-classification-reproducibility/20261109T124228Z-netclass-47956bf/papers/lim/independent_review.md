> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# LiM 独立复核

复核日期：2026-11-09 UTC。复核者与 LiM 执行审计代理分离；本复核没有修改上游、覆盖矩阵、静态审计或运行报告。范围为已归档 arXiv:2502.00586v2 的7页全文、`upstream/lim` 的两个 Python 源码、固定提交清单、运行日志、预测与指标，以及最终 `reproduction_report.md`。

结论：现有证据支持“作者提供的 CSV 上核心离线分类达到 R2”，不支持论文原始评估、资源性能或在线能力复现。报告清楚保留了这一边界，没有把接近或高于论文的 accuracy 当成论文复现成功。未发现遗漏已取得预印本中的编号表格或明确实验用例；最终 ACM 版未取得，最终版独有变化仍为 Unknown。

## 覆盖复核

| 论文内容 | 矩阵覆盖 | 独立判断 |
|---|---|---|
| §3.1 NetMatrix 三个字段、五个加密应用数据包、双向会话、30字节表示 | M1–M3 | 覆盖；指出缺少会话切分、原始 PCAP、TLS1.3 显式版本检查及30字节打包器 |
| §3.2 原样 vanilla XGBoost | M4 | 源码和原始分类器日志对应；已验证仅指该 CSV 的执行 |
| §4 每类400样本、十类的平衡评估 | E1 | 已识别实际4514行、两类不足400，与论文4000样本协议不等价 |
| §4.1 原硬件、Python/XGBoost版本 | E2 | 论文环境与本轮 README 兼容环境分开记录 |
| Table1 三个模型及 accuracy/recall/precision/F1 | T1-LiM、T1-ETBERT、T1-YaTC | 全部覆盖；两基线缺少对齐处理、权重、配置，未宣称已运行 |
| Table2 训练秒/样本、推理内存、GPU功率、吞吐 | T2-latency/memory/energy/throughput | 全部覆盖；整体进程用时未冒充论文计时或吞吐，GPU无测量保持 Unknown |
| §4.3.2 派生百分比声明 | T2-derived-percent | 已补入论文百分比算术不一致，绝对数值与派生关系分开 |
| §1 秒级适应新类别；C5 无握手/0-RTT/会话恢复/连接复用 | C1-newclasses、C2-handshakeless | 覆盖；没有专用增量或鲁棒性实验，均未验证 |
| 全文图与 Appendix | S1-figures、S2-appendix | 所获7页预印本只有 Table1/2，无编号图、无 Appendix；最终排版差异 Unknown |

矩阵当前18条：已验证1、部分覆盖6、缺失9、不适用2。这里是证据/代码覆盖状态，不是18项科学结果的复现通过率。

## 独立数值和资产检查

实际执行 `python papers/lim/independent_validate.py`，退出码0；完整输出见 `independent_validation.json`。该脚本只用 Python 标准库重新计算归档预测，没有重跑或修改分类模型。

- 测试903行中861行预测正确，accuracy=`861/903=0.9534883720930233`，与首次原样执行日志及 `metrics.json` 一致。
- 逐类 precision、recall、F1 与 `metrics.json` 的误差均小于 `1e-12`；903个 CSV 行索引唯一，真实标签逐一匹配4514行源 CSV。
- 源码 SHA256 `5d85513faae13ea905acfa07bbdacc4a962638480c79d7bc08d8594ac1ab3877`、CSV SHA256 `4385b283d64cf20346562bc4c389466aea4c9c5a4b240254d1acb4d76126f3d7` 与归档指标一致；上游 HEAD 为 `1b8ca187f7d02a51e595f797e5c200ae740b459f`，`git status --porcelain` 为空。
- `readme_classifier.json` 记录原样脚本退出0；`readme_preprocess.json` 虽退出0，但只生成表头。报告明确不把空输出视为数据处理成功。
- 数值一致性不能证明原始会话独立性、作者标签来源、TLS1.3符合性、样本选择、训练测试划分与原论文等价，仍为 Unknown。

## 发现与处理

1. 初始矩阵若干行号超过实际文件末尾（分类器54行、预处理126行）。已先通知执行代理；最终矩阵已修正定位，未更改上游代码。
2. 预处理仅筛选 `tls` 和 `app_data`（源码48–53行），没有 TLS1.3 版本约束。已补入 M1 缺口和运行报告；无原始 PCAP 时不推断版本符合性。
3. 论文 §4.3.2 多处把 `ratio×100` 写成 “higher%”，而增加百分比应为 `(ratio−1)×100`。例如 ET-BERT/LiM 训练秒/样本的增加比例为86460%，正文写86560%；LiM/ET-BERT 吞吐的增加比例约52202%，正文写52302%。已加入 T2-derived-percent 与 `evidence/lim/paper_arithmetic.json`。这只验证论文数字之间的算术关系，不验证任何真实吞吐或资源测量。

没有遗留的已知报告级夸大问题；R3/R4 所需原始4000样本、处理与划分、完整基线、资源协议及部署验证均未满足。

## 离线候选字段的附加复核

同一标准库检查还检查了 `catalog/offline_candidates.json` 的4条记录及47个 `evidence_files` 路径，全部为实际文件。四条均标为 R0，`execution_status` 均以 Unknown 开头；目录中的公开代码/数据链接描述没有暗示候选算法已运行成功。完整数据与模型访问和校验仍按各记录登记 Unknown。
