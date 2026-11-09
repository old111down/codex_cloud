> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# ETC_NOMS_2024 复现报告

本轮等级为 **R2，仅针对附带真实 NIMS 样本上的RF训练/压缩核心算法**。模型表项生成及两项修复有独立软件验证。原论文全部用例/指标、P4编译、交换机仿真、真实Tofino硬件均未复现；相应结果为 Unknown，不给论文整体授予R2以上结论。

## 固定来源与静态范围

- 论文：[作者接受稿](https://dspace.networks.imdea.org/bitstream/handle/20.500.12761/1791/etc_noms24_postprint.pdf?sequence=1&isAllowed=y)，NOMS2024，DOI `10.1109/NOMS59830.2024.10575394`。
- 作者仓库：[nds-group/ETC_NOMS_2024](https://github.com/nds-group/ETC_NOMS_2024)，`main@52de99ad76d9eff2f64a0fa28df0500e423b58b2`。论文p.1脚注与README互相验证关联。
- 全文Methods/Implementation/Evaluation已读取；无Appendix。`coverage_matrix.csv`列出Fig.1–4、Algorithm1、TableI–II、三个数据集及重要资源/时延/线速声明。`static_audit.md`列出缺口和静态缺陷。
- 上游保持未修改；最终 `git status --porcelain` 为空。无显式代码许可证，许可 Unknown；未把作者源码、数据和生成的第三方大文件复制进审计Git提交。

## 实际环境

宿主Debian13(trixie)、Linux x86_64；本次Cloud主机资源见共享 `environment/` 清单（4CPU配额/16GiB内存，无GPU）。原论文测试床是3台Edgecore Wedge100BF-QS/Tofino BFN-T10-032Q、2台Xeon8核2GHz/48GB服务器、100Gbps光链路，本机不等同于该环境。

独立Conda前缀：`.conda/etc_noms_2024`。实际Python3.8.20、NumPy1.19.5、SciPy1.5.4、pandas1.1.5、scikit-learn0.23.2、Matplotlib3.3.4、Seaborn0.11.2、netaddr0.8.0、XGBoost1.3.3。系统GCC/G++14.2.0、binutils2.44、glibc2.41。Python `platform` 的兼容基线字符串显示glibc2.17，不替代实际 `getconf GNU_LIBC_VERSION=2.41` 记录。PyTorch/CUDA未安装且该RF路径不需要；`tshark`、`bf-p4c`、`p4c`、`simple_switch`不存在。

环境依据是notebook metadata中Python3.8.5和原pickle中sklearn0.23.2，其他版本为本次明确选择的兼容组合，**不是原作者完整锁定环境**。原环境其他版本 Unknown。没有关闭TLS校验，也没有安装专有Intel SDE/BFRT/P4 Insight。

文件：`environment/etc_noms_2024/environment.yml`、`requirements.txt`、`conda-explicit.txt`、`pip-freeze.txt`、`runtime-versions.json`。pip完整解析来源/下载校验值在 `pip-install-report.json`；Conda包的确定URL在explicit清单。

## 实际命令和原始日志

所有相对路径以审计仓库根目录为基准。运行器 `scripts/run_logged.py` 记录实际argv、cwd、UTC时间、退出码和stdout/stderr；以下命令的精确版本在同名前缀JSON中。

| 顺序/动作 | 实际命令或入口 | 结果/证据 |
|---|---|---|
| README原样尝试1 | cwd=`upstream/etc_noms_2024/Offline_ETC`; `bash data_preparation/pcap2csv.sh datafile.pcap` | exit127：tshark缺失；`logs/etc_noms_2024/readme_pcap2csv.{json,log}`。README示例文件也不是附带数据，未声称执行了真实PCAP抽取。 |
| P4编译器探测 | `bf-p4c --version` | exit127，命令不存在；`p4_compiler_probe.{json,log}`。README只说“compile”而没有完整编译指令，无法按原文真正启动构建。 |
| 环境创建 | `.tools/miniforge3/bin/conda create --prefix /workspace/traffic-repro-audit/.conda/etc_noms_2024 --override-channels -c conda-forge --yes python=3.8 pip=24.3.1` | exit0；`conda_create.{json,log}`。 |
| 依赖安装 | `.conda/etc_noms_2024/bin/python -m pip install --only-binary=:all: --report environment/etc_noms_2024/pip-install-report.json -r environment/etc_noms_2024/requirements.txt` | exit0；`pip_install.{json,log}`。 |
| 最小执行/核心样本 | `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLBACKEND=Agg python scripts/run_logged.py --log logs/etc_noms_2024/notebook_subset --timeout 180 -- .conda/etc_noms_2024/bin/python papers/etc_noms_2024/run_notebook_subset.py` | exit0；原notebook选定单元逐个输出；`notebook_subset.{json,log}`。 |
| README原样尝试2 | cwd=`upstream/etc_noms_2024/Offline_ETC`; 独立环境 `python data_preparation/pkts2flows.py` | exit1：`inputdir`占位路径不存在；`readme_pkts2flows.{json,log}`。README要求修改路径，因原数据未获取而不虚构替代路径。 |
| 原样模型翻译 | 把原generator、pickle、testCSV按hash复制到独立runtime目录；cwd=`papers/etc_noms_2024/runtime-artifacts/generator`; 独立环境 `python generate_table_entries.py` | exit0但7776票项超过P4声明容量；`model_generation.{json,log}`。 |
| 补丁1 | `git apply --check`，再`git apply --directory=papers/etc_noms_2024/runtime-artifacts/patched patches/etc_noms_2024/0001-unique-voting-mode.patch`；运行同一generator | check/apply/generate均exit0；`patch_check`、`patch_apply`、`model_generation_patched`。 |
| 首次表项对照 | 独立环境 `python papers/etc_noms_2024/validate_generated_tables.py` | exit1，feature0范围与随附表不符，原失败保留 `table_validation.{json,log}`。 |
| 补丁2 | 顺序check/apply `0002-feature-range-domains.patch`，再次运行generator | exit0；`patch2_check`、`patch2_apply`、`model_generation_patched_v2`。 |
| 最终表项对照 | 同一`validate_generated_tables.py`入口 | exit0；`table_validation_v2.{json,log}`。所有生成表项集合和7776种投票输入通过对照。 |

环境导出实际执行：`.tools/miniforge3/bin/conda list --prefix .conda/etc_noms_2024 --explicit`、`.conda/etc_noms_2024/bin/python -m pip freeze`。依赖安装日志、所有失败日志均保留，没有以最终成功输出覆盖早期失败。

## 数据和模型

来源/字节数/SHA256集中保留在 `evidence/etc_noms_2024/data_model_sources.json`，所有上游追踪文件hash在 `upstream_files.csv`。附带 `NIMS_IMA_sample_data.csv` 为作者README说明的2022-11-08一天派生数据，1867行、6类；SHA256 `dd8090a26c846a7dd15ba9b91881196a4d029cf91abb2aa01f42fec0627e9cac`。完整原始PCAP未获取，原始提取流程的等价性 Unknown。

选定原notebook过滤后1714行，75/25分层seed42切分为1285训练、429测试。标签顺序是Discord、WhatsApp、Signal、Telegram、Messenger、Teams。没有合成流量替代原数据。保留的429行testCSV来自作者仓库，并非本轮真实交换机回传结果。

原 `noms2024_20_5.pkl` 来自同一固定commit；执行前用pickletools审阅操作码/全局名及内嵌版本，记录 `model_pickle_review.json`，再在180秒限时的独立子进程中用于模型表项生成。该审阅不是形式化安全证明。核心训练测试没有加载该pickle，而是用原notebook单元重新训练；审计重训权重只留本地runtime目录及hash。

Netflow QUIC、ISCX VPN及NIMS完整PCAP只记录作者给出的原始来源链接，未成功下载，因此它们的文件校验值、许可、完整标签分布和实测可达性均为 Unknown。

## 样本结果与论文指标

原样执行的是notebook单元0、1、2、4、6、10、11、12、14、15、18；跳过cell8完整模型搜索、cell13压缩搜索、cell16/17覆盖上游模型/数据的保存操作，以及cell20/21缺失硬件digestCSV的后处理。**不是完整notebook执行。** 选定固定深度20、5树、max_leaf_nodes500，四特征为Flow IAT Min、Max Packet Length、Flow IAT Max、Packet Length Total。

| 指标 | 本轮真实样本压缩模型（Python离线） | 论文NIMS硬件Fig.4 | 可直接比较？ |
|---|---:|---:|---|
| Accuracy | 91.6084% | 89.74% | 否：运行位置/评估范围及投票语义不同 |
| Macro F1 | 91.6056% | 90.29% | 否 |
| Weighted F1 | 91.6479% | 89.82% | 否 |

逐类指标和单元耗时见 `core_sample_metrics.json`；cell12耗时约0.0387秒，cell14约0.0260秒，均包含单元内数据处理/训练/预测/报告，并非独立训练耗时基准。只执行一次固定seed测试，无置信区间；训练时间、峰值RAM、能耗或系统吞吐与论文的可比结果 Unknown。

论文Netflow QUIC Accuracy95.28%、ISCX VPN87.16%均未测；Table I全部三数据集/模型/类别条目仅静态覆盖。Table II资源比例、383–398ns时延、线速与40Gbps背景负载全部未验证。没有将样本分数高于论文分数解释为超越或复现论文性能。

## 编码修复及实验等价性

`patches/etc_noms_2024/README.md`逐项解释原因、分类、适用SHA和应用顺序。补丁1为环境兼容性修复，显式恢复与随附投票表一致的唯一众数行为；补丁2为数据处理修复（RF→P4编码配置），限制末区间为P4的15/16/8/16位域。

原样票表7776项，随附/修复后5256项；360种有效决策差异在修复后消除。所有feature/code/voting/target-flow表项参数集合与随附脚本一致，最终指标在 `table_validation_metrics.json`。端口配置仍不同，完整部署脚本字节不相同。表项一致不证明scikit-learn RF概率平均预测与P4硬投票一致。

位宽补丁只适用于固定模型，未提供任意新模型阈值越界保护；32位时间戳/16位总长度溢出、逐流IAT单位、包截断、长流、碰撞与控制器时序没有包级仿真。这些语义和真实数据预处理一致性均为 Unknown。

## 分层结论与下一步

| 层 | 本轮结论 |
|---|---|
| README原样运行 | 两个可复制数据准备命令已尝试并失败；安装/训练/P4构建没有完整锁定命令，不能宣称README全流程通过。 |
| 最小Smoke | 原notebook导入/函数/样本切分和小型RF拟合已执行通过；仅软件Python路径。 |
| 真实样本核心算法 | R2：1285/429的真实附带样本训练/压缩测试通过。 |
| 原数据预处理与12折评估 | R0/Unknown：缺完整原PCAP、全量中间文件、原实验配置及可核对折分。 |
| P4模型表项生成 | 原样执行暴露兼容性/位宽问题；两隔离补丁后软件表项对照通过。 |
| P4构建 | 未执行成功：SDE9.7.0及bf-p4c缺失。 |
| 软件交换机/包级仿真 | 未执行：无BMv2实现/拓扑/测试且源码依赖TNA。AST/穷举投票测试不算P4仿真。 |
| 真实交换机资源/性能 | R0/Unknown：无Tofino硬件和授权SDE，不声明线速、时延或资源复现。 |

下一轮应先获取可合法使用的完整数据并固定处理/切分协议，修复/验证离线RF调用接口与min_iat作用域，明确软投票/硬投票比较；若研究者选择硬件复现，再准备授权SDE/真实Tofino、全部三用例配置及负载/资源测量协议。所有尚无证据的性能、完整流程和算法等价性结论保持 Unknown。
