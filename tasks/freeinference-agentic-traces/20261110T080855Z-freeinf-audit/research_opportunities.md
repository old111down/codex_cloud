# FreeInference 用于 Agent 网络研究的价值与边界

本报告区分已核实来源事实、可检验研究假设与待验证条件。相关项目的运行成功、论文分类精度和 PCAP 对齐精度均未在本子审计中验证；本任务实际执行情况以 [reproduction_report.md](reproduction_report.md) 为准。关联来源与版本见 [related_work_comparison.csv](related_work_comparison.csv) 和 [来源笔记](research_notes/related_agent_measurement_work/notes.md)。

## 研究定位与明确判断

FreeInference 的主要创新是从单条 LLM request 转向长生命周期 session，对真实 human-driven Agent 的上下文复用、工具等待、用户间歇与缓存开销进行服务端测量，并提供经过匿名化的结构化 trace。它为 Agent serving 研究提供生产环境证据；论文没有建立“只看加密网络包识别 Agent 行为”的分类基准。论文自己指出缺少精确客户端 tool 执行测量，session 需要重建，异构生产使用模式的结论不必适用于其他服务。[论文 §3/PDF p.3、§9/PDF p.13](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf)

**A．是否适合作为 Agent 网络流量研究的数据来源？** 适合用作应用侧工作负载依据、标签设计依据和实验设计依据，不能单独构成网络侧分类数据集。公开 trace 可帮助研究 session/turn/step 的规模、请求密度、工具类型、上下文变化和人类间歇，避免只用短小单轮任务设计实验。其 token、tool、cache 指标的含义也可帮助定义网络实验的混杂变量。要研究真实 packet 长度、方向、IAT、重传或连接复用，必须增加网络观测；token 数量并不等于线上字节数，cache token 也不直接告诉我们密文 packet 形状。

