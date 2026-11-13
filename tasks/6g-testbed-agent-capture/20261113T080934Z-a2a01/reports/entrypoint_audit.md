# Agent/A2A 官方入口审计

审计对象为 5G-MAG/6G-Testbed 的论文指定提交 `d055fa68ef4de30b93a8a30838ae51fe3e4b561c`，不是 current main，也不把历史论文制品视作本次运行结果。根目录规则已读；`rg --files -g AGENTS.md` 未发现上游附加规则。本报告不包含上游完整源码、原始任务内容或网络标识。

## 已确认入口与安全 help

| 入口 | 源码角色 | 初次实际检查 | 限制 |
|---|---|---|---|
| `aitestbed/run_full_tests.sh` | README 指定的全矩阵复现入口 | `bash …/run_full_tests.sh --help` 退出 0 | 仅审查并执行 help；运行本体会执行训练等超出本次范围的后处理，不能作为单任务最小入口 |
| `aitestbed/orchestrator.py` | 官方单 scenario CLI | 原始环境退出 1 缺 colorlog；专用环境实际 `--help` 退出 0 | 成功日志 `logs/entrypoint/orchestrator_installed_help.log`；首次失败仍保留 |
| `python -m a2a_agents.echo_agent` | 官方确定性 A2A 服务端 | 缺包两次失败保留；补 server extra 后实际 help 退出 0 | 成功日志 `logs/entrypoint/echo_server_extra_help.log`；服务启动位于参数解析之后 |
| `python -m a2a_agents.orchestrator_agent` | 官方多代理服务端 | 缺包两次失败保留；补 server extra 后实际 help 退出 0 | 成功日志 `logs/entrypoint/orchestrator_agent_server_extra_help.log`；本次只查 help，不运行多代理场景 |
| `clients/a2a_client.py` | 官方带指标的协议客户端类 | 无独立 CLI | 不存在可据此假定的客户端命令；由官方 scenario 驱动 |

全部 help 从新建私有工作目录运行，设置 `PYTHONDONTWRITEBYTECODE=1`、只读源码 `PYTHONPATH`，命令、工作目录、退出码和耗时另存 `logs/entrypoint/*.json`。没有安装依赖、启动容器、抓包或修改 qdisc。

`orchestrator.py:23–25` 在解析参数前调用 `load_dotenv()` 三次；`74–101` 配置 logging，并在当前工作目录创建 `logs/`、以 `mode='w'` 覆盖 `logs/orchestrator.log`。`--help` 在 `1119` 的 `parse_args()` 退出，先于 `1121` 的 `TestbedOrchestrator()`，因此 help 本身不会实例化模拟器。`--list-scenarios` 则会先构造模拟器和 SQLite logger，不能当作同等无副作用探针。

`run_full_tests.sh:16–20` 在 help 之前可能 shell-source 当前目录 `.env`；`30` 调用 Python 读取 `configs.DEFAULT_CAPTURE_FILTER`。本次工作目录确认不存在 `.env`，其余预解析代码为配置/函数定义；help 在进入 `main` 前退出。

## 确定性单任务的源码契约

官方配置 `aitestbed/configs/scenarios.yaml:1028–1043` 定义：

- scenario 名称 `a2a_single_task_local`，类型 `a2a_single_task`，provider `a2a`，model `echo`，`streaming: false`。
- 目标和本地服务端口均为 `9001`；`loopback_ports: [9001]`；子进程模块为 `a2a_agents.echo_agent`，参数 `--behavior echo --stream-chunks 1`。
- 官方默认配置有两个 prompts；因此 `--runs 1` 默认产生两个独立 task，不能描述为“一次单任务”。严格单任务可用私有配置保留上述官方字段，将 prompts 换成唯一的一条本地合成标记，并将 defaults 的 retry_count 设为 0、inter_run_delay_sec 设为 0；必须记录这是受控配置差异，不能称作原始配置完全复现。

调用链为 `orchestrator.py` → `A2ASingleTaskScenario` → `A2AAgentFleet/A2AAgentProcess` → 官方 echo 子进程和 `A2AClientSession`。`orchestrator.py:372–376` 为 `provider=a2a` 使用 `NullLLMClient`，不会构造付费 LLM 客户端。echo 的变换为字符串前缀 `echo: ` 加原始输入；单 chunk 不插入人工 stream delay。

