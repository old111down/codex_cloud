# Agent 测量相关工作：来源、观测层与可比较边界

检索与阅读时间：2026-11-10 UTC。本文仅记录来源审计，不表示运行了相关项目。公开报告不附原论文、第三方源码、PCAP 或应用原始日志。

## ANT 是否确为 Agent 网络测量工作？

### Takeaway

是。论文直接描述同步采集的客户端 PCAP 与执行日志，目标包括场景、风险和行为 primitive 分类。它与 FreeInference 的推理服务工作负载 trace 具有不同的观测层。

### Cited findings

- arXiv:2610.06514v1，2026-10-05，题名为 *ANT: A Multi-Granularity Network Traffic Dataset and Benchmark for Agents Behavior Auditing*。§3、PDF pp.3–4：3,114 episodes、20 tasks、5 scenarios、276,417 双向 flows、40,049 primitive segments，合为47 macro groups。每个实例运行于独立 network namespace；tcpdump 与 session 日志同时采集。以上数字是论文报告值，本次未复算。[论文 v1](https://arxiv.org/pdf/2610.06514v1)
- §3.2、PDF pp.4–5：按 session 日志中 primitive 的开始时间给 packet 分段；跨越边界的同一 transport flow 按 packet 分配。DeepSeek-v4-pro 从对齐日志产生 primitive，再以 embedding 聚类为47组。因此这些标签包含 LLM 辅助语义归纳，不是直接从密文中观测或逐条人工真值。[论文 v1](https://arxiv.org/pdf/2610.06514v1)
- §5、PDF p.9：作者承认 AI 标注/聚类可引入不透明或错误决策；受控本地环境的 timing 可能有别于部署环境。文中人工抽查2,000例的描述不能替代逐类一致性或端到端对齐误差评估。[论文 v1](https://arxiv.org/pdf/2610.06514v1)
- Ethics/Reproducibility statement、PDF p.10：论文直接指向匿名 artifact，并声明 code GPLv3、作者数据贡献 CC BY4.0；包含 packet traces、sanitized logs、metadata、annotations。已核实“论文指向该 artifact”；此次只读取匿名站 landing shell，未枚举文件、验证数据下载或固定源码 SHA。[论文 v1](https://arxiv.org/pdf/2610.06514v1)、[论文所链 artifact](https://anonymous.4open.science/r/ant-main-suite-7BC0/)

### Inferences

ANT 可借鉴“同期 PCAP + 应用事件 + namespace 隔离”，但不能把其语义标签直接迁移给 FreeInference 历史记录。其按时间分段也不意味着一个 primitive 与一条 flow 一一对应。

### Gaps

artifact 当前可下载内容、源码 SHA、精确时钟误差、逐条语义标注可靠性、训练测试跨任务/部署泛化尚未独立验证。未运行其13个基线。

## MAGIC26 是什么，是否有同名混淆？

### Takeaway

本任务可辨认的 MAGIC26 是 Simula 的 `simula/magic26` 项目，研究单/多 Agent × LLM backend 的加密网络特征，不是泛称 MAGIC 数据集。关联目前由仓库自述与 workshop 官方节目交叉支持，正式论文 PDF/DOI 未找到。

### Cited findings

- 固定 SHA `bf6797f7da735a6fccb8f140f27106c78a87490f`，README 将项目关联至 *Network-Level Characteristics of LLM-based AI Agents: A Traffic Analysis Study*，自述 MAGIC/CNSM2026 workshop；官方 workshop 节目标题写为 *Network Traffic Characteristics of LLM-based AI Agents*。标题有差异，不能据此擅自补 DOI 或认定两份完整论文已核对。[固定 README](https://github.com/simula/magic26/blob/bf6797f7da735a6fccb8f140f27106c78a87490f/README.md#L1-L12)、[MAGIC 官方节目](https://sites.google.com/view/magic-cnsm/home)
- 固定 README：单 Agent ReAct 与 Planner/Executor/Synthesizer 多 Agent，backend 为 OpenAI/Gemini/DeepSeek，weather、research-assistant、no-tools 工作负载；六类为 execution type × backend。它们不是 Create/Debug 等用户意图标签。[固定 README](https://github.com/simula/magic26/blob/bf6797f7da735a6fccb8f140f27106c78a87490f/README.md#L134-L251)
- `react_agent.py` L492–540：`AsyncSniffer(store=True)` 在构建 Agent 前开启，执行后写 PCAP；代码打印 start/end、模型/backend 与 tool 次数。仅凭这段实现不能认定每次 LLM 请求/工具均已与 PCAP 精确同步。[固定源码](https://github.com/simula/magic26/blob/bf6797f7da735a6fccb8f140f27106c78a87490f/agents/react_agent.py#L492-L540)
- README L58 宣称生成 events.jsonl/summary.jsonl；已读的 `react_agent.py` 没有相应写入入口，且 L511–512 的 `run_dir/logger` 是 None。这里只能确认该文件与 README 不一致，未证明其他代码路径均无日志功能。[固定 README](https://github.com/simula/magic26/blob/bf6797f7da735a6fccb8f140f27106c78a87490f/README.md#L58)、[固定源码](https://github.com/simula/magic26/blob/bf6797f7da735a6fccb8f140f27106c78a87490f/agents/react_agent.py#L510-L525)
- README 将 train/test 称为 Random Forest，但 `ml/models/RF.py` 的 RF 继承 `nn.Module`，含卷积、batch normalization 与 pooling，ML README 明确来源为 Robust Fingerprinting。不能仅因缩写 RF 就认定其为随机森林；notebook 中可能另有 RandomForest，尚未审计。[模型源码](https://github.com/simula/magic26/blob/bf6797f7da735a6fccb8f140f27106c78a87490f/ml/models/RF.py#L6-L85)、[ML README](https://github.com/simula/magic26/blob/bf6797f7da735a6fccb8f140f27106c78a87490f/ml/README.md)

### Inferences

该项目可作为受控客户端采集设计参考，主要回答路径/backend/单多 Agent 的可分性；高准确率不自动说明语义行为可识别。endpoint、任务模板、模型/provider 的混杂需单独控制。

### Gaps

正式 PDF/DOI、数值结果、完整 PCAP 公开范围、逐事件日志覆盖、实验规模、划分方法与跨路由泛化 Unknown。看到了预生成 npz 的 Git tree，但未下载或运行，不把文件存在等同于论文结果复现。

## TraceLab 与 FreeInference 的 trace 有何差别？

### Takeaway

两者都主要服务 Agent/LLM serving 工作负载研究；TraceLab 从客户端本地 Claude/Codex 日志抽取，FreeInference 从服务端收集后重建 session。客户端应用日志也不等于客户端 PCAP。

### Cited findings

- *TraceLab: Characterizing Coding Agent Workloads for LLM Serving*，arXiv:2606.30560v2（2026-06-30）。§3、PDF pp.3–4：本地 Agent 记录交互与 tool events，抽取 token/timing 等信息；公开版移除用户消息和 tool input/output 正文，保留字符数与匿名 ID。PDF Table1：4,265 sessions、43 users、357,161 LLM steps、432,510 tools。本次未复算。[论文 v2](https://arxiv.org/pdf/2606.30560v2)
- 固定源码 SHA `5c6550b0d08beff983e9159fe2575e7a2334c8c1` 的 README L209–259：collect → sanitize → analyze → validate；脚本读取已有本地 Claude/Codex history，再导出 normalized JSONL/DuckDB。输出不是 packet capture。[固定 README](https://github.com/uw-syfi/TraceLab/blob/5c6550b0d08beff983e9159fe2575e7a2334c8c1/README.md#L209-L259)
- README L372–438：每个 LLM round 有 ordered `timing_events` 与 nested tools；`tool_wall_latency_ms` 是结果事件与调用发出事件的差，区别于 runner 内部耗时，不应直接当作网络 RTT 或纯 tool service time。[固定 README](https://github.com/uw-syfi/TraceLab/blob/5c6550b0d08beff983e9159fe2575e7a2334c8c1/README.md#L372-L438)
- 官网当前宣布数据 v0.0.2，显示52 contributors、8,058 sessions、665,453 steps、743,819 tools；固定 README 则给数据 v0.0.1 与上面旧计数。数据 release 版本与论文 arXiv v2 是不同维度，不能把官网新计数写成旧论文 Table1 值。[官网](https://tracelab.cs.washington.edu)、[固定 README](https://github.com/uw-syfi/TraceLab/blob/5c6550b0d08beff983e9159fe2575e7a2334c8c1/README.md#L119-L125)

### Inferences

TraceLab 更适合比较应用事件保真度、客户端 tool wall time 与 Gateway 推断时间的差异。没有同时捕获的网络观测与连接关联信息，仍不能从公共日志恢复加密的真实 packet 序列。

### Gaps

此次未运行 collector、validator、replay 或读取其发布数据；最新 v0.0.2 与论文统计差异不能解释为复现错误。支持哪些具体 transport/stream mapping Unknown。

## FreeInference 能直接为独立 PCAP 提供标签吗？

### Takeaway

不能。公开历史应用 trace 与后来独立采集的 PCAP 不是同一次执行，也没有已证实的逐请求共同连接标识。可用作设计工作负载与标签本体的来源，不能直接当现成的 network supervised dataset。

### Cited findings

- FreeInference 论文 §3、PDF p.3：服务端汇集 metadata，harness 由 user-agent/system prompt 推断，多数客户端不提供 session ID，使用内容/tool ID 等关联重建；95% 一对一验证仅针对有显式 session ID 的子集。§9、PDF p.13：没有精确客户端 tool 执行测量，session 重建可能不同于客户端定义。[官方论文](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf)
- 固定代码 `2b795dbf5eac490a7c081906fdce6cc7a184b7ef`，README 明确公开版没有消息/提示/工具结果正文或原始标识；release schema 给 application metadata，provider 为匿名字母。仅有 start/end 时间并不提供 flow/HTTP stream 对应关系。[固定 README](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/README.md#L26-L33)、[固定 schema](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/release/schema.py#L64-L120)
- 论文 §7、PDF p.12/Fig16：八类 intent 使用 LLM 对随机抽样1.8K sessions 的约10K turns、few-shot 标注；公开版无 prompt 正文时不能独立重做相同的语义判断。未给模型、完整标注模板、人工一致性统计。公开 schema 无 intent 列、当前 paper registry 到 Fig15，不能将 Fig16 当作已可公开重做的实验。[官方论文](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf)、[固定 schema](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/release/schema.py#L67-L120)、[固定 paper registry](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/__init__.py#L118-L139)

### Inferences

网络模型的 input 必须是网络侧实际可见量；harness/tool/model/provider 可用于监督或分层审计，但不能偷偷作为“纯网络模型”输入。harness 识别与用户 task 意图是不同任务；provider/路径可分性也不等于 Agent 行为可分性。

### Gaps

我们自己实验的 Gateway trace 导出接口、Hermes hook/transport 可观测性、mimo-v2.6-flash 当前可用 route，由 alignment 审计继续确认。此处不声称这些条件已经满足。

## 检索降级与证据保存

### Takeaway

Tavily 一次查询返回429属于搜索 provider 限频，不能据此宣称论文或仓库网站不可访问。

### Cited findings

- 搜索先用 advanced、每次最多10结果；MAGIC26 一次429后停止该 provider 的重复请求，转用独立 web search 发现官方仓库/会议页，再合法 HTTP 读取主源。以上目标主源链接见前节；固定文件下载来源/UTC时间/字节数/SHA256保存在本地 private evidence manifests，原全文不公开。

### Inferences

本节的检索过程不足以证明不存在未发现的 MAGIC26 正式 PDF。

### Gaps

MAGIC26 的正式全文仍为 Unknown；没有借无关同名论文补齐。
