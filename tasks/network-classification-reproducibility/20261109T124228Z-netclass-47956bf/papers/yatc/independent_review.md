> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# YaTC 独立复核

2026-11-09 UTC；核对固定 `main@a220b75f8365acaf63dbac7df87aaaa357698b85`。复核范围为本轮report、覆盖矩阵、关键原源码（MFR、训练/评估engine、fine-tune数据/加载/主循环）、两项隔离patch、合成harness与原始失败/成功日志。未重新运行模型，也未声称独立读到了被拒绝访问的全文。原始tracked文件逐项SHA256与source_manifest相符，上游Git状态为空。

## 结论

在上述范围内，最终报告没有已知实质夸大。只能支持**兼容辅助的合成组件R1**；论文全文、全部图表、第五数据集、原真实数据/权重/划分与原指标覆盖均Unknown。不能把“已读全部公开源码”转换成“完整审读/覆盖论文全部实验”。

- `PAPER-FULL`明确记录Method/Implementation/Evaluation/Appendix和编号图表Unknown；四个数据行明确来自README而不是杜撰论文章节。官方摘要称五数据集，差异未强行补齐。
- 原README预训练/微调日志确实在SummaryWriter导入处失败，单独timm导入又显示`container_abcs`缺失。补丁1/别名bootstrap只解决兼容导入，随后仍缺真实数据。报告没有把这一前进等同于原训练成功，也把protobuf初次选择冲突归为审计方环境选择。
- 原CPU engine在`engine.py:148`无条件`torch.cuda.synchronize()`失败；补丁2仅保护两处训练/预训练同步，合成单batch日志成功。完整CPU/GPU训练、分布式路径及数值/性能等价性仍未验证。
- `engine.py:209`确用`average='weighted'`，222–224行键名为macro。独立以标准库按10条给定真值/预测重算：weighted P/R/F1为0.36/0.60/0.45；macro为0.12/0.20/0.15，与归档结果一致。它证明实现键名语义不符，不证明论文报告也错误。
- `data_process.py:20–23`保留IPv4包字节；合成PCAP结果证实IP和端口字段进入MFR。原外部PCAP可能先做匿名化，故报告只标潜在捷径风险，未宣称真实训练测试泄漏。
- `fine-tune.py`每epoch评估test目录并打印max、没有模型持久化调用，以及`--eval`跳过`--finetune`加载的描述均有源码支持。论文实际采用何种结果选择和归档协议Unknown。

发现的一处证据定位已由主审计者修正：`EVAL-SELECTION`原引用165–166实际上是device/seed附近；现已改为151–152（train/test目录）、173–174（构建数据集）、308–326（epoch评估/max）。已重读修正后的矩阵。未改动对方源文件。

复核数值和版本元信息见 `independent_review.json`。模型参数量、随机loss、mask数量和函数walltime只按原日志作为有限Smoke观察审查，没有独立重新计算，更不当成论文精度或性能复现。
