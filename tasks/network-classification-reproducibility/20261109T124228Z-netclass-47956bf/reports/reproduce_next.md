> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# 下一轮复现对象与具体路线

以下排序依据可获得证据、尚待解决的关键问题和所需前置条件，不依据Star或引用量。所有建议尚未执行；本轮运行和等级见 `reproduction_results.csv`。R3必须恢复原协议与可比较指标，不能靠换数据、改算法或接近的accuracy达成。

## 1. Flowrest：优先恢复可比离线评估

**理由：** 已合法获取作者公开CSV，UNIBS完整12个notebook代码单元（含原grid）运行通过；UNSW还存在可复测的时间处理不对称，单因素对照有明显变化。比直接投入交换机更容易形成明确结论。

- 固定CSV SHA、原notebook及两版论文；先核实三个时间列原始单位、原始抓包→CSV转换和是否已缩放，不能选分数最高的变换当作“正确”。
- 保留原版与对照两条路径，核实训练/测试ID、标签顺序、随机种子、RF参数、树/规则数量；复核特征选择为何读取test及阈值99。
- 恢复原文每个用例和原评价协议；缺失的流管理模拟器/成本与流长权重逻辑应向来源获取或单列重新实现，不能声称上游已提供。
- 通过标准：每个对照都有来源/变换/划分证据；原文表格可逐项计算，可比较与不可比较项目分开。P4位宽修复仅在独立补丁中做软件域验证，随后再讨论编译。

证据：`papers/flowrest/`、`evidence/flowrest/core_*metrics.json`、独立逐样本复核。

## 2. ET-BERT：先澄清损失/配置，再投入真实训练

**理由：** 原base CPU forward和tiny训练链已可运行；损失0.1系数与论文公式、dropout配置覆盖有精确反例和历史证据。直接用当前HEAD长时间训练可能复现另一套协议。

- 明确原论文使用的commit、MLM/SBP损失归一化/权重、dropout0.5或0.1、tokenization/头部处理以及checkpoint。
- 从真正的下载端点取得官方权重并校验内容类型、大小、SHA256；README的`/view`页面不能当权重文件。
- 固定真实数据和样本/会话分组；确认packet随机划分是否跨会话。若要比较0.1/1损失或不同dropout，作为新敏感性实验报告，不能静默修成另一算法。
- 通过标准：能从同一数据/配置复跑预训练、微调与各任务评估，报告随机性和统计差异。现有132M随机权重短序列前向、两步tiny预训练只支持R1。

## 3. Lens：低成本先复评分布指标和核对数据身份

**理由：** 主模型训练仍R0；原指标/划分函数的合成诊断已暴露需要澄清的定义和协议，进一步调查不必先训练大模型。

- 获取原预测/目标分布，以作者原函数和常见标准定义分别重算TVD/HD，查明作者是否采用自定义归一化。保留两套数值，不能把重命名或归一化变更混作原结果。
- 获取发布集的文件/flow ID清单，区分重复路径、重复会话、不同粒度标签与无监督transductive exposure；对照论文协议，不能仅据参考脚本重叠指控标签泄漏。
- 固定TMLR/arXiv版本、模型权重和任务配置，补齐外部基线、五个fuzzing分类器及消融/新类扫描。
- 通过标准：在真实公开输出上闭合指标定义与数据身份，再决定是否投入GPU重跑分类/生成。

## 4. LINC：优先完成完整增量路径的正确性闭环

**理由：** 原NN与修复后的CPU合成训练/导出可运行，但局部default分区修复后仍有`values[N]`条件越界；论文的多次增量更新没有真实数据运行证据。

- 先用固定小规则集合覆盖matched/unmatched、default bucket、新类误分类和parent mask；对原/补丁每步缓存分区、规则集合与预测做对照。
- 解决default bucket的完整更新语义，再取得合法ISCX/UNIV/UNSW原数据和预处理，不从`RATIO=1`推断实际新类样本条数。
- 按论文顺序复跑Streaming/P2P/VoIP等新增类实验，记录每阶段数据ID、模型规模、规则数、训练/更新时间与旧类性能。
- 通过标准：完整增量入口在来源明确真实数据上运行，且每一步语义可核对；合成R1和局部索引修复均不足以声称算法完整修复。

## 5. Leo：先验证离散阈值和特征域，再构建P4

**理由：** 原P4文本生成/资源模型可CPU运行，但CART阈值量化和16位域存在限定数值反例，`--transient`控制面仍Disabled。

- 对固定模型特征的真实整数域做完整谓词对照，含半整数、边界值、MSB提取、溢出/截断。所有量化修改独立归档并验证与scikit-learn等价。
- 获取原始特征提取/标签/训练测试材料，确认公开代码缺失部分；不能用资源公式代替编译器资源结果。
- 在受支持且可合法安装的公开open-p4studio环境探索编译/软件模型，单列历史SDE兼容性。真实线速与交换机资源仍需要真实硬件。

## 6. Pegasus：验证当前公开软件artifact，标明原权重不可直接核验

**理由：** 作者说明原论文权重遗失，当前权重为重训；软件/硬件差异也已说明。它适合研究当前artifact可执行性，但不能把当前state_dict叫作原论文权重。

- 获取官方链接的测试CSV/JSON并保存许可、大小和SHA；先复跑当前公开软件CLI和指标，核对论文§7.1对“accuracy”的实际定义。
- 区分原权重、当前重训权重与本轮新训练；确认seed、标签、样本范围、预处理和模型结构。无法取得原物应保留Unknown。
- BMv2样例省略feature extraction、且只覆盖部分模型的范围单列；不能以生成包仿真代替真实流量或真实设备吞吐。

## 7. LiM、ETC、Mousika：延续首轮，但先补数据与协议

| 项目 | 下一步最关键材料 | 验证目标 |
| --- | --- | --- |
| LiM | 原4000样本ID/PCAP/划分、准确Python/XGBoost环境、对齐ET-BERT/YaTC配置/权重、资源计时协议 | 从原PCAP重建NetMatrix并复核Table1/2；单CSV较高accuracy不够 |
| ETC | 三数据集完整处理材料/12折/配置、软投票对硬投票、n=4与n=8处理、原负载/资源协议 | 从真实流量到模型/表项逐层闭合；表项一致不能代替包级/P4/硬件验证 |
| Mousika | ISCX/Bot-IoT处理与loader、原教师配置/LSTM、两版不同划分协议、v2 Gini原/修复敏感性 | 先复现应用分类而不是仅UNIV流大小demo；不把算法修复后的结果视为原文等价 |

## 下一批仅做静态审计的P0候选

FENIX、Synecdoche（2026）、Jewel、Caravan、netFound及TrafficFormer等已有关联证据，适合作为下一批。先审全部任务/数据/配置和权重可达性，再选择计算资源。Jewel公开范围已由作者限定；netFound的2026修订与2023首次版本必须按同family关联；CATO/PTU等本轮官方仓库仍Unknown，不应拿第三方同名仓库替代。

无需在下一轮开始前采购设备或联系作者；先形成缺失材料清单、固定可获得版本和运行预算。若研究者选择进一步取得数据/设备，应遵守其访问与许可条件。
