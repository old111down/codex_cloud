# 需要优先复查的证据

这里区分已确认的源码/运行观察与原因解释。没有证据证明实验不当；版本、筛选或统计口径均可能影响差异，未定位的原因保留 Unknown。

1. **Table 6 batch mix 数值不一致（Verified 观察）。** 固定代码与全 16 周 Parquet重新计算 SameTool=64.0174%、Mixed=35.9826%；作者随仓库发布的 CSV 也为此值，PDF p6 Table 6 为71.3%/28.7%。按 request/call 的两种口径检查未解释纸面71.3%。原因 Unknown。见 `paper_metric_comparison.csv`、`reports/batching_denominator_check.json` 及官方检查日志。
2. **84.5% 的统计对象有差别（Verified 源码及运行）。** 论文称 requests，`paper/metrics/tools.py` 的宽度分布按 call rows 计算；84.4816% 是 call-weighted，request-weighted 单工具比例93.2316%。不影响所有其他结果，但不能复述为同一个概率。见上述分母检查与独立论文审查。
3. **Table 5 / Fig 5 有条件分母（Verified）。** 工具 Time/latency 只使用 single-call requests；Fail 仅在非空 outcome 内计算。不可把它解释为所有并行工具的单工具独立耗时，或所有工具的失败率。公开 gap 也未找到论文 p5 所述 RTT subtraction 的执行路径；上游私有处理是否已扣除 Unknown。
4. **重建与标签准确率不能独立验证（Partially Verified）。** 95% 是有显式 Session ID 子集上的一对一对应声明，不是全体准确率；验证材料未公开。Harness 的论文优先级与代码不同（论文 UA→system，代码 intro phrase→UA）。原始文本/UA 缺失，实际影响 Unknown。Human 集合要求至少2个 user turns、1个 tool-triggered turn，SWE只要求后者，跨群体比较应保留这一选择条件。
5. **Intent 重复标注缺关键输入（Unknown）。** Fig 16 的8类意图为 LLM few-shot 辅助标注；公开结构化表没有意图标签或正文，所用模型/完整prompt/人工一致性评估未找到。Tool category不等于这些意图。
6. **时间戳不是客户端真实网络边界（Verified当前源码；历史Unknown）。** 导出 `start=end-latency`。当前公开 Gateway 的 DB默认 NOW() 且异步入库，不能把 timestamp 当最后providerchunk，也不能将其直接与客户端包时间相减作为网络耗时。历史部署对应关系与日志排队延迟未验证。
7. **退出0可能仍缺对照组（Verified运行）。** 单周无SWE，官方入口产生8个NaN；全16周补齐后0NaN。独立补丁只改善空子集报告，未用于全量主结果。pytest收集0项，不能声称官方测试通过。
8. **完整缓存模拟与公开曲线重绘应分开（Verified运行范围）。** 全周模拟在审计120秒限时内未完成；3个真实Session小子集通过。Make复用作者缓存仿真材料，不是本轮独立全量仿真。
9. **数据质量异常数量很小，但解释未证实（Verified观察）。** 4条负工具gap（3batches），4条cached>prompt、共63tokens；供应商语义/归一化可能性只是推测。原始数据保留私有，公开仅聚合数值。

每项固定源码链接、PDF页码、分母和证据位置见 [独立论文复核](reports/independent_paper_review.md)、[数值对照](paper_metric_comparison.csv)、[Session审计](session_reconstruction.md) 与 [数据质量](reports/quality_findings.md)。论文中“Provider D在15分钟后median低于50%”的文字与当前 retention 曲线的独立检查仍待最终审查，不先断言模型标签互换或原因。
