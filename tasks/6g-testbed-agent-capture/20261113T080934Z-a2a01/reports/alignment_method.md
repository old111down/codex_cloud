# Agent / A2A 日志与网络证据的可审计对齐方法

本方法只适用于本次授权的固定本地 Agent / A2A 任务。它规定证据如何匹配，以及何时必须保留 `ambiguous`、`unmatched` 或 `BLOCKED`；本文件本身不构成实测 PASS。运行结果应以逐轮原始证据、运行清单与主审计报告为准。没有可解析的真实 PCAP 时，日志↔PCAP 对齐与实际 RTT 对照均为 **BLOCKED**，不能用日志时间、配置延迟或模拟 JSON 替代。

## 1. 静态证据范围

权威源码是官方 `6G-Testbed` 的 `d055fa68ef4de30b93a8a30838ae51fe3e4b561c`。以下行号均指该 commit，读取方法为 `git show <SHA>:<path> | nl -ba`。先前默认分支曾显示 `7231ae8e5670b67564cf28d397c2820d9403ecdc`，它不能替代论文 commit。论文版将网络采集与分析迁到 `netemu`：`aitestbed/capture/__init__.py:12` 从 `netemu.capture` 导入采集器；`aitestbed/analysis/__init__.py:18` 从 `netemu.pcap` 导入分析器。

| 官方证据 | 实际记录的粒度或限制 | 对本次审计的含义 |
|---|---|---|
| `aitestbed/analysis/logger.py:23–69` | session、turn、run_index、浮点时间、字节来源与 metadata；没有接口、netns、socket、连接 epoch 或 monotonic 时钟字段 | 单凭 SQLite 行不能证明某个 TCP 连接属于某轮任务 |
| `aitestbed/scenarios/base.py:114–116,154–225` | session 为 UUID；`timestamp=time.time()` 是创建日志行的时间，通常在操作结束之后 | 用 `t_request_start` 与实际结束事件构造操作窗，不把 `timestamp` 当发送时间 |
| `aitestbed/scenarios/agent.py:479–690` | 一 turn 内可有多轮 LLM iteration 和多次 MCP tool 调用；共享 turn_index | 增加 event_id、iteration、tool_call_index、parent_event_id，防止 turn 内混合 |
| `aitestbed/scenarios/a2a_agent.py:144–190,231–264` | 每 prompt 一条 A2A turn 记录；保存 agent_url、streaming、event_count、output_chars；不保存 message/task/context/request ID 或客户端端口 | 官方结果可提供应用轮次真值，仍需 wrapper 连接与请求级证据 |
| `aitestbed/scenarios/a2a_agent.py:245–264`、`analysis/trace_logger.py:68–71` | A2A `_turn_record` 没有传 trace_request/response/events；即使启用 TRACE_PAYLOADS 也不会由该调用产生 payload trace；http_status 为 success 派生的 200/0 | 不期待开关自动补齐 A2A 请求 ID 或真实 HTTP status；需要独立 hooks/PCAP 验证 |
| `aitestbed/clients/a2a_client.py:129–149,171–192` | httpx hooks 估算请求体+头、响应头+Content-Length；Agent Card 获取发生在 `_cur` 尚未设定的建会话阶段 | 字节估计不等于线上字节；Card / readiness 流量必须单列，不能归入任务 |
| `aitestbed/clients/a2a_client.py:48–73,177–186` | first/last chunk 是 SDK 交付的任意 A2A event 时间；文本 event 才增加 chunk_count；total_latency 到最后 SDK event | A2A TTFT 更准确称“首 SDK 事件延迟”；不能声称首网络包、首 token 或每包行为标签 |
| `aitestbed/a2a_agents/launcher.py:51–64` | readiness 持续 GET Agent Card；子进程 stdout/stderr 被丢弃（44–48） | 采集可能包含启动探针；wrapper 应记录 readiness 和 capture-ready 边界 |
| `aitestbed/a2a_agents/orchestrator_agent.py:34–51,70–82` | 下游请求在 `for` 中依次执行，异常可被转换为返回文本 | 官方场景描述中的 fan-out 不能被理解成并发；client-facing success 也不证明每个下游成功 |
| `aitestbed/scenarios/a2a_agent.py:104–124` | 官方只对 client-facing target 端口应用 loopback shaping；下游仍被采集 | 三条 hop 的 RTT 不能混用，必须逐路径报告 |
| `aitestbed/orchestrator.py:1149–1170,1404–1432,1461–1489` | capture metadata 有 invocation 级 run_id、interface；PCAP capture 是独立 `pcap_*` session；应用记录没有同一 run_id；采集包围一次 CLI invocation | 用外部 manifest 显式将 capture_id → invocation → 应用 session 绑定；本次每轮独立 capture，禁止跨轮目录自动推断 |
| `netemu/src/netemu/capture.py:92–127,159–168` | 启动 tcpdump 后延时检查进程；sidecar 记录 wall start/end；退出检查只要求文件存在且至少 24 字节；没有 clock_id、monotonic 或丢包计数 | 起止 wall 时间和文件存在都不能替代 collector-ready、真实包读取和双向协议验证 |

