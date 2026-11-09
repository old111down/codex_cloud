# YaTC 隔离兼容性修复

适用官方 `main@a220b75f8365acaf63dbac7df87aaaa357698b85`。所有上游与已安装包保持未修改，补丁只应用到 `papers/yatc/runtime-artifacts/` 中的副本。数据和论文指标等价性均未验证。

1. `0001-original-dependency-import-compat.patch`：**环境兼容性修复**。README指定torch1.9.0和timm0.3.2；本次新环境中原命令先因`distutils.version`未导入失败，独立`import timm`再证实`torch._six.container_abcs`已不存在。补丁显式导入`distutils.version`并将`collections.abc`提供给旧timm所期待的名字。没有改变神经网络、损失或输入处理。补丁检查/应用成功后，原预训练参数进入数据加载，继而因`./data/ISCXVPN2016_MFR/train`不存在失败。`compat_bootstrap.py`提供相同的审计运行时别名用于函数测试；bootstrap不是声称原命令已成功。
2. `0002-guard-cuda-synchronization.patch`：**运行错误修复（CPU设备边界）**。训练和预训练engine两处无条件`torch.cuda.synchronize()`改为只在传入device为CUDA时同步。单CPU样本原训练在engine.py:148触发`Torch not compiled with CUDA enabled`，补丁副本上的同一单批次harness成功。它没有替换原模型参数或梯度计算，但CPU/GPU数值与性能等价性未验证；不涵盖分布式GPU路径、完整训练或原数据。

实际命令/退出码分别位于 `logs/yatc/{import_patch_check,import_patch_apply,readme_pretrain_import_patched,cpu_patch_check,cpu_patch_apply,engine_cpu_probe,engine_cpu_patched}.{json,log}`。完整源SHA与文件校验见 `evidence/yatc/source_manifest.json`。本轮没有把`macro_*`命名或潜在地址捷径改为新的实验逻辑；这两项只作证据核查，不能在无原论文时擅自决定应修成哪种指标/数据处理。
