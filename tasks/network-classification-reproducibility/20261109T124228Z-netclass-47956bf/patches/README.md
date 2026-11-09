# 隔离补丁登记

所有上游checkout保持原始固定SHA与干净Git状态；本目录补丁只在审计输出副本中尝试。补丁文件不表示作者认可或论文实验等价。

| 试点 | 补丁 | 类别 | 范围与等价性 |
| --- | --- | --- | --- |
| Mousika main | `0001-accept-integral-decimal-class-labels.patch` | 运行错误修复 | 将形如`1.0`的有限整值类别解析为整数；只涉及规则输出/转换接口，需与原样路径分别记录 |
| Mousika Mousikav2 | `0002-v2-correct-right-branch-gini.patch` | 算法逻辑修改 | 补足右子节点类别概率和的平方；会改变分裂目标，不能视作论文等价结果 |
| ETC_NOMS_2024 | `0001-unique-voting-mode.patch` | 环境兼容性修复 | 避免Python3.8后`statistics.mode`平票行为改变，恢复随附表的平票处理；仅与固定artifact做软件对照 |
| ETC_NOMS_2024 | `0002-feature-range-domains.patch` | 数据处理修复（RF→P4编码配置） | 按固定P4各feature键位宽设置末端区间；对固定模型静态验证，不构成P4编译或硬件证明 |
| LiM | 无 | 不适用 | 未静默改变采样、缩放、划分或模型参数 |
| ET-BERT | `0001-portable-confusion-output.patch`、`0002-import-classifier-module.patch` | 运行错误修复 | 结果输出位置和导入路径；合成案例41个权重张量等价，不改变损失/dropout |
| YaTC | `0001-original-dependency-import-compat.patch` | 环境兼容性修复 | 对历史依赖提供显式导入别名；原数据与模型结果仍Unknown |
| YaTC | `0002-guard-cuda-synchronization.patch` | 运行错误修复（CPU边界） | 仅CUDA设备同步；不证明CPU/GPU数值或性能等价 |
| LINC | `0001-small-batch-progress.patch` | 运行错误修复 | 修复日志取模0，不改变优化步骤 |
| LINC | `0002-cpu-export-simulator.patch` | 环境兼容性修复 | CPU导出/规则模拟；不覆盖完整增量或真实P4 |
| LINC | `0003-default-subspace-index.patch` | 算法逻辑修改 | 保留正确default bucket；局部反例通过，完整增量仍有条件越界 |

适用SHA、应用顺序、原样失败、补丁复验和未解决问题分别见 [Mousika登记](mousika/README.md)、[ETC登记](etc_noms_2024/README.md) 及逐论文报告。审计harness提取函数、选择notebook单元或归档指标也均在报告说明，不把它们冒充完整README/论文流程。

追加登记：[ET-BERT](et_bert/README.md)、[YaTC](yatc/README.md)、[LINC](linc/README.md)。共11个补丁，全部仅对隔离副本应用。Flowrest的时间对齐只作为单因素审计harness运行，不是静默上游修复；Leo/Lens的语义/度量发现没有擅自修改论文算法。
