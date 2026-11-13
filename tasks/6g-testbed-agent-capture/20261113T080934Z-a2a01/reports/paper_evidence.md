# Agent/A2A 论文证据审计

审阅时间：2026-11-13 UTC。仅进行官方材料只读获取与方法审计；本文没有新场景运行、抓包或网络整形结果。论文为 [arXiv:2611.07250v1](https://arxiv.org/html/2611.07250v1)，重点完整阅读 §3–4、Table 3、§5.3–5.4/Fig. 3、§6 和 §7.1。相关声明逐条见 [paper_claims.csv](paper_claims.csv)。

结论：该论文支持将本轮工作描述为“对指定版本官方 Agent/A2A 功能、应用日志与私有 PCAP 关联、受控路径延迟对照的验证”。论文不支持把本轮本地 A2A 验证直接称为历史 S4aP260148 campaign 的数值复现、真实 WAN 多跳 Agent 性能复现或 6G 无线系统验证。下文“可验证声明”是论文的明确陈述；是否已被指定源码正确实现、是否在本轮成立，需要另行核验，不能由论文本身代替。

## 来源、版本和可核验程度

| 材料 | 已读证据 | 版本与关联 | 限制 |
| --- | --- | --- | --- |
| 官方 arXiv HTML/PDF | 已下载、完整阅读相关章节；HTML 和 PDF 对 Table 3、Fig. 3 轴/图注及 §7.1 一致 | 固定 `2611.07250v1` | 论文转述 workbook 数值，不等于获得原始 campaign 文件 |
| 官方源码 | 仅只读查看版本及文档 | checkout 和短 SHA `d055fa68ef4d` 均解析为 `d055fa68ef4de30b93a8a30838ae51fe3e4b561c` | 本报告没有把当前源码视为每个历史 worksheet 的执行版本 |
| 历史报告/workbook | §5、§7.1、参考文献 [2] 明确指向 TR 26.870 V0.6.2 / S4aP260148，2026-10-23 分发 | §7.1 将“implementation review revision”和“report/workbook snapshot”分开陈述 | 官方 ZIP 引用 URL 返回 HTTP 403；本审计未独立读到 ZIP，不能声称 workbook 单元格已核对 |
| 历史 Agent 贡献 | 论文参考文献 [24] 标为 Qualcomm S4-261814（S4-261446 的修订），2026-08 | 说明文献关系 | 贡献文档、原始 session/PCAP 未获得，不能建立逐 run 关联 |

私有保存目录：`private/evidence/paper/`，保留 HTML、PDF、转换文本、目标章节、响应头及失败下载元数据，均不应公开。来源 URL、时间与 SHA-256 见私有 `manifest.json`。关键原件摘要：

| 文件 | 官方 URL | SHA-256 |
| --- | --- | --- |
| HTML（315,924 B） | https://arxiv.org/html/2611.07250v1 | `f032d94a82c6c70b774700073adf618da2bbae1c86dc1af42192f13a15d95e7b` |
| PDF（112,706 B） | https://arxiv.org/pdf/2611.07250v1 | `e3de79b1b00c88515297372bb694afc899e50619bc2407b5d21f12d20f1b6f9e` |

下载完成并建档时间为 `2026-11-13T07:57:54.670159Z`。官方 ZIP URL 是 `https://www.3gpp.org/ftp/TSG_SA/WG4_CODEC/3GPP_SA4_AHOC_MTGs/SA4_Plenary/Docs/S4aP260148.zip`；精确 URL 请求于约 `07:58:16Z`，返回 HTTP 403，相关响应头已私存。未绕过访问限制。

## §3–4：本轮验证应继承的方法

| 章节/定位 | 可验证声明 | 本轮应对照的证据 | 适用边界 |
| --- | --- | --- | --- |
| [§3.1](https://arxiv.org/html/2611.07250v1#S3.SS1) | 指标必须关联 scenario、profile；session ID 关联配置、应用记录及 capture；每一层保留自身字节口径 | 独立 run/session 标识、版本、配置、时间窗、应用记录和 PCAP 的双向匹配 | 同名 profile 或同一目录不证明同次运行；跨 profile aggregate 需声明总体与权重 |
| [§3.2–3.3](https://arxiv.org/html/2611.07250v1#S3.SS3) | netemu 负责整形/capture/PCAP 分析，aitestbed 负责实验；主接口 HTB+netem/IFB 与 loopback native-rate 队列不同 | 实际使用接口、路径、方向、已执行 tc 参数及捕获接口的私有记录 | 同名输入不能保证主接口与 loopback 的延迟、排序一致 |
| §3.3 | capture 的 sidecar 记 scenario/profile/run；过滤器只覆盖声明端口；论文称 TCP handshake 在可用时确定 client/server | 本轮预期 A2A 连接是否双向可见，发现请求/任务请求/流响应是否在过滤覆盖内，角色由协议/握手/本轮连接确定；源码实现另行核验 | PCAP 文件存在不证明有效覆盖；端口大小顺序不可靠；没有 handshake 时角色仍可能不明 |
| [§3.4](https://arxiv.org/html/2611.07250v1#S3.SS4) | 每 request 记录尺寸、token、开始与首末 chunk 时间、状态/error；timeout 算完成，其他失败可能重试 | 保留全部尝试、重试、timeout、成功、排除理由；成功 task 与日志映射 | completed-run 数不是服务可靠性分母；timeout 不自动归因为网络 |
| [§3.5](https://arxiv.org/html/2611.07250v1#S3.SS5) | loopback 与 WAN egress 分开；跨 session 持久连接按 session 边界分段 | 接口、连接、session、时间窗联合归属；不明归属单列 | 不可仅凭 IP/port 将共享连接所有包归入某一任务 |
| [§4.1](https://arxiv.org/html/2611.07250v1#S4.SS1) | Agent 个人助手为本地 runtime 驱动 model/tools；A2A 为 JSON-RPC、SSE；local/remote 指 inference 所在路径 | 本轮实际 A2A 实现、交互类型、拓扑、是否含 inference | 本地 synthetic A2A 不代表 hosted Agent runtime 或真实 WAN；loopback 不模拟无线协议栈 |
| [§4.2](https://arxiv.org/html/2611.07250v1#S4.SS2) | profile 表列的是 nominal inputs；`lossy` 为独立丢包压力测试 | 记录名义 one-way delay 与实测 RTT、丢包、排序分别是什么；纯 delay 对照需其他参数固定 | 6G/5QI 命名不验证 6G 无线系统，也不保证实际路径 percentile；多参数 profile 不提供单因素归因 |
| [§4.3 Eq.1](https://arxiv.org/html/2611.07250v1#S4.SS3) | TTFT=`t_first−t_start`，TTLT=`t_last−t_start`；first/last 指记录的 response-chunk 到达 | 从源码核对本轮 timer 起止；应用总延迟、首 chunk、末 chunk 与 PCAP handshake RTT 分列 | chunk 可含多个 model token；非流式首末时间相同；不能将 TTFT 当网络 RTT |

## Table 3：观察面与字节口径

[Table 3](https://arxiv.org/html/2611.07250v1#S5.T3)（PDF 第 7 页）标题将 network 列明确限定为 capture 中的 **IP payload**。正文解释网络计数包含 transport headers、ACK 和 retransmissions。它不是以太网线速总字节，也不能自动等同 TCP application payload；本轮需逐项核对分析器实际加总字段。

| 历史 scenario / 观察面 | UL B/turn | DL B/turn | UL/DL | 可支持的解释 |
| --- | ---: | ---: | ---: | --- |
| Personal assistant，control/application | 144 | 20,230 | 0.007 | driver 发送小任务并接收含较多 metadata 的本地结果 |
| Personal assistant，control/network | 3,817 | 49,981 | 0.076 | 同一个控制面在 capture 层的协议开销明显 |
| Personal assistant，WAN egress/network | 175,649 | 353,972 | 0.496 | runtime 的 hosted model/tool 流量是另一观察面；约 176 kB UL/turn |
| A2A，所有 variants，loopback/network | 1,931 | 4,084 | 0.473 | 三类 A2A 的本地网络层汇总，不能作某一 variant 的逐 run 值 |

§5.1 使用 **mean UL / mean DL**，与 mean(每 turn UL/DL) 有别。表中的 network aggregates 均未显示 UL 大于 DL；不能用“agent”类别名称推断 uplink-heavy。应用序列化尺寸排除 transport/TLS 开销，个人助手 driver 尺寸还排除了 runtime 自身的流量（§6.5）。容量推断必须先证明哪个观察面实际跨过接入链路。仅抓本地控制面不能验证 WAN 数值，也不能不加区分地合并 loopback 与 egress 成一份“agent 流量”。

本轮可报告自身每 variant、每 profile 的 matched-turn UL/DL 计数及明确公式，随后说明与历史 Table 3 的观察面和口径是否可比。历史字节数不是本轮通过阈值。

## §5.4 / Fig. 3：延迟与多跳边界

[§5.4](https://arxiv.org/html/2611.07250v1#S5.SS4) / [Fig. 3](https://arxiv.org/html/2611.07250v1#S5.F3)（PDF 第 10–11 页）针对不调用 LLM 的 deterministic A2A agents。图的横轴是 **configured round-trip delay = 2 × nominal one-way delay**，纵轴是 mean per-turn latency。横轴不是从 PCAP 测得的 RTT。

论文可直接核对的数值是 single-task 在 `satellite_geo` 的 687 ms 对 nominal 680 ms；delegation unshaped baseline 为 277 ms。streaming 含配置 chunk pacing。delegation 只整形 client-to-orchestrator hop，而且下游任务顺序派发；论文没有声称每条下游 hop 都加入相同 impairment。`cell_edge` 和 `congested` 的上偏差/失败发生在多种 impairment 同变的条件，论文不区分原因。

本轮若具备隔离整形能力，适合比较：同 variant、固定 chunk pacing/执行配置、零延迟 baseline 与仅 delay 改变后的应用延迟差，同时独立报告 handshake RTT 变化。需先验证请求和响应方向各经过几次 queue；`delay=d` 只说明队列输入，不能未经路径核对便写成实测 RTT=d 或 RTT=2d。双方同机不需要跨机时钟校正，但 wall clock、monotonic timer 与 PCAP 时间仍要说明转换、窗口与精度；若跨主机，一向延迟需要可靠的时钟同步。

允许的结论是“在本轮声明的本地路径及计时口径下，改变队列延迟后观察到应用时间与网络时间如何变化”。不能外推为真实多跳 Agent 的共同 QoS、packet-error-rate 目标、LLM 推理性能、WAN 接入网容量或 6G 无线性能。若整形被平台限制，RTT 对照应标为 BLOCKED；不能用 fallback 自建流水线替代官方场景 PASS。

## 时间层次、可靠性和版本约束

1. [§5.3](https://arxiv.org/html/2611.07250v1#S5.SS3) 明确 TCP/TLS 的样本数不同；中位数/percentile 不可相加为 end-to-end setup。流级连接复用比例不等于 request 级新建连接比例。chunk gap 包含 server buffering、transport delivery、client reads；与 RTT pooled median 比较不能隔离生成时间或证明网络无影响。
2. §5 开头将 commercial、local 和 agentic populations 视为独立 campaigns。agentic worksheets 的历史总体是个人助手 200 turns；三种 A2A 分别 198、99、100 turns，跨十个 profiles。它们不是本轮分母，也不提供固定 profile 的重复运行置信区间。
3. §5.4 个人助手 baseline mean 11.4 s、HRLLC 9.7 s，而 baseline 范围 5.4–31.2 s；论文明确不将均值降低归因为 profile。200 turns 全成功仅描述样本；长 timeout、可靠传输、retry/resume 和未观测尝试会限制可靠性推断。
4. [§6.1–6.4](https://arxiv.org/html/2611.07250v1#S6) 指出 per-packet jitter 可导致 reordering；main 与 loopback native rate 行为不同；correlated random loss 可能严重抑制低概率事件；Gilbert–Elliott 字段映射及早期实现发生变化。名义 profile 不能替代实测路径。不要把 random-loss 的第二参数归零操作套到 Gilbert–Elliott，否则 bad state 可能吸收。
5. [§7.1](https://arxiv.org/html/2611.07250v1#S7.SS1) 明确源码和 nominal profiles 不足以重建历史 hosted behavior；还需 model config、prompts、执行命令、软件版本、capture、session records。原始 hosted captures 未随论文公开。当前 repo 的 `AGENTIC.md` 是计划文档；其中设计本身不证明历史运行完成。

## 给本轮结论的证据门槛

| 本轮结论 | 可以判定的最低证据 | 证据不足时 |
| --- | --- | --- |
| 官方 A2A 功能 | 指定 SHA 官方实现，实际任务/响应与预期协议可核验，退出/错误保留 | FAIL 或 BLOCKED；自建 fallback 单列为 pipeline demonstration |
| 应用日志 ↔ PCAP 一致 | 本轮接口、连接、session、clock window 同时匹配；双向预期 A2A 交换经实际读包核对；附排除/负对照 | unmatched/ambiguous 明列，不因有文件而 PASS |
| 延迟/RTT 对照 | 已确认隔离路径，记录实际 shaping 方向/次数；名义 d、实测 RTT、应用 latency 分列，固定其他配置 | 平台能力不足标 BLOCKED；不转述历史 Fig. 3 为本轮证据 |
| 历史 workbook 数值复现 | 同观察面/字节口径/总体；逐 run 的版本、配置、命令、数据、session/PCAP provenance | 当前为未建立；只可称“与论文历史值作语义对照” |

其中负对照与明确 PASS/FAIL/BLOCKED 是本轮审计要求；论文提供 session 配对、分层报告和版本限制的依据，并未给出本轮的验收状态。全文与原始数据应继续保留在私有目录，公开交付仅包含原创审计结论、无敏感配置和汇总结果。