协议名称须区分源码概念与实际版本：源码把 non-streaming 场景称为 `message/send`，不同 SDK 版本可能在 wire 使用 `SendMessage`、不含旧版 `kind` 的 text part 或 `task.artifacts` result 包装。源码 docstring 的版本号不是安装证明；安装版本以本次环境 `importlib.metadata.version` / freeze 为准，实际 method 与 envelope 以 PCAP 重组为准。解析器不能为了迎合注释而把真实请求当空流量，也不能无条件接纳任意 JSON。请求/响应 envelope、ID、输入内容与结果 artifacts 应一起验证。

## 2. 外部 instrumentation 接口与本次实现边界

保持官方仓库不变。下表是可迁移到 CLI/桌面 Agent 的增强接口；wrapper 可在官方调用前后记录 JSONL 事件，或在明确采用该方案时 hook 已存在的 HTTP 请求与响应。它不是对本次已采字段的宣称。本次 root 选择直接运行官方 CLI、保留 SQLite 与逐轮 run manifest，不注入 per-send hook；因此没有逐发送的 monotonic 边界或 SDK/socket ID。实际存在的字段及其空缺必须由生成的 manifest 和只读核验器明确列出。原始字段仅保存在 private；公开输出只使用合成别名和计数。

| 字段组 | 必要字段与含义 |
|---|---|
| 版本与轮次 | `schema_version`, `event_id`, `experiment_id`, `capture_id`, `run_id`, `scenario_id`, `session_id`, `run_index`, `turn_index`；event_id 不因同 turn 多事件而重复 |
| 任务与阶段 | `task_alias`, `task_hash`, `phase`（preflight/cold/hot/turn/teardown），`event_kind`（readiness/card_fetch/a2a_send/a2a_event/mcp_tool 等），`parent_event_id`、iteration/tool_call_index |
| 进程与采集面 | `host_alias`, `process_role`, `pid`, `netns_inode`, `interface_name`, `ifindex`, `capture_linktype`, `pcap_sha256`, `capture_ready_*`, `capture_stop_*`；接口名仅在同一 namespace 内有效 |
| 连接 | `connection_id`, `protocol`, `local_addr`, `local_port`, `remote_addr`, `remote_port`, `connect_*`, `close_*`；TCP key 必须加 SYN/连接建立 epoch，不能只用可复用的四元组 |
| 请求级关联 | `http_method`, `route_class`, `http_version`, `http_stream_id`（适用时），JSON-RPC request / A2A message / task / context 的本地加盐 HMAC，及 parent/child request 关系；不保存公开可逆原文 |
| 时钟 | `clock_id`、`clock_source`、`t_start_wall_ns`, `t_end_wall_ns`, `t_start_mono_ns`, `t_end_mono_ns`；锚点另存 `mono_before_ns`, `wall_ns`, `mono_after_ns` |
| 结果 | `success`, `error_class`, `application_bytes_source`, `request_bytes`, `response_bytes`, `sdk_event_count`；文本结果只在 private 用作确定性任务断言 |

本次请求级关联的可接受基础是：每轮新 capture + 全部进程在已确认的自有 netns + 固定本地任务 + DB 操作边界 + 实际 HTTP 连接端点 + 私有协议请求/响应重组，结合源码确认的串行发送顺序、预期内容与数量交叉验证。未取得的 SDK ID 不由 PCAP ID 反向伪填为“应用已记录”；未取得的 per-send monotonic duration 不由 run duration替代。仅有目标 server port 不满足客户端 socket / 请求级唯一性；如果 SDK 无法暴露连接，须以私有明文 HTTP/TCP 重组和连接生命周期补足，否则按连接候选输出，不升级 packet 标签。

