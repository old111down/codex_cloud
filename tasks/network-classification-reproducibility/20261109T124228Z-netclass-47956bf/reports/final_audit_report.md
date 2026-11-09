> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# 网络流量分类自主复现审计综合报告

本轮沿用首轮证据，扩展检索与审计，**没有任何论文被认定为完整结果复现成功（R3/R4）**。代码公开完整性A、代码运行B和论文结果复现C分开记录。安装成功、随机权重前向、合成数据、P4文本生成和指标函数反例都不能替代论文结果。

## 覆盖范围与实际时间

研究窗口为2021-11-09至2026-11-09。检索覆盖加密/应用分类、离线服务器模型、在线/增量学习、P4/Tofino、基础模型与相关明确分类机制；普通web访问量预测、道路交通模拟不纳入主范围。异常/DDoS工作仅在有明确分类或可复用分类机制时纳入，并标注类别。

本轮T0为2026-11-09T11:06:24Z（北京时间19:06:24），最多3小时；真实结束时间和累计耗时见 [执行时间线](execution_timeline.md)。首轮基线为`e3136eb`。旧运行保留原时间，在统一结果表标为`inherited_round1`；本轮新增运行标为`autonomous_round2`，没有重算旧命令为新增工作。

初筛37条论文/版本/排除记录，按family去重为36组；其中一个web预测负例排除，**35个范围内论文族，30个论文族有官方仓库关联证据**。31条已核实关联记录中有一组会议—期刊扩展，不能当作两个独立研究计数。其余五个范围内论文族的官方仓库仍Unknown；未找到不等于未开源。精确命令统计见`aggregate_summary.json`，命令记录数不等于科学实验数。

共10个详细静态审计包、574条覆盖项。九个包审读了可取得的公开全文版本及图表/附录；**YaTC官方全文访问受阻，只有源码和官方文章页，完整论文实验覆盖为Unknown**。Mousika/Flowrest两版论文分别映射；LiM/Pegasus等公开作者版与无法取得的最终出版版差异保留Unknown。版本日期不自动等于首次发表：Lens/netFound的2026修订和更早首发通过family及`first_publication_year/year_basis/date_basis`关联。

## 代表性开源研究有哪些

以下工作均有明确主源关联，完整题名、DOI或Unknown、作者仓库、全SHA、许可、更新时间、任务/标签/数据/模型见 [统一目录](../catalog/papers.csv)。

| 路线 | 代表工作 | 本轮证据范围 |
| --- | --- | --- |
| 2021–2023代表性工作 | ET-BERT、YaTC、Mousika、Flowrest、NetBeacon、Henna、Soter、HorusEye | 前四项详细审计；其余关联/范围初筛。HorusEye明确标为异常分类机制次级范围 |
| 2024在线/P4/增量 | ETC、Leo、LINC、Brain-on-Switch、IIsy、Jewel、Caravan | ETC/Leo/LINC详细审计；其他为候选，不能推断实现完整 |
| 2024–2026轻量/基础模型 | LiM、Lens、netFound、TrafficFormer、两项不同TrafficLLM、MH-Net、NetMamba、MM4flow、NetBench、NetGPT、FlowTransformer | LiM/Lens详细审计，其余主要为关联核实；版本/名称/任务分别保存 |
| 2025–2026新系统 | Pegasus、FENIX、Synecdoche | Pegasus详细审计；FENIX/Synecdoche原文与官方仓库关联核实，运行Unknown |

这不是穷尽式文献综述。通过论文脚注/附录、作者主页、DOI、固定README和GitHub API交叉核实，不以Star、搜索摘要或名称相似性建立关联。两处第三方目录错链被拒绝：网络TrafficFormer不能替换成web预测项目；网络TrafficGPT不能替换成SUMO道路交通项目。

## 哪些实现完整，哪些只是核心或演示

**本轮没有确认任何仓库完整闭合了其论文全部任务、数据集、对比、配置和性能评估。** 这不是说所有核心算法都缺失；下表给出可确认的公开范围。

