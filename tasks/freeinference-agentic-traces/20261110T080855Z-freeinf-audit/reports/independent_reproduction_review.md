# 独立数据与复现审查

**结论：全 16 周公开 Parquet 的核心描述统计能够执行，Table1 的顶层 Session、Request、Tool Call、Token 及全部 14 个 Harness 数量得到交叉核对。论文 Table6 的 Batch Mix 存在可确认数值差异；批次宽度还存在分母语义差异。缓存图主要由作者发布中间表重新聚合/绘制，全期 Cache Simulation 未重新完成，不能称完整独立复现。**

此审查独立读取其他执行代理保存的统计、日志、公开源码及论文声明，使用标准库脚本复核聚合算术与输出质量；没有重新训练模型、下载新数据或重新执行作者全量管线。只检验已保存证据的范围和一致性，不能替代对私有原始采集真值的验证。

## 审查范围与版本

- 源码固定 SHA：`2b795dbf5eac490a7c081906fdce6cc7a184b7ef`；数据集 revision：`bb26cf72c9c20f2b05f765d88548156a74d3c253`。
- 全期统计：[aggregate_stats.json](aggregate_stats.json)，16 周，2026-05-17 至 2026-09-05；逐周 Row Count 与 SHA256 对作者 manifest 的检查共有 96 项，均为真。
- 作者 CLI 输出：私有运行产物 `private/runtime/figures/numbers.json`；可公开对照：[paper_metric_comparison.csv](../paper_metric_comparison.csv)、[paper_metric_comparison_summary.json](paper_metric_comparison_summary.json)。后者是选定数值声明清单，未穷举所有方法与实验声明。
- 独立检查程序：[review_reproduction_evidence.py](../scripts/review_reproduction_evidence.py)，运行命令 `python scripts/review_reproduction_evidence.py`；结果 [independent_reproduction_review.json](independent_reproduction_review.json)，28 项范围/计数/输出一致性检查通过，0 项失败。通过数只代表所列检查，不表示论文全部通过。
- 已交叉读 [独立论文审查](independent_paper_review.md)、[实际 Schema](observed_schemas.json)、[字段字典](../data_dictionary.csv)、公开 `release/schema.py`、`release/population.py`、`paper/metrics/tools.py`、`paper/metrics/gaps.py` 等固定版本源文件。

## 计数范围：顶层、子代理与 Human/SWE

| 范围 | Session | Request | Tool Call | 用途 |
|---|---:|---:|---:|---|
| 全部发布行 | 14,036 | 1,222,199 | 1,275,252 | 包含 Child，不能直接与 Table1 对比 |
| Top-level，含 SWE-Bench | 12,002 | 1,186,582 | 1,213,347 | Table1 的正确总体 |
| Child | 2,034 | 35,617 | 61,905 | 是父 Trace 的一部分，单独列出 |
| Top-level Human | 10,967 | 1,125,604 | 1,152,306 | 主文默认 Agentic Scope，排除 SWE |
| Top-level SWE-Bench | 1,035 | 60,978 | 61,041 | 仅指定比较实验纳入 |