同一 HTTP keep-alive 连接可以承载多个 turn；同一 A2A 请求可以产生多个 SDK event；一个 TCP segment 可以拼接或切分应用 event。因此 `event ↔ connection`、`request ↔ HTTP message` 和 `SDK event ↔ packet` 是不同关系，必须分别标注。HTTP/2 多路复用若缺少 stream ID 或协议重组，只能保留共享连接层关联。

## 3. 时钟映射与误差

官方主要计时使用 `time.time()`，没有 monotonic 校准。新增 duration 用 `time.monotonic_ns()` 或明确命名的 `perf_counter_ns()`；不要把这些数值直接当 Unix epoch。PCAP timestamp 的精度、kernel / hardware 来源、所在主机必须从文件头与采集器记录确认。

本次外置 `scripts/packet_capture.py` 使用 AF_PACKET 原始 socket、只保存 child netns 的 lo 上 TCP 9001/9009 的 PACKET_HOST 帧，写纳秒表示的 classic PCAP / DLT_EN10MB；时间来自 Linux `SO_TIMESTAMPNS` 软件接收 timestamp（CLOCK_REALTIME），不以用户态 `recv` 时间回填。collector 绑定与 header fsync 后才写 ready，SIGINT 后排空已排队帧，并保留 socket drops 与 SHA。它是原创外置采集器，不是官方 tcpdump CaptureController；nanosecond 表示精度也不等于 nanosecond 测量准确度。

本次 collector 具有 start/ready/end 与约每秒 wall↔monotonic 锚点，run wrapper 可额外记录 run 边界；官方每 turn 的 DB 时间仍是浮点 CLOCK_REALTIME。相同主机的 kernel realtime 与 DB realtime 不需要跨主机 epoch 偏移，但仍受 wall-clock 跳变、浮点量化与事件语义延迟影响。保留原始 float/取整方式并计入其 ULP 量化尺度；不能声称已测得每 turn 的 monotonic latency。有限锚点与 timestamp 倒退检查无法排除两锚点间发生又恢复的短暂跳变。

在每轮 capture 前、turn 前后和 capture 后读取锚点：`m_before = monotonic_ns(); w = time_ns(); m_after = monotonic_ns()`。该次 offset 的区间为 `[w−m_after, w−m_before]`，估计值 `d=w−(m_before+m_after)/2`，采样半宽为 `(m_after−m_before)/2`。使用两侧锚点插值 `d(m)` 后，`wall_est(m)=m+d(m)`。保留全部锚点，不能只公开一个“已同步”布尔值。

输出 `anchor_count`、采样半宽最大值、offset 起止变化、拟合/插值残差、PCAP timestamp 分辨率、估计总容差 `epsilon_ns`。容差至少包括采样半宽、观测残差和 PCAP 量化误差；跨主机还必须计入实测同步不确定度。该容差是“无未观测时钟跳变”假设下的估计，有限锚点不能证明全程最坏误差。若 `Δwall−Δmono` 超过预先声明的阈值，或时间倒退/锚点区间不一致，拆分 clock epoch 并将跨 epoch 对齐标为 ambiguous/BLOCKED；不能静默扩大窗到所有流量都匹配。

原始匹配窗为 `[start_wall,end_wall]`，候选窗只可按事先记录的 `epsilon` 扩为 `[start−epsilon,end+epsilon]`。同时报告原始窗和扩窗结果；若唯一性依赖大幅扩窗，明确暴露该依赖。函数返回前已接收但尚未写日志等调度延迟属于应用观测语义，不应伪装成 PCAP 时钟误差。

## 4. 匹配规则与可证明范围

逐轮首先核验 capture SHA、真实 packet 数、首末 timestamp、linktype、截断与捕获结束状态；解析双向请求与响应，证明安装版本的预期 A2A HTTP / JSON-RPC 操作存在（如旧版 `message/send` 或实际观察的 `SendMessage`），并校验 envelope/ID/内容。24 字节头文件、仅握手、只有一个方向或只含探针均不能通过任务流量审计。连接方向由已知客户端/服务角色确定，不能只取较小端口为 server。

对应用事件 E 建立 candidate 集合 C，依次施加所有可验证条件：

1. **轮次身份**：同一 manifest 中的 experiment/run/capture，绑定同一 session/turn/event；文件名和时间重叠只用来发现候选。
2. **采集面**：相同 host + netns + interface/ifindex + capture epoch；不同接口的副本不重复计数。
3. **连接**：协议、双向端点和 TCP 建连 epoch 一致；NAT、proxy 或转发路径需记录前后端映射；下游 hop 独立匹配。
4. **时钟窗**：确认 clock epoch 后，连接/消息与事件窗相容；零交集直接排除。非零交集只表示时间相容。
5. **请求证明**：优先匹配 HTTP stream/message 与 JSON-RPC/A2A 请求 ID 或私有重组证据；流内重试、Card fetch、健康检查分别编号。若字段缺失，降低证明粒度。

