# 5G-MAG Agent/A2A 采集链路云端验证

现在可迁移的是**版本固定的本地A2A单任务驱动、每轮独立捕获、日志—连接关联、负对照与完整性审计流程**；真实时延干预、TLS/并发CLI或桌面Agent广域出口仍缺证据。

## 三项验收

| 项目 | 判定 | 证据与范围 |
|---|---|---|
| A2A场景复跑 | PASS | 原版orchestrator与echo agent，固定论文审查提交，10个分开的基线轮次，各一个合成任务；[逐轮表](runs.csv)、[协议摘要](reports/per_run/) |
| 应用日志↔PCAP | PASS | 10/10唯一关联到一个HTTP/1.1 A2A任务连接，10个负对照连接可见且排除；只验证运行/连接粒度 |
| RTT干预对照 | BLOCKED | 新建隔离child loopback上`tc netem delay20ms`返回`Specified qdisc kind is unknown`；不加载共享宿主内核模块，不用应用sleep替代网络整形，B组0轮 |

官方场景PASS限本地确定性A2A功能路径，不代表整个测试床、Docker、全部矩阵或内建采集器通过。此处实际使用自有外置AF_PACKET采集器，原版sudo/tcpdump CaptureController没有执行。

## 来源、环境及操作约束

代码固定`d055fa68ef4de30b93a8a30838ae51fe3e4b561c`，处于detached checkout，上游未修改。论文v1的§7.1用该提交审查实现；历史报告/workbook `S4aP260148`是另一来源，不能认定同次运行。官方历史ZIP本轮HTTP403，未独立核对workbook单元格。详见[论文证据](reports/paper_evidence.md)、[入口审计](reports/entrypoint_audit.md)。

Linux Debian13.6，CPU配额4核、内存限制16GiB；独立Conda Python3.12.16。安装A2A及orchestrator import所需的轻量依赖，真实仓内custom aiortc源码经PYTHONPATH导入，未安装或运行torch/GPU/VLM。原依赖锁与仓内custom aiortc声明有矛盾，详见版本和原始安装日志；这是可审查的环境选择，不声称复原历史锁环境。

普通父进程无AF_PACKET权限；本轮实际授权路径是创建自己的user+network namespace，仅包含lo，并验证父子namespace不同、每轮父qdisc前后相同。只在该child内置lo为UP和抓取本任务9001/9009端口。未修改父/共享接口或qdisc，未调用付费API、生产流量或其它场景。

## 固定任务与连接策略

私有最小YAML保留官方scenario type/provider/agent参数，只把默认两个prompts改为一个固定合成任务，retry_count=0。任务内容/原始配置不上传，哈希与去正文快照见[配置](environment/scenario_snapshot.json)。每轮重新启动官方server及SDK session，先获取Agent Card再发一次任务；实际task所在keepalive连接同时含card GET与task POST。因此不能把它笼统称为冷TCP请求，也未将冷热连接混合统计。

每轮原始PCAP、数据库、原日志和私有连接证据单独保存，路径及SHA见runs.csv和manifest。namespace inode在销毁后可能复用，不作为跨轮全局身份；同一固定task哈希用于全部轮次，每轮有各自run/session记录。IP/端口/服务身份/session及runID仅作关联真值，不是未来分类输入。记录的实际wire RPC方法是 **SendMessage**；源码注释中的message/send不当作实测字符串。

## 小样本结果

以下只有A组，不存在B组效应估计。SYN指标是**同一loopback软件RX观察点上SYN→匹配SYN-ACK的时间差（packet-based RTT estimate）**，不等于独立socket/ICMP端到端RTT校准，也不等于论文图3名义2d。

| 量 | n | 中位数ms | 范围ms |
|---|---:|---:|---:|
| 官方SDK任务时延 | 10 | 7.548451 | 6.587267–10.089636 |
| 观测点SYN→SYNACK估计 | 10 | 0.111419 | 0.010991–0.271431 |
| POST首字节→其响应末字节 | 10 | 4.265704 | 3.435602–5.815071 |

这些是10个分开轮次，不自动视为IID统计样本；不报告P95为稳定尾部结论。APP与HTTP跨度的差值也不能直接归因于计算/模型开销。没有可比较的第二组，不能验证论文“任务时延随RTT变化”的干预结论。

