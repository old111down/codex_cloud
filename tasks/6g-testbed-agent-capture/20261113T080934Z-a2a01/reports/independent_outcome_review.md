# A001–A010 独立结果复核

本审查仅只读现有证据，没有重跑场景、采集、分析器或 tc，没有修改 upstream/source。已读逐轮公开结果、私有 run/collector/launcher 清单、SQLite、PCAP、权限/netem 探针，以及采集器与严格分析器源码。原始证据、最终 `REPORT.md`、`manifest.json`、`runs.csv` 与 `summary.json` 已复核通过；三项判定的数值、计时定义和适用范围一致。

## 可以支持的三项结论

| 判定 | 证据支持的范围 | 不应扩大的范围 |
| --- | --- | --- |
| 官方 A2A 功能 PASS | 固定 SHA `d055fa68ef4de30b93a8a30838ae51fe3e4b561c` 的 stock orchestrator / `a2a_single_task_local`，受控单条合成 prompt、零 retry，10 个分开的 `no_emulation` 本地基线轮次；实际任务回复符合 deterministic echo，task completed | 不是其它 Agent/A2A variants、OpenClaw、LLM、WAN、多跳或全部 A2A 标准实现的认证；单 prompt/defaults 是声明过的配置差异 |
| 运行/连接对齐 PASS | 每轮一个官方 app task 对应唯一 HTTP/1.1 JSON-RPC A2A send 连接，协议 ID/私有合成任务/回复、方向、连接 epoch、接口、run/session 与时间窗交叉核对；负对照被排除 | 不是逐 SDK event 与每个 packet 的 ground truth；不是任意持久连接或并发多任务归属验证；外置 collector 成功不验证内建 CaptureController |
| RTT 干预对照 BLOCKED | 子 namespace 内 netem 探针明确失败，未获得可执行的整形组 B | 基线 packet time delta 可描述，不能支持加入 delay 后的应用变化、`2d` 关系、路径校准或因果结论 |

直接读取 400 条原始 PCAP records，10 轮逐一独立验证：匹配 SYN/SYN-ACK 的方向、序号/确认号及时间差与逐轮 JSON 一致；原始 HTTP request 的 wire method 均为 `SendMessage`；按 HTTP Content-Length 读取的原始 response 均为 completed task 并含预期私有 echo；每轮官方 SQLite task duration 与 `t_last_token−t_request_start` 一致。PCAP hash、launcher 隔离关系与父/子 qdisc 前后相同证据也一致。原始任务、地址/端口元组、ID 和 PCAP 未公开。

## 独立重算的描述统计

| 指标 | 样本单位 / n | Median ms | Min–max ms | 解释 |
| --- | --- | ---: | ---: | --- |
| 官方 APP task duration | 每轮一个 task / 10 | 7.5484514 | 6.5872669–10.0896358 | 官方 wall-clock 请求开始至末事件时间；不包括整个进程/服务启动周期 |
| HTTP request 首字节至匹配 response 末字节 | 每轮选中的 task HTTP exchange / 10 | 4.2657040 | 3.4356020–5.8150710 | 同一 PCAP 软件接收观察点的应用消息到达跨度，不是网络 RTT |
| SYN→匹配 SYN-ACK 的软件 RX 时间差 | 每轮匹配连接一个 handshake / 10 | 0.1114185 | 0.0109910–0.2714310 | 同一 loopback 采集观察点的 packet-based RTT estimate；不是独立 socket/ICMP RTT 或绝对端到端校准 |

这些是 10 个基线轮次的描述，不能推出统计独立性、总体可靠性、稳定尾延迟或 profile 效应。APP duration 与 HTTP 到达跨度的计时边界不同，两者之差不能直接解释为计算或模型开销。建议不报告 P95；如果保留某个插值 percentile，必须说明公式并标为小样本描述，不能解释为可靠尾界。

## 报告必须保留的边界

