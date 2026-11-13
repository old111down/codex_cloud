# A 组采集器独立复核

A001–A010 共 10 轮的**采集完整性检查全部通过**：实际只读检查 400 条 PCAP record / 55,470 frame bytes，各轮纳秒 little-endian PCAP header、DLT_EN10MB、文件大小公式、SHA、packet/byte 数、首末 timestamp 均与 manifest 一致；没有截断、timestamp 倒退或 socket reported drops，SIGINT 后均已排空队列。原始文件未改动。

独立读取每轮 launcher、run 与 collector 清单，确认其 parent/child namespace 关系一致、child 只有 loopback、launcher 使用 user+net namespace；父及子 qdisc 前后读取均成功且内容相同。公开摘要仅保留检查结果，没有 namespace inode、进程 ID、原始接口状态或 payload。

每轮最大 collector clock sandwich 区间的中位数为 1,859.5 ns，范围 1,320–8,811 ns；每轮 offset midpoint 观测范围的中位数为 220 ns，范围 77–3,298 ns。run 边界的最大 sandwich 区间为 1,010–1,397 ns。DB 浮点秒的 ULP 均约 238.4 ns。计算先使用整数 `2×wall−mono_before−mono_after` 再求差，避免 epoch 绝对值转浮点造成量化损失。完整逐轮检查见 `collector_baseline_review.json`。

静态复核已确认 collector 的边界检查、指定端口 TCP 过滤、PACKET_HOST 选择、必需 SO_TIMESTAMPNS、私有输出、信号后 drain、hash/drop/finalization error 记录。离线检查覆盖 IPv4/IPv6、片段/截断拒绝、时间戳缺失拒绝和 PCAP header。可选的 expected-child 参数不替代实际 launcher 证据；本次已逐轮交叉核验其 parent token 与真实记录。

上述时钟统计是观测不确定度摘要，不是最坏精度保证；有限锚点不能排除两锚点之间短暂 wall-clock 跳变，官方 turn 也没有独立 monotonic duration。采集完整性 PASS 不代表 SDK event↔packet 行为真值；A2A 协议、任务结果、连接 epoch 与负对照由独立 `analyze_capture.py` 核验。
