# 用户请求范围验收与待集成项

验收对象：用户上传的《任务：FreeInference Agent Traces 深度调研与网络流量研究可行性验证》全文；于2026-11-10T08:32:05Z重新读取。本文是任务进行中的独立范围检查，反映本地材料与已知待根代理集成内容，**不是最终上传或全部实验成功证明**。任务起点仍为2026-11-10T08:06:28Z，上限2026-11-10T11:06:28Z，没有因归档或本次验收重启预算。未新增大实验或文献搜索。

## 范围结论

论文、源码、真实Parquet、字段/标签和网络可行性已经有实质交付；原任务要求的“至少一项真实代码或数据验证”有实际日志支撑。网络侧部分按用户意图完成了**可执行方案与门槛审计**，没有将合成匹配检查冒充真实Hermes/模型/PCAP实验。暂未发现需要另开大规模研究才能补齐的内容遗漏。最终运行报告、时间线、总索引与持久化交付仍须由根代理完成。

以下“已覆盖”表示相应报告/证据存在并已检查其范围，不表示论文所有数值已独立复现。

| 用户要求 | 现有证据与文件 | 验收判断与限定 |
|---|---|---|
| 完整阅读、研究定位与全部九类实验 | `paper_analysis.md`；18页PDF、23个编号图表清单、修订73条选定数值声明 | 已覆盖。明确serving workload与packet classification的区别；真实观测、估计、LLM标签、模拟分层 |
| Session/Turn/Step/Request/Tool/Subagent关系图 | `architecture.md`、`paper_analysis.md` | 已覆盖包含与触发关系；明确不等于flow/burst/连接 |
| 采集位置、Provider/Gateway/Tool与匿名发布 | `architecture.md`、`session_reconstruction.md` | 已覆盖；当前Gateway源码与历史采集部署关系Unknown，不偷换为历史埋点实证 |
| Session重建源码而非仅复述 | `session_reconstruction.md` | 已覆盖tool-ID、8-word shingle/90%覆盖、账户/128请求窗口、周界、主链、subagent启发式；95%真值材料缺失清楚标明 |
| 真实Parquet与完整字段字典 | `data_dictionary.csv`、`data_validation_report.md`、`reports/observed_schemas.json` | 已覆盖68行字典含38个顶层列、role子字段、JSONL派生别名/缺失字段；用户列出的同名字段错误已纠正 |
| Harness/tool/intent标注机制 | `label_mechanisms.csv`28行；`session_reconstruction.md` | 已覆盖直接记录、规则、算法推断、LLM和人工Unknown；没有把tool category当作task语义 |
| 每图表/声明代码与数据覆盖 | `paper_code_coverage.csv`56行、`paper_metric_comparison.csv`73行、独立论文审查 | 已覆盖静态路径、入口、执行层与缺失。Fig16、95%验证及私有输入/测试不被称为完整公开复现 |
| 独立Conda、版本与资源 | `environment/freeinference/`、`environment/host_summary.json`、安装日志 | 已覆盖environment.yml、explicit conda、conda-list、pip-freeze、运行版本；CPU/RAM/disk/GPU/网络/权限有记录 |
| 至少一个完整周、最小真实统计 | 单周与全期profile日志、manifest、聚合与质量报告 | 已超过最低数据范围：48个Parquet/16周/8,371,191,139bytes实际读取与校验；没有解压108GB JSONL。`block_ids`完整值未在常规profile读取须继续披露 |
| README原命令、原版/修复、模拟和指标比较 | `paper_code_coverage.csv`、运行日志、patch、`paper_metric_comparison.csv` | 证据已有；根代理待整合`reproduction_report.md`，应逐项区分官方算法、全期统计、预计算重画、小数据模拟及修复后运行 |
| A–D四组网络监督目标 | `research_opportunities.md`标签表、`label_mechanisms.csv`、数据混杂审计 | 已覆盖harness、trigger/tool/subagent/outcome/mutation、model/provider/规模密度及intent；公开性、粒度、PCAP不可直接观测和泄漏风险均明确 |
| 对齐10项问题 | `trace_pcap_alignment.md` | 已覆盖双时钟、offset/drift/RTT非对称、推导起止、TLS、H2/H3、复用、burst、重传、并发、ID和拒绝匹配规则 |
| Hermes/MiMo/单网卡/少量任务MVP | `mvp_experiment_plan.md`；公共HTTP检查、11个合成检查 | 已覆盖拓扑/数据流/标签流程/具体步骤。MiMo授权route、capture能力、Gateway精确join Unknown；真实Agent/PCAP/模型调用均0，不当成功 |
| ANT、MAGIC26、TraceLab比较 | `related_work_comparison.csv`、来源笔记、`research_opportunities.md` | 已覆盖准确项目识别、观测点、PCAP、标签与差异；MAGIC26正式PDF/DOI Unknown，不套用同名论文 |
| 最终A–E研究决策 | `research_opportunities.md`前段及本报告末段 | 已覆盖明确回答及证据边界，不强行把历史trace说成PCAP训练集 |
| 时间线、总README、最终归档与PR | `run_info.json`、公开仓库规范/分支已建立 | 根代理待最终集成和验证，详见下一节 |

