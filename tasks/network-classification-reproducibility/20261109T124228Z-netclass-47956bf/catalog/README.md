# 候选记录维护

追加任务的当前统一目录是 `papers.json` / `papers.csv`，由 `scripts/build_autonomous_tables.py` 从基线、`round2/`初筛、详细metadata与实际日志重建。37条记录按family去重为35个主范围论文族，另有1个web预测负例；会议—期刊扩展不重复计算独立研究。同名错链、Unknown关联和版本日期依据均保留。`year`可能表示审计修订版，须结合`first_publication_year/year_basis/date_basis`，不能把2026修订当作首次发表。

`reports/audit_assessments.json`是人工审查后的A/B/C边界，汇总时覆盖旧的候选阶段运行描述。重建汇总不会自动验证论文或运行代码，也不会从exit0推断算法成功。原始结构化命令与逐论文摘要共同生成 `reports/reproduction_results.csv`；未结构化的首轮setup命令仍见原报告/日志。

`candidates.json` / `candidates.csv` 为首轮统一目录，共11篇。原始非试点记录分为 `offline_candidates.json`（4篇）和 `network_candidates.json`（4篇）；三个试点的权威记录为 `papers/<id>/metadata.json`。

修改与审查来源记录后执行 `python scripts/build_catalog.py`，再运行结构检查。脚本只统一字段/时间格式，不检索、不补齐未知事实；候选被标“关联已验证”必须先人工核验明确论文链接或作者证据。证据位于 `evidence/candidates/` 和各试点目录，包含原始API、固定SHA README、论文/文章页及失败访问记录。

`last_commit_utc`是固定分支HEAD的提交时间；`repository_pushed_at`可能属于其他分支；`repository_updated_at`包含star/元数据活动，不是源码更新时间。全SHA与检索日同时保留；不存在的DOI、许可证、原始数据访问、GPU最小资源等一律Unknown。候选目录不表示代码/数据/权重可完整执行。
