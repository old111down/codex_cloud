# 完整周缓存 Replay 独立审查

**两个完整公开周已由原版 Simulator 新计算，并与作者各自同周结果逐键、逐数值匹配。Jun07 周覆盖 Human，May31 周覆盖 Human 与 SWE-Bench；独立检查分别60/62项通过，全部数值严格相等。八张新 Parquet 的字节哈希均不同，不构成数值偏差。** 全16周 Cache 论文声明仍不升级。

本审查只读取已保存的输入、输出、日志与固定源码，没有重新执行缓存模拟。独立代码为 [review_complete_week_artifacts.py](../scripts/review_complete_week_artifacts.py)，机器结果为 [independent_full_week_review.json](independent_full_week_review.json)。输入匿名 Request Key 仅用于内存 Join/集合核验，未写出任何 Request/Session ID 或原始行。

## 第一周：Jun07，完整 Human 周

- 选择规则为16周中 `requests.parquet` 压缩文件最小者，不进行 Session 或行抽样；该文件 7,885,194 bytes，6859行，Block列解压约318.49MB。80个 Session 均为 Top-level Human，Harness 为 Pi35/Kilo34/OpenCode9/Cline2；无 Child、无 SWE-Bench。[选择记录](full_week_replay_selection.json)
- 原版 SHA `2b795dbf5eac490a7c081906fdce6cc7a184b7ef`，实际 `python -m simulation --week 2026-06-07 --release .../private/data/release --output .../private/runtime/complete_smallest_week_simulation --processes 1`，8GiB 地址空间限制、300s超时。exit0，110.294s。[命令/时间](../logs/official_checks/simulation_complete_smallest_week.json)
- `--week` 显式分支无条件执行 `simulate_week` 与 `cheaper_reads.write_week`，不会进入“未过期所以跳过”的分支；日志有该周“the cache replay and the cheaper-reads model”完成消息。新目录及其任务目录内全部祖先均非 Symlink，与作者目录分离，每个文件均非相同 inode，新文件 mtime 均落在命令起止之间。证据支持本次确实新算，没有将作者文件当新输出。
- 使用原版64 partitions、16 Token/block、13 TTL、4 policy；Cheaper Reads 为3 TTL×21折扣点。实际强制压缩阈值参数900,000 Token，源码还按该 Session 最大既有 Prompt 调整；未修改原版配置。配置详情见[作者路径比较结果](complete_smallest_week_simulation_comparison.json)。

| 表 | 行数 | 复合 Key | 独立逻辑对比 |
|---|---:|---|---|
| tallies | 52 | scope, policy, ttl | Key 唯一且两边集合相同；Hit/Miss整数与两个Token-seconds浮点列全部严格相等 |
| totals | 1 | scope | 全列严格相等；Requests/Output还与原始 Top-level 输入独立核对 |
| request_misses | 6859 | scope, session_id, step | Key 唯一、覆盖全部6859个 Top-level请求；missed_tokens全部整数严格相等 |
| cheaper_reads | 63 | ttl, read_price_cut | Key 唯一、集合相同；所有Token和计数列严格相等 |

作者比较脚本公开716个聚合单元格；6859条 Request-level Miss 不公开，仅报告比较计数。独立脚本直接重读两套 Parquet、输入主键及三张输入表哈希，得到60项检查通过、0失败；全部数据列最大绝对差为0。浮点容差 `abs(delta)≤1e−6+1e−12×abs(reference)` 在原比较脚本中显式记录，NaN/Inf会失败；**本次即使不用容差也相等**。整数列采用精确比较。[数值比较](complete_smallest_week_simulation_comparison.json)、[独立结果](independent_full_week_review.json)

输入 `tables.json` 绑定当前 Manifest，三张输入文件 SHA/Rows 与记录相符；两边 `sources.json` 都完整列出四张输出表，全部绑定当前 Manifest SHA `cb568f2be6d718d015ff67886042f86ac43637d73a61995ad6010e64177dcf56`。这验证了相同公开输入的来源关联；不等于验证私有原始日志及重建真值。

## 字节哈希与数值相等是不同检查

四张新 Parquet 与作者文件 SHA256 全部不同。直接读取 Footer 可见，作者文件 Writer 为 `parquet-cpp-arrow version 25.0.1`、pandas metadata为3.0.6；本次为 Arrow26.0.1、pandas3.1.1。列和键对应后的所有数值却严格相等。因此不能把不同 SHA 自动判为复现失败，也不能称文件逐字节一致。Writer/metadata差异已经观察到；没有穷举每一个字节差异的全部原因。

## 第二周：May31，含 Human 与 SWE-Bench

