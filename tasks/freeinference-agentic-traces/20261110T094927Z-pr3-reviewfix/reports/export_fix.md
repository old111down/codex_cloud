# Exporter 批次拒绝安全修复

**状态：Verified，范围仅限本次回归和导出安全逻辑。** 未重新运行论文实验、下载原始数据或真实导出旧任务，也未修改旧任务的 manifest、审核时间、科学报告或私有原证据。

## 问题与修复

原 `scripts/export_reviewed_archive.py` 先创建公开目标目录，再逐文件扫描并写入，直到整批处理结束才因 credential pattern 抛异常。因此后序文件被拒绝时，前序文件及被拒绝内容已经可能写入公开树，旧的 approved 文件也可能被覆盖。

现在先完成完全只读的整批 preflight：

1. 读取并验证 run metadata、两个 allowlist 的类型和全部相对路径；拒绝越界、保留 manifest 输入、敏感文件名及 source/target 重叠。
2. 使用不跟随 symlink 的目录描述符读取普通源文件，检查大小、二进制与 UTF8，拒绝源路径任何 symlink 祖先或叶节点。
3. 仅在内存中净化允许的 Conda build URL，再扫描最终公开内容；同时校验全部目标路径类型与 symlink 祖先/叶，以及可再生成的 source receipt 路径。
4. 整批通过后才在目标 worktree 中建立临时 staging，并先完整写入所有已审核字节与 manifest。随后通过 `O_NOFOLLOW` 目录描述符和逐文件 `os.replace` 发布；**公开 manifest 最后发布**。
5. 成功后原子更新 source `reports/publication_manifest.json`，保留既有构建流程所需的审核索引。它是可再生成 receipt；源科学文件及净化前原内容不修改。临时 staging 清理掉。

按 root 的依赖要求，将新增自有 helper `scripts/pinned_release_download.py` 加入显式导出列表，没有改动历史 `data_publication_review.json` 或其哈希/时间。

## 实际回归证据

测试为 `scripts/test_export_safety.py`，通过真实 `main()` 入口操作 `TemporaryDirectory` 中的独立 source/public fixture。拒绝检查对整棵临时树（目录、内容哈希、两个旧 manifest）做前后比较，断言不转储文件内容。没有在权威公开树或私有旧审计根运行导出。

| 版本 | UTC | pytest 结果 | 证据 |
|---|---|---|---|
| 原版，扩展17项 | 2026-11-10 10:03:55 | **15 failed / 2 passed，exit1** | `logs/export_regression.before_extended.json`、`.log` |
| 最终修复版，同17项 | 2026-11-10 10:04:18–10:04:19 | **17 passed，exit0** | `logs/export_regression.after_extended.json`、`.log` |

原版源 SHA256 为 `e186f8e86e261416fdd13ffca62a59a4b5adb05a0fcf94a64bbd357823d2ec10`。最终修复版测试时 SHA256 为 `23db96855f6de1ed0473d066a587b14d08d010a699db47e03a5e1dbf5f859d6e`；准确命令、解释器、退出码、源/测试SHA及时间见上述 JSON。扩展基线从只读 `git show HEAD` 获取原版，验证与首次基线SHA一致，仅在自动清理临时目录加载。使用 `PYTHONDONTWRITEBYTECODE=1` 和 `pytest -p no:cacheprovider`，未在公开树留下测试 cache。最初15项套件的原版13fail/2pass与初版修复15pass也分别保存在 `export_regression.before.*`、`after.*`，没有覆盖原始失败记录。

17项用例覆盖：后序 credential、缺文件、越界路径、超大、二进制、UTF8失败均不发布前序 good 文件、不覆盖旧内容；新目标不创建；allowlist 类型错误；源 symlink 祖先、目标 symlink 祖先及叶；run path 越界；manifest 不能作为输入；clean success 的 source/published SHA 与实际字节一致；净化后扫描通过且净化前原证据不变；带underscore分隔符的credential内容及文件名均被拒绝，异常不回显marker。GitHub/API pattern边界改为负向alnum，使underscore可作为分隔符，仍避免把正常单词内部的类似前缀当作独立值。

合成 credential marker 只在运行时拼接并写入自动清理的临时 fixture，没有真实凭据、持久 fixture 或 literal token。四份日志扫描均为 **0个 marker 输出/0次日志净化**；失败日志只记录 case、状态和不含内容的断言。

## 明确限制

这保证整批**验证、净化和扫描拒绝**时不写目标树或 source/public manifest，也先完成 staging 后才动正式目标。单个文件替换是原子的，但多个文件加两个 manifest 不是跨文件事务：磁盘故障、进程崩溃或并发导出仍可能造成部分替换；没有声称对所有 IO 故障回滚，也未新增跨进程锁。若 public manifest 发布成功而 source receipt 更新失败，公开文件可完整而本地 receipt 仍旧，调用会报错。

路径描述符操作针对当前 Linux 环境；pattern scan 仍不是对所有敏感内容的完备证明。本修复没有改变论文数值、许可判断或出版白名单的人工审核责任。
