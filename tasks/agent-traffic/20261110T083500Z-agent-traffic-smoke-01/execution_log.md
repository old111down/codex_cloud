# 执行记录

此文件整理原批次的已知执行证据。命令中的本机目录以相对路径或角色表示。没有留存的精确 UTC 起止时刻和退出码记为 `Unknown`。表中的 `python3` 代表已验证的 Python `3.12.14` 解释器，预检通过 `PATH` 加载已验证的 PDF 渲染入口。

| 阶段 | 实际执行入口 | cwd 角色 | UTC 时间 | 退出状态与证据 |
| --- | --- | --- | --- | --- |
| 主机与工作区核对 | `uname -sm`、`pwd -P` | 指定工作区 | Unknown | 0，Darwin arm64 |
| 工作流预检复测 | `python3 -B scripts/env_check.py --json --strict` | 上游工作流检出目录 | `2026-11-10T10:02:47Z` 至 `2026-11-10T10:02:48Z` | 0，Python `3.12.14`，`core_ready=true`、`pdf_render_ready=true`。原试跑在指定工作区通过上游脚本的绝对路径运行，最小 PATH 初检曾失败。 |
| 控制目录 | `python3 -B <upstream-checkout>/scripts/init_workspace.py --root <isolated-controller>` | 指定工作区 | Unknown | 0，控制目录生成 |
| 检索与全文获取 | Tavily 和学术检索，公开 arXiv PDF HTTP GET | 公开来源检索与试跑目录 | Unknown | v2/v3 PDF 均 HTTP 200。[检索式与版本](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/sources.md) |
| PDF 全文探针 | `python3 -B <upstream-checkout>/scripts/pdf_probe.py 2606.07150v3.pdf --pages 1-23 --no-render --out probe` | 隔离研究目录 | Unknown | 0，全文文本通过。 |
| PDF 选页渲染 | `python3 -B <upstream-checkout>/scripts/pdf_probe.py 2606.07150v3.pdf --pages 10,11,18,19 --out visual-probe` | 隔离研究目录 | Unknown | 0，选页图像通过。[证据页](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/note.md) |
| 模拟非交互分析 | `codex -a never exec -s read-only --ephemeral --json` | 隔离试跑目录 | Unknown | 0，收到 `turn.completed` 和中文证据复核 |
| 阶段恢复 | `run_harness.py ingest` → `resume` → `ingest` | 隔离试跑目录 | Unknown | 受控退出 75 后恢复成功，同批重复输入退出 0 并跳过。[原试跑结果](incremental_acceptance.md) |
| 归档重试测试 | `run_harness.py simulate-upload-failure` → `retry-preview` → `verify-next-batch` | 隔离试跑目录 | Unknown | 模拟失败退出 75。随后验证同批哈希、版本升级与去重。[原试跑结果](incremental_acceptance.md) |
| 归档预览日志 | `run.log` 写入 | 隔离归档目录 | `2026-11-10T08:35:00Z` | [原阶段日志](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/run.log) |
| 原附件提交 | `git commit` | 隔离归档克隆 | `2026-11-10T08:50:41Z` | 0，[提交](https://github.com/old111down/codex_cloud/commit/36001c487d496c0896b3fedf0aa94f18f00388ad) |
| 推送与建 PR | `git push`、`git ls-remote`、`gh pr create` | 隔离归档克隆 | PR 创建于 `2026-11-10T08:51:58Z` | 0，核对远端分支与原附件提交。[PR #2](https://github.com/old111down/codex_cloud/pull/2) |
| 实况重放 | `gh pr list`、`verify-live-pr.py 2` | 隔离试跑目录 | Unknown | 首次远端清单读取超时退出 1，有限重试退出 0。判定 `reuse-existing-pr`，跳过重复调研和建 PR |

v3 PDF 的 SHA-256 记录在[来源清单附件](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/manifest.json)。历史事件时间来自原日志、Git 提交或 GitHub PR 元数据。工作流预检复测时间由本轮执行记录。增量和恢复的结果来自原试跑，临时验收脚本版本按原会话完整回读的 SHA-256 标识。[脚本指纹](incremental_acceptance.md)
