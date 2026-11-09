# ET-BERT 隔离运行补丁

基准 `linwhitehat/ET-BERT@d59470624acd11405f9e88da650cf3bf65521e9a`，原始checkout保持干净，补丁仅应用于 `papers/et_bert/runtime-artifacts/patched/` 中相同路径的源码副本。

| 补丁 | 类别 | 原因与等价性 |
| --- | --- | --- |
| `0001-portable-confusion-output.patch` | 运行错误修复 | 原evaluate(True)固定写 `/data2/lxj/pre-train/results/confusion_matrix`，云端训练完成后失败。改写到已有模型输出路径旁的`.confusion_matrix`。不改变数据、网络、损失、优化或预测。 |
| `0002-import-classifier-module.patch` | 运行错误修复 | 原inference脚本只能找到项目root，但找不到`fine-tuning/run_classifier.py`；显式加入该目录供导入Classifier。不改变推理模型或权重。 |

两补丁独立check/apply命令及退出码见 `logs/et_bert/patch{1,2}_{check,apply}.*`。应用后合成tiny分类/推理通过。原样训练产生的41个state_dict张量与补丁后相同seed训练逐张量完全一致，见 `evidence/et_bert/patch_equivalence.json` 与 `logs/et_bert/patch_equivalence.*`。字节文件hash不同是输出序列化文件名等差异；没有将字节不同误当参数差异。该等价性只验证本次合成案例，不能替代所有真实实验的验证。

原README分类/预训练还需要 `PYTHONPATH=<upstream绝对路径>` 才能导入uer；这是显式环境设置，未改上游代码。Scapy2.4.4在本机Python3.8/系统libc查找时失败，试用2.5.0后可导入；这是已记录的环境兼容性调整，非论文原环境。

**没有修改预训练损失或dropout以追平论文。** 原文Eq4与当前MLM权重0.1、论文dropout0.5与有效config0.1的差异保留为重要审计发现。loss历史跨版本变化已归档，需要确认论文原实验代码后才能决定算法修复及其等价性。