| 输出状态 | 判定 | 可报告的结论 |
|---|---|---|
| `unique` | 所需粒度上全部硬条件满足且唯一候选；记录其证据列表 | 唯一连接关联或唯一 HTTP 请求关联；必须标出 `association_grain` |
| `ambiguous` | 候选数大于 1，或虽只有 1 个时间候选但缺少连接/请求证据、clock epoch 不确定、共享/多路复用无法拆分 | 保留全部候选与 reason；不能任选最近包 |
| `unmatched` | 数据完整且条件已知，候选数为 0 | 本轮某事件未找到对应网络证据；不自动等于“没有网络行为” |
| `BLOCKED` | 无 PCAP、格式不支持、严重截断/缺方向、采集接口/clock 身份无法确认 | 无法检验对齐；不计为 unmatched 或成功率分母 |

即使请求关联为 unique，也不从“在该事件时间段内”推出每个包的行为标签。握手、ACK、重传、SSE buffering、后台连接都可同时发生。报表分别给出 event 总数、eligible 数、unique/ambiguous/unmatched 数、blocked 原因、target connection 数、双向 packet / payload 字节，并保留不匹配分母。不同粒度的 unique 不可相加。

## 5. 负对照

至少执行并保留一项真实负对照，推荐两项。负对照同样进入汇总，不能在看过结果后挑选容易通过的窗口。

* **同轮非任务连接**：使用同一自有 capture 中可证明是 readiness/Agent Card 或自有非目标连接的记录；保持其真实时间，尝试匹配 task 请求。请求 ID/route/连接规则应拒绝。若仅依据 server port + 时间而被接纳，暴露为 false association。无需向共享或生产服务发探针。
* **错误时间窗**：复制真实事件的匹配查询，保留 run/interface/connection 条件，把窗移动到该请求结束、连接关闭且超过 epsilon 的已观测区间；预先记录 shift 和期望 0。没有这样的已观测区间则该项 BLOCKED，不能假造“空 capture”。

负对照期望为零 unique task 匹配；ambiguous 也须列出。故意修改查询条件不产生新的实测任务、网络包或真值样本。正对照与负对照都通过，才说明本次规则能区分已观测数据；不能外推为识别任意 Agent 行为的分类准确率。

本次初步 smoke002 的实际负对照是自有 lo:9009 的 TCP connect/close，没有 HTTP payload。它能核验非目标连接在同一 PCAP 中存在且被目标端点/协议规则排除；不能称为 HTTP 健康检查或同协议语义负样本，也不能证明网络行为分类的 false-positive rate。最终逐轮表应如实标注该控制的粒度。

## 6. 官方网络分析器的使用边界

`netemu/src/netemu/pcap.py:367–374` 在过滤端口前累计总帧/字节与 capture 时间；目标 TCP 记录在 `393–430` 后处理。故 `total_packets`、`total_bytes`、基于它们的吞吐不是自动限定的 A2A 数值。只对已确认的目标连接重新计数，并区分 frame bytes、IP bytes、TCP payload bytes、去重 application bytes。

该分析器固定以 Ethernet 解码（375–377），没有按 pcap datalink 分派；不支持的 RAW/NULL/SLL 等不能当“零流量”。IPv6 TCP/UDP 有处理分支（442–473），但仍需从实际文件验证 linktype。TCP flow 以双向四元组聚合（677–708），未按新 SYN epoch 分开；每轮新 capture/连接可降低合并风险，不能消除跨 turn keep-alive 语义歧义。方向优先用 target_ports，否则 lower-port heuristic（884–890），应以 wrapper 服务角色复核。

`TCPFlow.handshake_rtt` 实际是 SYN→第三 ACK（106–117）；`syn_ack_rtt` 是 SYN→SYNACK。第三 ACK 识别缺少严格方向与 seq/ack 验证（734–736）。本次重检同一目标 TCP epoch 的 SYN→SYNACK，检查反向端点、SYN/ACK 标志、ACK=client_ISN+1，排除重传/丢包歧义；单点抓包的该值称“观测 SYN→SYNACK 时差”，只有测点与路径明确时才解释为路径 RTT。netem 的 delay 配置是自变量，不是实测 RTT；应用 latency 也不是 RTT。

