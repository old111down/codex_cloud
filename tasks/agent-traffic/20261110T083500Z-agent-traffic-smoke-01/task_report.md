# Agent 网络流量文献调研与归档验收

## 任务标识与范围

| 字段 | 值 |
| --- | --- |
| Task ID | `agent-traffic:20261110T083500Z-agent-traffic-smoke-01` |
| Task Slug | `agent-traffic` |
| Run ID | `20261110T083500Z-agent-traffic-smoke-01` |
| Start Time (UTC) | Unknown |
| End Time (UTC) | Unknown |
| 产物记录时间 (UTC) | `2026-11-10T08:35:00Z`，来自原批次日志 |
| Objective | 验收一批公开 Agent 网络流量文献的检索、全文阅读、增量去重、检查点续跑、GitHub PR 归档和同批重放。 |
| Related Runs | 原文献批次 `20261110-agent-traffic-smoke-01` |
| Final Status | **Verified**，单篇公开全文的证据笔记、真实开放 PR 归档及同批重放。 |

本次标准记录补录回应了 [PR #2 的索引与任务记录反馈](https://github.com/old111down/codex_cloud/pull/2#issuecomment-6764104703)，沿用原批次和原 PR。

## 来源仓库与版本

| 官方来源 | 分支或版本 | 完整提交 | 许可或访问 | 证据 |
| --- | --- | --- | --- | --- |
| [codex-literature-workflow](https://github.com/ParkerGong/codex-literature-workflow) | `main`，v1.0.0 | `84b7fff758271db15175e7e02781df00446a8d8c` | MIT | [固定版本](https://github.com/ParkerGong/codex-literature-workflow/tree/84b7fff758271db15175e7e02781df00446a8d8c) |
| [归档仓库](https://github.com/old111down/codex_cloud) | `main`，原预览基线 | `fc58e1e33b49666469c47f1231b55105b8508c42` | 公开可读 | [基线提交](https://github.com/old111down/codex_cloud/commit/fc58e1e33b49666469c47f1231b55105b8508c42) |

## 运行环境与命令

原试跑在 Mac `Darwin arm64` 上进行，使用 Codex 自带 Python `3.12.14`、`pypdf` 和 `pdftoppm`。现有 Codex、Tavily 与 GitHub 认证通过模拟非交互环境检查。资源配额和实际后台调度环境为 `Unknown`。详见[执行记录](execution_log.md)。

## 已完成工作

| 工作 | 状态 | 证据与范围 |
| --- | --- | --- |
| 公开文献筛选 | Verified | 筛选两篇，全文处理 arXiv:2606.07150v3，第二篇查阅官方摘要。[来源清单](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/sources.md) |
| 全文证据笔记 | Verified | 提取 23 个物理页，选页渲染并按页码记录方法和局限。[笔记](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/note.md) |
| 增量和恢复 | Partially Verified | DOI/arXiv 去重、v2→v3 更新、检查点续跑和模拟重试来自原始试跑记录。逐项预期、实际结果与临时脚本的 SHA-256 已记录。[验收证据](incremental_acceptance.md) |
| 真实归档和重放 | Verified | 原 5 件附件提交 `36001c487d496c0896b3fedf0aa94f18f00388ad` 已推送。PR 开放后，同批重放从其远端清单命中 DOI 和 arXiv ID，返回 `reuse-existing-pr`。[PR #2](https://github.com/old111down/codex_cloud/pull/2) |

## 失败与修复

| 尝试 | 观察 | 处理与复测 |
| --- | --- | --- |
| 最小非交互 PATH | 缺少渲染入口，严格预检失败 | 显式指定已验证的解释器和渲染路径，严格预检退出 0。 |
| 首次读取 PR 远端清单 | GET 超过 20 秒后退出 1 | 调整只读请求超时并加入有限重试，随后读取清单及去重判定成功。 |

受控退出和模拟上传失败的逐项结果来自[原试跑记录摘录](incremental_acceptance.md)。预检相对命令已从固定版本的上游检出目录复测，退出 0 且 `core_ready=true`。[执行记录](execution_log.md)

## 重要发现与未验证项

作者报告真实 A2A 分类准确率为 0.67，按能力组合留出后为 0.18。笔记分别记录了作者结论、对当前项目的推断和待验证假设。[原文第 18 页](https://arxiv.org/pdf/2606.07150v3#page=18)

论文实验复现、跨部署和旁路 PCAP 泛化、真实无人值守调度仍为 **Unknown**。

## 产物与公开范围

- [note.md](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/note.md) · 中文文献笔记及页码依据
- [sources.md](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/sources.md) · 检索式、获取状态、筛选与版本对照
- [manifest.json](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/manifest.json) · 文献标识、版本、证据页和公开 PDF 哈希
- [increment.md](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/increment.md) · 增量摘要
- [run.log](../../../literature/agent-traffic/20261110-agent-traffic-smoke-01/run.log) · 原始归档预览阶段的公开日志

上述文献附件沿用原提交，新增[增量与恢复验收证据](incremental_acceptance.md)记录脱敏摘录。哈希见[元数据](metadata.json)。本次新增记录只收录原始分析和公开题录，执行命令按相对位置和工具名整理。全文 PDF、页图、全文文本、未筛选的日志、认证信息及本机路径保留在公开归档范围之外。

## 最终状态

**Verified**。已完成单篇公开文献试跑、真实 PR 归档及同批去重。原文献分支为 `literature/agent-traffic/20261110-agent-traffic-smoke-01`，原附件提交为 [`36001c4`](https://github.com/old111down/codex_cloud/commit/36001c487d496c0896b3fedf0aa94f18f00388ad)。本标准记录与文献附件在 [PR #2](https://github.com/old111down/codex_cloud/pull/2) 中一并评审。
