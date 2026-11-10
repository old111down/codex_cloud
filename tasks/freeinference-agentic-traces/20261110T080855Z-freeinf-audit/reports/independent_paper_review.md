# 论文分析与声明清单的独立复核

复核开始：2026-11-10T08:24:10Z。对象为 `paper_analysis.md`、`research_notes/paper_workload_characterization/paper_claims.csv` 初稿的71条选定数值声明，以及官方18页 PDF。反馈后原作者补入2条 Table6 batch mix 声明；最终复核清单为73条。未新增网络搜索、数据下载或大实验；结论来自论文逐项核对、固定源码与已发布小型 CSV 的静态对照。运行与全数据统计由其他审计报告负责。机器可读范围、校验值及逐条状态见 [independent_paper_review.json](independent_paper_review.json)。

**总评：论文分析正确区分了生产应用观测、规则重建、时延估计、LLM 标签与 trace-driven 模拟。没有发现把网络分类或真实部署优化写成已复现成功的问题。** 进一步源码交叉检查发现 Table6 分母与 batch mix 的可确认差异，以及 RTT 扣除路径、筛选规则和 Tool 指标条件口径。已直接通知原作者与根代理，并确认最终主报告新增披露这些问题；上游方法/数值差异仍待验证。没有修改他人的主文件。

## 已确认的关键差异

### R1．Table6 的宽度分布是 call-weighted，不能直接称 request 概率

论文 Table6/PDF p.6 和 p.7 正文将84.5/8.7/3.5/3.3描述为每 request 发出1/2/3/4+ tools 的比例。固定代码 `paper/metrics/tools.py` L150–169 明确按每条 tool-call row 的 `width` 做 `value_counts(normalize=True)`，没有对 `(session_id, step)` 去重；注释也说明3-call request 会被计3次。因此代码统计的是随机抽取一个 call 时其所属 request 的宽度分布，而非随机抽取一个 request 的分布。零 tool request 也不在 calls 表内。