`aitestbed/analysis/ran2_metrics.py:183–229` 依据文件名时间桶与 dominant scenario/profile 进行关联；`423–475` 使用 pooled PCAP handshake 统计。它们不能替代本方法要求的逐轮、同接口、同连接、同路径匹配。

## 7. 固定任务、cold/hot 与小样本对照

每轮使用完全相同、无外部检索/付费模型的本地确定性输入与叶子行为，保存 task_hash 和配置哈希。A2A echo 的预期输出由 `_transform` 确定（`a2a_agents/echo_agent.py:26–32`）；功能断言应验证输出内容和错误状态。不要把只返回 HTTP 200 当任务成功；多 Agent 场景还需验证两个下游均按预期返回。

明确区分：process cold start（启动/就绪）、session cold（新 SDK session/Agent Card/连接）、hot turn（已就绪且明确复用同一 session 的后续发送）。记录实际连接是否复用，不能仅按 turn_index 推断 hot。官方 A2A 每个 run 启停 fleet、在一个 session 中遍历 prompts（`scenarios/a2a_agent.py:153–196`）；本次 wrapper 若改变这些边界，必须记录为不同执行方式。ready/Card 的成本分别列出，不能混入 hot latency。

每轮一个独立 capture；基础与加延迟条件使用同一固定本地任务、同一路径/接口/目标 hop、相同 cold/hot定义；记录实际 qdisc 验证、退出/失败、超时和 capture 状态。RTT 样本必须来自该轮该目标连接或明确同路径的独立探测，不能把其他接口或下游 hop 的样本拼接。netem 设定值、应用 latency、观测 SYN 时差分别成列。

小样本公开每轮结果、有效 n、median 与 min–max；分 cold/hot 与条件汇总，保留失败分母。若比较延迟，优先同阶段/同任务的逐轮或配对差值；顺序效应和热身差异仍作为限制。n 很小时 P95 基本由最大值或插值控制，不能据此声称稳定尾延迟或统计显著；不把同一连接的多个包伪当独立实验重复。

## 8. 字段迁移与公开交付

配套 `reports/agent_field_migration.csv` 将 CLI/桌面 Agent、A2A 与未来 network-only 输入分开。session、连接/IP/port、进程、应用 request/task ID、工具名、payload、任务标签和 profile 标签只用于采集控制/链接真值或验证，不可作为 network-only 行为识别输入。网络候选特征限于在事先声明测点可观察的长度、方向、时序等，且后续识别实验另行授权；本次不训练分类器、不宣称识别准确率。

可公开：原创方法/脚本、合成别名逐轮聚合、状态与误差摘要、去敏配置。保留私有：完整官方源码与论文、raw payload / PCAP / IP端口 / 真实 session/task/connection ID、系统状态、原始 trace、salt。trace_logger 的凭证键脱敏（14–32）不等于任务内容隐私脱敏，不能直接上传 trace。

## 9. 首次真实采集器核验（smoke002）

`reports/collector_smoke_review.json` 是独立只读核验摘要，不把 smoke 自动加入正式重复试验的 n。核验实际读取了私有 PCAP：40 条 record、5,547 frame bytes、6,211 file bytes，满足 `file_bytes=24+16×records+frame_bytes`；SHA、record 数、frame bytes、首末 timestamp 与 collector manifest 均一致。socket 记录 80 个收到的 frame / 0 drops，保存 40 条 PACKET_HOST，符合 loopback outgoing/host 去副本设计；该比例只描述这一轮观察，不能当通用去重保证。SIGINT 后已 drain，timestamp 无倒退。

5 个 collector wall↔monotonic 锚点均满足 sandwich 顺序，最大读取区间为 2,095 ns；用整数 `2×wall−mono_before−mono_after` 后求差，offset midpoint 观测范围为 363 ns，起止变化 −290.5 ns。run 边界锚点最大读取区间为 1,109 ns、起止 offset 变化 −22 ns。DB 浮点秒在本轮 epoch 的 ULP 约 238.4 ns。这些是观测分辨率/漂移摘要，均不是端到端时钟误差的最坏上界。

首包发生在 ready wall 之后约 15.466 ms，末包在 SIGINT 之前约 628.751 ms。该采集完整性检查不替代双向 A2A HTTP/JSON-RPC、确定性结果、连接 epoch 与负对照核验；这些由独立 `scripts/analyze_capture.py` 与其逐轮输出承担。正式 A 组所有轮次还需逐一执行相同检查。
