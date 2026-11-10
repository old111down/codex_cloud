# 对齐与 MVP 报告交叉复核

复核时间：2026-11-10 08:31–08:34 UTC。复核对象为 `trace_pcap_alignment.md`、`mvp_experiment_plan.md`、`architecture.md`、`session_reconstruction.md`，以及相应固定源码、已有脚本和日志。**关键语义一致性通过复核；真实 Hermes/模型/PCAP 对齐仍未执行。** 发现的两处证据引用错误已由原作者修正，未发现尚未修复的关键 ID、时间、标签或权限误述。

独立性范围：本复核对 alignment/MVP 主稿进行了独立源码与日志复查；architecture/session 主稿与本复核由同一审计分工作者撰写，对它们只能称一致性复核，不构成外部盲审。本次不新增网络请求、模型调用、安装、抓包或实验，也不修改他人主稿。

## 核对结果

| 核对项 | 复核证据 | 结论 |
|---|---|---|
| 历史发布与当前 Gateway | 四份主稿均固定 trace SHA `2b795dbf…` 与 Gateway SHA `7f7585bc…`，明确网站显示源码版本不证明历史部署相同 | Verified：没有把当前实现回填为历史观测 |
| 历史 start/end | trace `fields.py:174–192`、`requests_table.py:137–158`：end来自raw timestamp，start由end减logged latency推导 | Verified：公式与物理打点语义分开；历史 tap 保持 Unknown |
| 当前 DB 时间 | `grant_auth.py:302–323`、baseline `api_logs.py:350–356`、`postgres_log.py:96–122`、异步logger：timestamp为响应完成后调度的DB insert time | Verified（当前源码）：未声称它是客户端发送/末包；历史误差数值未推断 |
| TTFT 与工具时间 | 当前 `_TTFTTracker` 首meaningful delta且fallback可重置；公开工具延迟为相邻推导start/end gap、同batch共享 | Verified：均未当成独立客户端首包或每工具秒表；RTT修正缺口另有说明 |
| 三种 Gateway ID | middleware回显header；handler另生成内部ID；stream另生成completion ID，DBmetadata保留response_id桥 | Verified：公共GET回显不被当作DB精确join证明 |
| 普通用户/管理员/internal权限 | JWT `get_current_user`、user-filtered recent-requests；admin导出依赖admin；grant router受dispatch-token保护 | Verified：没有将API key、JWT、admin或dispatch权限互换；未认证GET401只证门槛 |
| Hermes 跨retry身份 | `conversation_loop.py:1767–1771`先分配ID/start，再调用`1577–1606` retry loop；loop内重新build/send | Verified：MVP正确保留“一个source ID可跨多个attempt”的风险，没有只按ID计wire requests |
| Hermes回调内容与队列 | `turn_api_request.py:76–104`含raw兼容内容；`plugin_stream_hooks.py:1–6,42–57`队满丢最旧 | Verified：主稿要求白名单metadata、source/receipt分列与丢失审计；未把sanitized等同无正文 |
| 标签来源 | 历史session/trigger/category/outcome为不同规则或算法标签；intent标注模型/材料缺失；95%仅历史特定subset的一对一声明 | Verified：没有把tool category当八类intent，也没有给PCAP标签附会95%准确率 |
| 未运行的MVP | 两份对齐稿开头、步骤、配置/抓包示例与末尾均说明真实Agent/模型/PCAP为0，授权MiMo路由Unknown | Verified：未把方案或占位代码描述为完成部署 |
| 11个合成检查 | 已有JSON/log记录08:24:25Z、exit0、11通过；逐读脚本，10次check加invalid interval case构成11项 | Verified（已有日志）：仅自建匹配器条件检查，不是网络/时钟/Hermes/模型实测 |
| 匿名catalog | 已有日志只记录无auth `/v1/models`200，3项无exact MiMo；主稿不外推所有账户或未来不支持 | Verified（已有日志）：可发现性与真实推理能力保持分离 |

## 已修正的发现

1. **IR-AL-001，低严重度，已解决。** 对齐报告的 F2 源码链接原为不存在的 `export/release/schema.py`；原作者已改为 `release/schema.py`。复查当前文件与上游路径一致。影响是证据可点击性，不改变schema结论。
2. **IR-AL-002，低严重度，已解决。** 对齐稿把论文 §9 引为 PDF p12；逐页文本确认位于 p13，原作者已修正表格和来源。影响是页码准确性，不改变 provider-side 局限结论。

上述问题已通知 root 与原作者后复查。主稿可能继续更新；本次所核版本的文件 SHA256 保存在同名 JSON 中。

## 不应被本复核认证的内容

- Hermes recorder尚未实现或运行；本地 `attempt_seq` 建议还需在真实retry、SDK透明重试、辅助调用和orphan事件下验证。
- Gateway内部存在response ID桥，不等于普通账户当前能取到该桥；合法授权后的端到端join、分页完整性、写入延迟仍Unknown。
- 合成匹配器假定transport ID、connection epoch与uncertainty已独立获取并可信；测试没有证明这些输入可由加密PCAP恢复。其时间唯一候选不输出hard label，与报告的保守设计一致。
- 当前source中的DB插入、回调队列和时间模型只是可审计机制，不证明历史数据负gap的成因，也不测定其误差上界。
- 一个Hermes/一个模型及少量任务的计划不能证明harness或intent分类泛化；目前也没有分类Accuracy/F1结果。

## 复核依据

主要固定源码链接已在四份主稿中给出；以下是本复核特别重新读取的关键路径：

- [Hermes ID/start分配](https://github.com/NousResearch/hermes-agent/blob/b7db40d82568ea68ce321ac1ead3bfea354c7f56/agent/conversation_loop.py#L1767-L1771)；[retry loop](https://github.com/NousResearch/hermes-agent/blob/b7db40d82568ea68ce321ac1ead3bfea354c7f56/agent/conversation_loop.py#L1577-L1606)。
- [Hermes pre字段与raw兼容内容](https://github.com/NousResearch/hermes-agent/blob/b7db40d82568ea68ce321ac1ead3bfea354c7f56/agent/turn_api_request.py#L60-L107)；[post字段](https://github.com/NousResearch/hermes-agent/blob/b7db40d82568ea68ce321ac1ead3bfea354c7f56/agent/turn_response_intake.py#L66-L108)；[队列丢弃机制](https://github.com/NousResearch/hermes-agent/blob/b7db40d82568ea68ce321ac1ead3bfea354c7f56/agent/plugin_stream_hooks.py#L1-L57)。
- [Gateway JWT依赖](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/deps.py#L349-L410)；[用户请求接口](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/user_routes.py#L1279-L1388)。
- [Gateway DB时间语义](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/grant_auth.py#L302-L323)；[内部grant保护](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/agent_grants.py#L49-L60)；[桥接字段](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/agent_grants.py#L313-L377)。
- 本地已有证据：`scripts/alignment/match_intervals.py`、`scripts/alignment/synthetic_checks.py`、`scripts/alignment/check_public_gateway_metadata.py`、`logs/alignment_synthetic_checks.json`、`logs/alignment_synthetic_checks.log`、`logs/alignment_public_http_checks.json`。本复核只读这些文件，没有重跑网络检查。
