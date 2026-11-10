# P2：一致性审查状态与退出码修复

已修复旧审计脚本可能把失败检查输出为 Verified 并退出0的问题。改动仅涉及归档旧run的 `scripts/review_reproduction_evidence.py`，以及本新run的回归测试、说明与日志；原始科学结果和运行日志没有改写，没有重新执行数据处理、模型、图表或缓存模拟。

## 问题与改动

旧实现虽然逐项记录了 `checks[].status=Failed`，但顶层 `status` 恒为“Verified consistency checks…”且脚本没有非零退出；调用方据此可能把失败的聚合一致性检查当成通过。输入缺失或JSON损坏时又直接抛错，不能留下结构化失败报告。

现在只有一致性审查完成且通过时才输出 `status=Verified`、exit0。任一原有检查失败，或附加完整周审查的顶层/单周/子检查状态或失败计数为Failed，都会先写出 `status=Failed` 的报告，再exit1。附加审查为Unknown/Partially Verified时不会提升为Verified，也返回非零。原有28项科学检查的总体、数值和比较规则保持不变；Table6 Batch Mix等已确认论文差异继续作为科学发现保存，不会被当成一致性检查失败。

新增 `main`、`--root` 和 `--output`，便于读取旧证据、把新复核报告写入新run。输入缺失、JSON损坏、结构不适用及非标准NaN/Infinity JSON常量会生成带 `input_errors` 的Failed报告；如果输出本身无法写入，则返回非零并报告持久化失败，不声明通过。

## 实际回归结果

测试文件：[test_review_status.py](../scripts/test_review_status.py)。**默认只需要公开checkout和pytest**：复制旧run已经归档的聚合JSON、CSV及选定日志，并将目标脚本的相同字节版本复制到pytest临时目录。公开归档未包含完整CLI `numbers.json`，所以测试在临时目录构造带 `_regression_fixture.synthetic=true` 标记的最小片段，只含由公开Top-level计数生成的 `dataset.trace_summary`。这用于测试状态/退出码传播，**不验证完整绘图数值或缓存结果**。每次CLI只写临时输出；没有使用原始Trace行、Request/Session ID、PCAP、数据集或模型。

显式设置 `FREEINFERENCE_EVIDENCE_ROOT` 才会使用该外部目录的真实saved CLI聚合；默认不依赖 `/workspace/freeinference-audit` 或任何私有运行文件。`FREEINFERENCE_REVIEW_SCRIPT` 只供基线复核指定脚本；正常公开测试不需要此变量。

11项测试覆盖：真实saved聚合正例、Request计数扰动、manifest布尔值为false、多项失败累积、完整周审查顶层/单周/失败计数传播、必需输入缺失、JSON损坏、无效结构，以及保留真实论文差异仍通过一致性正例。

| 版本 | 实际结果 | 证据 |
|---|---|---|
| 公开默认fixture、修复前基线 `34678ab` | 2通过、9失败，pytest exit1 | [public-before.log](../logs/review_regression.public-before.log)、[命令与版本哈希](../logs/review_regression.public-before.json) |
| 公开默认fixture、修复后 | 11通过，pytest exit0 | [public-after.log](../logs/review_regression.public-after.log)、[命令与版本哈希](../logs/review_regression.public-after.json) |
| 较早的真实saved聚合fixture、修复前 | 2通过、9失败，pytest exit1 | [before.log](../logs/review_regression.before.log)、[元数据](../logs/review_regression.before.json) |
| 较早的真实saved聚合fixture、修复后 | 11通过，pytest exit0 | [after.log](../logs/review_regression.after.log)、[元数据](../logs/review_regression.after.json) |

执行时设置 `PYTHONDONTWRITEBYTECODE=1`，并用 `pytest -p no:cacheprovider`，没有在公开树创建pycache或pytest cache。

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider -q \
  tasks/freeinference-agentic-traces/20261110T094927Z-pr3-reviewfix/scripts/test_review_status.py
```

公开基线通过 `git show 34678ab:<旧run脚本路径>` 读取到临时文件，未改写工作区或Git历史；新日志保留原有日志，没有覆盖。

**独立的真实saved证据正例：** 另外直接调用修复后的真实归档脚本，读取旧私有工作区的saved聚合，将结果写入本新run的 [saved_evidence_recheck.json](saved_evidence_recheck.json)：exit0、28项Verified、0项Failed。该复核没有重跑科学实验；四份原科学输入/报告在调用前后的SHA256均相同。[命令、时间和哈希](../logs/review_regression.saved-evidence.json)、[输出](../logs/review_regression.saved-evidence.log)。

## 适用边界

Verified仍只表示脚本列出的聚合、范围与输出一致性检查通过，不代表原始采集、标注准确率、论文全部结果或网络分类已验证。现有科学发现及未验证内容保持原结论。此次修复不提交Git、不推送、不发送PR评论；由父任务统一审查归档。
