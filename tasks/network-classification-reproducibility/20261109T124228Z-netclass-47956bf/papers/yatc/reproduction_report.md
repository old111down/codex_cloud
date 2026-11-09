> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# YaTC 本轮复现报告

**R1，仅限兼容性辅助的合成Smoke；没有原论文结果复现。** 原README命令在新建独立环境中实际失败；导入兼容后仍因未取得数据失败。完整模型的CPU forward/backward、合成PCAP→MFR和指标语义反例已运行，原训练engine又实测CPU边界错误。没有真实流量数据、原权重、原split或论文指标比较，不能授予R2/R3/R4。

## 来源与论文可读性

官方 `NSSL-SJTU/YaTC`，`main@a220b75f8365acaf63dbac7df87aaaa357698b85`，最终上游Git status为空。论文AAAI2023 DOI `10.1609/aaai.v37i4.25674`；原始全文OJS两路403，BotStopper和提取失败已归档。仅官方摘要/元信息与全部公开源码可读；所有论文编号图表、完整五数据集清单、Method/Implementation/Evaluation/Appendix及原报告数值为Unknown。详细路径见 `static_audit.md`与覆盖矩阵；未以其他论文替代原文。

## 实际环境

独立 `.conda/yatc`：Python3.8.20、torch1.9.0+cpu、torchvision0.10.0+cpu、timm0.3.2、NumPy1.19.5、scikit-learn0.24.2。README明确给出的Python/timm/torch/NumPy/sklearn版本均保持；`+cpu`是官方CPU构建，无CUDA。补充依赖版本为本轮选择（SciPy1.5.4、Pillow9.5.0、skimage0.18.3、TensorBoard2.10.1、protobuf3.19.6、Matplotlib3.3.4、Scapy2.5.0、tqdm4.66.1），原作者补充依赖锁Unknown。

首次选择protobuf3.20.3与TensorBoard2.10.1冲突，属于**审计方补充环境选择失败**，不是上游代码缺陷；保留`install_pinned_dependencies`日志后改为protobuf3.19.6并成功。CPU torch/vision来自官方download.pytorch.org索引，其他包走继承pip源/TLS。本机Debian13、4CPU配额/16GiB共享、无GPU；本项目线程上限1，模型未缩小。原论文硬件/软件完整等价性Unknown。完整环境见 `environment/yatc/{environment.yml,conda-explicit.txt,pip-freeze.txt,runtime_versions.json,pip-install-report.json}`。

## 实际命令、执行与日志

命令以仓库根为cwd，除README源程序为隔离输出使用`papers/yatc/runtime-artifacts/readme` cwd。所有运行均在 `logs/yatc/<run_id>.json/.log`保存实际argv、UTC时间、退出码与stdout/stderr。对README使用绝对路径调用同一上游文件及同一参数，未编辑上游。

| run_id | 实际入口/命令概要 | 结果 |
| --- | --- | --- |
| `clone` | `git clone https://github.com/NSSL-SJTU/YaTC.git upstream/yatc` | exit0，固定SHA |
| `conda_create` | `conda create --override-channels -c conda-forge -y -p .conda/yatc python=3.8 pip=24.3.1` | exit0 |
| `install_torch_original` | `pip install --no-cache-dir torch==1.9.0+cpu torchvision==0.10.0+cpu --index-url https://download.pytorch.org/whl/cpu` | exit0 |
| `install_pinned_dependencies` / `install_dependencies_compatible` | 实际完整版本参数见JSON，第二次改protobuf3.19.6 | 首次依赖解析exit1，第二次exit0 |
| `readme_pretrain` | `python pre-train.py --batch_size 128 --blr 1e-3 --steps 150000 --mask_ratio 0.9` | exit1，SummaryWriter/distutils版本属性错误 |
| `readme_finetune` | `python fine-tune.py --blr 2e-3 --epochs 200 --data_path ./data/ISCXVPN2016_MFR --nb_classes 7` | 同上，exit1 |
| `original_timm_import` | `python -c 'import timm'` | exit1，缺torch._six.container_abcs |
| `import_patch_check` / `import_patch_apply` / `readme_pretrain_import_patched` | 补丁1应用副本，同原预训练参数 | 补丁exit0；程序进入数据阶段后exit1，data目录缺失 |
| `readme_finetune_compat` | audit `run_with_compat.py`设置别名后runpy执行原fine-tune，同README参数 | exit1，数据目录缺失 |
| `synthetic_smoke` | `.conda/yatc/bin/python papers/yatc/synthetic_smoke.py` | exit0，原数据函数及两个完整模型工厂运行 |
| `engine_cpu_probe` | `.conda/yatc/bin/python papers/yatc/engine_cpu_probe.py` | exit1，原engine.py:148无条件CUDA同步 |
| `cpu_patch_check` / `cpu_patch_apply` / `engine_cpu_patched` | 补丁2的engine副本，`engine_cpu_probe.py --patched` | 全部exit0，合成单批次训练 |
| `metric_semantics` | `.conda/yatc/bin/python papers/yatc/metric_semantics_probe.py` | exit0，导出的macro_*实际上weighted |

