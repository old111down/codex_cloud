> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# ET-BERT 本轮运行报告

**等级R1：CPU合成功能验证。未取得论文真实数据与原始预训练权重，未达到R2/R3，全部论文指标复现结论为Unknown。** 本轮实际完成原base网络前向、原预处理与tiny两步预训练，以及运行错误修复后的tiny分类/推理。合成输入或随机权重结果不是网络流量分类精度复现。

## 环境与来源

根目录 `/workspace/traffic-repro-audit`。独立Miniforge/Conda前缀`.conda/et_bert`，Python3.8.20、NumPy1.19.2、PyTorch1.13.1+cpu、Scipy1.6.3、scikit-learn0.24.2；Scapy先按README2.4.4安装并导入失败，后明确升级2.5.0。系统Debian13、GCC/G++14.2，4CPU配额/16GiB，测试线程固定1。无CUDA/GPU、TShark/SplitCap/Wine。论文使用PyTorch1.8.0/V100S，当前CPU环境不等价；未安装Apex、TensorFlow或专有软件。

`environment/et_bert/` 保存声明YAML、实际导出、Conda explicit、pip freeze、runtime版本及三个pip安装报告中的下载来源/校验值。Conda explicit不锁pip包，CPUtorch需官方wheel index。未修改系统Python或关闭TLS校验。

源码固定 `linwhitehat/ET-BERT@d59470624acd11405f9e88da650cf3bf65521e9a`，MIT，完整Git clone。来源与tracked-file哈希在 `evidence/et_bert/upstream_files.json`；最终git status为空。论文与仓库的直接关联证据沿用 `evidence/candidates/et_bert/`，本轮全文/代码审计见 `static_audit.md`、69行矩阵。

## 实际命令与原始日志

全部精确argv/cwd、UTC起止、exit和时限在 `logs/et_bert/<run_id>.json`，原始合并stdout/stderr为同名`.log`。以下入口均实际执行，长命令不以伪代码替代归档argv。

| 动作 | 实际入口/配置 | 结果与run_id |
| --- | --- | --- |
| 环境 | conda create py3.8/numpy1.19.2；官方CPUtorch1.13.1；再`pip install -r requirements.txt` | 成功：`conda_create`、`install_torch_cpu`、`readme_install` |
| README分类 | 原README完整命令，cwd upstream/et_bert | exit1缺uer：`readme_classifier`；只补PYTHONPATH后exit1缺原train TSV：`readme_classifier_pythonpath` |
| README推理 | 原README完整inference命令 | exit1缺run_classifier：`readme_inference` |
| README预训练 | 原8-rank/500000-step命令 | 原样exit1缺uer：`readme_pretrain`；只补PYTHONPATH后exit1无GPU：`readme_pretrain_pythonpath`，没有启动500000步计算 |
| base前向 | `python papers/et_bert/cpu_model_smoke.py`，原base_config、原词表 | exit0：`cpu_base_forward`；12层/12头/768，132127490参数（2类测试头），2×16 token→2×2有限logits |
| 原tiny训练 | 原`fine-tuning/run_classifier.py`，tiny_config、8/4/4合成样本、1epoch、batch2、seq16、seed7 | 训练/dev完成，最终写`/data2/.../confusion_matrix`失败：`synthetic_cli_original` |
| 补丁tiny训练/推理 | 仅源码副本应用两项runtime补丁，相同合成输入/seed；原inference使用本地生成checkpoint | 均exit0：`synthetic_cli_patched`、`synthetic_inference_patched`；合成test2/4正确仅为接口检查，不是论文值 |
| 参数对照 | `python papers/et_bert/validate_patch_equivalence.py` | exit0，41个state tensor逐值相等：`patch_equivalence` |
| 原预处理 | 原`preprocess.py`，24个合成双句document，seq16/dup1/process1 | exit0：`synthetic_preprocess`；只处理合成text，不是PCAP原处理成功 |
| 原CPU预训练 | 原`pre-training/pretrain.py`，tiny_config、world_size1无GPU ranks、2steps/batch2 | exit0：`synthetic_cpu_pretrain`；MBM/SBP loss有有限输出、保存本地权重，非原30GB/500000步预训练 |
| 源行为probe | `source_behavior_checks.py`，合成PCAP及已知session packet样本，外部方向提取/数据返回处明确mock | `source_behavior_checks`因Scapy2.4.4导入失败；改2.5后`source_behavior_checks_compat`因审计harness缺父目录失败；修正harness后`source_behavior_checks_final` exit0 |
| 精确损失probe | `loss_equation_probe.py`执行原forward_propagation，输入MLM10/SP2 | exit0：`loss_equation_probe_location_corrected`；actual3、grad0.1/1，paper Eq4为12；初次同值probe只更正源码引用行号，原日志也保留 |

