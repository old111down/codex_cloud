# FreeInference Agent Traces 研究决策报告

审计总体状态为 **Partially Verified**：全文、源码、字段和公开统计已经核验；原始生产采集、95% 重建准确率、意图标注、完整缓存重算和真实网络分类尚未验证。Task ID `20261110T080855Z-freeinf-audit`；实际起止和运行记录以 `metadata.json` / `execution_timeline.md` 为准。

## A. 是否适合作为 Agent 网络流量研究的数据来源？

**适合作为服务侧工作负载参考、应用事件定义和实验采样依据；不具备独立的网络侧训练样本。** 论文从 Request 转向 Session，揭示上下文重放、用户停顿、工具等待和会话内 cache 复用；这些是选择采样时段、事件粒度、长连接与缓存混杂控制的依据。它不是网络 packet 测量论文。

我们对 16 周公开 Parquet 的独立聚合得到 Table 1 的 12,002 个顶层 Session、1,186,582 个请求、1,213,347 个工具调用及匹配印刷精度的 Token 总量。还有 2,034 个子代理 Session，单独统计。公开标签包含规则归一化 Harness、工具类别、算法推断触发和父子关系，不能把它们当作客户端直接测得的 ground truth。人类数据还经过至少2个 user-triggered steps及1个tool-triggered step筛选，先验只适用于该集合。

## B. 能否直接为 PCAP 提供可靠行为标签？

**不能。** 没有配对 PCAP、socket/stream、客户端 request 身份或本次实验的共同事件。历史匿名用户/Session ID 不足以连接另一次采集。请求时刻由服务端完成时间减 latency 得到，不是独立客户端 wire 时间。当前 Gateway 的日志 timestamp 是异步 DB insert time；该当前源码与历史部署的版本对应关系 Unknown。

八类用户意图也不在公开表中，原始正文、完整标注 prompt、模型和核验材料缺失。Tool Category 不能替代 Create/Debug 等任务意图。即使未来配对成功，工具触发/上下文变异仍可能是推断标签；应单列其误差与标签可得时间。

## C. 最少增加什么采集？

在**同一次自己的任务运行**中同时收集：客户端 metadata-only 事件（session/turn/每次真实 HTTP attempt）、wall+monotonic 双时钟、连接epoch/五元组与可用stream身份，以及单网卡PCAP和capture丢包统计。记录重试、辅助模型、并发、子代理，避免把一个逻辑请求误作一次wireattempt。内容、凭据、原始PCAP私有保存。

优先以 Hermes hook + transport 事件建立账本；hook 的 request ID 在所审版本可跨 retry 复用，必须补充 attempt_seq 和实际发送时间。Gateway 用户元数据可作合法授权后的额外核对，不是必需的唯一方案；header echo 不证明 internal DB ID 可 join。普通用户列表未暴露完整 response-ID 桥，禁止依赖 admin/internal grants 权限补齐。多路复用时仅有PCAP无法凭空恢复TLS内stream归属；歧义事件应拒配或仅保留连接级标签。

## D. 当前最值得执行的实验

先做 **单 Hermes、精确单模型、单网卡、少量短任务的标签—网络对齐验证**，以请求覆盖率、歧义率、边界误差、连接覆盖、重试事件闭合和采集开销为结果。先串行，再有控制地加入连接复用、重试和并发；保留失败和拒配。

`mimo-v2.6-flash` 在本次匿名 `GET /v1/models` 的3项中未出现；认证账户的精确路由和实际调用能力仍 Unknown。没有静默替换成其它模型或发起模型调用。下一轮须先满足合法账户/路由/额度门槛。详细可执行步骤、拓扑、数据流、标签流程和停止条件见 `mvp_experiment_plan.md`。当前只运行了11项合成区间检查，不是该MVP真实结果。

## E. 成功或失败能证明什么？

成功只能证明在指定版本、模型、协议和受控负载下，可以把自有应用事件转为有误差界限的配对网络标签，为后续数据集奠基。单一Harness/模型实验不能证明Harness分类、多类意图可识别、跨Provider泛化或端到端网络分段性能。

失败可定位具体假设：hook漏报、透明retry、时钟漂移、连接错配或H2/H3并发不可区分；能排除当前采集/匹配方案足够可靠的假设，不能排除一切Agent网络分类可能性。后续分类只能输入包长、方向、IAT等真正网络可观测字段，使用group/session/task/time holdout并控制模型/Provider/任务混杂。用真实标签切好的窗口训练得到的是“已知边界分类”，应与网络端到端分段分别报告。

## 复现证据与主要问题

- **Verified运行：** 独立Conda和原版源码执行、48个文件校验、全16周统计/绘图入口、真实3Session缓存模拟。主要统计与Table1/多项图表值一致。
- **Partially Verified：** 作者缓存仿真中间表可重画/汇总；完整独立仿真未完成。73项选定声明比较69项，其中67项符合印刷精度，含上述仿真材料，不表示67项独立实验成功。
- **确认差异：** Table6 batchmix 71.3/28.7与当前原版64.0174/35.9826不一致；84.5%的宽度按call加权，不等于按request单工具占比93.2316%。ProviderD部分cache文字与当前曲线也需澄清。原因Unknown。
- **Failed且保留：** 原始Make缺`.venv`；pytest0项；无SWE单周输出8NaN；完整单周cache在120秒审计时限超时。均未隐去或描述为算法复现成功。
- **Unknown：** 95%重建验证、Fig7完整Subagent profile、Fig16意图流程、历史部署打点、RTT预处理、真实Gateway/PCAP关联与所有网络分类精度。

源代码/数据固定SHA、具体命令和所有边界见 `reproduction_report.md`、`paper_execution_report.md`、`paper_code_coverage.csv` 与 `paper_metric_comparison.csv`。数据/标签字段与相关工作分别见 `data_dictionary.csv`、`label_mechanisms.csv`、`related_work_comparison.csv`。

ANT 提供更直接的PCAP及行为对齐目标，但本轮未运行其artifact；MAGIC26是可审查的网络采集/分类实现，局部README与代码语义仍需核对；TraceLab是客户端应用Trace，补充FreeInference的服务侧视角，不能自动充当PCAP。论文与实时站点不同版本的统计分别记录。

完整第三方源码、数据、论文PDF/全文、原始HTTP页面、真实标识及运行子集均不上传。公共档案仅含原创分析、聚合证据、环境锁定、自建审计脚本、少量日志和必要补丁。归档分支独立、PR面向main、不合并；远程验证以单独收据和最终回复的SHA为准。