`a2a_agents/common.py:53–86` 构造 JSON-RPC AgentCard、内存 task store 和 Starlette 路由；card discovery 是 `GET /.well-known/agent-card.json`（launcher 常量），RPC endpoint 为 `POST /`。`streaming: false` 由 `ClientConfig` 选择 `message/send`，不是 SSE；任务完成应包含确定性 echo artifact。实际 PASS 仍须检查 wire method、完成状态及预期合成 echo，而不能只检查 HTTP 200 或官方 success 字段。

## 安装范围及入口缺陷

系统初始 Python 为 3.12.14。协议服务端和客户端的直接声明范围为 `a2a-sdk>=1.1.0,<2.0.0`、`httpx>=0.28.0`、`uvicorn>=0.27.0`、`starlette>=0.40.0`；lock 将 SDK 记为 1.1.2。root 已安装专用环境 `.conda/agent`，安装命令与退出码见 `logs/a2a_dependencies.json`，实际版本由其环境清单提供。

该环境的原版 orchestrator 实际 help 成功；echo/orchestrator agent 的首次 help 在 SDK 的 `a2a.compat.v0_3.jsonrpc_adapter` 导入处发现 `sse_starlette` 缺包。已直接读安装的 SDK 1.1.2 metadata：`sse-starlette` 由 `http-server` extra 声明，裸 `a2a-sdk` 不安装它。服务端最小依赖应包含 `a2a-sdk[http-server]==1.1.2`，而不仅是裸 SDK 加 starlette；`requirements.lock` 本身列有 sse-starlette。root 后续安装 server extra 成功（`logs/a2a_server_extra.json`），两服务端实际 help 均退出 0；失败及修复证据分别保留。

原版 CLI 的导入范围大于 A2A 的运行范围。`clients/__init__.py:38` 无条件导入 `realtime_webrtc_vlm_client.py`，该文件 `15–20` 强制导入 `aiortc`、定制的 `aiortc.codecs.tokenId.TokenIdEncoder` 和 `av`；所以仅安装通用 PyPI aiortc 不能被假定足够。可使用同一提交下真实的 `aiortc-main-clean/src` 和 `netemu/src` 加入 `PYTHONPATH`，无需改源码、无需构造 VLM 对象。

此导入链不要求加载 GPU 模型：`tokenId.py:14` 导入 numpy；`aiortc/shared.py:15–20` 仅在调用 `get_liquid_bridge()` 时导入 liquid tokenizer；VLM client 的 `TokenIdEncoder.preload_bridge()` 位于构造函数内，而 A2A 不构造该类。CLI help 的额外直接依赖为 colorlog、PyYAML、python-dotenv、openai、requests、提供 `websockets.asyncio.client` 的 websockets、httpx、numpy；google-genai、anthropic、azure-ai-inference 在各自构造函数中懒导入。dpkt 和绘图库有缺包降级保护。无需安装 torch、torchvision、transformers、Playwright 或启动其它场景。

定制 aiortc 的 `pyproject.toml:27–35` 声明 `aioice>=0.10.2,<1`、`av>=14,<17`、`cryptography>=44`、`google-crc32c>=1.1`、`pyee>=13`、`pylibsrtp>=0.10`、`pyopenssl>=25`。这些真实导入依赖通常可用 CPU wheel 提供；具体大小与耗时未测，不作数值承诺。

静态发现的安装材料矛盾：

- `requirements.lock:13,43,361` 的 aiortc 1.10.1、av 13.1.0、pyopenssl 24.3.0 不匹配仓内定制 aiortc 1.14.0 的范围；lock 也没有 txt 已声明的 colorlog。
- `aitestbed/Dockerfile:99–113` 仅装 netemu 和两个 lock，仅复制 aitestbed/training，没有复制或安装定制 aiortc。
- Dockerfile 第 105 行要求 `training/requirements.lock`，本提交没有该文件；这是未构建即能确认的路径缺失。本次未执行 Docker build/run。
- Docker 的默认 `--help` 是 `docker/entrypoint.sh:125–168` 的静态 shell 输出，并不验证 Python CLI 导入成功。

## 最小启动与观测方案

依赖齐全且 root 已确认独立 user/network namespace 后，候选官方单 scenario 参数为：

```text
python <upstream>/aitestbed/orchestrator.py
  --scenario a2a_single_task_local --profile no_emulation --runs 1
  --config <private-single-synthetic.yaml> --interface lo
  --db <private-run>/traffic_logs.db --report <private-run>/report.json
  --run-timeout 30 --stop-on-error
```

这些参数均来自 `orchestrator.py:965–1119`，且已由专用环境实际 help 确认；场景功能仍须实际执行日志确认。工作目录应为独立私有 run 目录；`PYTHONDONTWRITEBYTECODE=1` 同时保护 launcher 在上游目录运行的子进程不写 `__pycache__`。本次不建议执行全矩阵 shell，也不建议绕过隔离启动原版 CLI。