前三行由 [aggregate_stats.json](aggregate_stats.json) 的 `totals`、`cohort_totals` 直接核对，逐列满足 All = Top-level + Child。后两行由作者 CLI Scope/计数以及差值核对；公开 [`population.sessions_in_scope`](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/release/population.py#L30) 只选无 Parent 的 Session，并将 `eval:swe-bench` 单列。不能将 All 与 Agentic 混用，也不能把 Child 当作独立人类任务。

Top-level Input `209,199,292,539`、Output `552,524,061`、Cached `197,064,717,672`，分别按论文精度为 209.2B / 552.5M / 197.1B。Table1 全部十四个 Harness 数量逐项相等。稳定且非空的 `salt_series` 下得到 267 个不同匿名账号，并不是把逐周用户数相加；账号不保证等于自然人。证据见上述统计与 [Table1、PDF p1](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=1)。

## 实际执行与“通过”的含义

| 运行 | 保存结果 | 独立判断 |
|---|---|---|
| 原样 `make figures PROCESSES=1` | exit 2，`.venv/bin/python` 不存在 | 环境路径阻断，不能说原始命令成功，也不能判定算法缺陷 |
| Conda 解释器下 `pytest` | exit 5，收集 0 tests | 没有公开测试可运行；不能写 tests passed |
| 单周 `python -m paper` | exit 0，但 8 个 NaN；两项 TTFT/Benchmark 对比有 skip 原因 | Exit Code 不能代表结果质量；该周没有 SWE，相关比较不具备所需输入 |
| 全 16 周、显式 Conda `PYTHON`、资源限制下的 `make figures` | exit 0，约 64.24s；全期 Numbers 无 NaN、无显式 skip | 已执行所注册的公开图表管线；源码未覆盖的 Figure7/16 等不因此补齐 |
| 一完整周 Cache Simulation | 120s 后超时退出 124 | 有资源/时间界限的未完成运行，不是全期算法失败证明 |
| 选定真实数据子集 Cache Simulation | 3 Session、42 Request、39 Tool Call，exit 0，约 2.43s | 真实子集 Smoke/Core Replay；不能代替一周或全期复现 |

证据：[原样 Make 日志](../logs/official_checks/readme_make_figures_original.json)、[pytest 日志](../logs/official_checks/public_tests.json)、[单周数值质量](paper_one_week_numeric_quality.json)、[全期执行](../logs/official_checks/paper_all_weeks.json)、[全期数值质量](paper_all_weeks_numeric_quality.json)、[一周模拟超时](../logs/official_checks/simulation_one_week_guarded.json)、[子集运行](../logs/official_checks/simulation_small_realdata.json)、[子集来源](small_realdata_subset_provenance.json)。

子集 Replay 验证了 52 个 Policy/TTL Tallies、Hit+Miss 保守、无限 TTL 首次 Miss 等于不同块数量、TTL 越大 Hit 不下降，以及 Cheaper-read 零折扣基线一致等性质。[small_realdata_simulation_validation.json](small_realdata_simulation_validation.json)。这是合理核心功能检查；样本按审计规则选择且没有子代理，统计代表性与子代理路径没有因此被证明。

全期 Make 在隔离运行目录中使用已发布 Cache 中间表。模拟命令识别其 source manifest 后可复用结果，后续程序重新聚合/绘图。**运行了 `make figures` 不等于重新计算了全部 Cache Replay。** Fig10–13、Table7 的无限 TTL Prefill 归因，以及 Figure14 的 TTL 部分，凡来自作者缓存中间表的结果均应是 Partially Verified。作者提供的中间表哈希/来源匹配支持可追溯性，不构成独立重算。[readme_workspace_provenance.json](readme_workspace_provenance.json)、[覆盖矩阵](../paper_code_coverage.csv)、[数值对照](../paper_metric_comparison.csv)。

## 追加完整周 Replay 核验

初轮单周 Aug30 超时和小子集成功之后，追加了资源允许的完整 Jun07 周，原版命令重新计算而非复用中间表，80 个顶层 Human Session、6,859 个 Request，无子代理/SWE。110.294s 完成，同周四张表的键与全部数值严格相等；独立二次检查 60 项通过。四表 Parquet 字节哈希不同，作者/当前 Writer 分别为 Arrow25.0.1/26.0.1、pandas3.0.6/3.1.1，不能因此判数值不一致。具体独立结果及随后其他限定周状态见 [independent_full_week_review.json](independent_full_week_review.json)。随后May31含SWE完整周也成功，104/2/7157/63四表数值严格匹配、62项独审通过；其7324个全部Request中仅7157个Top-level进入模拟。两周结果见同一报告。它们提高了**这两个完整周**模拟的证据等级，没有升级全16周缓存论文值的独立复现状态。

## 数值核验及确实发现的差异

选定 73 条纸面数值中，69 条有可比值；67 条在论文显示/近似精度内，2 条超出，4 条 Unknown。这个统计混合了公开 Parquet 重算与作者模拟中间表的重画，**不能称 67 条独立复现成功**。数值、方法和真值验证是三个层面。[paper_metric_comparison_summary.json](paper_metric_comparison_summary.json)。

直接从公开 Parquet 重算、可核对的典型值：

- Session 的 User/Tool/LLM Step 中位 4 / 36 / 42；Turn 中位 60.617s，Session 中位 1813.187s；输入/Uncached/Output 中位 129,087 / 491 / 227 Token。
- 平均 Session 时间份额约 Idle 50.258%、Tool 21.708%、Decode 18.112%、Prefill 9.922%；这是测量加推断的分解，不是客户端 CPU/网络精确计时。
- 所选 Cache-reporting Human 请求中 Cached Token Share 为 97.4225%；分母只针对 1,077,413 条 cache-reporting、prompt>0 请求。它与 Table1 全部 Token 比例不同，不能混用。
- Gap 的 P90：Tool 17.2257s、Ask User 378.0666s、Subagent 371.3016s、User Idle 1042.3616s，与论文相应显示精度一致。

证据：[extra_paper_metrics_all_weeks_v2.json](extra_paper_metrics_all_weeks_v2.json)、[数值对照](../paper_metric_comparison.csv)、[论文 Figure2/4/8](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=4)。

### 确认差异：Batch Mix

论文 Table6a：Same Tool 71.3%、Mixed 28.7%。固定已发布 CSV 与本次全期重算均为 **64.0173758% / 35.9826242%**，绝对差均为 7.2826242 个百分点，超出一位小数舍入误差。相同数据改用 Call Weighting 后，同类份额为 64.6325914%，仍不能解释 71.3%。这确认了纸面与固定公开路径的不一致；历史版本、过滤或方法的根因 **Unknown**，不能据此推断造假。[Table6、PDF p6](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=6)、[固定发布表](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/figures/v1/tools/batching_profile.csv)、[batching_denominator_check.json](batching_denominator_check.json)。

### 确认语义差异：批次宽度分母

论文把 84.5% 描述为只有一个 Tool Call 的 Request 比例；当前代码对 Call 行加权得到 84.4815526%。在相同 Human 数据中，单调用 Request 占有调用 Request 的 **93.2315864%**，而不是 84.5%；零 Tool Request 也不在这个条件分母内。两种 estimand 都可计算，但不能互称。[tools.py L148–171](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/metrics/tools.py#L148)、[分母检查](batching_denominator_check.json)。

### 已排除的虚假偏差

- Human Session 的 30.2min 换算为 1812s 后，其原始显示精度仍是 ±0.05min，即 ±3s；重算 1813.187s 符合该精度。不能因换单位后是整数，就改用 ±0.5s。
- Figure10 caption 的 “about 120×” 是近似描述；重画 121.42× 不宜按整数精度 ±0.5 自动判失败。它还来自作者中间表，不能因近似匹配晋升为完整重模拟。
- §6.1 的 15–30min / >1h Hit Ratio 约 58% / 18% 与**均值** 58.4545% / 18.3614% 对应；中位数分别为 90.5548% / 0.6012%。直接拿 CLI 中位数与正文未注明的 aggregate 比较，会制造错误差异。

## 数据质量与派生时延

全期观察到 4 条 Tool Call 的 `latency_ms<0`，属于 3 个 Request Batch；其中两条来自同一批次并共享 −1497ms，另外为 −437ms、−180ms。全部 Tool Gap 与公开的 next-start−current-end 公式一致，差异行数为零。负值是应保留的时序观测问题，不能称“工具真实执行负耗时”，也不能未经证据归因为时钟漂移。底层 Logger 时刻、关联误差或重叠执行的贡献 **Unknown**。[aggregate_stats.json](aggregate_stats.json)。

另有 4 行 Cache Read Token 大于 Prompt Token，非负请求 Duration、TTFT 以及 TTFT≤Duration 检查均通过。公开指标对 Uncached 做 lower=0、Hit Ratio 做 upper=1 裁剪；裁剪保证后续指标范围，不代表 Provider 计数问题已经修复。其根因仍 Unknown。重复主键、孤立外键、缺父 Session、错误 Spawn Key、祖先环和枚举越界检查没有发现异常，范围限本版本发布数据。[相同统计](aggregate_stats.json)、[`tokens.py`](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/metrics/tokens.py#L23)、[`gaps.py`](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/metrics/gaps.py#L43)。

字典 68 行明确区分 38 个实际顶层字段、5 个 Role 子字段、16 个 JSONL Alias/Container 和 9 个缺失观测；未见字段遗漏/错型。列表叶节点的 Parquet Footer Null 数可能混合空列表、缺失列表和 Null Element，不能直接当顶层列表缺失率。Role Token 的 o200k 计数与 Provider Token 不相等不应自动当损坏；来源与 Tokenizer 不同。[字段字典](../data_dictionary.csv)、[Schema](observed_schemas.json)、[profile_parquet.py](../scripts/profile_parquet.py)。

## 方法差异与仍未验证的问题

以下方法问题已与 [独立论文审查](independent_paper_review.md) 交叉确认：

1. 人类样本必须至少两次 User Turn、一次 Tool Turn，SWE 只有 Tool 条件。该筛选比“过滤 single-request API”更强，会排除单用户输入、多步骤 Agent 任务；跨轮 Idle 与时长比较的总体外推受到限制。
2. 论文称 User-Agent 优先识别 Harness，源码先看 Intro Phrase，再回退 User-Agent，且 Intro 可含 System/User 消息；对冲突标签的影响 Unknown。
3. 论文称 Tool 有效时延扣除估计 RTT，已定位公开路径只做 Request 邻接差；私有 Logged Latency 是否提前校正 Unknown。
4. Tool Time/Latency 仅单调用、Failure 仅非空 Outcome、结果 Token 仅匹配结果；不能当所有工具真实执行资源的总体测量。
5. 子代理同步/异步细节、Figure7 Straggler 计算和 Figure16 LLM Intent Pipeline 的公开覆盖不足；4 条选定数值 Unknown，也不代表其余所有方法已验证。

Provider 保留曲线也应继续核查：公开重算的 C 在约 811.652s 的 bin 已低于 50%，D 在约 2051.923s 的点才首次低于 50% 且后续回升；论文 §6.1 却描述 D 在十五分钟后低于 50%。这不是简单拿最长点比较阈值，已经检查了完整点序列。匿名 Provider 映射是否变化、论文是否按另一个过滤/曲线计算仍 Unknown；当前不宣称 Figure8b 的每个字母曲线均与纸面一致。具体点与每 bin 样本数见 [extra_paper_metrics_all_weeks_v2.json](extra_paper_metrics_all_weeks_v2.json)，原文见 [PDF p8](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=8)。

本轮可以确认“发布数据上的多数核心描述统计可重算，预计算缓存结果可追溯地重画，并有真实子集模拟成功”。尚不能确认私有原始采集/重建的端到端重做、完整缓存重模拟、八类意图标注复现、全部子代理实验或任何 PCAP 分类效果。
