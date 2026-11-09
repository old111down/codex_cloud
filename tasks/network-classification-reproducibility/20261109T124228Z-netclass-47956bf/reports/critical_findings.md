> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# 重要复现发现与证据边界

本报告讨论公开artifact及本轮运行，不据此推断作者实际使用了哪一版代码，也不把局部反例等同于论文精度失效。证据分为：**已确认事实**（原文/固定源码）、**运行观察**（原始日志与输入来源）、**合理推测**（可能影响，未证实）、**未验证问题**（Unknown）。完整逐实验映射见 `coverage_matrix.csv`，实际命令见 `reproduction_results.csv`。

## F01：ET-BERT损失权重和dropout与论文描述不一致

**已确认事实 + 运行观察，高优先级。** 论文§3.3 Eq(4)写MBM与SBP损失求和；固定 `d59470624acd11405f9e88da650cf3bf65521e9a` 的 `uer/trainer.py` 实际把MLM损失除以10后再加SP，外层还有梯度累积归一化。直接调用原方法的数值探针确认这一系数及梯度。历史追踪最早在2022-04-01提交已发现0.1权重，后续2024/2025有改动/回滚；因此不能把当前版本简单等同于2022发表版本。配置加载还将命令行dropout0.5覆盖为0.1。

证据：[论文—代码审计](../papers/et_bert/static_audit.md)、`evidence/et_bert/loss_equation_probe.json`、`loss_history.json`、`source_behavior_checks.json`、`logs/et_bert/loss_equation_probe_location_corrected.*`；另有独立复核的梯度探针。**未验证：** 原论文实验的实际权重/commit、这一差异对真实任务精度的影响。未静默更改损失，也未以两步合成预训练宣称原预训练复现。

## F02：Flowrest时间特征处理不对称，真实CSV上有明显可复测差异

**已确认事实 + 运行观察，高优先级。** 固定 `13a527cfc0cac523b9f4be9a9366738bcdd3d5db` 的conference UNSW notebook训练阶段对三个time特征乘1000，测试路径没有对应变换。作者公开CSV上的原样选定单元：215484训练/73249测试，Accuracy0.645647、MacroF1=0.402694。仅在测试端对同三列追加×1000以匹配训练，其他条件保留，敏感性对照变为Accuracy0.987031、MacroF1=0.919989。

证据：[运行报告](../papers/flowrest/reproduction_report.md)、`evidence/flowrest/core_conference_metrics.json`、`core_conference_time_aligned_metrics.json`、两套逐样本预测与下载哈希，`logs/flowrest/conference_time_alignment_sensitivity.*`。**未验证：** CSV真实时间单位、论文实际转换/数据版本、这一对照是否恢复作者原协议。该对照不是原版成功，更不是论文指标复现；notebook旧注释也不算本轮结果。

同仓库的特征/超参数选择反复读取`X_test/y_test`，没有独立dev划分；`score∈[0,1]`的特征选择接口却收到阈值99。前者是公开代码的test-set selection路径，后者是数值接口不一致；它们是否影响论文实际报告值仍Unknown。

## F03：Leo的CART阈值转换存在整数域反例

**已确认事实 + 运行观察，高优先级。** 固定 `bd9fb79b8e0bd79b4922f3ca1ada88b9ee69eff2` 的解析器将树阈值用`round`量化，再生成严格小于谓词。阈值0.5对整数输入0，CART左支与生成条件发生不同路由；2.5也有反例，1.5并非同样失败。还保存了16位MSB/65535的边界诊断。

证据：[Leo静态审计](../papers/leo/static_audit.md)、`evidence/leo/threshold_counterexample.json`、`integer_domain_counterexamples.json`、`logs/leo/threshold_counterexample.*`。这是原源码谓词的数值比较，**没有运行P4或证明论文实际数据误分类率**。模型真实特征域、原数据、完整预处理及硬件结果仍Unknown。

## F04：LINC未匹配规则的subspace索引错误

