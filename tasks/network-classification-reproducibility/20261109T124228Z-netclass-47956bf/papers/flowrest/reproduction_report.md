> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Flowrest 本轮复现报告

**R2仅限UNSW16与UNIBS8公开作者派生CSV上的CPU核心算法；没有复现完整论文。** 原会议版与2025期刊扩展按同一family分开记录，覆盖83行；主/全部用例完整性为部分覆盖。

## 固定来源与环境

作者仓库main `13a527cfc0cac523b9f4be9a9366738bcdd3d5db`，最后commit2024-03-11T11:27:31Z，GitHub API更新时间另见metadata（不把updated_at当代码时间）。无显式许可证，Unknown。INFOCOM10页/ToN18页合法IMDEA作者稿均完整读取并SHA256归档。

独立Miniforge环境 `.conda/flowrest`：Python3.8.20、NumPy1.21.6、SciPy1.7.3、pandas1.3.5、sklearn1.0.2、Matplotlib3.5.3、seaborn0.11.2、IPython8.12.3。conference保存模型内嵌sklearn1.0.2，full旧模型0.23.2；本次明确选择兼容conference模型的环境，非作者完整锁定环境。宿主Debian13.6、GCC14.2、4CPU配额/16GiB，无GPU。核心脚本设置两个可用CPU affinity与OMP/OpenBLAS/MKL单线程；作者full get_scores内部n_jobs4仍保持，但仅有两个可用CPU，未静默改模型参数。实际工具链和无CUDA/PyTorch/P4编译器探测在 `environment/flowrest/runtime-versions.json`。

environment.yml、Conda explicit、pip freeze、pip下载report含URL/哈希均保存。Conda导出提示pip包不能由Conda可靠锁定；原始freeze与pip requirements另存。无GPU要求；没有安装SDE9.7.0/BFRT或管理员脚本。当前公开open-p4studio未做历史兼容构建验证。

## 数据、权重与代码

作者README公开share提供四个CSV，本轮成功下载约63.5MB，准确大小、HTTP200、时间、URL与SHA256见 `downloaded_data_manifest.json`。UNIBS原CSV为20664训练/19636测试行；UNSW经原MAC标签筛选后215484训练/73249测试行。原始捕获→CSV、时间单位说明、原论文日期/会话样本映射仍Unknown。文件许可未明确，不把公开链接当成任意再分发授权；数据只存本地ignored runtime目录。

三个作者RF权重均先审阅pickle opcode/字符串与来源/hash，再在独立限时进程中使用；静态审阅不是安全证明。全部tracked源码hash和洁净状态在source_manifest.json。生成文件、重训模型不复制进审计Git，保留hash/命令；上游从未修改。

## 原样尝试与实际运行

README没有安装、训练、编译命令或依赖锁，仅描述notebook/脚本入口。以下为实际执行的原入口/外部审计harness，并不称作“README全流程通过”。每项实际argv/cwd/UTC时间/exit/stdout/stderr均在 `logs/flowrest/<run_id>.json/.log`。

| run_id / 阶段 | 结果与边界 |
| --- | --- |
| conda_create / pip_install | 独立Conda和明确版本依赖安装exit0。 |
| original_conference_generator | 初始审计cwd未复制所需sav而失败，这是harness输入设置问题；失败原样保留。 |
| original_conference_generator_with_model | 将原sav按SHA复制到输出隔离目录后，原converter源码exit0（4.607s），生成BFRT表项脚本，未执行生成脚本。 |
| original_conference_notebook / original_full_notebook | 顺序执行原notebook codecell直到初始缺失rf3_train.csv / unibs2009_train_3_pkt.csv，exit1；下载数据后已解决该输入阻断。 |
| original_full_generator | YOUR_TRAINED_MODEL.pkl占位FileNotFoundError。 |
| full_generator_bundled_model_configured | 只把原full保存模型复制到占位文件名，不改源码，实测feature_names_in_ AttributeError。 |
| public_data_download | 仅四个README公开CSV文件，exit0，18.48s；没有下载整个2.5GB共享目录。 |
| synthetic_smoke | 原训练函数48行合成fit/predict、作者模型32行合成预测、F1量纲反例均通过。合成accuracy1只验证基本功能，不是网络或论文结果。 |
| generated_range_validation | 初始审计断言猜错末区间起点（猜8/32，实为7/26）而失败；未改作者输出。纠正harness预期后执行generated_range_validation_corrected_harness通过，确认两项越界。 |
| core_full | 原UNIBS notebook cells0/1/2/3/8/9，真实作者CSV，exit0（1.771s）。跳过grid、排序展示和保存，只跑固定原模型。 |
| core_conference | 原UNSW notebook选定模型/压缩/剪枝单元，真实作者CSV，exit0（6.792s）。跳过feature/bit/leaf全grid及保存。 |
| conference_time_alignment_sensitivity | 只改变一个条件：原cell20后将测试FlowIATMin/Max/Duration乘1000，与训练变换相同。原源码、数据、seed与模型保持，exit0（6.244s）。单位真实含义/论文等价性Unknown。 |
| original_full_notebook_with_public_data | 下载数据后，顺序执行UNIBS notebook全部12个原codecell源文本（含原grid、排序和保存）exit0（25.396s）；采用普通Python exec，不模拟IPython自动rich display，不是完整期刊实验流程。输出仅在隔离runtime目录。 |

