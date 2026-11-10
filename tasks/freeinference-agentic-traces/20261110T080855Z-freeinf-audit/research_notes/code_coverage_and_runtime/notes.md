# Code coverage and runtime audit notes

## 1. 是否公开了整篇论文的计算实现？

**Takeaway:** 主要会话、工具、缓存和benchmark统计代码公开，但 Figure7、完整Table6b、Figure16和95%验证链不完整。

**Cited findings:** 官方 [figure registry](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/__init__.py) 有41条细分映射；独立逐页 inventory 为 [paper](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf) Figure1–16、Table1–7，无Appendix。`paper_code_coverage.csv` 给出56条逐项证据。public [schema](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/release/schema.py) 没有意图标签，也没有public prompt文本。

**Inferences:** 已有父子session元数据可能支持新写subagent分析，但新实现不能冒充作者原Figure7实现或验证结果。

**Gaps:** 意图模型/提示/标签、straggler分组实现、明确session-ID ground truth验证子集及私有原日志不可用；95%和intent准确性Unknown。

## 2. 官方代码能在实际CPU环境运行吗？

**Takeaway:** 能运行公开处理后数据上的主要统计绘图和真实小样本完整模拟；完整周模拟本次限时未完成。

**Cited findings:** 官方 [Makefile](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/Makefile) 的受控原版目标实际exit0/64.24s，41registry项/88outputs，见 `logs/official_checks/paper_all_weeks.*`。115源码/配置字节一致，独立Conda依赖无替换。`simulation_small_realdata` 使用原 [simulation CLI](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/simulation/__main__.py) 处理3sessions/42requests/539494reads，2.43s exit0，52tallies+63cheaper-read rows及invariants通过。完整周120s exit124，无完整模拟产物。

**Inferences:** 小样本成功证明这条代码链和依赖可执行，不能估计原16周总耗时/峰值内存或声称所有模拟完成。

**Gaps:** GPU、实际KVcache资源、provider serving系统和网络包级行为未测试；8GiB虚拟地址guard/120s是审计条件，不是算法固有需求测量。

## 3. 数字与论文一致吗？

**Takeaway:** 73项selected数值中69有对照，67在印刷/近似精度内；包含作者缓存中间表重画。Table6 batch mix存在确认差异，provider-D文字需进一步解释。

**Cited findings:** `paper_metric_comparison.csv`、`reports/extra_paper_metrics_all_weeks_v2.json`、`reports/batching_denominator_check.json`。Table1top-level数值精确一致；Figure2中位数和cache-reporting97.4225%匹配。Table6paper71.3/28.7%，原 [batching_profile](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/metrics/tools.py) 为64.0174/35.9826%，call-weight variant64.6326也不解释71.3。Figure8a58/18%的文字对应mean而非median。D在17–27min median90%以上，与 [paperp8](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=8) 的15min后<50%未直接一致。

**Inferences:** 分母、时段、字母和版本差异都是待查假设；没有证据可以选一个当确定根因。两个batchmix差值来自同一分布。

**Gaps:** 四项无输出为fan-in同步/异步比例、两个intent比例。源数据/方法正确性并不由对照精度证明。

## 4. 运行退出码及测量/推断/模拟如何区分？

**Takeaway:** exit0不等于每个实验有效；单周缺SWE时出现8NaN。原版和修复结果分开保留。

**Cited findings:** 单周原版 `paper_one_week` exit0，`paper_one_week_quality` exit1；全16周quality0NaN。`patches/0001-report-empty-benchmark-scope.patch` 仅私有副本验证，未用于原版全16周。公开 [latency metrics](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/metrics/latency.py) 推断prefill/queueing并用15min cap做2×假设；[weekly simulation provenance](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/simulation/weekly_files.py) 校验trace manifest来源，但不证明本次重跑cache。public pytest实际0tests/exit5。

**Inferences:** 不能将simulated KV资源/成本、假设加速、gap估计或历史trace称为真实GPU优化、实际账单、TCPflow或自采PCAP。

**Gaps:** 私有logged latency是否已有RTT修正Unknown；公开路径未找到显式RTT扣除。负gap/cached>prompt有不同clip/eligibility，影响应按指标分开看，不能自动称数据损坏。
