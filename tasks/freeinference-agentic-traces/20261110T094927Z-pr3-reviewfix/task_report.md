# PR #3 评审修复报告

本轮三个P2修复及回归状态为 **Verified**，范围限审计工具；首轮论文状态仍为 **Partially Verified**。

Task ID：`20261110T094927Z-pr3-reviewfix`；开始UTC：2026-11-10T09:49:27Z；报告封版UTC：2026-11-10T10:12:11Z。原研究T0与三小时截止不重置。用户要求续改PR #3，因此保留原分支，新run记录修复关系与验证，不再创建PR或合并。

1. 下载：固定revision元数据自动初始化；selected→full及部分目录经哈希核对后复用。已有完整目录也重新核验；LFS SHA-256、非LFS Git blob及manifest绑定失败时保留证据，不静默覆盖。使用本地小型HTTP惰性字节验证，未重新下载8.37GB。
2. 导出：整批路径/内容验证、净化和扫描拒绝之前不写目标树或两个manifest。通过后staging，逐文件原子替换，公开manifest最后、本地receipt随后；不是所有I/O错误的跨文件事务。
3. 复核：原28项规则保持，任何失败都保存Failed报告并非零退出；缺失/损坏/不可序列化输入同样失败。论文已确认的数值/方法差异保留，不能与一致性失败混淆。

最终独立公开副本迁移回归 **44通过、0失败、0错误、0跳过**；移除私有fixture环境覆盖，完整保留仓库目录层级，只复制公开归档和临时夹具。[汇总](reports/relocated_regression_summary.json)、[日志](logs/relocated_regression.log)。默认CLI numbers是明确标注的最小合成片段，不代表完整绘图结果验证；真实旧聚合另行只读复核28项通过，见[saved recheck](reports/saved_evidence_recheck.json)。

原版基线失败、初版/最终成功及独立边界验证分别保存于logs与三个修复说明。根运行器首次flatten目录导致15个定位失败，已保留layout-error记录并修复；先前38项通过是早期scanner版本快照，最终以上述新结果及其源SHA为准。没有把中途失败隐去。

原206个文件中，仅声明的7个文件允许修订；另新增一个下载helper。其余 **199个文件逐字节不变**，含全部82份历史运行日志；原metadata所有字段值保留，只新增修订关系和历史哈希范围。[变更记录](reports/change_inventory.json)、[独立保全](reports/independent_archive_preservation.json)。原始科学结论、模型/数据/上游代码和数值对照不因本轮工具修复而升级。

已知限制：没有重复真实全量网络下载；hardlink要求同文件系统支持；未保证断电/并发导出的全批回滚；secret pattern不是完整安全证明；原论文的私有输入、意图/95%重建验证与全16周缓存独立重算仍Unknown或未完成。

源码基线：`old111down/codex_cloud@34678ab6d88546fcc3d038706a38b41afbbba73d`；作者版本仍为`2b795dbf5eac490a7c081906fdce6cc7a184b7ef`。实际命令见[execution_log.md](execution_log.md)，详细修复见[README](README.md)，公开范围见[清单](reports/publication_manifest.json)。不上传原始Trace、PCAP、完整第三方源码、环境或凭据。最终上传SHA在PR描述和回复中核对，避免提交自引用。