所有Smoke设置`PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg`。导入兼容借助`compat_bootstrap.py`显式导入distutils.version与collections.abc别名；它不更改已安装包或上游文件。补丁具体类别和等价性见 `patches/yatc/README.md`。

## 数据、模型及观测值

没有下载作者数据zip或预训练pth。公开landing页可读，名称为YaTC_datasets.zip/YaTC_pretrained_model.pth，实际文件内容、大小、校验值和许可仍Unknown。未加载任何外部pickle/torch checkpoint。模型权重均本次随机初始化seed0、只在内存使用，没有把随机模型当作者模型。

`synthetic_smoke.py`构造3个合成IPv4/TCP包，调用原read_MFR_bytes/MFR_generator，得到40×40矩阵并验证少2包补零；src/dst IP和TCP端口仍存在。它只验证程序行为，不能证明真实数据已泄漏或已匿名化。输入PCAP、MFR和2×1×40×40合成tensor的SHA256见 `evidence/yatc/synthetic_smoke_metrics.json`，所有来源见 `data_model_sources.json`。

原工厂MAE为2,331,460参数，分类模型7类为1,859,335参数；未经缩小。MAE重建输出2×400×4、mask361/400，有限MSE loss0.8714236并能反传；分类logits2×7、合成交叉熵2.1528695，SGD后head权重确实变化。这些是随机输入功能Smoke输出，**不是Accuracy/F1或论文训练结果**。记录的函数耗时约0.78/0.26秒不具性能协议可比性。

原CPU训练engine在反传后CUDA同步失败；补丁2同一harness单batch成功，loss约2.0223。指标语义反例用10个已知合成label，原evaluate导出`macro_f1=0.45`等于weighted F1，实际macro F1=0.15。仅证实实现命名不一致；原论文究竟报告weighted还是macro、是否存在数值错误为Unknown。

## 分层结论与阻断

| 验证层 | 结论 |
| --- | --- |
| A 代码公开完整性 | 模型、预训练、fine-tuning、评估与MFR函数公开。论文全文不可得，全部图表与第五数据集身份未核实，不能声称主要任务完整实现。无原始flow分割、split与全实验配置清单。 |
| B 代码运行可复现性 | 原README失败；兼容辅助的完整随机模型/合成PCAP有限Smoke通过，R1。原CPU engine失败，隔离补丁后单batch通过。 |
| C 论文结果可复现性 | Accuracy/Precision/Recall/F1、原数据/标签/split、checkpoint/随机种子、推理耗时、论文模型规模与性能全部Unknown。无原数据，未达到R2；未复现R3/R4。 |
| P4/Tofino | 不适用；仓库未提供或声称该部署路径。GPU路径的完整训练/吞吐未测。 |

下一轮首先需要合法可读的AAAI原文、作者数据/checkpoint文件校验和split/标签/预训练组成，再核对metric平均方式以及PCAP前置匿名化。GPU完整预训练应在原配置明确后开展；本轮没有开付费资源、联系作者或向上游提交修改。
