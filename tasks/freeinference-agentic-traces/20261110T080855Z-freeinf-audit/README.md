# FreeInference Agent Traces：源码、数据与网络研究可行性审计

本轮结论：公开数据足以重新计算多项 Agent 服务侧工作负载统计；**不能直接训练或标注加密 PCAP 分类器**。它没有与请求对应的 packet、连接、客户端事件或公开任务意图标签。下一步应先验证自有客户端事件与同次 PCAP 的关联，再讨论分类精度。

- Task ID / run：`20261110T080855Z-freeinf-audit`。
- 实际开始：2026-11-10T08:06:28Z；最多三小时，截至 11:06:28Z。实际结束时间见 [metadata.json](metadata.json)。没有沿用或重跑其它任务的实验。
- 官方代码固定在 `2b795dbf5eac490a7c081906fdce6cc7a184b7ef`；HF 数据固定在 `bb26cf72c9c20f2b05f765d88548156a74d3c253`。
- 真实执行：独立 Conda Python 3.12；16 周 / 48 个 Parquet 校验和与聚合检查；原版 Make 统计绘图；真实小子集及两个完整周（5月31–6月6、6月7–13）的独立缓存模拟；合成对齐检查。全16周缓存重算、原始日志重建验证、意图重标注及真实 Agent/PCAP 实验没有完成。

## 阅读顺序

| 文件 | 内容 |
|---|---|
| [task_report.md](task_report.md) | 决策结论、A–E 回答、已验证与未知边界 |
| [paper_analysis.md](paper_analysis.md) | 全文方法、16 图 / 7 表、测量与反事实模拟 |
| [architecture.md](architecture.md) | Gateway 采集位置、实体关系、当前源码与历史部署边界 |
| [session_reconstruction.md](session_reconstruction.md) | 128 候选、8-word shingle、tool ID、主链与筛选 |
| [data_dictionary.csv](data_dictionary.csv) | 68 项实际/声明字段，来源、粒度、可观测性和泄漏风险 |
| [label_mechanisms.csv](label_mechanisms.csv) | Harness、工具、行为与八类意图标签生成机制 |
| [paper_code_coverage.csv](paper_code_coverage.csv) | 逐实验代码、入口、证据与缺失项 |
| [reproduction_report.md](reproduction_report.md) | 环境、原版与补丁、实际命令和成功/失败范围 |
| [paper_metric_comparison.csv](paper_metric_comparison.csv) | 73 项纸面声明的数值对照及来源限定 |
| [trace_pcap_alignment.md](trace_pcap_alignment.md) | 时钟、异步 DB、ID、连接、并发和拒配策略 |
| [mvp_experiment_plan.md](mvp_experiment_plan.md) | Hermes + 精确模型路由门槛、拓扑与逐步实验设计 |
| [research_opportunities.md](research_opportunities.md) | ANT、MAGIC26、TraceLab 对照与可证伪研究问题 |
| [critical_findings.md](critical_findings.md) | 最需复查的比例、分母、时间戳和私有材料问题 |
| [execution_timeline.md](execution_timeline.md) / [execution_log.md](execution_log.md) | 真实时间线与命令记录 |
| [reports/](reports/) / [logs/](logs/) | 聚合证据、独立审查与经检查的日志 |

## 重跑的边界与路径

公开目录不包含原始 Parquet、完整第三方源码、PDF 或完整 Conda 环境。按 [environment/source_provenance.json](environment/source_provenance.json) 的官方 URL / SHA 获取上游；按 [reports/data_manifest.csv](reports/data_manifest.csv) 的固定 revision、文件大小与 SHA-256 获取数据。数据和原始日志请保存在自己的私有工作区。

精确命令及执行时的路径见 [execution_log.md](execution_log.md)。本轮私有工作区为 `/workspace/freeinference-audit`；脚本内的默认目录需在不同机器调整。环境的 [environment.yml](environment/freeinference/environment.yml)、[Conda explicit](environment/freeinference/conda-explicit.txt)、[pip freeze](environment/freeinference/pip-freeze.txt) 和 [版本](environment/freeinference/runtime_versions.json) 均保留。不要把仅创建 Conda 环境或退出码 0 当作论文结果已复现。

原版 `make figures` 需要显式指定 Conda `PYTHON`、正确的 release/simulation 数据路径。它会复用作者已经发布的缓存仿真结果；这不等于本轮独立计算全量缓存曲线。审计补丁仅针对缺少 SWE 子集时的空分母报告，见 [patches/](patches/)，没有用于全量原版结果。

## 状态与公开范围

`Verified` 只针对附证据的具体事实或运行；`Partially Verified` 表示执行或材料只覆盖一部分；`Failed` 保留实际错误；`Unknown` 表示无充分证据。合成输入、选出的 3 个真实 Session、作者缓存产物和全16周公开 processed Parquet 统计分别列示。

[publication_manifest.json](reports/publication_manifest.json) 记录逐文件 SHA-256 与公开变换；[withheld_artifacts.md](reports/withheld_artifacts.md) 列出未上传证据。只上传原创分析、聚合值、来源版本、自己的脚本、环境声明、少量日志及必要补丁。PR 供研究者审查，不自动合并。
