> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Mousika 首轮复现报告

截至 2026-11-09，本试点达到 **R1（限定组件 Smoke Test）**，没有复现论文全量指标。main 原始 RF→BDT 函数已在公开 UNIV CSV 的小前缀上运行；它是流大小预测示例，不是论文 ISCX 应用分类结果。应用分类、恶意流量检测、P4 编译、软件仿真和真实硬件均未完成，分别保持 R0/Unknown。

## 固定版本、论文与环境

- `main`：`76c9db9b4200a7c591bd1e9476ba5ab44a467512`；`Mousikav2`：`3326869d4c1f25768a9304a2df672e82f38972f9`。二者 Git status 为空，补丁未落入 upstream。
- 两版全文均已合法取得并阅读。来源、URL、取得时间、PDF SHA256、编号对象清单在 `evidence/mousika/access_research/`；静态结论见 `static_audit.md`、82行 `coverage_matrix.csv`。
- 实际机器：Debian 13；本机工具链 GCC/G++ 14.2（精确命令输出见 `environment/mousika/runtime-versions.json`）；父审计的 cgroup 检查为4 CPU、16GiB、无GPU，完整主机信息见仓库 environment 目录。
- 独立 Conda prefix `.conda/mousika`；实际 Python3.10.22、NumPy1.24.4、pandas1.5.3、scikit-learn1.2.2、imbalanced-learn0.10.1、PyTorch1.13.1+cpu。CUDA unavailable，`torch.version.cuda=null`；`p4c`、`nvcc`、`nvidia-smi` 不可用。
- 这些是本轮选择并实际测试的兼容性环境，不是声称恢复作者环境。ToN 写明 Python3.6/NumPy1.19.3，故环境等价性 **Unknown**。CPU Torch 来自官方 `https://download.pytorch.org/whl/cpu`，只用于导入/RF路径，未将 GPU 神经网络训练替换为 CPU 训练。
- 完整锁文件：`environment/mousika/environment.yml`、`conda-explicit.txt`、`pip-freeze.txt`、`runtime-versions.json`。Conda explicit 只锁Conda包，pip包另由 YAML（含CPU wheel index）和freeze说明。

## 实际命令与原始日志

以下命令均实际执行。除初始 Conda 创建/克隆外，执行入口统一为 `python scripts/mousika/run_logged.py NAME TIMEOUT CWD COMMAND...`，相应 JSON 保存实际命令、cwd、UTC起止、退出码、时限和线程限制；同名 `.log` 保存stdout/stderr。

| 阶段 | 实际命令/工作目录 | 结果 | 日志 |
|---|---|---|---|
| 原样源码 | `git clone https://github.com/xgr19/Mousika.git upstream/mousika`；另 `git worktree add --detach ../mousika-v2 origin/Mousikav2` | 成功；两个固定SHA | `logs/mousika/clone.log`；metadata.json |
| 环境创建 | `.tools/miniforge3/bin/conda create -y -p .conda/mousika python=3.10 pip numpy=1.24 pandas=1.5 scikit-learn=1.2 imbalanced-learn=0.10` | 成功，实际解析版本在锁文件 | `logs/mousika/conda-create.log` |
| README原样首次BDT | cwd `upstream/mousika/Distillation`，`.conda/mousika/bin/python bdt_test.py`（命令实际使用绝对python路径） | exit1：缺torch；无上游依赖安装清单可直接执行 | `readme_bdt_initial.*` |
| README原样DT | 同cwd，`python dt_test.py` | exit1：仓库只有ZIP，CSV尚未解压 | `readme_dt_initial.*` |
| 安装显式CPU依赖 | `.conda/mousika/bin/python -m pip install --no-cache-dir torch==1.13.1+cpu --index-url https://download.pytorch.org/whl/cpu` | exit0 | `install_torch_cpu.*` |
| README原样BDT再次 | 同cwd，`python bdt_test.py` | exit1：缺解压后的 `./Dataset/univ/univ1-1.csv` | `readme_bdt_after_dependency_install.*` |
| README v2原样 | cwd `upstream/mousika-v2/Distillation`，`python bdt_test.py` | exit1：无条件CUDA初始化，在CPU Torch缺 `_cuda_setDevice`；没有改动代码绕过 | `readme_v2_bdt.*` |
| README converter | 在 `papers/mousika/runtime-artifacts/readme-rule2entry/` 的原样源副本中 `cd code; python rule2entry.py` | exit0，五个ruleset生成。副本仅隔离输出，未改源码 | `readme_rule2entry.*` |
| 合成组件Smoke | `.conda/mousika/bin/python scripts/mousika/smoke.py` | 首次发现Tree浮点标签导出不兼容converter；限定范围后32向量预测、SoftTree导出与ternary语义、五套作者规则转换均通过 | `synthetic_smoke.*`（原失败），`synthetic_smoke_scoped.*`（限定通过） |
| 真实数据前缀Smoke | `.conda/mousika/bin/python scripts/mousika/real_subset_smoke.py` | 原RF软标签函数→SoftTree→256预测成功；非论文评估 | `real_subset_smoke.*` |
| 修复验证 | `python scripts/mousika/patch_smoke.py`、`python scripts/mousika/v2_gini_counterexample.py` | 两项隔离验证通过，详见补丁README | `parser_patch_smoke.*`、`v2_gini_counterexample.*` |

