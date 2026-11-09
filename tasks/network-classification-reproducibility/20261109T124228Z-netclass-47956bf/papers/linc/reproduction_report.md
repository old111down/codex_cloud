> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# LINC 有限CPU复现报告

**本轮等级R1：仅自定义神经网络与规则匹配的限定合成Smoke。没有真实流量数据运行，不达到R2；论文结果、完整增量流程和硬件结果均Unknown。** 原版forward/backward在明确披露的兼容环境通过；原始安装和原始小batch训练失败；修复后的合成训练/导出另行记录。

## 来源、数据与环境

- 论文：*Linc: Enabling Low-Resource in-Network Classification and Incremental Model Update*，ICNP2024，DOI `10.1109/ICNP61940.2024.10858585`；合法作者PDF来源见 `metadata.json`。全部12页已读，无附录；覆盖细节见静态审计与41行矩阵。
- 源码：`https://github.com/haolinyan/LINC`，`main@4a44171c84547de885a54e5f1a234640cd8501d4`，许可证Unknown，最终upstream保持clean。源码文件哈希、编号证据在 `evidence/linc/source_manifest.json`与`numbered_*.txt`。
- ISCX预处理pickle仅由README指向Baidu。普通HTTP可达性探测失败，代理403；未登录、未绕过访问限制、未下载或执行pickle。数据内容、原始许可、hash、标签映射、样本数量、训练/验证/测试独立性均Unknown。UNIV1/UNSW完整LINC输入未取得。没有下载外部权重。
- 测试全部由 `smoke.py`生成合成二类位向量；无网络含义。NN独立forward为32×96，seed2023；训练64、验证32、测试32、8bit、1epoch、E2/k2/T0.6。训练数据使用生成seed1、验证2、测试3；模型初始化seed2023。没有用它们替代论文数据计算论文指标。
- 实际宿主Debian13.6、4CPU配额/16GiB，GPU/CUDA/p4c/bf-p4c/simple_switch未找到。独立`.conda/linc`：Python3.10.22、Torch2.0.1+cpu、最终NumPy1.26.4、scikit-learn1.5.1、SciPy1.14.0、pandas2.2.2。系统GCC/G++14.2.0；Python构建编译器GCC14.4.0。详见 `environment/linc/runtime_versions.json`。

原始requirements安装因SwANLab固定版本不可用失败，先保留原NumPy2.0.1复验桥接失败，再明确降为1.26.4。PyTorch使用官方CPU同版本wheel；未启动CUDA/付费计算或远程实验跟踪。兼容性选择和原环境freeze见 `environment/linc/README.md`；最终environment.yml、Conda explicit/MD5、pip freeze和解析报告均保存。论文Python3.9/Torch1.12/M60环境没有重建。

## 实际执行命令

所有原始命令、cwd、UTC起止、退出码、时限、stdout/stderr均见 `logs/linc/<run_id>.json/.log`。工作区为 `/workspace/traffic-repro-audit`；运行测试用 `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`。精确命令由 `scripts/run_logged.py`封装。

