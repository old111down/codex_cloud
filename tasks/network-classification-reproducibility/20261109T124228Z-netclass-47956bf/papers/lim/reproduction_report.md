> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# LiM 首轮复现报告

**结论：R2（仅作者附带CSV上的核心分类算法），未复现论文完整评估。** 原样源码完成训练与903条测试样本的推理，accuracy 为0.9534883720930233；这不是对论文0.942指标的成功复现，因为实际数据、Python/XGBoost版本与原始划分的等价性不成立或为Unknown。原始PCAP重建、两项基线、资源性能和增量/在线用例未验证。

## 固定版本与证据范围

- 论文：*Less is More: Simplifying Network Traffic Classification Leveraging RFCs*，WWW Companion2025，DOI `10.1145/3701716.3715492`。
- 静态阅读：arXiv:2502.00586v2，2025-02-04，7页，全部正文与参考文献；§3方法、§4.1实现、§4.2–4.3评估已读。Table1和Table2为全部编号表，无编号图/Appendix。最终ACM PDF HTTP403（`logs/lim/acm_fetch.stderr.log`），最终4页版是否有独有修改为Unknown。
- 官方源码：`https://github.com/nime-sha256/LiM`，`main@1b8ca187f7d02a51e595f797e5c200ae740b459f`。论文p2脚注1与README精确引用形成双向关联。MIT；源码未修改，最终git status为空。

## 实际环境与依赖

实际宿主为Debian13.6、x86_64、Linux6.18.57；完整CPU/RAM/磁盘/权限/无GPU检测见 `environment/host_probe.json`。本次独立Conda前缀为 `/workspace/traffic-repro-audit/.conda/lim`，由Miniforge建立（`logs/lim/conda_create.*`）。

Python3.11.18；pandas2.2.2、NumPy1.26.4、scikit-learn1.4.2、XGBoost2.1.1、Pyshark0.6、tqdm4.66.1，均按README `requirements.txt`安装。PyTorch未安装且LiM不依赖它；`nvcc`、`nvidia-smi`、TShark均未找到。XGBoost的pip wheel附带NCCL依赖不代表有GPU或已经运行CUDA。系统gcc/g++为Debian14.2.0；Python构建编译器为GCC15.3.0。详见 `environment/lim/runtime_versions.json`。

论文§4.1描述Ubuntu24.04.1、Python3.13.0、XGBoost2.1.2、双Xeon Silver4208/125GiB/4×T4。本轮选择Python3.11满足README所锁NumPy1.26.4等依赖；这是明确的兼容环境选择，不是原论文环境。没有无说明替换依赖。模型执行设置 `OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2`；这些是线程环境提示，本报告不把整体进程walltime当论文训练或推理性能。