1. **实际 wire 方法与文档操作名分开。** `message/send` 可用来说明文档/逻辑操作；本轮原始 JSON-RPC method 是 `SendMessage`。公开逐轮 JSON 已同时保存 observed method 和 canonical operation。不能将文档字符串当成本轮抓包过滤和实际报文证明。
2. **外置采集器分开。** 本轮是 original `AF_PACKET` collector，只保留隔离 loopback 的 `PACKET_HOST`、必需 `SO_TIMESTAMPNS` 软件 RX timestamp；官方内建 CaptureController 未运行。第三方/自编采集器的有效运行不能写成“官方 tcpdump CaptureController 通过”。官方 scenario 本身确实运行，与纯自建 scenario fallback 有别。
3. **包与字节计数分观察面。** 十轮合计 PCAP 400 packets，其中目标端口 340、负对照 60；每个匹配连接为 18 packets。每个匹配连接都含 AgentCard GET 和 task POST 两个 HTTP requests/responses。因此 `matched_connection_counts` 仍是连接总量，不是精确单 task 网络字节；`target_filter_counts` 还包括其它 readiness/discovery 连接。frame bytes 包括捕获帧头/ACK 等，不能等同论文 Table 3 的 IP payload，亦不能和官方序列化 request/response bytes直接相等。
4. **时钟证据只描述实际观测。** `clock.status=valid` 表示锚点结构与顺序有效，不代表 UTC 准确度或同步已校准。collector 最大 sandwich 读取区间为 1,320–8,811 ns、offset midpoint 观测范围为 77–3,298 ns；这些是锚点读取区间与观测偏移变化摘要，均不是 packet timestamp 精度上界。纳秒 PCAP 表示不证明纳秒准确度。有限锚点不能排除中间短暂 wall-clock 跳变；官方 turn 没有独立 monotonic duration。
5. **匹配容差不是时钟误差。** 50 ms 是预声明的关联容差，不是实测 clock error；10 轮任务 request/response 实际均位于未扩展的官方 task 窗口内。容差、锚点统计、float 秒 ULP（约 238.4 ns）三者不能互换。
6. **packet RTT estimate 不作 `2d` 校准。** 这里是 Linux 软件 RX 观察点的 SYN→SYN-ACK 时间差。未来若在 egress 加 queue，首 SYN 可能在请求排队后才被观察，不能假设这个差包含两次单向排队。论文 Fig. 3 的横轴是 nominal `2×d`，本轮没有组 B，既未验证该关系，也没有复现其数值。
7. **平台阻塞描述具体。** 已保存的子 namespace 命令 `tc qdisc replace ... netem delay 20ms` 退出 2、报 `Specified qdisc kind is unknown`。外层探针脚本退出 0 不代表 tc 成功，应读内层命令状态。此证据说明本轮隔离路径缺少可用 netem qdisc；不应泛称所有 Cloud 不支持 netem、整形权限拒绝或所有 Linux qdisc 都不可用。没有加载共享 kernel module 或改共享 qdisc。
8. **版本与历史来源分开。** d055 是本轮源码和论文 implementation review revision；S4aP260148 是历史报告/workbook provenance，不能由相同 SHA 宣称同次运行。论文原始 hosted captures 未分发，官方历史 ZIP 本次 HTTP 403。当前 local single-task 数据不能验证历史 WAN egress、全部 A2A variants、6G 无线栈或真实多跳性能。
9. **跨轮身份不只依赖标记或 namespace token。** 十轮使用相同 seed，私有 task hash 只有一个不同值；每轮 app session 则不同。每次 launcher 都执行 `unshare` 并确认子 namespace 不同于父 namespace，但记录的 child token 在十轮相同，可能在前一实例销毁后复用，不能当跨轮全局唯一 ID。当前归属依赖每轮文件/启动清单、session、连接 epoch 与时间窗共同成立；不应写成“十个不同任务标记”或“十个不同 namespace token”。

## 最终文字与制品核对

最终 `REPORT.md` 已明确限定为本地 single-task 官方功能加外置 collector，保留 `SendMessage`、card/task 共连接、相同任务 hash、namespace inode 可复用、RX 观察点、50 ms 容差、小样本及历史版本边界。未把论文 nominal `2d`、Table 3 的其它观察面或原始 hosted campaign 当成本轮结果。环境 Debian 13.6、4 核 CPU quota、16 GiB limit 及专用 Python/SDK 版本与读取记录一致；不据此推断云地域或 WAN 性能。

`runs.csv` 的十个 A 行逐项对照原始/逐轮结果，时延、hash、计数、clock 摘要和 scope 一致；两条 smoke 都不纳入 A 总体。复核发现 excluded `smoke001` 曾虚填不存在的 selected-connection 关联路径，root 已修正为两列留空并保留 EXCLUDED 状态。该问题不影响 A 组结果，当前已无待修正的结论问题。`manifest.json` 内嵌 summary 与 `reports/summary.json` 一致。`environment/source_provenance.json` 的全部源文件 hash、执行 SHA 与 pristine checkout 一致；aitestbed/netemu 的 bundled LICENSE 标为 5G-MAG Public License v1.0，netemu pyproject 的 Apache-2.0 冲突单列为适用性未知，没有把声明冲突解释为可随意再分发源码。

只读查看 root 的额外 `reproduce.sh --smoke-only` 集成检查日志，退出 0，官方功能/采集/严格关联检查通过；它使用 fresh private copy、相同环境与只读官方 source 路径，不纳入本轮 A001–A010 统计，不形成 B 组证据。本审查没有自行执行该检查。

逐轮独立检查及审查时制品 SHA-256 见 [independent_outcome_review.json](independent_outcome_review.json)。最终复核结论为 **PASS：REPORT/manifest/runs/summary 对证据的转述准确**，支持本报告所限定范围内的官方 A2A PASS、运行/连接对齐 PASS、RTT 干预对照 BLOCKED。
