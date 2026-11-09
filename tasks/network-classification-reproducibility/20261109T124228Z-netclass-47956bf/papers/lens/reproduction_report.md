> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Lens 追加审计与限定诊断报告

**主模型R0；仅原始评估/参考划分函数为R1诊断组件。未复现任何Lens论文指标。** 论文与代码覆盖范围见 `static_audit.md` 和97行 `coverage_matrix.csv`。上游从未修改，没有上传PR、公开发布或使用收费资源。

## 本轮实际执行范围

完整Lens环境与README模型命令**未执行**。作者要求Python3.10/CUDA，论文使用4×A6000 48GB，代码模型加载选择flash attention/use_triton；本机无已验证GPU。本轮按静态审计发现建立了一个数值/划分诊断专用Conda环境，不把缺Torch的这个环境描述成完整Lens安装。

本轮没有下载模型、tokenizer、真实流量数据，也没有以合成输入替代论文数据。只直接加载两个固定commit的原样Python文件，以明确合成输入调用其中函数；绕过了不相关的Lens包模型导入，但没有改变函数或参数默认逻辑。

## 实际命令与日志

工作目录 `/workspace/traffic-repro-audit`。克隆并detached固定SHA：

```sh
GIT_LFS_SKIP_SMUDGE=1 git clone --no-checkout https://github.com/V-Enzo/Lens-foundation-model-for-network-traffic.git upstream/lens
git -C upstream/lens checkout --detach dc91fb981ccc27371556895f75546ea84dfd46e7
python scripts/run_logged.py --log logs/lens/metric_conda_create --timeout 600 -- .tools/miniforge3/bin/conda create -y --override-channels -c conda-forge -p /workspace/traffic-repro-audit/.conda/lens python=3.10 numpy=2.2.4 scipy=1.15.2 scikit-learn=1.6.1 pip
python scripts/run_logged.py --log logs/lens/metric_probe_dependencies --timeout 300 -- .tools/miniforge3/bin/conda install -y --override-channels -c conda-forge -p /workspace/traffic-repro-audit/.conda/lens pandas=2.2.3 tqdm=4.67.1
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python scripts/run_logged.py --log logs/lens/metric_split_probe --timeout 60 -- .conda/lens/bin/python papers/lens/metric_and_split_probe.py
```

以上三条日志封装命令均exit0。探针耗时1.117秒是整个Python进程walltime，不是Lens推理耗时。命令、cwd、UTC起止、退出码及stdout/stderr保留在 `logs/lens/*.json/.log`。上游clone/checkout来源另由API、完整tracked-file哈希与git状态记录保存。

专用环境实际为Python3.10.22、NumPy2.2.4、pandas2.2.3、SciPy1.15.2、sklearn1.6.1；这些数值包匹配作者pyproject所锁版本。Torch、Triton、Transformers等模型依赖**没有安装**。环境声明、Conda explicit、pip freeze、版本与导出命令在 `environment/lens/`。系统环境和无GPU证据复用实际宿主 `environment/host_probe.json`；本轮没有编译器或CUDA模型测试。

## 观察结果与解释边界

| 已运行组件 | 输入 | 原函数输出 | 可确认事实 | 尚不能确认 |
| --- | --- | --- | --- | --- |
| `cal_jsd_tvd_hd` | 两个不相交点分布[a,a]与[b,b] | JSD0.693147nats；TVD0.707107；HD1.414214 | 与常见标准TVD=1和Hellinger=1归一化不同；同分布控制输出全0 | 可能为作者自定义指标约定；Table6原预测、实际报告生成过程及绝对值影响Unknown |
| `split_dataset_by_label` + `split_dataset_to_train_val_test` | 400个明确SYNTHETIC flow IDs、2 coarse/8 fine类，各fine50 | coarsepretrain240；fine test40；交集22 | 相同记录全集独立生成两个粒度split时，参考代码可产生跨任务pretrain/test input重叠 | 实际HF数据/论文是否采用这些精确路径和是否允许transductive协议Unknown；不等于已证明监督标签泄漏 |
| 同coarse协议控制 | 同一400个fake IDs | test32与pretrain240交集0 | 同一split协议内部保持互斥 | 不推及所有实际任务/数据 |

原样源码SHA256、版本、结果和合成ID例子见 `metric_split_probe_results.json`。输入不包含真实网络通信、私有数据或凭据。未修复指标定义、未改动划分、没有创建算法等价性不明的上游补丁。

## 论文指标比较与未执行项

- Tables2/3的12任务Accuracy/MacroF1、Table4 per-class F1、Table5/14–16新类P/R/F1均为Unknown；没有模型训练、加载或真实测试集推理。
- Table6全部35个生成组合及JSD/TVD绝对分数Unknown；数值诊断不是这些实验的复现。
- Fig3五检测器fuzzing、Tables7/8/12/13的消融/敏感性、Table9统计与Table10原数据划分均未重建。
- 参数规模约0.25B和原GPU设置只是论文/源码事实；本轮实际模型规模、训练/推理耗时、峰值资源、吞吐均Unknown。
- P4构建、软件交换机和真实硬件层不适用：该论文没有提供P4方案，§5将真实系统部署留作未来工作。

后续最有价值的步骤是：固定HF数据/模型revision并获得原始flow ID及划分协议；确认TVD/HD作者定义与原始预测；补齐baseline/fuzzing/ablation配置；在合适且授权的GPU环境先只评估一个发布checkpoint，并与明确定义的纸面行比较。现有记录不能支持“论文完整实现/运行/结果已复现”。
