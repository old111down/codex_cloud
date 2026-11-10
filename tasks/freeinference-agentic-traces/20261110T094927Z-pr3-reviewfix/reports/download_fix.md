# P2：固定版本下载工作流修复

**Verified：本地小型 HTTP 回归通过，未重新下载真实数据。** 修改的是上一轮归档的两个审计下载脚本，未修改作者仓库、旧实验结果、数据 manifest 或私有研究工作区。

原 `download_selected_week.py` 在干净目录直接读取尚不存在的 `private/evidence/hf_repo.json`，导致 `FileNotFoundError`。手动准备 metadata 后，selected 只创建 requests 文件；随后 full 脚本试图用 staging 目录替换非空目标目录，导致目录发布失败。原 full 脚本也仅凭五个文件存在就跳过，不能识别损坏的已有表或错误 manifest 绑定。

两个入口现在共用旧 run 下新增的 `scripts/pinned_release_download.py`：

- 从固定 HF revision `bb26cf72c9c20f2b05f765d88548156a74d3c253` 的 HTTPS API 初始化 metadata，并拒绝不同 revision 的缓存。
- LFS 文件核对固定 metadata 中的 SHA-256；非 LFS 的 `manifest.json`、`tables.json` 核对 Git blob SHA-1（包含 Git blob 头），避免只检查文件大小。完整周还核验 tables→manifest SHA-256 绑定及三张表的 release SHA-256。
- 验证后复用已有 selected/staging 文件；通过同一私有文件系统上的 hardlink 合并缺失项，避免复制大型 requests 文件，也不再替换非空目录。manifest 最后发布。完整目录跳过前同样重新校验全部内容。
- 已有数据不匹配时停止并保留原件，不静默覆盖。新下载使用独立 `.partial` 文件，失败时保留在私有目录，不发布为有效文件；重跑不把该文件当已验证缓存。
- 保留两个下载线程和5GiB磁盘预留；预算包含小型 metadata，逐块写入也检查剩余空间。响应超过固定文件大小会停止。数据和传输记录继续只写入 `private/`。

selected 仍是单文件传输探针，不冒充完整可读取周；运行 full 后才补齐三表及 metadata。成功传输记录为追加历史，其中 selected 使用 `selected_download_records.json`，避免覆盖旧的单次记录。

测试位于 [test_download_workflow.py](../scripts/test_download_workflow.py)。它将入口脚本复制到临时干净 run，通过本地 HTTP server 提供仿照官方结构的 metadata、真实 SHA 和少量惰性字节；只重定向网络传输，不替换下载/校验函数。fixtures 不是真实 Parquet，不执行或包含 Trace 内容，也不提交临时文件。

| 阶段 | 实际结果 | 证据 |
|---|---|---|
| 修改前10项回归 | 9 failed / 1 passed，exit1；重现 bootstrap、partial目录和盲跳过问题 | [before.log](../logs/download_regression_before.log)、[before.json](../logs/download_regression_before.json) |
| 修复后相同10项 | 10 passed，exit0 | [after.log](../logs/download_regression_after.log)、[after.json](../logs/download_regression_after.json) |
| 增加同长度非LFS损坏、坏HTTP响应边界后 | 12 passed，exit0，6.42s进程耗时 | [final.log](../logs/download_regression_final.log)、[final.json](../logs/download_regression_final.json) |

覆盖干净 selected/full、selected→full、有效 partial staging 复用、幂等无二次传输、完成目录重新校验、已有/暂存损坏内容保留、manifest 绑定、错误 revision、低磁盘预留，以及非LFS同长度损坏和错误HTTP内容不发布。metadata日志记录各阶段源码 SHA-256，未将修复后测试冒充原版成功。

实际命令（cwd：归档仓库根目录）：

```bash
PYTHONDONTWRITEBYTECODE=1 /workspace/freeinference-audit/.conda/freeinference/bin/python -m pytest -q -p no:cacheprovider tasks/freeinference-agentic-traces/20261110T094927Z-pr3-reviewfix/scripts/test_download_workflow.py
```

这是下载和归档工具的运行错误修复，不改变数据 revision、数据字节、论文算法或统计口径。本次没有重跑8GB真实下载；真实网络限速、跨文件系统 hardlink、多个独立下载进程同时运行等未验证。hardlink 不支持时会显式失败，不自动采用未经说明的大文件复制。公开日志只含测试输出、路径和版本哈希；没有凭据、签名下载URL或真实 Trace 记录。