## 根代理必须完成的最终集成

截至本次文件存在性检查，8个专用核心交付已在工作目录；用户指定的 `reproduction_report.md`、`execution_timeline.md`、`README.md` 尚待根代理生成。全局归档约定额外要求的 `metadata.json`、`task_report.md`、`execution_log.md` 亦须生成。此为进行中状态，不将其误记为永久缺失。

建议最终集成按以下验收：

1. 运行报告写明实际命令/解释器/输入范围/开始结束/退出状态。全期Table1匹配是公开数据统计证据；预计算缓存结果重画不是全期缓存算法独立重算。当前73条比较表中的69项数值比较含不同来源，不能把67项舍入一致打包称为67项独立实验成功。
2. 保留失败、局部修复、已确认paper–code差异和Unknown。特别保留Table6 call加权分母、batch mix71.3/28.7对64.017/35.983、RTT扣除未定位、harness规则优先级差异、human多轮筛选与SWE豁免。
3. 时间线使用实际T0和实际结束时间，说明哪些动作由代理并行完成；不把计划表中的3小时写成实际已执行时长。无须空转到截止时间。
4. 公开导出只收原创报告、聚合、脚本、依赖/版本、必要patch与检查过的日志；原始Parquet、全文、上游源码副本、PCAP、身份/参数/用户文本保留私有。敏感信息与发布清单检查尚不能由本验收替代。
5. 归档目录必须为`tasks/freeinference-agentic-traces/20261110T080855Z-freeinf-audit/`；追加task index，保留历史。分支为`codex/freeinference-agentic-traces/20261110T080855Z-freeinf-audit`。最终push后核对远端SHA，创建指向main的PR并附加到任务；不得自动合并。

本次只读检查看到公开worktree已经写入根`AGENTS.md`/`README.md`持久约定，当前独立分支已存在；当时最近本地提交是初始化规范的`fc58e1e`。这不能证明本次研究成果已经上传，也不能替代最终远端SHA/PR验收。

## 标签、对齐与MVP的专项结论

**工具与任务语义没有混同。** `outcome=ok`是结果规则推断且可能默认ok，不表示task完成；category是功能/形式归一化，不是Create/Debug。八类intent的LLM模型、模板、样例、人工核验和一致性均Unknown；当前schema无intent列、registry未含Fig16，原prompt不公开，不能从hash/计数恢复同一标注实验。假名账户与harness也不是经认证身份真值。

**对齐设计没有假定一请求一flow。** 文档分别处理logical API call、retry attempt、transport connection epoch、HTTP stream、packet和tool；仅时间邻近时称候选/弱标签，并发缺少stream映射时拒绝唯一指派。历史公开trace与后来独立PCAP没有共同执行身份。当前middleware header ID、内部request ID和SSE completion ID之间没有经普通用户接口实测验证的完整join，不因公共GET回显header就升级为强匹配。