所有短日志位于 `logs/mousika/`。原始合成失败仍保留。真实数据前缀Smoke首次审计harness遗漏上游loader的重排，导致under-sampling后按类分块的2折无法提供合理软标签；该失败以 `real_subset_smoke_unpermuted_harness_failure.*` 保留。harness加入明确seed=5的重排后通过；不是上游代码修复。v2补丁首次CRLF应用失败同样单独归档。

## 数据与输出

数据来自上述固定main commit的 `Distillation/Dataset/univ.zip`，19,401,333字节，SHA256 `65e43ba19bd873e14db57ee65210129f5797c3f41947c6dc201d9abfbfb2b4bc`。ZIP内训练/测试CSV分别794,822/825,854行；文件SHA256、完整列名、来源与许可 Unknown 标记见 `evidence/mousika/data_manifest.json`。未运行从UNIV原始抓包到CSV的处理，作者论文标签/日期划分是否被精确实现仍 Unknown。未发现预训练神经网络权重；作者提供的规则文本已全部哈希，并未当成本轮生成模型。

真实前缀Smoke读取训练CSV前512行和测试CSV前256行，按上游字段表丢弃20个连续/地址列，训练集undersampling后70行、112位特征、二类；明确重排后调用原版 `produce_soft_labels(... round_num=1, fold_num=2, k=0, model='rf')` 和 `SoftTreeClassifier(... min_sample_leaf=5)`。输入数组SHA256在日志中。小前缀准确率为 **0.76953125**，RF+BDT功能路径耗时约0.65秒；这是单次本机Smoke输出，**不与论文全量精度或训练时间直接比较**，不用于提升整篇论文等级。完整CSV评估、原始预处理、完整教师/学生组合本轮未运行；没有观测到资源耗尽，也不声称资源不足已被证明。

## 论文指标对照

| 论文声明 | 本轮可比实测 |
|---|---|
| INFOCOM UNIV RF蒸馏BDT 94.95%；LSTM蒸馏树276.6秒、DT43170.6秒 | **Unknown**：数据规模/拆分/环境未恢复；70行训练Smoke不具可比性 |
| INFOCOM ISCX/Bot-IoT的三教师精度、训练时间与规则数 | **Unknown**：对应处理数据、loader、LSTM代码/配置缺失 |
| ToN ISCX RF蒸馏BDT97.66%、五折/五教师/混合参数扫描 | **Unknown**：主程序CUDA阻断，数据/评估代码缺失，另有Gini偏差 |
| INFOCOM 40/100Gbps、零丢包、466ns分类延迟、两阶段、资源百分比 | **Unknown**：无SDE/物理交换机/Keysight，未测 |
| ToN 三交换机100Gbps IMIX、5–26ns增量延迟、硬件资源/基线比较 | **Unknown**：未测 |

## 等级与剩余阻断

| 组件 | 等级 | 明确边界 |
|---|---|---|
| 整篇Mousika试点 | R1 | 隔离环境和有限Smoke，所有论文指标Unknown |
| main RF→BDT，UNIV前缀 | R2（仅此功能组件） | 已知真实数据上的核心函数运行；未恢复原评估，不代表应用分类复现 |
| main ISCX应用分类、Bot-IoT | R0 | 只有通用算法代码，无完整数据/配置/评估入口 |
| Python rule→ternary | R1 | 五套作者文本转换一致；无P4执行 |
| v2完整主路径 | R0 | 原入口CUDA失败，缺Dataset/完整教师选择/外层5折；算法修复后论文等价性Unknown |
| P4构建/软件仿真/真硬件 | R0 | 分层均未执行；吞吐、延迟、阶段/内存资源绝不声明复现 |

补丁分类、应用SHA、原因与等价性影响见 `patches/mousika/README.md`。最优下一步是先补齐 ISCX/Bot-IoT处理与评估路径和作者环境证据，再决定是否投入有授权的Tofino设备；这是建议，未执行外部采购/申请。