`no_emulation` 配置为 delay/jitter/loss 全零、无速率限制，但原版 `orchestrator.py:282–291` 仍调用 `emulator.clear()`；实验结束 `615` 再次 clear。`netemu/emulator.py:773–800` 会尝试 `sudo tc qdisc del`，所以该路径不能在共享/host interface 上作为“纯读基线”运行。官方 local scenario 对 `no_emulation` 不调用 loopback shaping；环境层是否完全无 qdisc 应由 root 在隔离路径检查。

抓包仅在 root 确认隔离路径后执行。若 primary interface 选择 `lo`，必须显式使用 `--capture-filter 'tcp port 9001'`：默认 filter 只含 HTTP(S)/8000/8080/WebRTC 端口，漏掉 A2A 9001；且 `orchestrator.py:1194–1198` 在 primary 已为 lo 时不另开 secondary lo。若 primary 是其它隔离接口，则 secondary 可用 `--capture-loopback-filter 'tcp port 9001'`。原始 PCAP 和标记留私有目录，公开报告只用合成别名和聚合量。

官方日志的可用证据为 SQLite `traffic_logs` 每 turn 一行：scenario/session/run/turn、network_profile、t_request_start、t_first_token/t_last_token、latency、success、bytes 和 metadata。A2A metadata 含 protocol、a2a_task、agent_url、streaming、event_count、output_chars；server stdout/stderr 在 launcher 的 `Popen` 中均送至 DEVNULL，官方 launcher 不提供服务端逐任务事件日志。

A2A `_turn_record()` 不传递 request/response/events payload；`TraceLogger.write_trace()` 在三者全空时直接返回。因此仅设置 `TRACE_PAYLOADS=1` 也不能为此 A2A 路径补出 payload trace。单 scenario CLI 的后处理只计算指标并写 JSON report，不会进入全矩阵脚本的训练步骤。

客户端每次 scenario run 新建一个 `httpx.AsyncClient` 与 SDK client，所有 prompts 共用此 session，结束时关闭；每次 run 也重启本地 fleet。readiness 的 `httpx.get` 使用独立短会话。SDK card discovery 使用 session 的 httpx 客户端，但发生在 `send()` 的 `_cur` 和请求时钟建立之前。故 PCAP 会含 readiness、card、任务和关闭流量；app bytes/latency 不能直接与整份 PCAP 字节/时长相等。源码没有连接复用开关；是否复用同一 TCP connection 必须实读 PCAP 确认，不能只据 `AsyncClient` 推断。

## 解释限制

- `A2AClientSession.send()` 初值 success=True，只有异常改为 False；未验证返回内容、非零事件数或 task completed。必须额外验证合成 echo 和 A2A task 状态。
- `scenarios/a2a_agent.py` 将 HTTP status 写成 `200 if turn.success else 0`，它是派生值，不是原始响应状态。
- `t_request_start/t_first_chunk/t_last_chunk` 采用 `time.time()`；SQLite `timestamp` 是写记录时的事后时钟。首事件即计作 first chunk，即使该事件没有文本，因此 TTFT 是首 A2A 事件口径。
- app session UUID 没有显式写入 A2A wire request；官方 capture run_id 也不直接写入每个任务记录。严格对齐需私有 run 映射、接口与 TCP 连接、唯一合成标记和请求时窗共同验证。连接和身份字段只用于 ground-truth linkage。
- `A2AAgentProcess.wait_ready()` 只验证 HTTP 200，且子进程错误日志被丢弃；不应把 readiness 当作预期服务器身份与功能验证。独立 namespace 能减少端口误匹配风险，最终仍应读 AgentCard 与任务回复。

官方 scenario 功能、日志↔PCAP 对齐与 RTT 对照由 root 的实际结果分别判定。任何 focused direct-module harness 仅算官方 component/demo，不能替代 stock CLI PASS；未执行的项保持 BLOCKED/NOT_RUN。

root 已选定实际实验路径为 stock orchestrator、一个合成 prompt、`no_emulation`、隔离 `lo`，由外置 AF_PACKET collector 采集；不启用内建 CaptureController。因此实际抓包结论应标明“外置 collector”，不能称为官方内建抓包链已验证。root 的隔离能力检查发现 netem qdisc kind 不可用，禁止加载 host 模块或绕过限制；本次不运行整形组 B，RTT 对照保持 BLOCKED。