环境记录：`environment/lim/environment.yml`为可维护声明，`environment-resolved.yml`为实际导出，`conda-explicit.txt`为Conda包URL锁，`pip-freeze.txt`为原始pip freeze。Conda导出警告其不能可靠锁定pip包；raw pip freeze中的Conda-managed `packaging @ <LOCAL_BUILD_PATH_WITHHELD>

## 数据与权重

使用固定SHA仓库的 `cstnet-tls1.3_5_packets.csv`（604107字节，SHA256 `4385b283d64cf20346562bc4c389466aea4c9c5a4b240254d1acb4d76126f3d7`）。作者标注为CSTNET-TLS1.3 NetMatrix，一行对应已选5个加密应用数据包的双向会话，15个数值特征，标签为10个域名。原始PCAP/会话映射缺失，无法独立核验每行来源与会话独立性。

实际4514行、每类372–486；并非论文“每类400，共4000”。无空值、无完全重复特征行，但不据此推断无来源泄漏。完整分布和数据检查见 `evidence/lim/data_audit.json`。数据随作者仓库公开，项目许可证为MIT；上游原始CSTNET数据许可与原始采样seed为Unknown。没有下载或加载外部模型权重，模型仅在内存训练，未持久化；权重来源/校验不适用。论文、CSV和证据文件校验见 `asset_manifest.csv`。

## 实际执行命令与结果

以下命令以 `/workspace/traffic-repro-audit`为工作目录；所有执行均有原始合并stdout/stderr、UTC时间、cwd、timeout和exit code（`logs/lim/*.log`及同名`.json`）。Conda建立前缀和源码克隆均保留版本信息。

```sh
python scripts/run_logged.py --log logs/lim/conda_create --timeout 600 -- .tools/miniforge3/bin/conda create -y --override-channels -c conda-forge -p /workspace/traffic-repro-audit/.conda/lim python=3.11 pip
python scripts/run_logged.py --log logs/lim/readme_install --cwd upstream/lim --timeout 600 -- /workspace/traffic-repro-audit/.conda/lim/bin/pip install -r requirements.txt
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 python scripts/run_logged.py --log logs/lim/readme_classifier --cwd upstream/lim --timeout 180 -- /workspace/traffic-repro-audit/.conda/lim/bin/python xgboost_classifier.py
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 python scripts/run_logged.py --log logs/lim/readme_preprocess --cwd papers/lim/runtime-artifacts/readme-preprocess --timeout 30 -- /workspace/traffic-repro-audit/.conda/lim/bin/python /workspace/traffic-repro-audit/upstream/lim/pcap_to_netmatrix.py
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 python scripts/run_logged.py --log logs/lim/synthetic_smoke --timeout 30 -- /workspace/traffic-repro-audit/.conda/lim/bin/python papers/lim/smoke_test.py
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 python scripts/run_logged.py --log logs/lim/core_capture --timeout 180 -- /workspace/traffic-repro-audit/.conda/lim/bin/python papers/lim/core_capture.py
```

README阶段先未改上游：依赖安装exit0；分类器完整4514行直接运行exit0，3611训练/903测试，整体进程2.128秒。预处理命令为保留上游洁净在审计输出目录调用相同源码，保留原始占位dataset_path；exit0却只输出表头，没有处理PCAP，**不算数据处理成功**。空输出已存 `evidence/lim/preprocess_empty_output.csv`。TShark缺失尚未在真实PCAP上触发，因为无数据路径可遍历。包选择条件也未明确检查TLS1.3版本；版本符合性仍依赖原始数据来源而为Unknown。

随后合成30×15特征的2棵树依赖/fit smoke exit0（1.269秒），只验证导入和基本分类器训练输出形状，不是网络流量或论文指标测试。为了保留精确指标与逐样本预测，`core_capture.py`第二次通过runpy执行**同一原样上游文件**，不改源码/参数/样本，仅在结束后读取内存结果、校验测试行索引并导出 `evidence/lim/metrics.json`和`predictions.csv`。这次exit0（1.977秒），accuracy与首次相同。两次是功能执行，不是重复性统计或性能基准。

## 论文指标与本轮观测

| 指标/用例 | 论文值 | 实际观测 | 结论 |
|---|---:|---:|---|
| LiM accuracy | 0.942 | 0.9534883720930233 | +1.1488个百分点；数据/版本不等价，论文复现Unknown |
| LiM precision | 0.943 | macro0.9541932013 / weighted0.9549739140 | 论文平均方式Unknown，不直接等同 |
| LiM recall | 0.942 | macro0.9530509966 / weighted0.9534883721 | 同上 |
| LiM F1 | 0.942 | macro0.9530904896 / weighted0.9537214207 | 同上 |
| ET-BERT/YaTC Table1 | 0.568 / 0.963 accuracy | Unknown | 本仓库无对应实现/对齐处理与配置 |
| LiM训练秒/样本 | 0.0005 | Unknown | 无论文计时协议；整体进程walltime不可替代 |
| LiM推理内存MiB | 196.38 | Unknown | 未重建RAM+GPU推理采样协议 |
| LiM GPU功率W | 0 | Unknown | 无GPU测量，0 GPU功率不代表0整机能耗 |
| LiM推理samples/s | 86251.23 | Unknown | 未重建batch/warmup/重复次数与推理计时 |
| 无握手/0-RTT/会话恢复 | 定性有效性 | Unknown | 只有包选择代码，无专用数据或实验 |
| 秒级适应新类别 | 定性声明 | Unknown | 无增量更新入口/新类别实验 |

对§4.3.2派生百分比另做纯算术核查：多处“higher%”写成比值×100，标准增幅公式为(比值−1)×100。例如ET-BERT训练延迟相对LiM应为86460% higher（正文86560%），LiM吞吐相对ET-BERT应为52202% higher（正文52302%）。证据为 `evidence/lim/paper_arithmetic.json`。这不验证Table2绝对测量值；绝对值按论文保留，实验性能仍为Unknown。

## 分层状态、修复与后续阻断

- 关联/静态覆盖已完成，完整矩阵见 `coverage_matrix.csv`。
- README安装和原样分类器成功；最小合成Smoke成功。
- 作者CSV上的核心离线分类为R2；原始PCAP处理和样本选择为R0；两基线和Table2资源指标为R0。没有满足R3完整原流程与指标协议，不能把项目整体描述为论文成功复现。
- 无上游代码修改、无算法补丁。本轮只增加审计harness与输出归档，不对scaler先拟合再切分、样本不平衡等问题进行静默修复。
- 下一阶段需要作者原始4000样本ID/PCAP/划分、TShark与版本、ET-BERT/YaTC准确配置和权重、原始计时/内存/GPU功率协议，以及原软件环境。缺少这些信息时仍为Unknown。
- LiM无P4或专有硬件部署入口，P4模型生成/构建/软件仿真/真实交换机四层不适用。本文的服务器实时/高流量适用性只作论文声明，本轮无在线服务或线速吞吐证据。
