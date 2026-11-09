> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Leo 追加轮复现报告

**R1，只验证独立CPU环境、原样文本生成和资源模型的有限Smoke。** 没有运行真实网络数据训练，没有完成P4编译/包级仿真/硬件；论文完整结果Unknown。阈值与位域诊断发现可复核的源码边界问题，不是论文全部实测结果的反证。

## 固定版本与环境

`https://github.com/Purdue-ISL/Leo`，main `bd9fb79b8e0bd79b4922f3ca1ada88b9ee69eff2`，MIT；原始checkout保持clean。原文p1573脚注明确官方源码；全文及Appendix已读，覆盖Fig1–23、Table1–2，`coverage_matrix.csv`逐实验列出缺失。

本轮CPU主机仍为Debian13.6/x86_64、4核配额/16GiB上限，无GPU。独立Miniforge前缀`.conda/leo`：Python3.10.22、NumPy1.24.4、sklearn1.3.0、pandas2.0.3、matplotlib3.7.2、Scapy2.5.0。后四项匹配README明确版本；Python相对README3.10.12有patch版本差异，NumPy为本次显式兼容选择，不声称原环境等价。Python构建编译器GCC14.4.0，宿主gcc/g++14.2.0。未安装PyTorch/CUDA，不需要它们执行本轮路径。`environment/leo/`保留声明、实际export、Conda explicit、pip freeze、版本探测。pip freeze包含Conda构建来源的本地URL，可移植性不能仅由freeze保证。

## 已执行命令

所有入口与stdout/stderr、UTC时间、退出码见`logs/leo/<run_id>.json/.log`；源代码不修改，生成文件写入隔离runtime目录。

| run_id | 实际动作 | 结果 |
| --- | --- | --- |
| conda_create | `.tools/miniforge3/bin/conda create -y --override-channels -c conda-forge -p /workspace/traffic-repro-audit/.conda/leo python=3.10 pip` | exit0 |
| pip_install | `.conda/leo/bin/python -m pip install numpy==1.24.4 scikit-learn==1.3.0 pandas==2.0.3 matplotlib==3.7.2 scapy==2.5.0` | exit0 |
| readme_dataplane_sram | 原样`leo_dataplane_generator.py --sram --filename demo.p4 --sub_tree 2 --depth 10 --features 12`，输出cwd=`papers/leo/runtime-artifacts/readme` | exit0；README示例参数，仅P4文本生成 |
| readme_resource_model | cwd=`upstream/leo/leo`，`python resource-model.py --tcam --muxed_alu_config 3,3,3,3` | exit0；模型打印511表项，未测硬件资源 |
| p4_compiler_probe | `bf-p4c --version` | exit127，命令缺失；不是实际编译成功 |
| readme_training_missing_data | 由README指向的样例训练入口推导，独立cwd调用原`dataset-processor-cicids2017.py` | exit1，CICIDS CSV不存在；原始文件名和trace保留 |
| threshold_counterexample | `.conda/leo/bin/python papers/leo/semantic_smoke.py` | exit0表示诊断成功找到失配，不表示转换等价性通过 |
| readme_ctrlplane | 原`leo_ctrlplane_generator.py --tcam --output_filename tree0_ctrl.py --sub_tree 1 --depth 1 --input_filename tree_0.txt --transient` | exit0；合成stump文本转换；输出“Disabled transient...”与`constraint=0`，未执行生成的BFRT调用 |
| integer_domain_diagnostic | `.conda/leo/bin/python papers/leo/integer_domain_diagnostic.py` | exit0表示确认16位域反例；仅Python bit-vector检查 |

所有上述Python入口设置`PYTHONDONTWRITEBYTECODE=1`；诊断线程数设1。没有sudo、运行未知安装脚本、发起付费服务或下载专有SDK。Git clone和读取/导出也已实际执行，来源版本在metadata/source manifest。

## 输入、数据和权重

本轮没有下载UNSW-NB15/CICIDS原数据、没有加载外部pickle/神经网络权重。它们的精确原文件校验、原split/采样/会话ID和原始数据许可仍Unknown。论文、原代码各文件SHA及源符号索引保留在`evidence/leo/`。Smoke数据是显式合成两点stump：整数`[a,a+1]`、标签`[0,1]`，a=0/1/2，entropy CART depth1/random_state42；不是网络流量。输入数组、导出树文本和源哈希存于诊断JSON，运行输出的P4/BFRT文本另有artifact清单哈希。

## 指标对照与限制

| 论文指标/实验 | 本轮观测 | 复现结论 |
| --- | --- | --- |
| CICIDS SRAM macro-F1约0.94、TCAM约0.98；NB15 SRAM约0.92 | Unknown，无原数据训练 | 未验证 |
| 多类/逐类F1、1.04M并发流时F1与Table2四配置 | Unknown | 未验证 |
| TCAM深度22/1024叶、SRAM完整深度10、硬件stage/table资源 | 仅生成器文本与资源公式运行 | 不等同编译可行性或硬件资源 |
| 约500ns数据平面分类、500×低于control plane | Unknown | 无交换机/流量/测时协议 |
| runtime tree updates无瞬态不一致 | 原control-plane transient生成被禁用 | 未验证；公开自动控制面有缺口 |
| parser保持sklearn分类边界 | 0.5→0及2.5→2，整数0/2路由失配；65535亦有MSB域反例 | 原源码可确认诊断，不外推论文实测误差 |

没有静默应用算法修复。下一阶段若修复，需要分别验证`<=t`到整数`<floor(t)+1`的边界映射、16位全域有符号/无符号比较、导出小数精度、所有子树形态、双树更新和真实P4包级语义；它们会改变编码逻辑，应独立补丁和重评估。现有证据只支持R1，不支持R2以上，也不支持完整论文主要任务已公开完整实现的断言。