| run_id | 实际入口/命令 | 结果 |
| --- | --- | --- |
| `clone` | `git clone https://github.com/haolinyan/LINC.git upstream/linc` | 成功固定SHA |
| `conda_create` | `.tools/miniforge3/bin/conda create -y --override-channels -c conda-forge -p .../.conda/linc python=3.10 pip` | exit0 |
| `readme_install_dry_run` | cwd原仓库；独立Python `-m pip install --dry-run -r requirements.txt` | exit1，仅预解析，单独保留 |
| `readme_install` | cwd原仓库；独立Python `-m pip install -r requirements.txt` | exit1，SwANLab固定版本无匹配 |
| `install_torch_cpu` | `pip install torch==2.0.1+cpu --index-url https://download.pytorch.org/whl/cpu` | exit0，披露CPU构建选择 |
| `install_runtime_original_numpy` | `pip install --report ... -r environment/linc/requirements-runtime-original-numpy.txt` | exit0；仅省略inactive不可得包与另装Torch，仍使用原NumPy2.0.1 |
| `readme_train_original_numpy` | 在逐文件hash一致的原样隔离源码副本cwd执行 `python train_nn.py` | exit1，缺`iscx.pkl`；同样保留NumPy桥警告。复制仅隔离checkpoint输出，未改源码 |
| `numpy_bridge_original` | `python -c '... torch.from_numpy(np.zeros(...)) ...'` | exit1，桥接报错；合成数组 |
| `numpy_compat_install` | `pip install numpy==1.26.4` | exit0；明确环境兼容修复 |
| `network_smoke` | `python papers/linc/smoke.py network`，导入原仓库 | exit0，原NN CPU forward/loss/backward |
| `train_small_original` | `python papers/linc/smoke.py train`，原LINCModel和合成Dataset | exit1，`num_batch//10`为0 |
| `default_subspace_original` | `python papers/linc/smoke.py subspace` | exit1断言，八查询中五个默认分区索引错误 |
| `patch{1,2,3}_{check,apply}` | `git apply --check/--directory=...`依次施加三个patch到输出副本 | 全部exit0；上游未改 |
| `train_export_patched` | `python papers/linc/smoke.py train --patched` | exit0，合成训练/导出/张量规则匹配通过 |
| `default_subspace_patched` | `python papers/linc/smoke.py subspace --patched` | exit0，八查询索引零差异 |

Conda explicit、freeze和版本探测也实际执行并归档。不是完整README执行成功：数据缺失和完整CUDA增量路径仍受阻。全部失败日志保留，没有覆盖成最终成功记录。

## 观测与论文比较

| 检查项 | 本轮观测 | 论文值/协议 | 可比性 |
| --- | --- | --- | --- |
| 原NN依赖/梯度 | 32×96、2输出，loss0.685883，19976参数，forward/backward通过 | 六类/三任务原数据训练 | 仅合成函数Smoke，不比较精度 |
| 修复后合成训练/规则 | 64/32/32、1epoch，2规则；合成测试100% | Fig5三任务指标与Fig7资源预算 | 不可比；100%无网络流量含义 |
| 默认子空间 | 原版5/8查询索引错误；补丁0/8 | Fig4分区机制 | 是局部可执行反例；真实数据发生率/论文准确率影响Unknown |
| 新类别数据 | 未取得 | TableII 0.05%：63/44/28样本，三连续更新 | Unknown；RATIO=1不强制63，但pickle可能预采样 |
| 训练/转规则 | 合成进程及局部计时仅存日志 | 原908469样本32epoch，137s/4s，TeslaM60 | Unknown，不比较时间 |
| 更新时延 | 未执行完整更新 | 三次平均14.31s/36.46s | Unknown |
| 资源与吞吐 | 无P4源码、无设备运行 | SRAM/TCAM/TMIX/stages/tables；99.9Gbps、<890ns、三交换机100GbpsIMIX | Unknown |

## 补丁、等级和剩余事项

补丁见 `patches/linc/README.md`。日志取模修复仅改变日志；CPU设备修复仅扩展导出/张量模拟器兼容性；默认子空间索引修复会改变缓存分配，归为算法逻辑修改，不能声称论文等价。保留default bucketN后，独立probe执行原`update_streaming.py:179`的索引表达式，确认新类未匹配样本可继续触发`values[N]`的IndexError（`independent_checks.json`与`logs/linc/independent_review_checks.*`）。因此修复仅局部，不能把反例通过说成整个增量算法已修好；完整GPU更新/真实数据影响仍Unknown。

本轮R1成立于兼容环境和有限Smoke。原始数据处理/训练/三次连续更新、全部四基线、比率/entry预算/采样消融仍R0。所有论文Accuracy/P/R/F1、原模型规模、原训练/推理耗时、硬件吞吐和资源可比结果均Unknown。没有取得R2/R3/R4证据。下一轮先合法获取原pickle和原始PCAP/split生成过程，确认63/44/28样本ID、默认子空间与P2P/VoIP更新，然后才值得进行完整CPU/GPU或P4恢复。