需要PYTHONPATH的调用均显式设为上游绝对根路径，原8-rank运行只添加该环境变量后即无GPU退出。模型/源行为测试显式设`PYTHONDONTWRITEBYTECODE=1`；线程环境为`OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`。精确逐命令override另保存在 `environment/et_bert/execution_env_overrides.json`（普通安装/clone操作没有这些强制线程设置），不输出继承凭据。各run摘要为 `execution_summary.json`，不将环境/补丁操作误当论文实验成功。

## 输入、权重与测量范围

训练8条、dev/test各4条均为显式人工hex-token TSV；模型base测试是随机初始化与16 token输入。24个重复合成document只用来走通原BERT数据/损失/CPU训练路径。没有下载或反序列化未知第三方checkpoint；torch.load只加载本审计刚生成并已记录来源的state_dict。源模型、toy输入与生成资产的尺寸/哈希在 `synthetic_input_manifest.json`、`patch_equivalence.json`、`runtime_artifact_manifest.json`。

README给出的Google Drive`/file/d/.../view` URL实测HTTP200、Content-Type=text/html，86586字节HTML，而非直接checkpoint；证据为 `checkpoint_view_probe.json`。这仅证明该wget示例URL的响应类型，不证明授权的正常Drive下载不可用。真实数据/corpus/权重的可达性、完整性、许可和实际校验值仍Unknown；没有绕过Drive权限或登录。

base一次CPU前向0.1352秒、进程MaxRSS766568KiB是本次功能观察，包含随机模型/短输入等条件，**不是原论文推理时延或吞吐复现**。tiny预训练log的tokens/s也只是极小合成执行输出，不作性能对比。

## 与论文指标的对照

| 论文范围 | 论文packet F1（公开稿Tables2–3） | 本轮可比指标 |
| --- | ---: | --- |
| Cross-Platform iOS / Android | 0.9754 / 0.9206 | Unknown |
| USTC-TFC | 0.9916 | Unknown |
| ISCX-VPN-Service / App | 0.9890 / 0.9937 | Unknown |
| ISCX-Tor | 0.9921 | Unknown |
| CSTNET-TLS1.3 | 0.9741 | Unknown |
| flow版本、11基线、七项ablation、三few-shot比例 | 逐项见coverage_matrix与原论文 | Unknown |
| Table5随机性/Fig3密码分布/AppendixA.1 t-SNE | 多项定量/可视化结论 | Unknown |

本轮确认当前实现对已归约损失额外加权0.1/1，与Eq4的显式无权重写法不同；数值probe没有验证Eq2/3整体sum/mean归约。有效dropout0.1与论文0.5不同，另存在预处理分支和packet group-disjoint保证缺口；这些是已确认代码/协议差异。它们可能影响结果是合理推测，影响的方向/幅度及作者原实验版本均未知。当前公开代码本身也跨2022/2024/2025发生损失语义变化，不能用当前HEAD测试倒推原发表实验。

## 结论与阻断

A代码公开完整性：主要建模机制与通用训练/推理公开，整套真实数据、全部对照/ablation/解释性/附录流程未完整覆盖。B运行可复现性：CPU合成原模型/数据序列化/预训练可运行，原样README与分类/推理存在已确认失败；隔离runtime修复后toy流程通过。C论文结果可复现性：全部原指标Unknown，未达到R2/R3。

下一步先固定原实验commit/损失/dropout/序列长度、取得合法原data与checkpoint及session级划分，然后优先比较packet-group拆分、full/flow/packet和目标权重敏感性。普通CPU可承载有限base前向/tiny训练；完整500000步base预训练及多任务finetune成本未实测，不声称CPU完成论文全流程。ET-BERT没有P4/交换机声明，P4编译/仿真/真实硬件层不适用。