**已确认事实 + 运行观察，高优先级。** 固定 `4a44171c84547de885a54e5f1a234640cd8501d4` 的 `linc/simulator.py:58` 对未匹配输入使用`len(self.scores)`，在反例中为1，而规则数N=3时保留default bucket应为3。八个3-bit输入中五个未匹配输入被误分配到rule1；隔离补丁后该反例零错。

证据：`evidence/linc/subspace_original.json`、`subspace_patched.json`、`logs/linc/default_subspace_*`、[补丁登记](../patches/linc/README.md)。这是缓存/分区语义错误；不是已测得网络分类精度下降。独立执行原更新表达式还确认：保留default index=N后，新类default误分类条件可使`update_streaming.py:179`读取`values[N]`触发IndexError，见 `papers/linc/independent_checks.json`。这是局部可达条件反例，不是完整增量入口已经运行；不声称增量算法已修复。

公开更新入口`RATIO=1`与小比例注释不一致，且没有明确63条的新类样本限额；未获取实际`iscx.pkl`，实际新类数量Unknown，不能据此断言论文的63条实验没有执行。

## F05：YaTC加权指标被命名为macro，CPU入口含CUDA假设

**已确认事实 + 运行观察。** 固定 `a220b75f8365acaf63dbac7df87aaaa357698b85` 的 `engine.py:209` 使用`average='weighted'`，却在输出键中写`macro_pre/macro_rec/macro_f1`。原评估函数的合成反例给出该键F1=0.45，真正按macro平均为0.15。原CPU训练入口在无条件`torch.cuda.synchronize()`处失败；两个隔离兼容补丁后单batch合成训练通过。

证据：[运行报告](../papers/yatc/reproduction_report.md)、`evidence/yatc/metric_semantics.json`、`synthetic_smoke_metrics.json`、`logs/yatc/metric_semantics.*`、`engine_cpu_probe.*`。原模型MAE/TraFormer可CPU forward/backward不等于原训练/论文评估已完成。

**未验证：** 论文是否把相应结果标成macro、全部图表/第五数据集及原结果协议。官方全文遭HTTP403/BotStopper，额外合法检索未解决；不能用代码反推整篇论文。输入表示保留IP/端口及每epoch评估test并记录Max值的行为已登记；实际泄漏/作者选值策略Unknown。

## F06：参考数据划分与测量定义需要单独核验

**已确认事实，影响边界单列。** LiM在切分前拟合StandardScaler，使用了未来测试集的分布信息；实际作者CSV4514行、类别372–486，与论文4000条平衡样本不一致。原始会话ID/PCAP不存在，无法确认来源独立性。它的CPU核心运行可验证，原论文评估等价性不能由接近或更高accuracy替代。

证据：[LiM报告](../papers/lim/reproduction_report.md)、`evidence/lim/data_audit.json`、`xgboost_classifier.numbered.txt`、`predictions.csv`。对树模型，仿射缩放信息泄入的具体精度影响本轮未单独测量；不据此宣称论文精度被抬高。

Lens当前原参考管线的跨任务预训练/测试划分探针和TVD归一化检查单列于其报告。参考代码路径重叠只说明可能存在transductive exposure，不自动等于标签泄漏；真实发布数据/论文协议仍Unknown。论文未给明确TVD公式时，与常见标准定义不同也不能直接判定论文Table6错误。见 [Lens审计](../papers/lens/static_audit.md) 和 `papers/lens/metric_split_probe_results.json`。

Pegasus原FlowDataset先展开window8再做validation切分；显式`val_ratio=.2`的合成机制反例出现同flow/原包共享，见 `evidence/pegasus/split_grain_diagnostic.json`。这不是默认配置、真实外部test或论文实际标签泄漏的证据。

## F07：Flowrest和ETC的P4生成成功不代表可加载

**已确认事实 + 运行观察。** Flowrest原generator exit0，但3-bit/5-bit键的末端区间写到65535，超出7/31的合法上限；只执行Python生成器不能称P4构建成功。ETC原generator受Python众数语义影响生成7776条投票项，超过固定P4容量5256；两隔离补丁后与随附artifact表项集合一致，全部7776个投票输入经软件比较通过。