| 仓库 | A：公开实现的可确认范围 | B：实际运行边界 | C：论文完整结果 |
| --- | --- | --- | --- |
| LiM | 单个NetMatrix→XGBoost分类器；原PCAP/4000样本/两基线/资源与在线声明未闭合 | 作者CSV分类核心R2 | Unknown |
| Flowrest | 两条公开CSV分析路径及转换器；扩展流管理模拟器/成本模型/多数用例缺口 | UNIBS完整notebook和UNSW选定单元R2；单因素敏感性单列 | Unknown |
| ETC | NIMS样本、约束RF与模型表项生成；三用例完整配置/硬件评估不足 | NIMS核心R2；表项对照R1 | Unknown |
| Mousika | UNIV示例、通用蒸馏和规则转换；ISCX/Bot-IoT及扩展全部流程未闭合 | 整体R1；UNIV前缀组件R2；应用分类R0 | Unknown |
| ET-BERT | 预训练/微调/推理主要模块公开；原始数据/七数据集协议、损失/配置差异待澄清 | 原base随机权重前向及tiny合成训练R1 | Unknown |
| YaTC | 模型/预训练/微调主要源码存在；论文全图表/第五数据集Unknown | 兼容辅助合成R1；原README入口失败 | Unknown |
| LINC | NN/规则蒸馏/增量入口存在；原三任务/数据/P4源码和完整更新链未闭合 | 原NN与隔离修复后的合成训练/导出R1 | Unknown |
| Leo | 训练、P4文本生成、资源公式；特征提取/瞬态控制面/原评估缺口 | 文本生成与公式组件R1；transient Disabled不算通过 | Unknown |
| Pegasus | 软件模型和部分P4/BMv2链；原权重丢失、特征提取与全部部署链未闭合 | 当前作者替代权重的CPU合成推理、文本生成R1 | Unknown |
| Lens | 分类/生成/参考处理模块；外部基线、fuzzing后处理、消融/完整扫描缺口 | **主模型R0未执行**；原指标/划分诊断组件R1 | Unknown |

在“已预处理作者CSV”的明确假设下，LiM分类器和Flowrest UNIBS分析路径有可运行闭环；不能把这一结论扩展到论文全部用例。仅核实关联、未做详细审计的其他候选，A/B/C均不能由README推断。IIsy的Iris默认演示不是网络任务，Jewel作者也明确限定公开用例范围。

## 普通云端CPU能验证什么

实际主机Debian13.6、x86_64，可见5个逻辑CPU但配额4核、内存上限16GiB；未发现GPU。共保留10个独立Conda前缀及声明/explicit/freeze/版本记录，**Lens环境仅用于数值诊断，不是其完整模型环境**。依赖失败和兼容差异均保留，系统Python和上游源码保持隔离。

| CPU结果 | 实际观测 | 与论文可比性 |
| --- | --- | --- |
| LiM作者CSV（继承） | 3611训练/903测试，Accuracy0.9534883721，MacroF1=0.9530904896 | 4514行而非4000平衡样本，协议/版本不等价 |
| ETC NIMS样本（继承） | 1285训练/429测试，Accuracy0.9160839161，MacroF1=0.9160557133 | 离线样本不等于原三数据集/12折/硬件 |
| Flowrest UNIBS（新增） | 20664训练/19636测试，Accuracy0.9960786，MacroF1=0.9715532 | 原notebook全12单元通过；全部论文协议/用例未恢复 |
| Flowrest UNSW16原版（新增） | 215484训练/73249测试，Accuracy0.6456470，MacroF1=0.4026941 | 原版选定单元；未运行全部搜索/硬件 |
| 同UNSW单因素对照（新增） | Accuracy0.987031，MacroF1=0.9199888 | 仅test三列×1000；真实单位及论文等价Unknown，**不是原版结果** |
| Mousika UNIV前缀（继承） | 70训练/256测试，Accuracy0.76953125 | 任意小前缀流大小预测，不代表应用分类/全量论文指标 |

这些数据集/任务不同，不能按分数排名方法。Flowrest逐样本预测和单因素变换由另一代理独立重算，指标误差低于1e-12；其真实时间单位仍Unknown。

深度模型方面，ET-BERT原base约132M参数在随机权重、短序列上CPU forward成功；tiny模型两步预训练和分类仅合成R1。YaTC原模型合成forward/backward可CPU运行，原训练engine则有CUDA假设；LINC和Pegasus仅有限合成路径。不能据此宣称大规模预训练、真实accuracy、训练效率或论文推理性能已在CPU复现。

