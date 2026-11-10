# FreeInference 论文代码覆盖与执行报告

状态：**Partially Verified**。实际完成全部16周公开 Parquet 上的官方统计/绘图入口、两个完整周的独立 cache replay，以及真实小子集 smoke。两个完整周的四张输出表均与作者同周数值完全一致；全16周独立 replay、私有原始日志重建、95% 验证和意图标注未复现。

## 版本与证据边界

- 论文：[From Requests to Sessions](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf)，本次获取18页，p13–18为参考文献，无 Appendix；PDF SHA256见 `research_notes/paper_workload_characterization/inventory.json`。
- 源码：[HarvardMadSys/freeinference_agentic_trace](https://github.com/HarvardMadSys/freeinference_agentic_trace)，固定 `2b795dbf5eac490a7c081906fdce6cc7a184b7ef`。原 clone 未修改。完整16周 Parquet 来源/哈希、Conda安装记录见 `data_validation_report.md`、`reports/data_manifest.csv` 和 `environment/`。
- `paper_code_coverage.csv` 有41条官方 registry 映射，加17条独立核查项目；覆盖状态描述代码/输入证据，不能解释为该论文所有实验数值均已独立复现。`paper_metric_comparison.csv` 单独记录结果对照。
- 原版统计入口使用公开数据中的已重建 sessions、分类和 token counts；计算一致性不会独立证明采集、重建、标签或 provider 计数正确。

## 实际运行环境

Debian13.6；CPU配额4核；内存上限16GiB；无已建立的 GPU、CUDA 或付费服务。独立 Conda Python3.12.16，pandas3.1.1、PyArrow26.0.1、Matplotlib3.11.2、NumPy2.5.4，依赖按官方 `pyproject.toml` 范围安装，没有替换依赖。完整列表见 `environment/freeinference/{environment.yml,conda-explicit.txt,pip-freeze.txt,runtime_versions.json}`。

运行设 `PYTHONDONTWRITEBYTECODE=1`、BLAS/OpenMP线程最多2、外置临时/Matplotlib目录；较重命令限制虚拟地址空间8GiB。这个 guard 是本次审计资源条件，不能拿来推断算法天然需要多少内存。

## README 与实际命令

所有完整 argv、cwd、UTC时段、超时、退出码和原始输出均在 `logs/official_checks/` 的同名 `.json/.log`，由 `scripts/run_logged.py` 记录。下表概括实际命令；长路径分别指独立 Conda Python、原版源码或外置数据目录。

| 记录 | 实际命令/条件 | 观察 |
|---|---|---|
| `readme_make_dry_run` | `make -n setup figures test week-2026-08-30` | exit0，仅展开命令；未在上游创建 `.venv`，未执行私有 maintainer pipeline |
| `readme_make_figures_original` | 原 clone 中 `make figures PROCESSES=1` | exit2，`.venv/bin/python`不存在；这是未执行原 `.venv` setup 的前置条件，不是算法缺陷 |
| `release_help` | Conda Python `-m release download --help` | exit0，核实公开 downloader 支持 `--tables/--traces/--week/--release/--hub`；没有下载108GB匿名JSONL |
| `public_tests` | Conda Python `-m pytest -p no:cacheprovider` | exit5，收集0项；公开 `tests/` 缺失，不能称测试套件通过 |
| `cache_synthetic_smoke` | 官方 `cache.sort_reads/tally`，3次合成读取，手算断言 | exit0；TTL1s/10s/∞的 hit tokens 分别0/16/32；不是论文指标 |
| `paper_one_week` | 原版 `python -m paper --release ONE_WEEK --simulation AUTHOR_SIM --output EXTERNAL` | exit0，24.29s，82个文件；8个 NaN 和空 benchmark trajectory，见下文 |
| `simulation_one_week_guarded` | 原版 `python -m simulation --week 2026-08-30 --release ONE_WEEK --output EXTERNAL --processes 1` | 8GiB guard，120.03s超时exit124；未输出完整模拟表 |
| `prepare_small_realdata` | `scripts/prepare_small_realdata_release.py` | 构造明确标记的真实数据小子集，保持原 schema/块ID，不改原数据 |
| `simulation_small_realdata` | 相同官方 simulation CLI，数据改为明示小子集 | exit0，2.43s，完整 cache replay 与 cheaper-reads model |
| `small_realdata_simulation_validation` | conservation、first-read、TTL monotonicity 和 counterfactual baseline 检查 | exit0，52条 policy/TTL tally 和63条 cheaper-read rows |
| `simulation_complete_smallest_week` | 原版 CLI，完整Jun07周，1worker/8GiBguard/300s界限 | exit0，110.294s；80个human top-level sessions，6859requests，无裁剪 |
| `simulation_complete_mixed_scope_week` | 原版 CLI，完整May31周，1worker/8GiBguard/600s界限 | exit0，190.867s；同时验证human和SWE两个独立scope |
| `compare_complete_*_week` | 同周四表按完整复合键、整数exact、浮点显式容差对照 | 两周均所有数值严格exact相同，maxabs0，未使用容差挽救差异 |
| `paper_all_weeks` | 原版副本中 `make figures PYTHON=CONDA_PYTHON PROCESSES=1` | exit0，64.24s；全部16周，88个输出文件，41个 registry 项均有数值结果 |
| `paper_all_weeks_quality` | 对最终 `numbers.json` 递归检查有限值 | exit0，0个非有限值，0个显式 skipped 项 |
| `extra_paper_metrics_all_weeks[_v2]` | 官方 gap/token 函数，列裁剪后的全16周数据 | 补取 cache-usage 子集比例、gap P90、均值/中位数及 provider 曲线；第二次针对独审提出的新口径问题 |
| `batching_denominator_check` | 相同人类 top-level 群体比较 request/call 加权 | exit0，给出 Table6 分母差异及 batch-mix 核验 |
| `empty_scope_patch_check` | 单独私有副本的补丁分支 | exit0，明确跳过7个缺少 SWE 的比较项目；未用于原版全16周结果 |

受控 Make 工作区由 `scripts/prepare_official_workspaces.py` 重建：115份原版源文件/配置逐字节一致，数据、作者模拟表和绘图输出链接到外置路径，仅覆盖 `PYTHON` 和进程数。原版 Make 先输出 `every released week is simulated from its current traces`，随后执行 `python -m paper`。这验证了作者模拟表的 manifest 来源检查和绘图流程；**没有重新计算16周 cache replay**。

## 代码公开完整性

已核对全文 Figure1–16、Table1–7、重要正文声明及维护入口。官方 registry 为41个细分输出：dataset1、sessions11、tools8、prefix-caching14、benchmark7。

- Figure2–6、8–15 的主要统计和模拟绘图入口公开。公开 Parquet 可重算会话结构、token/cost、延迟分解、工具使用、gap/hit、benchmark 对照等；缓存结果相关图还读取作者预计算中间表。
- Table6b 只有部分可复用实现：Table5能计算 Subagent session share；没有找到完整 fanout/fanin profile 入口。Figure7 的 synchronous-fanout imbalance/group-type 统计未找到对应 registry、分析或精确中间表。
- Figure16 所需少样本 LLM 意图分类代码、提示/样例、模型、标签表及公共 prompt 文本均不可得。public schema 没有 intent 列。其数值和可信度为 **Unknown**。
- §3的95% session reconstruction 验证无法从公开数据复验。公开 link 函数和维护参考比较不等于具有显式 session-ID ground truth 的该验证；私有原日志、验证子集和错误明细缺失。
- Table2是文献比较、Figure1是概念图；Table3描述内部日志字段，不能当成公开 release schema。maintainer `make week-*` 依赖私有日志、设置、salt/provider mapping，未尝试替造这些材料。

## 结果对照与已确认差异

73项独立转录的**选定数值声明**中，69项有可比输出，67项在明确记录的印刷精度/近似容差内。其余4项是两个 subagent fan-in 比例和两个 intent 比例，保持 Unknown。67项中含作者预计算模拟表的聚合/重画，CSV 对这些标记 Partially Verified；该计数不是“67项独立实验成功”。近似 `about120×` 和从30.2min换算出的1812s保留原文精度，不套用虚假的整数±0.5容差。

| 项目 | 论文值 | 本次值 | 证据性质 |
|---|---:|---:|---|
| Table1 sessions/requests/toolcalls | 12002 /1186582 /1213347 | 精确一致 | 公开 Parquet top-level，含1035个SWE sessions |
| Figure2 request/user/tool中位数 | 42 /4 /36 | 精确一致 | 人类 top-level，排除SWE |
| Figure2 turn/session中位数 | 60.6s /30.2min | 60.617s /1813.187s | 公开 Parquet统计 |
| Figure2 input/uncached/output中位数 | 129.1K /491 /227 | 129087 /491 /227 | provider token counts |
| cached token share | 97.4% | 97.4225% | 1,077,413个 cache-reporting、prompt>0人类请求；分母为input+output |
| 假设2×prefill/decode/tool加速 | 1.09 /1.16 /1.38 | 1.09437 /1.16369 /1.37572 | Amdahl式反事实；非实测系统加速 |
| Figure10 15m prefill超过∞floor | 60.9% | 60.9386% | 作者模拟中间表聚合，未独立 replay |
| Figure13 1day dead-block reduction | about36× | 35.8881× | 模拟dead token-time，非实测总显存减少 |
| Table6 same/mixed batch mix | 71.3% /28.7% | 64.0174% /35.9826% | 原版全16周数据/代码，差异确认 |

Table6 batch mix 的两个不匹配值来自同一个互补分布，并非两个独立实验缺陷。补充核验同样本的 call-weighted same share 为64.6326%，也不能解释71.3%；根因 **Unknown**。Table6 “1 call”84.5%确实对应**全部 calls 中位于单call请求的比例**84.4816%，若按 requests 计为93.2316%。需要明确分母，不能将84.5%解释为单call请求比例。

另有不在上述73项数值清单内的文字观察：paper p8称 provider D 在15min后 median hit ratio <50%。当前官方 provider-idle-gap 曲线在D的17.23/21.39/26.94min点分别为97.34%/90.83%/92.20%，34.20min为35.55%，之后又升高。不能把这些点与文字直接称为一致；字母、版本、样本窗口或方法原因仍 **Unknown**。精确 aggregate 点及每点样本数见 `reports/extra_paper_metrics_all_weeks_v2.json`。

Figure8a文本约58%/18%可由 mean58.4545%/18.3614%解释，不能与同bin median90.5548%/0.6012%混用而误报差异。

## 小子集模拟的明确界限

Aug30原完整 `requests.parquet` 190544行、20rowgroups；block-ID列解压总量约19GB，最大单组约1.54GB。Aug30完整周单worker模拟在本次120s预算内未完成；这不证明普通云CPU永远无法运行，也不证明依赖或算法损坏。随后选择更小的完整周，结果见下一节。

替代 smoke 使用3个完整 top-level、无child且各3–32requests的 sessions，共42requests/39toolcalls，539494个block reads，数据约1.17MB。确定性选择规则、原请求文件SHA、独立派生manifest及派生文件哈希见 `reports/small_realdata_subset_provenance.json`。官方64partition/13TTL/4policy CLI完整执行，得到52条tallies与63条cheaper-read rows；守恒、无限TTL first-read和TTL单调性均通过。该子集的输入块token数8631904、∞TTL first-read tokens530336仅是 smoke 的校验量，**不是论文的命中率或性能复现**。

## 两个完整周的独立 cache replay

对全部16周按真实 `requests.parquet` 文件大小排序，选择最小完整Jun07周和最小同时含human/SWE的完整May31周。输入使用原公开完整三表和原manifest，未裁剪行，也未用作者结果替代计算。显式 `--week` 分支会无条件执行 `simulate_week` 和 `cheaper_reads.write_week`；新输出位于两个独立fresh目录。源码、64partitions、13TTLs、4policies、16-token blocks及counterfactual参数未修改。

| 完整周 | 输入范围 | 原版replay时间 | 输出行数：tallies /totals /request_misses /cheaper_reads | 同周对照 |
|---|---|---:|---:|---|
| 2026-06-07–06-13 | 80human top-level；6859requests；0child；请求文件7,885,194B | 110.294s | 52 /1 /6859 /63 | 四表全部键和整数/浮点值exact相同 |
| 2026-05-31–06-06 | 65top-level=59human+6SWE，另11child；原请求文件7324行、16,381,638B | 190.867s | 104 /2 /7157 /63 | human/SWE分scope四表全部键和整数/浮点值exact相同 |

May31的7157条request_misses是官方top-level scope选择后的请求，原输入7324行仍全部保留；child请求不作为独立scope模拟。两周均逐表核对列、复合键唯一性、keyset、行数、原行键顺序和所有数值。整数要求exact；浮点设 `atol=1e-6, rtol=1e-12`，实际每列max absolute/relative delta均为0，没有依赖容差通过。request级keys和rows只在私有目录比较，不输出身份字段。所有作者/新结果source manifest均相同且对应当前输入。

八个Parquet文件的byte SHA均与作者版本不同，但逻辑数值全相同；footer明确作者Arrow25.0.1/pandas3.0.6、本次26.0.1/3.1.1，均为SNAPPY、格式2.6且原行键顺序一致。没有逐字节逆向归因，因此不把不同SHA误当数值差异。完整哈希/逐列比较与无身份aggregate cells见 `reports/complete_{smallest,mixed_scope}_week_simulation_comparison.{json,csv}`；实际命令见对应 `logs/official_checks/`。

Jun07未采集真实peakRSS，保持Unknown。May31用Linux wait4记录最大RSS统计1,907,608KiB（约1.819GiB）、user155.970s/system35.142s；这是kernel最大resident-set统计，不是并发所有进程RSS求和，也不是GPU内存。资源文件为 `reports/complete_mixed_scope_week_resource_usage.json`。外部`/usr/bin/time`不存在的前置失败单独保留exit127，原算法未启动；随后只使用自有测量wrapper执行一次原版replay，没有安装系统包。

这些结果将**两个指定完整周**升级为独立模拟验证；全16周论文缓存数值仍基于作者中间表，73项数值对照的等级/数量不升级。全16周在剩余预算内的运行时间只能依据块量作规划外推，约9.33h是推测而非实测。按原预算停止新增cache实验，未修改算法或生成缺失论文实验。

## 执行缺陷、修复与语义限制

原版单周绘图 exit0 不能证明所有输出有效：缺少 SWE 时四个 benchmark median 和四个 ratio 为 NaN，benchmark trajectory为零；只有 cache comparison 显式跳过。`scripts/validate_paper_numbers.py` 实际检出8个非有限值并exit1。隔离补丁 `patches/0001-report-empty-benchmark-scope.patch` 改为显式跳过比较section；仅在私有副本验证，上游和原版16周结果未改。补丁类别/等价性界限见 `patches/README.md`。

其他必须保留的口径：

- TTFT queueing 由长期cache miss的 median prefill-rate 推断；无对应 GPU queue telemetry。无可信TTFT的会话时间按已有比例回填；2×分析排除human idle并cap每次toolwait15min。
- tool latency为连续请求间的有效gap，Time/Figure5主要用single-call requests，failure分母为可见outcome。论文说排除estimated RTT，但公开链路未找到显式RTT扣除；私有logged latency是否预处理为Unknown。
- 4条cached>prompt观测在uncached函数中clip0，hit ratio中clip1，token-growth路径另报negative share；负gap在gap曲线被排除、session time被clip0，而single-call tool-share路径不统一clip。不能把这些观测直接称为数据损坏或负真实tool runtime。
- 价格模型为cached/uncached/output相对1/10/50，基础设施$1/M重算与$30/Mtoken-days存储假设。没有实测账单、GPU KV占用、吞吐或网络包捕获。

## 保持 Unknown 的项目

Aug30及全16周完整cache replay结果、真实provider cache策略/容量、真实GPU性能，私有Gateway原日志的重建验证、subagent Figure7完整方法、Table6b完整profile、Figure16意图标签质量，及 batch-mix/provider-D差异根因。两个已核对的小完整周不代表其余14周。未执行匿名JSONL→Parquet转换，未调用任何模型/API来补齐缺失标签，未将推断或模拟当作网络包、TCPflow或实测服务器性能。