| 轮次 | APP ms | SYN估计ms | 目标端口包数 | 匹配 | 负对照 |
|---|---:|---:|---:|---|---|
| A001 | 8.906126 | 0.271431 | 34 | unique_connection | PASS |
| A002 | 7.823944 | 0.081324 | 34 | unique_connection | PASS |
| A003 | 6.587267 | 0.237402 | 34 | unique_connection | PASS |
| A004 | 9.295940 | 0.017549 | 34 | unique_connection | PASS |
| A005 | 9.067297 | 0.097920 | 34 | unique_connection | PASS |
| A006 | 7.030487 | 0.124917 | 34 | unique_connection | PASS |
| A007 | 10.089636 | 0.010991 | 34 | unique_connection | PASS |
| A008 | 7.132530 | 0.083768 | 34 | unique_connection | PASS |
| A009 | 7.272959 | 0.156614 | 34 | unique_connection | PASS |
| A010 | 7.245779 | 0.236617 | 34 | unique_connection | PASS |

## PCAP、关联与时钟核验

10轮共400个实际捕获记录，其中目标过滤340包、匹配连接180包、负对照60包。匹配连接字节含card和task；目标过滤还含readiness等连接，都不能叫精确单任务网络字节。frame字节与论文Table3的IP-payload/应用层统计不能直接等同。

PCAP纳秒格式、Ethernet datalink、长度、哈希、首末时间、双向TCP、无截断/倒退、drain及内核报告丢弃数均核验；不是只检查文件存在。SYN/SYNACK及第三ACK方向与seq/ack吻合才给握手估计，重传歧义不强算。关联联合run/capture/interface、官方session记录、端点/连接epoch、时间窗、HTTP/JSONRPC id及确定性echo；全部匹配在未经扩展的官方APP窗内。9009空载TCP connect/close是已知非目标负连接，不冒充同协议语义负样本。[采集独审](reports/collector_baseline_review.md)、[分析器](scripts/analyze_capture.py)。

官方APP时钟是float `time.time()`，而wrapper/collector采样monotonic-before/realtime/monotonic-after锚点；PCAP是SO_TIMESTAMPNS软件接收CLOCK_REALTIME。DB时间float ULP约238.4ns。锚点读取夹序宽度最大8,811ns，观测offset range最大3,298ns；这些是读取区间和观测变化，不是UTC校准或packet误差上界。50ms是预声明匹配容差，不是测量误差，本轮10次未依赖它扩展APP窗。若未来加egress整形，RX tap可能位于第一单向排队之后，不能预设SYN差包含2d，必须再校验观测点与独立客户端RTT。

## 失败、修正及未验证内容

首轮审计中的smoke001应用/采集成功，但父namespace参数由包装器错误传入，故排除验收；原件和失败原因保留，smoke002改由launcher实际读取父namespace并核验后重跑通过。批运行门控首次使用了错误的summary字段而停止在首轮之前，修正为真实`match_status`并保留失败日志；没有因此伪造A组轮次。安装缺失包和首次CLI帮助失败均保留。这些历史记录不代表每次fresh复跑都会发生同一失败。当前运行未更改上游以隐藏失败。

缺口：未执行B组、未校准端到端socket RTT、未测TLS/H2/H3复用并发/重试/桌面后台流量、未验证个人助理WAN与真实多跳、无逐包工具语义真值。下一轮需要已授权且netem可用的隔离路径，在同一客户端时间基准验证RTT；再为自己的CLI/桌面Agent加进程/attempt/transport连接事件、双时钟和采集完整性计数。[迁移字段清单](reports/agent_field_migration.csv)。

复跑入口[reproduce.sh](reproduce.sh)只覆盖本任务A2A与降级分支；不执行全矩阵、AR/XR、视频、分类器或P4。入口的`--smoke-only`已在全新私有工作副本中实际执行通过（复用同一环境和只读源码，另一次任务/捕获，不计入上述A组样本）；默认十轮入口未再整体重复运行，但其基线与逐轮分析组成命令已实际执行。若未来环境已可用netem，full入口会明确停止，不能继续声称本轮的BLOCKED原因。只公开脱敏报告、脚本、汇总与环境元数据；原PCAP/明文/凭据不上传。