已发布 `batching_profile.csv` 对应84.4815526/8.6523892/3.5308330/3.3352252，舍入后能对上论文四个数字。这加强了分母疑点，但不能仅凭静态文件证明作者论文计算历史的每一步。不得未经重算替论文补出“正确 request 比例”。[论文 Table6](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=6)、[固定指标代码](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/metrics/tools.py#L150-L171)、[固定发布 CSV](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/figures/v1/tools/batching_profile.csv)

### R2．Table6 batch mix 与发布 CSV 不一致

PDF Table6 是 Same tool 71.3%、Mixed 28.7%；固定发布 CSV 是64.01737580122536%、35.98262419877464%。当前代码对 batched requests 按 `(session_id, step)` 分组后判断 category 唯一数，再取 request 级均值；这与宽度分布的 call 加权并不是同一种权重。差异可确认，原因可能涉及权重、过滤或版本，但目前均为 Unknown。这里不能把“预计算文件存在”写成“与论文数值一致”。[固定 CSV](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/figures/v1/tools/batching_profile.csv)、[当前计算](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/metrics/tools.py#L162-L171)

### R3．论文的 RTT 扣除在公开导出/指标路径未定位

论文 §5/PDF p.5 定义 effective tool latency 时排除 estimated network RTT。公开 `export/release/requests_table.py` L178–184 直接使用下一请求 start 减当前 end；`paper/metrics/tools.py` 的 tool wait 由 `turns.waits` 产生，后者同样是 start 减上一请求 end。`export/log_records/fields.py` 则由 logged end 与 latency 派生 start，未看到 RTT 字段或校正。这是论文描述与已定位实现之间的方法缺口。

保守结论是“所读发布导出与统计路径未定位 RTT 扣除”，不是“作者从未扣 RTT”：原始日志在更上游是否已处理仍 Unknown。独立 sessions 审计已交叉确认相同路径。不得将发布 `latency_ms` 或图中时延当作精确客户端工具进程计时。[论文](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=5)、[导出 gap](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/release/requests_table.py#L178-L184)、[指标 gap](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/metrics/turns.py#L42-L45)、[时间字段派生](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/log_records/fields.py#L174-L192)

### R4．Tool 指标具有条件分母

当前 `overview_table` 的 Time share 只使用 width=1 的 calls；`latency_by_category` 也只取 single-call requests 且等待非空。Failure rate 只对 outcome 非空记录计算；result-token 分布只用 matched/non-null result。故 Table5 的16.9% Interpreter time、5.8% Ask User time、3.3% failure 等若用于结果对照，应写明所用条件集合，不能解释成全部并行工具的真实 CPU 时间份额或全部任务的失败率。[固定 metrics/tools.py L86–105、L136–146](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/metrics/tools.py#L86-L146)

### R5．生产样本筛选比“过滤单请求 API”更强，且与 SWE 不对称

Table1 caption 说明过滤 single-request API traffic 和其他 benchmark replay。当前导出还要求 human main-chain 至少2个 user turns、1个 tool turn，而 SWE 只要求至少1个 tool turn。单用户 turn 但有许多 LLM/tool steps 的真实 Agent 任务也可能被排除。这会结构性选择具有多轮交互的人类 session，限制“所有生产任务都比 benchmark 更长/空闲更多”的泛化；不能据此量化偏差大小或否定已观察样本的结果。[Table1](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=1)、[固定筛选与 main-chain 入口](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/sessions/chains.py#L23-L24)、[筛选函数](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/sessions/chains.py#L89-L102)

## 重点结论的复核结果

| 项目 | 复核判断 |
|---|---|
| 研究创新 | 支持 session-level production serving characterization；未误称 packet/flow 测量创新。最大/首创等相对文献主张应归属作者，不能视为此次独立穷举证明 |
| 95% session matching | 报告准确限于有显式 session ID 的 harness 子集；未知子集规模、各类错误与验证独立性，不外推为所有 session/turn/subagent 的95%真值准确率 |
| TTFT/queue | 正确指出 cold long-context throughput 估计 prefill、residual 含其他 overhead；没有把它写成内部队列探针；外部模型两图不是全部模型绝对时延复现 |
| effective tool latency | 主报告已说是间接估计；还应纳入R3、R4的实现与分母限定 |
| Tool/Prefill/Decode 2× | 正确标注反事实模型；排除 user idle、tool gap cap15min，不是部署优化实测 |
| Fig10–13 | 正确标 trace-driven cache simulation/cost assumptions/lifecycle counterfactual，不是测到 provider 的真实 TTL 策略或缓存内存 |
| 36× | 正确保留 caption dead-block 与正文 accumulated-storage 口径差异；不能简化成“总硬件容量节约36×” |
| 62.5% | Table7 infinite-retention fresh-prefill attribution，报告限定正确；不是实际 provider miss 的62.5%实测归因 |
| Intent8类 | 定义与 few-shot/抽样来源相符；模型、模板、人工核验/IAA 未报告；公开 labels 不足以重做原实验，不当作 gold truth |
| Table1与Table3 | 正确说明 Table1 12,002含1,035 SWE；相减10,967为算术值。内部 Table3 的 messages 不代表公开 schema 存在正文 |

以上源定位主要为 PDF pp.1、3–5、8–13；没有发现这些重点边界被写成成功复现。正文人类与 SWE 的差异仍是带筛选的观察比较，不构成因果识别。

## 初稿71条、修订73条声明的完整性和限制

已检查初稿71行及新增2行的 ID 唯一性、页码/来源链接与数值单位，逐行核对对应 PDF 图表/正文。没有发现明显数值误抄。该清单是**选定数值声明**，并不覆盖论文全部方法与论断，例如95%验证、TTFT估计和 Figure12 价格反事实没有独立行，不能把“清单已复核”称为所有实验方法均已验证。新增 Table6 batch mix 两行正确保留纸面值及 artifact 不一致的限定。

反馈后已确认：Table1 包含 SWE 的总量与 `swe_sessions` 的 evidence kind 已改为混合 trace inventory/benchmark replay；Time/Fail 行已加入R4条件分母。主报告也单列了R1–R5。这些是证据类型与口径精化，不表示论文数值已被重新计算。每条 source claim 被核对只表示论文确有该报告值，不表示本次数据运行验证了它。

## 未完成与 Unknown

没有重跑全期统计、cache simulation、标签生成或三方 benchmark；没有确认R1/R2差异的作者历史版本与因果来源；没有验证 raw logger 是否已做 RTT 校正。上述差异不得被夸大为造假、数据泄漏或全部论文不可复现。后续应在固定公开数据上分别输出 call-weighted/request-weighted batch profile、明确 single-call/outcome 过滤，并保存与论文及预计算文件的三方比较。