这些先验只代表筛选后的样本。当前导出要求 human main-chain 至少2个 user turns 和1个 tool turn，SWE-Bench 只需 tool turn；它会排除部分单次用户输入但多步执行的真实任务。因此跨轮 idle 与长期 session 的分布适合作为所选 population 的实验依据，不能当作所有 Agent 的无偏总体。[固定筛选](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/sessions/chains.py#L23-L24)、[筛选入口](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/sessions/chains.py#L89-L102)

**B．能否直接为独立 PCAP 提供可靠行为标签？** 不能。公开历史 trace 与研究者后来独立执行的 Agent 是不同执行实例。公开 schema 中没有已证实的 client socket/5-tuple、TLS connection 或 HTTP stream 对应关系；request/session 标识与 `start_ms/end_ms` 不能凭空补出这些关联。即使时间段相似，也不能证明是同一个用户、任务或请求。原始 prompt、tool result、原始标识不公开，Fig16 的语义 intent 也不能从 hashed blocks 重新恢复。[固定 README](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/README.md#L26-L33)、[固定 schema](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/release/schema.py#L67-L120)

**C．最少增加什么机制？** 必须在我们自己同一次运行中，同期采集客户端 PCAP 与应用请求事件，并记录共同运行标识、任务/turn/request 的父子关系、单调时钟与 UTC 锚点、请求发起/首响应/结束/异常事件、固定 harness/model/route 配置。先用隔离进程或 network namespace 排除背景流量，并从单一 in-flight request 开始。只有时间窗口时，产物应称为带不确定度的弱标签；若要求逐请求强关联，还需要客户端 transport/HTTP stream 映射、可验证的独占连接，或对自有合法 TLS 会话进行仅用于校验的协议观测。正常分类器不得读取解密内容或应用 metadata。[具体对齐方案](trace_pcap_alignment.md)

**D．当前最值得做的一个实验？** 先做“单 Agent、单模型、受控短任务的配对采集与标签可信度实验”，验证能否可靠建立监督样本，再训练分类器。优先 Hermes，但 `mimo-v2.6-flash` 当前 route 需满足实际模型目录、账户授权与调用验证；本次匿名模型目录未列出该模型，不能假定原计划已经可运行。详细 hook、拓扑、执行与停止条件见 [MVP](mvp_experiment_plan.md)。此次不把其他模型的成功当作 MiMo 成功，也不把历史公共 trace 当作自己的 Gateway 日志。

**E．成功与失败的证据边界？** 成功可以证明：在记录的 harness、模型、网络路径、协议、并发条件下，可以得到已量化关联误差的应用事件—网络样本。它不能证明跨 provider/harness 的语义泛化、线上真实任务意图可识别、论文全部结果复现或线速性能。若串行条件下仍大量事件无法唯一映射，可以排除“这套事件粒度和时间匹配规则已足够生成高置信标签”；若仅并发失败，则排除该配置下简单一请求一 burst 的规则。失败不能排除所有 Agent 网络分类，也不能证明网络完全没有可辨别信息。

## 与三项相关工作的实质差异

| 工作 | 已核实的观测与目标 | 对本研究最有价值的部分 | 不能直接比较的部分 |
|---|---|---|---|
| FreeInference | 服务端应用 trace；筛选后的生产 session、tool/context/cache 工作负载 | 真实使用分布、长 session、人类空闲、上下文变化；为实验分层提供依据 | 无配对 PCAP；重建算法公开，但原始输入、95%验证材料与intent标签缺失，历史在线打点未知；不能比较网络 F1 |
| ANT | 同期客户端 tcpdump + session logs；episode 风险/场景与 segment primitive 分类 | namespace 隔离、按事件分段、应用日志与 PCAP 联合采集 | 受控 task 与 LLM-assisted 标签；按时间分段不是 flow 一一对应；未在本次运行其 benchmark |
| MAGIC26 | 受控单/多 Agent × backend；容器 Scapy PCAP 与 run 配置 | 明确的网络侧采集和 backend/执行模式指纹任务 | backend/路径标签不等于用户行为语义；正式全文/DOI与数值尚 Unknown；文档和已读源码有不一致 |
| TraceLab | 客户端本地 Claude/Codex 事件日志，归一化、匿名化后分析 serving | 本地 event timing 与 tool wall/internal 时间的区分、可借鉴日志结构 | 客户端应用日志仍不是 PCAP；官网新数据与论文/README旧数据版本不同 |

ANT 的论文 §3 描述将每个 packet 按 primitive 开始时间归入 segment，跨边界 flow 按 packet 分配，再利用 LLM 从日志生成 primitive。它是“先采集跨层证据，再建立标签”，并未证明只用 Gateway 历史表可以反推网络流。作者也承认 AI 标注错误和受控环境 timing 的局限。[ANT v1，§3/PDF pp.3–5、§5/PDF p.9](https://arxiv.org/pdf/2610.06514v1)

MAGIC26 此处专指 [`simula/magic26`](https://github.com/simula/magic26/tree/bf6797f7da735a6fccb8f140f27106c78a87490f)，不是无关同名项目。其 README 自述论文题名与 [MAGIC 官方节目](https://sites.google.com/view/magic-cnsm/home) 的标题有差异，正式 PDF 尚未定位。已查的 `react_agent.py` 确有 Scapy capture/save，却未找到 README 所述 events/summary 文件写入；ML README 指向 Robust Fingerprinting，`RF.py` 是含 Conv1d/Conv2d 的 `nn.Module`，不能将缩写 RF 直接解释成 Random Forest。此处仅确认已读文件存在文档不一致，不据此断定论文算法错误或全仓功能缺失。[capture 源码](https://github.com/simula/magic26/blob/bf6797f7da735a6fccb8f140f27106c78a87490f/agents/react_agent.py#L492-L540)、[模型源码](https://github.com/simula/magic26/blob/bf6797f7da735a6fccb8f140f27106c78a87490f/ml/models/RF.py#L6-L85)

TraceLab 论文直接链接作者组仓库，关联明确。论文 v2 Table1 与固定 README 数据 v0.0.1 为4,265 sessions、43 users、357,161 steps、432,510 tools；官网目前数据 v0.0.2 显示8,058、52、665,453、743,819。这是来源版本差异，不能混成同一个实验规模，也不能据此认定复现错误。[论文 v2 §3/PDF pp.3–4](https://arxiv.org/pdf/2606.30560v2)、[固定 README](https://github.com/uw-syfi/TraceLab/blob/5c6550b0d08beff983e9159fe2575e7a2334c8c1/README.md#L119-L125)、[官网](https://tracelab.cs.washington.edu)

## 哪些标签值得研究，哪些边界必须保留

公开字段的含义与生成过程见 [标签机制审计](label_mechanisms.csv)；以下是网络研究用途的判断，不把推断标签提升为人工真值。

| 分类对象 | 可用的应用监督依据 | 推荐粒度与条件 | 关键限制 |
|---|---|---|---|
| Harness | `harness`，由 UA/提示特征等规则识别 | 同次采集的 session/运行级标签；由实验配置复核 | 类别不平衡和任务/route 分布混杂；不能在模型输入中直接喂 harness 字段 |
| User/tool-triggered | `step_trigger`，依据链式关联与结果模式推断 | request 级；用客户端事件确认触发原因 | 不是 PCAP 直接可见事实；重建错误会污染标签 |
| Tool category | 归一化 tool 名、家族与 shell purpose 规则 | tool batch 或明确 action interval；保留未知/混合类 | 本地 Read/Bash 可能不出网；WebSearch 可能后台代执行；类别名不等于语义任务 |
| Subagent | nested session 与 spawning call 关联 | 父子 session/episode 级；需调用生命周期日志 | 子 Agent 可并发、共享连接或路由；不能假定另有独立 flow |
| Tool outcome | tool result 规则归一化 `ok/error` 等 | 结果可用后的离线事件级 | `ok` 不代表 task 完成；若预测实时状态，不能偷用未来结果 |
| Context mutation | 应用内容/块序列变化标签 | request 级；可检验网络变化的条件关联 | hashing/token 变化不是 packet byte 变化；模型、压缩、streaming/cache 会混杂 |
| Model/provider | 公开 model 名称、匿名 provider 标识及实验配置 | 作为控制/分层变量；也可单独定义路径分类任务 | provider 匿名字母不能直接映射公开 endpoint；路径分类高分不等于行为语义高分 |
| Session规模/密度/turn数 | 应用层分组与计数 | 适合事后 episode 统计或提前定义的在线目标 | session 结束后的总量用于在线预测会造成未来信息泄漏；session 与 flow 不同 |
| Create/Debug等 intent | 论文用 LLM + few-shot 标注抽样 turns | 先重新定义标注规范，再对自己合法可用的任务标注 | 公开 schema 无此列；原 prompt 不公开；标注模型/模板/人工一致性未给，无法独立恢复原标签 |

八类 intent 的论文证据在 Fig16/PDF p.12；当前发布 `paper/__init__.py` 图表 registry 到 Fig15，schema 无 intent。对这些类可以设计新的研究，不能声称已经有与历史 trace 完整配对的官方标签。[论文](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf)、[固定 schema](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/release/schema.py#L67-L120)、[固定 registry](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/__init__.py#L118-L139)

## 可继续推进的可证伪问题

以下均为研究假设，尚未由本任务实验验证。选题应先证明标签与样本可靠，再讨论分类准确率。

1. **带不确定度的跨层标签。** 问题是共享 TLS 长连接、并发和不精确事件边界下，能否用有界时间窗与 transport 证据产生可校验的样本，并对歧义样本主动 abstain。比较单纯最近时间匹配、事件窗口和带连接约束的映射，报告 precision、coverage、歧义率与边界误差。若 coverage 仅通过错误地强制唯一映射上升，该方案应被否定。FreeInference 的层次可作为输出本体，ANT 的同期采集可作为设计参考。
2. **控制路径混杂后的行为可识别性。** 固定 harness/model/provider/任务模板的因素后，比较网络特征能否区分有明确定义的本地/外部工具阶段。按 task instance 和整个 session 分组划分，增加跨 route/harness 的外推；设置只看 endpoint/总时长的简单 baseline。若去掉 endpoint 或跨 deployment 后能力消失，只能报告路径/部署特征，不应命名为通用 Agent 语义识别。
3. **生产先验能否改善受控 benchmark 的代表性。** 用 FreeInference 公开聚合分布选择长短 session、idle gap、工具 batch 与上下文规模，再比较短单轮 benchmark 下估计的网络开销偏差。它可以检验实验覆盖是否过窄；合成调度或 trace replay 生成的网络序列必须标记为模拟，不能冒充原生产 PCAP。
4. **上下文变化的网络可见代价。** 在自己的同次采集中控制输出规模、模型、route 和 streaming，检验 mutation/token 增长是否与请求上传字节或响应 timing 的条件变化相关。成功只证明该配置下统计关联，不能从密文直接断言发生哪种编辑、缓存淘汰或用户意图；因客户端/服务端缓存语义不同，须单独记录。

最优先选第1项。它直接解决后续研究的标签可信度，计算量小，也会暴露“多请求共享 flow”“一个请求多个 burst”“本地工具无网络”等关键问题。第2–4项应在第1项获得可靠样本后开展。

## 最小实验应怎样作出决策

第一轮固定一个合法可用且记录完整的模型 route、一个 Hermes 版本、单 NIC、隔离背景流量和少量独立短任务。至少包含无外部工具、本地工具、访问受控外部服务三种可核验机制；它们用于验证映射，不能直接当作普遍语义类别。先串行，再逐步加入连接复用/工具 batch/并发作为压力条件。每次失败也保留事件计数、capture 丢包统计、时钟锚点和配置，避免只分析成功运行。

推荐的**事先约定**是：对一组有独立可校验关联的测试请求，报告事件捕获 coverage、request–packet 关联 precision、歧义/弃权率、时钟/边界误差分位数与失败类别；在结果可得前不许把“时间窗覆盖了流量”叫做精确对齐。阈值应按目标任务的时间尺度预注册，由 MVP 明确给出；此处没有实测阈值或成功数。工具阶段并行重叠时，可以保留 multi-label interval 或 Unknown，不强塞一个单标签。

纯网络分类的特征可以来自 packet 长度、方向、IAT、burst 与 flow duration；工具名、model/provider/harness、应用 request ID、GT action 时间和 response outcome 只能用于标注/分层审计。若模型依赖其中任何一项，必须改称有应用辅助信息的模型。若任务是“在线预测”，截止时间之后的 packet、session 总长度、结束状态和 tool result 均不可作为输入。

还要单独披露样本边界的来源。若用真实 tool start/end 把 PCAP 切成片段，再只输入片段内网络特征，测到的是“已知边界条件下的分类”，并未解决纯网络侧如何发现行为开始/结束。后续应分别评估边界已知的分类、仅凭网络的分段，以及分段加分类的端到端误差，避免把应用真值带来的切片优势隐藏在高 F1 中。

最后，应先确认能获得我们自己的事件与 Gateway 对应信息，而非默认已有公开实时 trace 导出。已确认的 Hermes hooks 与 FreeInference 路由/接口限制以 [对齐审计](trace_pcap_alignment.md) 为准。没有付费推理、Gateway 身份或抓包权限时，可以完成本地事件管线与合成校验；这只证明管线可执行，不能替代真实加密网络实验。

## 尚未验证的事项

- ANT artifact 的当前文件、完整源码 SHA、数据可下载性、baseline 结果与标注误差未独立运行验证；论文中的 release 声明与我们实际读到了数据是两件事。
- MAGIC26 正式全文、DOI、实验规模、数值结果、公开 PCAP 范围与准确率尚 Unknown。当前资料足以确认研究方向与代码关联自述，不足以评价其论文全部任务覆盖。
- TraceLab 最新数据 v0.0.2 的内容与论文统计未复算；版本差异不构成已确认的算法问题。
- 没有执行真实 Hermes–MiMo–FreeInference 同期 PCAP 实验，也没有测出语义分类 F1 或真实对齐误差。公开的历史 trace 不能补上这项缺口。
