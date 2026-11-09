> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Lens 静态论文—代码覆盖审计

审计版本为 arXiv:2402.03646v5（14Jan2026，18页），不是2024初稿。已读§3方法、§4实施与全部评估、§5限制/结论、Appendices A–E；17张表、4幅图均列入97行覆盖矩阵。作者仓库README将现版标作TMLR2026，作者、题名与arXiv v5精确匹配；第一作者官方主页进一步在2026年6月宣布TMLR接收，并将该题名直接链接至本仓库Code。主页快照及获取哈希已保存。OpenReview页面/API本轮拒绝访问，最终TMLR独有修改及确切出版日仍Unknown。未把同family旧版另计论文。

固定作者源码 `main@dc91fb981ccc27371556895f75546ea84dfd46e7`，实际checkout为该SHA的detached状态且干净。来源API、固定README、论文与哈希在 `evidence/round2/modern_search/lens/`，完整跟踪文件/函数位置在其 `static/` 子目录。

## 已确认的代码事实

- 十二个分类任务全部出现在 `scripts/run_finetune.sh:32–45`；共用 `finetune_classification.py`、`cls/cls_digit`、生成式标签collator和prefix trie约束。不是只有一个VPN演示。评估确实计算Accuracy与macro/micro/weighted F1及classification_report。
- 七个数据分区（六个底层benchmark family，CrossPlatform拆Android/iOS）×五个header字段在 `run_generation.sh` 与generation collator中均有显式入口，对应Table6全部35个组合；JSD/TVD/HD评估位于 `utils/metric.py`。
- 两阶段新类扩展代码存在，包含按训练频率选新类、原类保留训练和仅新类训练、1/3/5类选择与old/new/all指标；可为Tables5/14/15/16产出相关结果。但实际数据和原checkpoint未获取，不能验证代码所选类是否恰好等于AppendixC中的命名类。
- 原始PCAP拆分、TShark文本/12字节payload、34包截断、IP占位token以及generation真实字段处理参考管线均公开。它不是turnkey流程：需要合法原pcap、外部SplitCap/Mono、TShark/editcap、手动选择dataset/mode。原始数据未随仓库分发。
- KG-MSP、context、T5模型与训练代码公开。网络BBPE训练入口/miniC4构建未找到，只加载作者已发布tokenizer。HF数据/模型加载没有固定revision；本轮未下载权重、真实数据或tokenizer。

## 缺失及与论文评估的距离

- Tables2/3的FS-Net、BiLSTM_Att、Datanet、DeepPacket、TSCRNN、YaTC、TrafficLLM、ET-BERT八个基线实现/配置/对齐样本未随Lens仓库提供；Table5的ET-BERT/LwF扩展基线、Table6的NetShare/TrafficLLM生成基线也没有本地复跑入口。
- Fig3包含MLP、DecisionTree、SVM、KNN、LogisticRegression五个下游检测器。`generation_fuzzing`在 `finetune_generation.py:510–516` 只对train_dataloader调用生成evaluate，缺少这些检测器在生成数据上训练并对真实test评估的后续阶段。不能把该mode名称当Fig3全实验覆盖。
- Tables7/8/12的去context/去KG/random-span对照和Table13的θ/k参数扫描没有完整配置/driver/checkpoint；普通随机span helper并不等于发布了网络侧random-masking对照实验。
- Table9全量包数/token统计脚本、Table10所有具体抽样比例/约10k样本选择及原始路径ID缺失。Table11的类数须用真实发布集核验；原始映射20个USTC类/Android212注释与论文最终16/209可能来自稀有类别过滤，不足以认定代码错误。
- 默认配置不唯一对应论文：预训练dropout0.0而论文0.1，context prompt遮罩0.50而论文§3.2称15%，高优先字段概率硬编码0.60而AppendixB.2文字称最终采用0.50；Table13参数未暴露为配置。分类launcher40epochs与正文20不符，但AppendixE写max40。130k vs780k可能是update/microstep口径，不能仅凭文本判错。原训练日志/config/权重产生过程Unknown。

## 运行观察与仍未验证问题

原样函数诊断见 `reproduction_report.md` 和 `metric_split_probe_results.json`，没有启动Lens模型。两个观察必须限定范围：

1. `metric.py:56–60` 的TVD比常见标准TVD多除sqrt2，HD则未采用常见Hellinger的1/sqrt2归一化。直接原函数在不相交点分布上分别得到0.7071/1.4142，而常见标准均为1。论文只给名称和口述，无明确公式；可能是作者自定义约定，不能据此声称Table6分数已证实错误。原预测及论文绝对数值影响Unknown。
2. `2_split_pcap_by_label.py:230–248` 先从所有flow生成coarse预训练manifest，再从同一全集独立生成fine-task train/val/test；类似结构也存在于Tor/USTC/DoH/IoT。合成400path记录上确有22个fine-test path出现在coarse-pretrain，作为控制同一coarse协议pretrain/test无重叠。这里只证明参考管线允许transductive input exposure。论文§4称不使用fine-grained task labels，但未明确所有raw-flow跨任务inductive互斥；无监督input exposure不等于监督标签泄漏。真实HF发布集、论文实际管线和其允许的协议仍Unknown。

另有纯文本一致性问题：§4.1叙述中Task2/3的84.06/89.79与Table2排序相反；§1平均96.31与abstract/Table3约96.33不同。`static/paper_consistency.json`保留原值和表内平均算术；不据此推断底层模型性能或研究不当。

静态结论为：Lens主要方法与全部主任务入口覆盖较广，但论文的完整比较、fuzzing、消融/敏感性和原始数据/训练协议不能从现有源码独立完整重放。完整实现结论Unknown；论文结果复现Unknown。
