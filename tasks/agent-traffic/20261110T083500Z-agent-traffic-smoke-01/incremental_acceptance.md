# 增量与恢复验收证据

批次 `20261110-agent-traffic-smoke-01`，2026-11-10。下表摘录原始试跑工具返回中的命令、预期和实际结果。摘录省略本机路径，保留原输出标记和受控退出码。逐步执行时间为 `Unknown`。

原试跑使用 Python `3.12.14` 在隔离目录执行临时验收脚本 `run_harness.py`。该脚本属于本批试跑，独立于上游 `codex-literature-workflow@84b7fff758271db15175e7e02781df00446a8d8c`。原试跑后的完整文件回读文本的 SHA-256 为 `d66980a9e32f26e33ca1571780acc520837c3a2df53d1a659bc1373cfdbb9a32`，用于标识这次试跑的脚本版本。原临时目录已清理，当前归档保留逐项结果摘录与脚本指纹。归档状态为 **Partially Verified**，范围为原始记录中的逐项观察。

| 验收项 | 原命令或阶段 | 预期结果 | 原试跑实际结果 |
| --- | --- | --- | --- |
| 同批重跑 | 第二次 `ingest` | 同一 run ID 返回重复，跳过新增产物 | 退出 0，`ingest=duplicate run_id=20261110-agent-traffic-smoke-01 no_additional_artifacts` |
| DOI 与 arXiv ID | `verify-next-batch` | 相同版本分别用 DOI 和带版本 arXiv URL 匹配，均跳过 | `duplicate_by_doi=skip`、`duplicate_by_arxiv_id=skip` |
| 公开版本更新 | `verify-next-batch` | 同一论文由 v2 更新到 v3，识别为版本更新 | `public_revision_update={"from":2,"to":3}`。[版本与获取记录](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/sources.md) |
| 探针检查点续跑 | 首次 `ingest`，随后 `resume` | 探针后受控退出，恢复时跳过下载和探针 | 首次受控退出 75，`checkpoint=probed`。恢复退出 0，`resume=probed->artifacts-ready skipped_download_and_probe=true` |
| 模拟失败后重试 | `simulate-upload-failure`，随后 `retry-preview` | 保留五件产物，按相同 run ID 和哈希重试 | 模拟失败退出 75，`archive_upload=simulated_failure retained=5`。重试退出 0，`retry=verified_same_run_and_hashes files=5 run_id=20261110-agent-traffic-smoke-01` |
| 归档与开放 PR 夹具 | `verify-next-batch` | 归档夹具跳过，开放 PR 夹具复用 | `next_batch_archived_fixture.action=skip-archived`、`next_batch_open_pr_fixture.action=reuse-existing-pr` |

真实推送后的开放 PR 重放是后续独立验收。它从 PR 的远端提交读取来源清单，匹配 DOI 与 arXiv ID，判定 `reuse-existing-pr`。上表中的模拟上传失败和 PR 夹具只对应原始隔离试跑。[执行记录](execution_log.md) · [PR #2](https://github.com/old111down/codex_cloud/pull/2)
