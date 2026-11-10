# 实际复现结果与边界

**结论：公开处理后数据的主要统计流程已在 CPU 上运行，整体论文结果仅部分验证。** 原始服务日志、Session 准确率验证和意图标注材料不公开，发布数据也未提供配对 PCAP，不能由本轮补齐。缓存图可以用作者预计算结果重绘；本轮另完成两个完整周的独立缓存模拟，但未重算全16周。

## 环境与来源

代码：`HarvardMadSys/freeinference_agentic_trace@2b795dbf5eac490a7c081906fdce6cc7a184b7ef`，原始克隆保持干净；执行副本 115 个源码文件逐字节相同。HF 数据：`harvardMadsys/freeinference_agentic_trace@bb26cf72c9c20f2b05f765d88548156a74d3c253`，48 个 Parquet / 16 周，8,371,191,139 bytes，全部 SHA-256 对照 LFS 值通过。来源、许可和哈希见 [source_provenance.json](environment/source_provenance.json)、[data_manifest.csv](reports/data_manifest.csv)。没有下载解压约 108 GB 的 JSONL。

Debian 13.6，CPU 配额 4 核、内存限制 16 GiB；未发现 GPU、CUDA、`tcpdump` 或 `tshark`。原生编译器 GCC 14.2；Conda Python 3.12.16；pandas 3.1.1、PyArrow 26.0.1、Matplotlib 3.11.2、tree-sitter 0.26.0 / bash 0.25.1、tiktoken 0.14.0。按官方声明安装，未做版本替代。独立的11项合成对齐检查使用系统 Python 3.12.14，日志另行记录；它没有使用论文数据或统计依赖。详见 [host_summary](environment/host_summary.json)、[环境锁定](environment/freeinference/)；GPU/PyTorch 不属于本次统计管线的必要条件。网络实际成功访问官方论文、GitHub 与 HF；没有调用模型推理或付费计算。

## 已运行的层次

| 执行 | 观察 | 状态及可证明范围 |
|---|---|---|
| 原始 `make figures PROCESSES=1` | exit 2：`.venv/bin/python` 不存在 | Failed：Make 默认解释器前置条件，随后按用户要求显式指定 Conda |
| 原版 pytest | exit 5，收集 0 项 | Failed：公开仓库没有维护者测试；不是发现算法单元测试失败 |
| 最小缓存 fixture | 3 个合成 read，TTL=1/10/∞ 的 hit tokens=0/16/32 | Verified：原算法小输入执行；不是论文数值 |
| 一个完整周的官方 paper 入口 | exit 0，82 项输出；质量检查发现 8 个 SWE 相关 NaN | Partially Verified：该周没有 SWE；不能把进程成功当作所有指标有效 |
| 全 16 周原版 `make figures PYTHON=<Conda> PROCESSES=1` | exit 0，64.24 秒；41 个注册输出项；numbers 0 NaN / 0 skip | Verified：完整公开范围统计和绘图入口，缓存图复用作者发布的仿真材料 |
| 完整 2026-08-30 周缓存模拟 | 1 worker / 8 GiB address-space / 120 秒，exit 124 | Failed：本次设置的时限到达；没有证明代码错误或三小时内必然不可行 |
| 3 个真实完整 Session 的原版 simulation | 42 requests / 39 tool calls / 539,494 block reads，exit 0，2.43 秒 | Verified：原算法真实小子集；52 个 policy×TTL tally 的 token 守恒等检查通过；不是全周 cache hit ratio |
| 完整 2026-06-07–06-13 周独立 simulation | 未裁剪的80个顶层人类Session、6,859个请求；exit0，110.29秒；该周无SWE或子会话 | Verified：52 tallies、1 totals、6,859 request_misses、63 cheaper_reads与作者同周表逐键及全部数值完全相同；不是全16周结果 |
| 完整 2026-05-31–06-06 周独立 simulation | 输入76 Session / 7,324 requests；65顶层（59human+6SWE）/11child；exit0，190.87秒 | Verified：104 tallies、2 totals、7,157 request_misses、63 cheaper_reads与作者同周表全部数值逐键完全相同；保留原版scope筛选，没有输入裁剪 |
| 自建保守区间匹配器 | 11 个合成检查通过 | Verified：拒配/歧义处理的合成逻辑；没有 Agent 或真实 PCAP 对齐精度 |
| 公共 Gateway GET | 模型目录 200，header echo 匹配；用户 recent-requests 未授权 401 | Verified：只读公共路径；未获得自身推理 Trace，MiMo 精确路由仍 Unknown |

所有实际命令、cwd、UTC 起止、exit、时限与日志见 [execution_log.md](execution_log.md)。数据检查、公开模式与汇总见 [data_validation_report.md](data_validation_report.md)；逐项代码覆盖与数值来源见 [paper_code_coverage.csv](paper_code_coverage.csv)、[paper_metric_comparison.csv](paper_metric_comparison.csv)。

`make -n setup figures test week-2026-08-30` 仅展开命令，**没有执行官方 `.venv` setup 或私有维护管线**。实际安装的是独立 Conda 中的同一官方依赖声明。下载器执行了 help 检查；真实数据由本轮固定 HF revision 的校验下载脚本取得，没有把 help 当作下载成功。

