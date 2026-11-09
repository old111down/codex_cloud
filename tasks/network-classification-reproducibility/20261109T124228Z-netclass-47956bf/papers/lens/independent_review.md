> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Lens 独立复核

2026-11-09 UTC。固定作者源码 `dc91fb981ccc27371556895f75546ea84dfd46e7`，审计稿为arXiv:2402.03646v5（2026版本），不是2024初稿或已独立取得的最终TMLR排版。核对报告、97行覆盖矩阵、论文编号caption/关键数据协议/指标/附录文字、任务launcher、扩展数据选择、原metric/split函数、诊断harness及日志。本次没有训练/加载Lens模型、tokenizer或真实网络数据。

## 结论与完整性边界

在本次独立检查范围内，未发现实质夸大。主模型应保持**R0**，只给原评估和参考划分函数的限定诊断组件R1；数值包专用Conda环境不是完整Torch/Triton/Transformers环境，不能记为Lens主模型安装/训练成功。

独立从原文caption重新提取出17张表、4幅图；矩阵为97行，含12个分类任务、35个数据分区×字段生成组合、Android/iOS各1/3/5新类别的6个扩展设置。AppendixA的统计/划分/类数、B的对照与敏感性、C的新类逐类结果、D的输入例子和E的超参数均有覆盖项。该核对确认inventory和声明范围，不等于这些实验已运行。

launcher确实列出全部12分类任务和7数据分区×5生成字段；CrossPlatform拆Android/iOS使7分区对应6个底层benchmark family，报告没有重复计独立数据源。扩展代码按train频率选择new classes并保留old/new/all评估入口；是否正好选出论文命名类别需要真实数据，报告保留Unknown。fuzzing模式在原`finetune_generation.py:510–516`只调用生成evaluate，并不含Fig3五个检测器的完整训练/真实test后处理；矩阵没有把mode名称视为完整实验实现。

## 两项诊断的独立核对

1. **指标归一化**：原`metric.py:56–60`的TVD为`0.5*L1/√2`，HD为未归一化平方根概率向量欧氏距离。对P=(1,0)、Q=(0,1)，标准总变差`0.5*L1=1`，代码TVD=0.70710678；未归一化HD=1.41421356，常见归一化Hellinger=1。标准库独立重算与归档输出吻合。论文§4仅给指标名称与口头说明、引用NetGPT设置，没有明确公式；可确认的是与常见定义不同，不可据此断言论文Table6绝对分数、排名或作者约定错误。
2. **跨任务输入暴露**：原参考脚本先从同一record全集生成coarse预训练manifest，再独立生成fine任务train/val/test。用另一组明确命名为SYNTHETIC_REVIEW的400个合成ID，独立调用未修改原函数/default seed42，重现pretrain240、fine test40、交集22；同coarse协议test32与pretrain交集0。这个结果是参考管线允许transductive input exposure的反例；不是已发布HF真实数据重叠证据，也不是监督fine标签泄漏或论文失效证明。论文明确说预训练只用coarse类别、不用fine labels；是否要求全部raw-flow跨任务inductive互斥和实际发布协议仍Unknown。

## 来源与运行核对

原始tracked文件逐项SHA256与保存清单一致，上游Git状态为空。原probe及独审轻量probe均exit0，只有指标函数/数据划分算术，约1秒整个进程walltime不能当作模型推理性能。没有改指标定义、改划分、应用上游补丁或下载未授权资源。论文与2024同family旧稿、最终TMLR可读性和出版日的Unknown边界在报告保留。

独立数值、caption、源码hash数和矩阵hash见 `independent_review.json`，实际轻量核对命令与stdout见 `logs/lens/independent_review_probe.{json,log}`。没有发现需要修改主报告的遗留项；主模型完整任务/基线/消融/fuzzing、原始数据划分/权重与所有论文指标复现仍未建立。
