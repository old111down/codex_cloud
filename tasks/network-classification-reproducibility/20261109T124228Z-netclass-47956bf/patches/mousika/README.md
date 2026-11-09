# Mousika 独立补丁

所有 upstream 文件保持原样。补丁应用与验证只发生在临时副本。

| 补丁 | 基线 | 分类 | 原因与等价性影响 | 已执行验证 |
|---|---|---|---|---|
| 0001 | main `76c9db9b4200a7c591bd1e9476ba5ab44a467512` | 运行错误修复 | converter 接受整值十进制分类标签（如 Tree 导出的1.0）；不改变整数标签规则的 mask/value/class。拒绝非整值及非有限值。对未测的规则文件等价性 Unknown。 | `logs/mousika/parser_patch_smoke.log`：整数/整值十进制接受，小数/非有限拒绝，五套作者规则输出相同 |
| 0002 | Mousikav2 `3326869d4c1f25768a9304a2df672e82f38972f9` | 算法逻辑修改 | 修正右节点Gini中缺失的类计数平方，与论文Eq5一致；改变分裂评分，实验等价性 Unknown，不能混入原版结果。保留CRLF。 | `logs/mousika/v2_gini_counterexample.log`：8行反例对照独立Gini公式；仅单反例验证，不代表论文指标验证 |

复查命令（从审计仓库根目录）：

```sh
.conda/mousika/bin/python scripts/mousika/patch_smoke.py
.conda/mousika/bin/python scripts/mousika/v2_gini_counterexample.py
```

第二项最初生成的LF补丁不能直接匹配上游CRLF，失败日志保留为 `v2_gini_counterexample_crlf_failure.*`；随后以保留CRLF的补丁和 `patch --binary` 验证通过。没有删除或覆盖这次失败证据。