## 论文指标对照

顶层口径（含 SWE-Bench）为 **12,002 Sessions / 1,186,582 Requests / 1,213,347 Tool calls**，与 Table 1 相同；input=209,199,292,539、output=552,524,061、cached=197,064,717,672 tokens，匹配论文印刷精度。14 个 Harness 行逐项通过。另有 2,034 个 child Session / 35,617 requests / 61,905 tools，不能混入纸面顶层总量后判断不一致。

当前 73 项纸面数值声明中比较 69 项，67 项在印刷精度内，2 项不匹配；其中缓存仿真声明即便数值吻合也只标 Partially Verified，因为使用了作者预计算结果。4 项没有独立数值验证。不能把该比例作为论文全部实验“成功率”，它没有覆盖所有定性声明、原始标签或采集准确性。

两个完整小周另行做了直接Parquet复核；实际模拟输出路径不在作者结果目录内、没有符号链接或同inode复用，命令显式计算没有cache-skip。两周各四个Parquet字节SHA不同，但全部数值逐键exact-equal；footer显示作者Arrow25.0.1/pandas3.0.6与当前版本不同，不能将文件编码差异误报为科学结果偏差。见 `reports/complete_smallest_week_simulation_comparison.json`、`reports/complete_mixed_scope_week_simulation_comparison.json` 与 `reports/independent_full_week_review.json`。

Jun07未实测peak RSS，8GiB虚拟地址guard不能当内存峰值。May31以自建`wait4` wrapper观测最大单进程RSS=1,907,608KiB（约1.819GiB），不是并发进程RSS之和；最初拟用的`/usr/bin/time`不存在，exit127前置错误单独保留，当时原算法未启动。没有安装系统包或改算法。完整16周原版每scope反复扫描64次的资源模型与只读估计见 `reports/cache_replay_resource_plan.md`；约9.33小时的线性外推只是规划推测，不是实测完成时间或“不可能运行”的证明。

独立源码复核还确认，发布缓存模型在scope内按输入token的salted block hash复用，没有按model/provider/account另作缓存隔离；这是理想化反事实模型的条件，不能据数值复算一致宣称真实跨Provider缓存策略得到验证。caller salt链及准确路径见 `reports/independent_full_week_review.md`；未读取或发布私有salt值，影响大小仍Unknown。

确认差异是 Table 6 的 SameTool/Mixed：论文 71.3% / 28.7%，当前全量原版产物为 **64.0174% / 35.9826%**。这是同一互补分布的两个值，不是两个独立实验问题。另论文称 84.5% requests 为单工具，代码按 tool-call 行对 batch width 加权：84.4816% 是 call-weighted；按 request 去重后，**有至少1次tool call的人类顶层请求（排除SWE，分母1,044,159）中**单工具为 **93.2316%**。这是分母口径差异，不能因数值接近便标为相同统计对象。更多文字声明及条件分母问题见 [critical_findings.md](critical_findings.md)，精确源码与独立复核保留在 reports 中。

全量数据还观察到 4 条负衍生工具 gap（3 个请求 batch）和 4 条 cached>prompt（合计差 63 tokens）；原因 Unknown，不能推断数据损坏、泄漏或系统错误。不同 provider 的 token 语义与缺失量应按原始定义检查。

## 修改与实验等价性

上游没有修改。独立补丁 [0001-report-empty-benchmark-scope.patch](patches/0001-report-empty-benchmark-scope.patch) 只在私有执行副本检查：空 SWE 子集时报告不可比较，防止 NaN 或 0 被误读为对照结果；不改变非空样本、模型、数据、模拟策略或算法结果。全 16 周主运行没有应用补丁。详情及补丁验证见 code 运行报告和 `reports/empty_scope_patch_result.json`。

自己的 downloader、quality checker、metric comparison 和 alignment 工具仅补充审计证据，不代替缺失的作者实验实现。数据字典内的程序字符串、tool arguments 等始终作为不可信数据，不执行。

## 复现等级与阻断

本轮使用局部等级：R0=仅收集材料；R1=环境/合成 smoke；R2=公开真实数据上的核心管线；R3=原论文完整数据、独立计算与匹配指标；R4=采集/生产部署条件独立验证。**整体 R2，部分公开统计达到指标级验证；不认定整体 R3/R4。**

- 原始私有 prompts/responses、维护者测试、显式 Session ID 验证集缺失，95% 一对一声明无法重算。
- Fig 16 的八类意图标签、标注模型、完整 prompt/few-shot、人工核验材料未公开，不能由已去正文数据重新生成。
- 当前 Gateway 源码与历史采集部署版本的对应关系 Unknown；当前 timestamp 为异步 DB insert time，历史误差不能从代码计算出来。
- 全16周缓存独立模拟未完成；小子集及两个完整周成功不能代替论文全期 TTL / 成本最优结果。
- 没有账号授权、精确 MiMo 路由验证、Hermes运行、真实PCAP或网络分类器训练；下游 MVP 是可审查设计。