**MVP目标合理且限度明确。** 已提供固定Hermes/模型、单NIC、5个短任务各3次的计划、metadata白名单、官方observer hooks/auxiliary路径、transport补充与可选loopback代理。代理会改变流量，单harness/单model不能证明harness分类泛化。11个合成检查仅验证自建匹配逻辑；真实对齐误差、监督label precision和分类性能仍Unknown。

后续真实执行前，宜预注册与时间尺度相符的误差/弃权门槛；现文档给出了要报告的coverage、precision、歧义、残差与drop指标，没有虚构已达成的数值阈值。已知应用边界切片的分类必须与纯网络分段加分类分别评估。

## 2026当前网页值与历史论文版本检查

| 来源 | 本任务使用的版本 | 已检查的防混用边界 |
|---|---|---|
| FreeInference论文/trace | PDF SHA256 `0ab3b7968bb57f3edd27d7102cb48d99a23c72c0fcb42e6178f81bd8ba077c46`；作者代码`2b795d…`；HF revision`bb26cf…`；16周为2026-05-17至09-05 | 不用当前官网模型目录、当前Gateway埋点替代历史部署；Table1顶层包含SWE，子会话另算 |
| 当前Gateway | 官网2026-11-10显示`7f7585…`，本次实际匿名公共GET | DB timestamp/异步日志、ID桥与当前目录是当前路径证据；与历史采集版本对应仍Unknown |
| MiMo路由 | 2026-11-10匿名`/v1/models`只有3项，未含`mimo-v2.6-flash` | 只能证明该匿名响应未列出，不能证明所有授权账户永久不支持，也不能据历史model名证明今天可调用 |
| TraceLab | arXiv2606.30560v2(06-30)，固定README数据v0.0.1；当前官网数据v0.0.2 | 旧Table1为4265sessions/43users/357161steps/432510tools；官网为8058sessions/52contributors/665453steps/743819tools。数据release v2与arXiv v2不合并 |
| ANT | arXiv2610.06514v1(10-05)及论文所链匿名artifact | 规模和release是论文报告；本次未下载数据、未验证artifact完整性或baseline，不写成运行观察 |
| MAGIC26 | `simula/magic26@bf6797…`与官方workshop程序 | repo自述题名与会议标题有差异，正式全文/DOIUnknown；不把仓库README高精度描述当本次测量结果 |

未发现上述关键版本在最终已有专报中被混成同一事实。验收中发现并已由alignment代理修正两处引用：公共schema路径应为`release/schema.py`，论文§9为PDF p13。对主报告/CSV中固定作者commit的GitHub文件路径做本地存在性扫描，未发现无效路径；本检查不等于外部链接端到端可用性验证。

本代理也修正了自身研究对比中的过宽旧措辞：**重建算法确已公开**；缺失的是原始输入、95%验证材料与intent标注等，不再称“重建实现未公开”。并把多用户turn筛选加入工作负载先验的适用范围。

## 最终A–E要点

- **A：适合作为来源，但用于应用侧证据与受选population的工作负载/标签设计；不是现成网络包数据集。**
- **B：不能直接为独立PCAP提供可靠逐请求/逐包行为标签。**缺同一次执行、共同身份、连接/stream映射与可校准时间；语义intent正文/标注材料也不公开。
- **C：至少同期自采客户端应用事件与PCAP、双时钟锚点、task/session/request/attempt关系和固定配置。**时间窗只给弱标签；强关联需transport映射或可验证独占条件，Gateway信息仅在合法授权且ID桥实证后补充。
- **D：先做单Hermes、单合法可用模型、单NIC、少量短任务的配对采集与标签可信度实验。**精确MiMo路由未证实前不称原计划可运行；先验证事件与连接，暂不以训练高F1分类器作为首要成功标准。
- **E：成功只证明限定部署条件下能获得有误差界的监督样本；不能证明语义泛化或完整论文复现。**失败可排除该条件下简单时间匹配/一请求一burst规则，或暴露缺hook/stream证据；不能排除全部Agent网络分类可能性。