- 使用2026-05-31至06-06完整周，原三张输入为76 Session、7324 Request、7595 Tool Call，没有裁剪。Top-level 65个，由59 Human与6 SWE组成；另11个Child。官方模拟 Scope 只纳入7157个Top-level Request，167个Child Request没有被误算为独立任务。
- 原版同一 `simulation` 入口，`--week 2026-05-31 --processes 1`，8GiB地址空间 Guard、600s超时；实际exit0、190.867s。新目录为 `private/runtime/complete_mixed_scope_simulation`，已检查非Symlink、与作者目录不同、四表mtime都在运行窗口内、显式week分支和完成日志。[原始命令](../logs/official_checks/simulation_complete_mixed_scope_week.json)
- 四表分别为104条Tallies（2 Scope×4 Policy×13 TTL）、2条Totals、7157条Request Miss、63条Human Cheaper Reads。复合Key唯一且集合相等；按原始Harness独立重建预期Scope，逐Scope验证Request/Output总量。所有整数及浮点数均严格相等，最大绝对差0。独立62项检查通过。[比较结果](complete_mixed_scope_week_simulation_comparison.json)、[独立结果](independent_full_week_review.json)
- 两边四张表都绑定当前Manifest SHA `96191219dd2602fbc6ae18e051e55bfa1775d6fbca8ff7f5894c17bed1f109be`，三张输入SHA/Rows均匹配记录。928个聚合单元格公开，Request Key/原始行没有输出。
- 资源包装器记录 `max_rss_kib_linux_wait4=1,907,608`（约1.82GiB），语义是Linux wait4最大Resident统计，**不是父进程与Worker并发RSS总和**。用户/系统CPU时间约155.97/35.14s；不将单次耗时外推为全16周性能实测。[资源记录](complete_mixed_scope_week_resource_usage.json)

该周有Child输入，但官方缓存Scope排除独立Child请求；成功不等于验证所有Subagent缓存或生命周期行为。

## 静态模型边界：Scope内共享Block Hash，无显式Model/Provider/账号隔离

已沿公开调用链核对外层Salt来源，而非仅检查哈希函数参数。以下全部来源固定于SHA `2b795dbf5eac490a7c081906fdce6cc7a184b7ef`：

1. [`export/paths.py` L24](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/paths.py#L24) 定义统一私有release salt文件；[`export/__main__.py.run_build` L48–52](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/__main__.py#L48) 只调用一次 `pseudonyms.load_salt(paths.SALT)` 放入BuildInputs。这里只阅读源码，没有读取或导出Salt值。
2. [`build_steps.run_digests` L89–90](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/build_steps.py#L89) 将同一个 `inputs.salt` 交给 `write_week_digests`；后者在 [`digests.py` L140–147](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/request_inputs/digests.py#L140) 将同Salt传给每个Row-group Worker，未按Model、Provider或账号派生新Salt。
3. [`digest_row_groups` L115–129](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/request_inputs/digests.py#L115) 构造的RequestInput只有request_id、prompt、system_prompt、tools；[`request_digest` L83–97](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/request_inputs/digests.py#L83) 用渲染后的输入Token与同Salt生成Block Hash，未将request_id等作为Block Hash的域标识。
4. [`block_hashes` L54–69](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/request_inputs/digests.py#L54) 第一块从空前缀开始，以Token Bytes和Salt作链式BLAKE2b；[`week_block_ids` L197–201](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/release/requests_table.py#L197) 仅在整周Hash数组中factorize为整数ID，没有额外按Model/Provider/账号隔离。
5. [`simulate.py` L26](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/simulation/simulate.py#L26) 将Agentic/SWE-Bench分开且每周从空缓存开始；[`WeekRequests` / `week_requests`](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/simulation/block_reads.py#L23) 未携带Model/Provider/用户命名空间；[`cache.sort_reads` L70–73](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/simulation/cache.py#L70) 按Hash与Arrival排序，Session字段用于生命周期信号，并不是缓存隔离Key。

**已确认实现事实：** 这是按Scope共享Block Hash的理想化复用模型，在该公开完整调用链未见外层按Model、Provider或账号重Seed/分Cache。输入文本本身可以含模型/用户差异，但那不等于一个显式缓存命名空间。

**解释与Unknown：** 同周输出匹配证明同一个模型可重算；不证明不同模型/Provider上的物理KV可共享，也不验证租户隔离或生产路由策略。真实系统的隔离策略、相同Prefix跨这些域的频度及其对论文指标的影响均Unknown。本审计没有据此认定算法错误，也未量化偏差或修改模型。

## 可以与不能证明的内容

可以确认：对列出的完整周，固定公开版本能在普通云CPU上独立执行其缓存模型，并产生与作者同周逻辑值相同的结果。第一周无Child/SWE；第二周验证了Human/SWE两Scope，但Child独立请求仍按官方规则排除。

仍然不能确认：剩余周的完整 Replay、全16周合并 Cache 指标的独立重算、真实Provider缓存策略、GPU内存/吞吐、原始私有采集/重建准确率、任何PCAP对齐或网络分类效果。全期 `paper_metric_comparison.csv` 中依赖作者中间表的缓存项仍为 **Partially Verified**；此次同周匹配不能替它们全部升级。