命令范式（真实完整argv在对应JSON；根目录为审计仓库）：

```sh
python scripts/run_logged.py --log logs/flowrest/conda_create --timeout 300 -- .tools/miniforge3/bin/conda create --prefix /workspace/traffic-repro-audit/.conda/flowrest --override-channels -c conda-forge --yes python=3.8 pip=24.3.1
python scripts/run_logged.py --log logs/flowrest/pip_install --timeout 300 -- .conda/flowrest/bin/python -m pip install --only-binary=:all: --report environment/flowrest/pip-install-report.json -r environment/flowrest/requirements.txt
python scripts/run_logged.py --log logs/flowrest/public_data_download --timeout 300 -- python papers/flowrest/fetch_public_data.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg PYTHONDONTWRITEBYTECODE=1 python scripts/run_logged.py --log logs/flowrest/core_full --cwd papers/flowrest/runtime-artifacts/full --timeout 180 -- /workspace/traffic-repro-audit/.conda/flowrest/bin/python /workspace/traffic-repro-audit/papers/flowrest/run_core.py full
```

## 指标与论文比较

| 条件 | Accuracy | MacroP / R / F1 | WeightedP / R / F1 | 解释 |
| --- | ---: | --- | --- | --- |
| 原样UNSW16选定单元 | 0.645647040 | 0.566307 / 0.382577 / 0.402694 | 0.687338 / 0.645647 / 0.636482 | 本轮真实观察；不是旧notebook注释结果。 |
| UNSW16测试时间×1000敏感性 | 0.987030540 | 精确值见core_conference_time_aligned_metrics.json | 同左，MacroF1=0.919988848 | 仅数据处理敏感性条件，未声称原流程或论文等价。 |
| 原UNIBS8固定模型 | 0.996078631 | 0.967172 / 0.976970 / 0.971553 | 0.996244 / 0.996079 / 0.996094 | 同一作者派生CSV可运行，原期刊选择/硬件未重建。 |
| INFOCOM Fig6 | 未给单一全表精确accuracy | F1约0.99（二类）到0.86（26类） | 图中精确全项未数值化 | 数据任务/模型/运行位置不等价；不能拿UNSW16本地值代替26类图。 |
| ToN UNIBS Python TableV | Unknown | 0.98716 / 0.99759 / 0.99203 | 0.99944 / 0.99939 / 0.99940 | 本轮MacroF1=0.971553不同；exact模型/输入/选择协议不明，不判论文结果成功。 |
| ToN UNSW Python TableV | Unknown | 0.84051 / 0.82190 / 0.81010 | 0.95320 / 0.94668 / 0.94586 | 期刊UNSW26与本轮conference16类不同，不能直接比较。 |
| ToN TableVI | 不适用 | 延迟364.75–436.07ns | 线速/资源等均Unknown | 未做P4构建/硬件测量。 |

逐样本预测、各类P/R/F1、模型参数/树节点/叶数、输入hash、seed和单元耗时均归档。单元walltime含处理/训练/评估，不能代替可比训练或推理性能。完整原始raw处理、所有任务、基线、模拟器、资源代价选择、packet流长度权重、延迟校准均未复现。R3/R4不成立。

## 已确认、观察、推测与未知

- 已确认事实：官方关联、固定源码、公开CSV实际可下载、上述缺失文件/接口/量纲与变换不对称、generated键范围越界；证据逐项在static_audit和coverage矩阵。
- 运行观察：两个真实数据组件可执行；原UNSW低分与单因素敏感性改善；full原模型接口失败；表项生成exit0但越界。
- 合理推测：训练/测试时间尺度不一致可能解释UNSW偏差；测试集选模型可能使原结果偏乐观。真实单位与偏差量未获独立原始数据证据，不提升为论文错误定论。
- 尚未验证：原论文样本/模型和版本等价、精度/速度/规则数/资源全项、真实数据无泄漏、历史SDE与当前公开SDK兼容、交换机吞吐/时延。

本轮无上游补丁。时间对齐只存在于明确命名的审计敏感性harness分支，属于数据处理变更条件，不作为已确认修复或论文等价结果。下一轮优先向公开证据补齐单位/日期和原selected模型，再验证完整三个/五个用例；不先投入硬件。
