# ETC 编码补丁说明

基线：`nds-group/ETC_NOMS_2024@52de99ad76d9eff2f64a0fa28df0500e423b58b2`。上游 checkout 保持 pristine；补丁只应用到 `papers/etc_noms_2024/runtime-artifacts/patched/` 的独立运行副本，按编号顺序应用。

| 补丁 | 分类 | 原因 | 等价性及限制 |
|---|---|---|---|
| `0001-unique-voting-mode.patch` | 环境兼容性修复 | Python3.8起 `statistics.mode` 对并列众数不抛异常，导致7776票表项超过P4声明容量5256并改变360个有效决策 | 显式只为唯一众数生成表项，其他输入走上游P4 `class0` 默认动作；6^5输入与随附表完全一致。不是对RF算法提出新投票规则，也不证明与sklearn预测相同。 |
| `0002-feature-range-domains.patch` | 数据处理修复（RF→P4编码配置） | generator末区间65535与P4压缩IAT的15/8位键域不符 | 末值匹配固定P4的15/16/8/16位域及随附表项；不改变训练数据/模型参数。仅适用于该固定NIMS模型，其他P4配置必须重新确定位宽。BFRT实际装表行为 Unknown。 |

首次仅应用补丁1后的全表对照失败日志保留在 `logs/etc_noms_2024/table_validation.log`，以免隐藏发现过程。两补丁后的复验为 `table_validation_v2.log`，对应 `papers/etc_noms_2024/table_validation_metrics.json`。测试比较AST解析后的所有`add_with_`表项参数集合，并穷举7776种票输入，没有执行生成脚本内的BFRT API。

未修改端口配置、模型结构、标签、训练过程、数据切分或P4源码。未修复静态报告中列出的其他离线流程问题；这些问题的实验影响仍为 Unknown。
