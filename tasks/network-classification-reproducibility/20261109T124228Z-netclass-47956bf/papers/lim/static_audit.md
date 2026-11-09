> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# LiM 静态论文—代码覆盖审计

审计日期：2026-11-09。论文范围为公开 arXiv:2502.00586v2（2025-02-04，PDF 7页）；已读完整正文、§3 Methodology、§4.1 实现配置、§4.2–4.3 评估、参考文献。该版本只有 Table 1、Table 2，无编号图、无 Appendix。出版元数据为 WWW Companion 2025，pp1398–1401，DOI `10.1145/3701716.3715492`；最终 ACM PDF 下载遭 HTTP403（logs/lim/acm_fetch.stderr.log），最终排版是否有独有修改为 Unknown，不将预印本与最终排版完全等同。

## 关联与源码

论文 PDF p2 脚注1直接写明源码 `https://github.com/nime-sha256/LiM`，仓库 README 8–13、86–100行精确给出题名、作者、会议和 DOI，因此不是按同名推断。固定 `main@1b8ca187f7d02a51e595f797e5c200ae740b459f`，MIT。提交时间 2025-05-24T10:19:07+10:00；GitHub pushed_at 为2025-05-24T00:19:08Z，updated_at 为2026-11-05T05:02:12Z（后者包含非代码活动，不能解释为代码最近修改时间）。完整证据见 `metadata.json` 和 `evidence/lim/upstream_manifest.txt`。

## 全部实验与关键缺口

- §3.1 NetMatrix 的15个数值特征有明确实现：5个 TLS application-data 包的 IPv4 total length、TTL、IAT。TLS选择依赖 Pyshark/TShark，代码没有明确TLS1.3版本约束；脚本假设输入已按双向会话切好，不提供原始 PCAP 分流及分类标签来源。30字节表示只在概念字段宽度上成立；实际输出 CSV/IAT float，没有3字节IAT打包器。
- §3.2 vanilla XGBoost 和 Table1 LiM 行有 `xgboost_classifier.py`；脚本直接加载随仓库 CSV、StandardScaler 在切分前拟合、80/20随机切分（seed42、无stratify），XGBoost只显式设置 `eval_metric`。Scaler 使用测试集分布；对树模型通常影响有限，仍不应悄悄修复后声称等价。
- §4要求10个超过400样本的类别、每类400样本。实际 CSV 为4514行，10个域名标签，每类372–486；其中 nvidia.com372、netflix.com397，脚本既不平衡采样也不提供原论文会话ID/选择seed。这是原论文实验等价性的实质缺口，不能靠接近的accuracy消除。
- Table1 的ET-BERT、YaTC及其预训练权重、对齐样本划分和预处理代码均未随此仓库提供。README运行第一个分类器不能覆盖整个比较实验。
- Table2 的训练秒/样本、推理RAM+GPU、GPU功率、吞吐四类测量均无计时/采样/批量/warmup/重复次数工具。论文把GPU功率（W）称为energy；GPU0W不能解释为CPU或整机0能耗。训练time/sample不能解读为推理延迟。
- §4.3.2多项“higher%”派生数字将比值×100写成增幅；例如ET-BERT训练延迟相对LiM应为86460% higher而非86560%，吞吐相对ET-BERT应为52202% higher而非52302%。详见 `evidence/lim/paper_arithmetic.json`；此为论文数字算术核查，不是性能实验复现。
- §1声称秒级适应新类别，但无增量学习入口、新类划分或专门实验。C5/§3.1无握手选择条件有代码，但0-RTT、TLS会话恢复和连接重用的独立验证集与结果缺失。
- §4.1写Python3.13.0与XGBoost2.1.2，而requirements锁NumPy1.26.4和XGBoost2.1.1。最小测试选Python3.11满足README依赖；这属于明确记录的执行环境选择，不是论文原环境重建。

## 可核验资产

`evidence/lim/data_audit.json`提供CSV尺寸、SHA256、列、逐类计数和基础完整性检查。CSV无空值、无整行或特征完全重复；这只说明该表示层面的基本性质，不能证明原始会话独立、无来源偏差或无训练测试关联。原始CSTNET PCAP、抽样映射、会话拆分、采集时间、原始数据许可和重建参数为Unknown。仓库MIT覆盖项目文件，不能据此推断上游原始流量的再分发权。

覆盖矩阵逐条列出所有编号表格和重要方法/实验声明；`status`只表示证据覆盖，科学指标复现另见 `reproduction_report.md`。