证据：`evidence/flowrest/generated_table_validation.json`、`logs/flowrest/generated_range_validation_corrected_harness.*`；`papers/etc_noms_2024/table_validation_metrics.json`、[ETC补丁](../patches/etc_noms_2024/README.md)。**未验证：** BFRT加载、逐包语义、时间戳/累计长度wrap、端口/控制器时序、真实资源和线速。ETC表项一致只是恢复随附artifact，不证明RF软概率平均与P4硬投票等价。

## F08：主要模块存在，全部论文用例仍未公开闭环

**已确认事实（固定仓库清单/作者说明）。** Mousika提供UNIV demo和通用蒸馏/规则转换，不能覆盖ISCX/Bot-IoT全流程；ETC只附带NIMS样本，另外两用例P4配置/硬件评估缺口显著；LiM缺两项基线及资源/增量测量；Flowrest扩展版的流管理模拟器、成本约束及多数用例没有完整实现；Leo控制面`--transient`只打印Disabled；Jewel作者README明确只公开四用例中的一个。

证据：逐论文矩阵与静态报告；`evidence/round2/network_search/jewel/README.md`、Leo `logs/leo/readme_ctrlplane.*`。没有把原README第一条demo或作者“完整实现”表述当作全部任务覆盖证据。

## F09：Pegasus当前公开权重与原论文权重的区别

**已确认事实（作者声明），运行范围另见报告。** 软件子目录README说明原论文`.pth`丢失、现权重重新训练；它还说明软件/硬件因寄存器冲突与丢包不完全一致，与顶层README的一致性表述需要分开阅读。

证据：`evidence/round2/network_search/pegasus/software__README.md`、固定SHA与来源日志，以及 [Pegasus报告](../papers/pegasus/reproduction_report.md)。这证明当前权重不是可直接核验的原始权重；**不证明重新训练不可能达到原论文指标**。没有将新权重或合成输入推理冒充原模型复现。

## F10：两处同名错链会污染候选目录

**已确认事实（第三方目录与主源不符）。** 网络TrafficFormer原文关联`IDP-code/TrafficFormer`；另一个`kojunseo/Trafficformer`是web访问量预测，已排除。网络TrafficGPT论文被第三方目录指到`lijlansg/TrafficGPT`，该仓库对应另一篇道路交通/模拟分析论文及SUMO工具；该关联被否定，网络论文的官方仓库本轮仍Unknown。

证据：`catalog/round2/modern_screening.json`、`evidence/round2/modern_search/`固定README、论文和检索日志。错误来自目录关联，不能归责于论文作者，也不能据此断言网络论文没有开源。同名TrafficLLM两项不同研究、YasodGPT→LLM扩展按不同研究/同family分别建模。

## F11：运行兼容性与科学等价性不能混为一谈

**运行观察。** LINC原requirements的swanlab版本不可解析，Torch2.0.1与NumPy2.0.1桥接失败，小batch训练日志取模0；ET-BERT原入口有PYTHONPATH/硬编码结果路径问题；YaTC历史timm/torch/distutils组合有导入不兼容。兼容或运行补丁可让有限测试继续，但不恢复缺失数据、原划分、原权重和论文性能。

证据：`logs/linc/`、`logs/et_bert/`、`logs/yatc/`原始失败和逐论文补丁登记。安装、编译器探测、空CSV、Disabled输出和`git apply`成功不会被自动授予算法运行等级。

## F12：公开SDK可获取性需要更新，硬件验证仍缺

**已确认事实（官方源码） + 未验证问题。** `p4lang/open-p4studio`固定提交公开了可构建的Tofino软件模型、BFRT与编译相关源码。因此不能笼统认定所有软件验证都只能依赖不可获取的专有SDK。历史SDE兼容性、公开版本实际构建、物理BSP/特定驱动授权及真实设备可用性是不同问题。

证据：`evidence/round2/open_p4studio/audit_note.md`与固定README/许可证/二进制说明。本轮未安装/编译SDK；这是预算优先级下未执行，不是已观察到编译失败或已证明资源不足。所有线速、硬件资源、真实时延结论仍Unknown。
