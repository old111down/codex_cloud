> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# 现代文献目录独立复核

对象：`catalog/round2/modern_screening.json`的16条记录；本复核只核对官方关联、主源身份、时间边界、分类范围及family去重，不重复Lens静态审计，也不认证代码完整性或运行结果。

**结论：目录身份和去重检查通过，无已知错链被计作已核实的网络论文仓库。** 16条中9条`included_verified`、5条`included_unverified`、1条关联会议/期刊扩展、1条排除的网页访问量预测。10条“论文—仓库已验证”记录合并后是9个网络论文family；全部主范围候选合并后为14个family。不可把10个仓库记录或16条初筛记录直接当作16个独立开源论文。

## 固定版本和证据文件

逐条检查了全部`evidence_files`存在性；已验证记录逐条核对GitHub仓库规范URL、commit API完整SHA、固定SHA README下载URL和实际README Git blob SHA1。10个已核实仓库记录全部一致；排除的`kojunseo/Trafficformer`作为负例也与其独立API快照一致。检查细目、目录SHA256、时间和每条身份见 `modern_catalog_independent_review.json`。Git blob SHA1用于与GitHub文件身份交叉核对，不替代仓库统一SHA256证据封存。

`trafficgpt_long`目录里的GitHub API/README刻意保存的是被拒绝的道路交通同名仓库，canonical仓库/SHA仍是Unknown；这不是官方源码证据。后续自动采集不可忽略该负例标记，直接从文件名`repository_api.json`补回错误身份。

| 记录 | 核对结果与边界 |
| --- | --- |
| Lens | 原README精确作者/题名/arXiv匹配，2024早期版与2026知识引导版同一arXiv family。2026日期是所审v5日期；TMLR独立接受详情仍Unknown，不把README引用当独立出版方确认。Lens具体覆盖由单独静态审计负责。 |
| netFound | 原文§7直接链接`SNL-UCSB/netFound`，另有独立paper-evaluation artifact；两者不可自动视为相同完整实现。2023早期版与2026v5不重复family计数，最新正式venue保持Unknown。 |
| TrafficFormer | 作者论文明确指向`IDP-code/TrafficFormer`；主源题名、六作者、Crossref DOI一致。与网页访问量预测`kojunseo/Trafficformer`区分正确。 |
| Generic TrafficLLM | 原论文与`ZGC-LLM-Safety/TrafficLLM`直接关联；作者Cui/Lin/Li/Chen/Yin/Li/Xu，不是Ginige等人的open-set TrafficLLM。 |
| MM4flow | 作者主页将确切ACM DOI和`Shangshu-LAB/MM4flow`并列，README/Crossref七作者匹配，公开README含PCAP/Zeek处理和classifier train/test入口，范围是网络分析而非道路预测。全文/完整任务覆盖仍Unknown。当前GPU字段较保守：README已有四GPU分模态CUDA示例，但最小要求仍未知。 |
| FlowletFormer | 公开全文提到代码在supplementary material；未取得其官方GitHub关联。目录保留“未找到”而非“作者未开源”，正确。 |
| NetBench | 原论文摘要直接链接`WM-JayLab/NetBench`，明确15分类/5生成任务；benchmark纳入是因明确分类任务，不是把数据汇编误称新分类模型。 |
| NetGPT | 原文首页与`ict-net/NetGPT`直接关联；2023首版/2025v3同一family，不把新arXiv版本当独立2025论文。正式venue/DOI不从无关Crossref结果推断。 |
| Open-set TrafficLLM + TrafficGPT | 两README和Crossref精确题名/作者/DOI匹配，会议仓库明确指向期刊扩展代码，合并`yasod_trafficgpt_llm`为一个family；两个真实仓库记录仍分别保留。 |
| CATO | 官方USENIX NSDI2025与作者论文/博客身份匹配；明确有IoT设备分类及可复用serving优化，分类相关部分可纳入。回归结果不计作分类复现。未找到官方仓库不等于证明无源码；未采用无关同名CATO项目。 |
| PTU | Crossref及ICNP官方会议页精确五作者/DOI匹配。独立最小publisher读取再次核对作者，Introduction提及应用分类/入侵检测；但具体分类实验/全部评估未取得，应继续作为P2相关候选而非已核实开源实现。 |
| FlowTransformer | 原文脚注明确`liamdm/FlowTransformer`；Crossref题名/作者/ESWA DOI一致。NIDS有显式flow分类任务，符合主范围；2023arXiv/2024期刊不重复计数。 |
| Long TrafficGPT | JianQu/XiaoboMa/JianfengLi长网络流论文与`lijlansg/TrafficGPT`道路智能体无关。后者README指向另一arXiv、SUMO、道路数据库及LLM服务；正确拒绝。LaBackDoor模型卡明确为SoK实验者release，不视为原作者官方artifact。 |
| TFE-GNN | 原论文/精确Crossref核实文献身份；“未来将公开代码”不等于已公开。当前官方仓库仍Unknown，未采用普通ntc-gnn同名项目。 |
| Wrong Trafficformer | README明确预测Wikipedia网页访问量；排除主范围正确。它的GitHub存在和固定SHA不能用于S&P2025网络流量分类论文计数。 |

## 时间、范围和Unknown边界

已核实GitHub commit时间均不晚于2026-11-09。目录2026条目为Lens v5（1月14日）、netFound v5（5月12日）、open-set TrafficLLM期刊issue（1月），均在本窗口内；这些日期语义不同，不应混作首次发表日。MM4flow为2025年11月，晚于2025-11-09但早于本任务截止2026-11-09，不构成越界。未知DOI/venue保留Unknown，没有补造。

五条未核实仓库记录均保留`code_public=Unknown`，没有把一次403/503、未检索到或未取得补充材料写成“确定未开源”。当前目录对数据/权重、最小GPU、全部实验完整性、实际执行均保留Unknown或“未下载”限定；不能据README或GitHub Star声称主要任务完整实现。

独立新增最小主源核查为PTU出版方metadata/Introduction；原文PDF无权限，未绕过。MM4flow出版方补充摘要读取失败，记录在 `modern_catalog_mm4flow_primary_probe.json`；官方关联依靠已保存作者主页与精确书目信息，不受该次失败替换。没有新增模型运行或依赖安装。