所有整体walltime/单元耗时与输入规模都有日志；本轮没有恢复论文的batch/warmup/重复、功率、资源采样协议，故**可比较推理延迟、训练时间、吞吐、GPU功率和硬件资源均Unknown**。

## GPU、SDK、硬件和数据依赖

ET-BERT/YaTC/LINC的部分模型数学可CPU运行，但原脚本含GPU假设或原大规模实验使用GPU。Lens官方模型路径涉及CUDA/flash attention，本文未构建；NetMamba/MH-Net/其他基础模型候选的GPU声明来自主源，最小资源和CPU等价性未经本轮实际验证。不能把包名含CUDA/NCCL解释成存在GPU。

P4项目严格分模型/规则生成、编译、软件模型、真实硬件四层。**本轮没有P4编译、包级软件交换机仿真或真实交换机验证通过记录。** Python生成文本、AST和穷举表项都只是软件组件证据。Pegasus BMv2样例只覆盖部分模型、用生成包省略特征提取；未安装需系统配置/权限的整套环境。

2026公开的`p4lang/open-p4studio`提供软件模型/BFRT/编译相关源码，纠正了“所有Tofino软件验证只能依赖不可获取的专有SDK”的笼统前提。本轮仅审读固定源码，未构建；历史SDE兼容性、物理BSP/特定驱动、P4Insight与真实设备另行核实。没有把未执行写成已证明资源不足或已发生构建失败。

## 实际确认了哪些问题

完整证据、严重性及事实/推测/Unknown边界见 [重要发现](critical_findings.md)。优先关注：

1. **ET-BERT方法—代码差异**：MLM额外0.1系数、dropout覆盖，历史和数值梯度探针可核；原论文实际commit和精度影响Unknown。
2. **Flowrest数据处理与选择路径**：train/test时间变换不对称、真实CSV敏感性、test参与特征选择、阈值99；不把对照当论文成功。
3. **Leo/LINC规则语义**：离散阈值量化和默认分区反例；LINC局部修复后完整更新仍有条件越界，不能宣称增量机制已修复。
4. **指标语义**：YaTC weighted计算命名macro；Lens归一化不同于常见定义，但论文没给明确公式；Pegasus公开稿“accuracy”实为packet macro-F1。三者分别处理，不直接指控论文指标错误。
5. **数据身份与原资产**：Lens参考跨任务预训练/下游测试路径可能重叠、Pegasus窗口后validation切分的条件反例；无实际发布集/外部test/论文标签泄漏结论。Pegasus原权重丢失则是作者明确说明的事实。
6. **可执行性与覆盖缺口**：不可解析依赖、NumPy桥接/导入/CUDA/路径错误、P4位宽越界、缺失模拟器/控制面/基线与实验配置。原失败和修复后成功分别保存。

审计本身也有局限：Pegasus首次CNN-L README尝试在静态pickle审查前已执行`torch.load`反序列化，随后缺数据、尚未`load_state_dict`；静态审查是事后补做，没有倒称预审。后续MLP限定使用预审文件和`weights_only=True`。该顺序偏差及原日志保留。其余harness定位/顺序错误同样不冒充上游错误。

## 建议投入顺序与交付审查

优先Flowrest原协议/时间单位、ET-BERT损失与配置、Lens真实输出重评分，再推进LINC完整更新和Leo量化语义。LiM/ETC/Mousika继续补原数据与任务路径；Pegasus先复核当前公开artifact而非原权重。具体材料、步骤和通过标准见 [下一轮路线](reproduce_next.md)。FENIX/Synecdoche等2026候选适合下一批静态审计，当前不能给完整实现背书。

七项要求的文件均在`catalog/`和`reports/`。逐论文`metadata/static_audit/coverage_matrix/reproduction_report`、环境锁、原始日志、数据/模型来源和SHA、隔离补丁及独立复核可逐层追查。全部结论以固定commit和实际证据为准；尚未得到证据的问题保持Unknown。

最终分支为`audit/autonomous-20261109`，检查点`7bf940b`保存扩展检索；后续审计/汇总提交见Git历史。结构/命令谱系/证据校验只验证档案完整性，**不构成论文科学结论认证**。实际结束与归档状态见执行时间线和最终提交。
