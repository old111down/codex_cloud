# 隔离补丁说明

上游固定版本为 `2b795dbf5eac490a7c081906fdce6cc7a184b7ef`，未修改上游工作区。

`0001-report-empty-benchmark-scope.patch` 属于**运行结果报告错误修复**。原版在只有 Aug30 公开周、缺少 SWE-Bench 群体时，绘图进程 exit0，但输出四个 `median_benchmark=NaN`、四个 `ratio=NaN`，以及全零 benchmark trajectory。补丁在比较群体为空时显式跳过整个 benchmark comparison section，并保留原因。

该补丁只在 `private/runtime/empty_scope_patch_source` 的源码副本上执行。`scripts/prepare_official_workspaces.py --empty-scope-patch` 可重建副本；`scripts/check_empty_scope_patch.py` 验证这个缺失 SWE 的分支，实际 exit0，见 `logs/official_checks/empty_scope_patch_check.json`。

等价性影响：两个群体均非空时，原统计路径按代码检查保持一致；该分支没有在补丁版上重跑全16周。缺少任一群体时，补丁也会跳过仍可单独绘制的人类 trajectory，属于保守输出策略。补丁没有修改样本、标签、cache 算法或价格模型。论文 Table6 batch mix 和 provider D 的差异尚无证据确定正确修复，未修改算法来强行匹配论文。
