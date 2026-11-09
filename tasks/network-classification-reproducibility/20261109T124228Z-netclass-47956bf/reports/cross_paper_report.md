> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# 网络流量分类复现审计：首轮跨论文报告

审计日期：2026-11-09；范围：2021-11-09—2026-11-09。**已建立11篇论文—作者仓库关联核实记录、三个试点的138行覆盖矩阵、三个独立Conda环境与实际最小测试。没有任何试点达到论文完整结果复现（R3/R4）。** R0–R4是本仓库的本地分层约定，见 `AGENTS.md`，不是外部统一认证。

LiM和ETC在作者附带真实派生CSV上完成了限定核心算法测试，分别记为组件R2；Mousika整篇保持R1，UNIV前缀组件单独标R2，ISCX应用分类仍为R0。三个试点均保留原样失败、原始日志及未验证项。真实交换机、线速吞吐、硬件时延与资源结果全部未验证，对应复现结论为 **Unknown**。

## 首轮交付与审查入口

| 验收项 | 实际产物与结论 |
| --- | --- |
| 仓库基础结构与约束 | `README.md`、`AGENTS.md`、日志/环境/来源/校验/目录构建脚本；本地Git分支 `audit/round1` |
| 至少10篇核实候选 | `catalog/candidates.csv` / `.json` 共11篇；包含题名、年份、会议/期刊、DOI或Unknown、论文/仓库、分支/SHA/许可/更新、任务/数据/模型/部署/依赖及关联证据 |
| 三试点静态覆盖 | Mousika82行、ETC38行、LiM18行；每篇均有独立复核。计数粒度不同，不计算跨论文“覆盖率排名” |
| 环境和最小运行 | 三个独立Conda环境、README原样尝试、限定Smoke与核心样本日志；精确包清单、版本、数据/模型来源与校验值已归档 |
| 跨论文比较与归档 | 本报告、逐论文 `reproduction_report.md`、隔离补丁、上游固定版本及校验清单。未发布到外部Git托管或网站 |

所有相对路径以仓库根目录为基准。结构与证据文件完整性检查入口为 `python scripts/validate_audit.py`、`python scripts/verify_checksums.py`；它们不证明科学结论正确。

## 候选目录与关联依据

首轮是经核实的候选集合，并非对五年文献的穷尽式系统综述。没有把名称相似的普通软件项目纳入，也没有把非网络演示当成网络分类证据。

| 论文/简称 | 年份与出处 | 作者仓库 | 已核实的关联及范围 |
| --- | --- | --- | --- |
| Mousika | 2022 INFOCOM | [xgr19/Mousika](https://github.com/xgr19/Mousika) | 原论文结论直接链接仓库；作者官方主页链接全文。原版三教师与ToN扩展版五教师分开审计 |
| ET-BERT | 2022 WWW | [linwhitehat/ET-BERT](https://github.com/linwhitehat/ET-BERT) | 论文首页直接给出源码；精确题名/作者/DOI匹配 |
| YaTC | 2023 AAAI | [NSSL-SJTU/YaTC](https://github.com/NSSL-SJTU/YaTC) | 出版方文章页直接给出源码；README引用匹配 |
| ETC | 2024 NOMS | [nds-group/ETC_NOMS_2024](https://github.com/nds-group/ETC_NOMS_2024) | 论文p1脚注直接链接；不把2025期刊扩展脚本计入NOMS覆盖 |
| Leo | 2024 NSDI | [Purdue-ISL/Leo](https://github.com/Purdue-ISL/Leo) | 原文脚注明确源码；在线分类。权威BibTeX未提供DOI，本轮DOI为Unknown |
| Brain-on-Switch | 2024 NSDI | [InspiringGroup-NeoLab/Brain-on-Switch](https://github.com/InspiringGroup-NeoLab/Brain-on-Switch) | 论文原链接重定向到该规范仓库；迁移与作者引用有证据。DOI为Unknown |
| LINC | 2024 ICNP | [haolinyan/LINC](https://github.com/haolinyan/LINC) | 作者托管全文脚注直接链接；覆盖增量更新候选 |
| IIsy | 2024 IEEE/ACM ToN | [In-Network-Machine-Learning/IIsy](https://github.com/In-Network-Machine-Learning/IIsy) | 作者仓库精确DOI/作者关联，原论文有UNSW-NB15网络分类。当前默认Iris演示不是网络复现 |
| NetMamba | 2024 ICNP | [wangtz19/NetMamba](https://github.com/wangtz19/NetMamba) | 原论文脚注直接链接；原版与NetMamba+分开 |
| LiM | 2025 WWW Companion | [nime-sha256/LiM](https://github.com/nime-sha256/LiM) | arXiv v2脚注与README精确引用双向关联 |
| MH-Net | 2025 AAAI | [ViktorAxelsen/MH-Net](https://github.com/ViktorAxelsen/MH-Net) | 原论文首页直接给出源码；README引用匹配 |

除三个试点外，另外八篇只做目录/关联核实，等级R0，执行结果全部Unknown。候选的数据、权重未下载者，其可达性、许可、校验值均不从链接存在推断。YaTC全文直接下载403，使用官方文章页确认关联；README四数据集与摘要五数据集之差仍待完整审计。MH-Net日期来源差异保留在候选unknowns。

## 三个试点的覆盖和实际执行

| 维度 | Mousika | ETC_NOMS_2024 | LiM |
| --- | --- | --- | --- |
| 固定主SHA | `76c9db9b4200a7c591bd1e9476ba5ab44a467512` | `52de99ad76d9eff2f64a0fa28df0500e423b58b2` | `1b8ca187f7d02a51e595f797e5c200ae740b459f` |
| 论文阅读范围 | INFOCOM作者版10页；ToN作者版14页，独立版本映射 | NOMS作者接受稿9页；2025期刊版不另行复现 | arXiv:2502.00586v2共7页；最终ACM4页版HTTP403，最终独有修改Unknown |
| 全部用例 | UNIV流大小预测、ISCX六类、Bot-IoT二类；两版教师/评估/硬件差异分别覆盖 | NIMS六类、Netflow QUIC五类、ISCX VPN七类及离线/交换机评估 | CSTNET十类、LiM/ET-BERT/YaTC两表、无握手与秒级新类适应声明 |
| 编号对象 | 原版Fig1–10、扩展Fig1–18，各自TableI/Algorithm1/Listing1–2 | Fig1–4、TableI–II、Algorithm1，按三数据集展开 | Table1–2；公开版本无编号图/Appendix |
| README原样 | 保留缺torch、未解压CSV、v2无条件CUDA失败；五套原规则转换通过 | 数据提取因tshark/占位路径失败；训练/编译指令不完整 | 安装和原样分类器通过；PCAP占位路径exit0却仅写空CSV，不能算预处理成功 |
| 限定Smoke | 原Tree/SoftTree、ternary转换、补丁数值反例；通过 | 原notebook选定单元、样本切分与小RF训练；通过 | 合成依赖/fit及真实CSV原样运行；通过 |
| 真实数据核心 | UNIV训练前512/测试前256，undersampling后70训练行；仅组件 | NIMS1867原始行→1714过滤行；1285训练/429测试 | 作者4514行CSV；3611训练/903测试 |
| 等级边界 | 整篇R1；UNIV函数组件R2；ISCX/Bot-IoT R0 | NIMS样本核心R2；其他原流程/硬件R0 | 作者CSV核心R2；原PCAP、完整原评估/资源/在线R0 |
| 许可 | 未发现许可证，Unknown | 未发现许可证，Unknown | MIT；原始流量许可不据此推断 |

覆盖矩阵的“已验证”仅限清楚注明的执行项。其余大量“部分覆盖”表示存在部分对应代码/证据，不表示论文精度或部署已经运行成功。全部尚无实验依据的性能、完整流程、数据等价性结论均保留Unknown。

## 观测指标与等价性

| 试点/指标 | 本轮实际结果 | 论文参照 | 为什么不能称为论文复现 |
| --- | --- | --- | --- |
| Mousika UNIV前缀 | Accuracy0.76953125 | INFOCOM UNIV RF蒸馏BDT94.95% | 小前缀/70训练行，仅验证函数链；不代表ISCX网络应用分类，不与全量精度或时间比较 |
| ETC NIMS压缩RF | Accuracy0.9160839161；MacroF1=0.9160557133；WeightedF1=0.9164790889 | NIMS硬件Fig4：Accuracy89.74%、MacroF1=90.29%、WeightedF1=89.82% | 单日样本、离线Python位置、原始PCAP/12折/硬件投票语义未等价；QUIC/VPN未运行 |
| LiM作者CSV | 903测试中861正确；Accuracy0.9534883721；MacroF1=0.9530904896 | Table1 Accuracy0.942、F1=0.942 | 4514行、每类372–486，不是论文4000行平衡样本；Python/XGBoost与论文不同；样本ID、原划分和平均方式不明 |

以上结果针对不同任务和数据，不能据其高低比较方法优劣。独立复核重新核对了LiM全部逐样本预测和指标；ETC固定split与RF均有seed42。单次/功能性重跑不构成重复实验统计或性能基准。各命令整体walltime/单元耗时已记录，但可比训练时间、峰值内存、能耗、吞吐测量均Unknown。

LiM另有两类证据：代码在切分前拟合StandardScaler，原始会话来源/独立性不可核验；正文部分“higher%”按ratio×100而非(ratio−1)×100计算，纯算术问题已单独归档。这些发现不验证或否定未重测的Table2绝对性能值。

## P4必须分层解读

| 层级 | Mousika | ETC | LiM |
| --- | --- | --- | --- |
| 模型/规则生成 | CPU函数和五套文本→ternary限定验证；未完整恢复三任务 | 原样generator运行但暴露投票容量/位宽问题；两补丁后与随附artifact的表项参数集合一致 | 不适用 |
| P4构建 | 未成功执行；缺SDE与公共include等 | 未成功执行；缺SDE9.7.0/bf-p4c | 不适用 |
| 软件交换机/包级仿真 | 未执行，无可核验BMv2流程 | 未执行；TNA实现、无BMv2拓扑/测试。AST/穷举投票不是P4仿真 | 不适用 |
| 真实交换机 | 未验证Tofino/Keysight或扩展版三交换机结果 | 未验证Tofino、原负载/端口/资源和时延 | 不适用 |

没有把软件表项一致、代码静态存在或CPU精度解释为线速吞吐/硬件资源复现。也没有使用未经授权的专有SDK、软件或数据。

## 环境、来源与补丁

实际主机Debian13.6、x86_64，可见5逻辑CPU但cgroup配额4核、内存上限16GiB、初始可用磁盘约29.8GiB、无swap，未发现GPU/CUDA工具。普通agent用户、无sudo；网络策略enforced/unrestricted，GitHub/Conda/pip和公开作者站均有实际访问证据。完整原始探测见 `environment/host_probe.json`，不要将宿主可见内存等同于容器上限。

使用官方Miniforge3 `26.9.4-2`，安装器SHA256已对照官方release API digest。每篇独立前缀，未修改系统Python。

| 环境 | Python | NumPy / scikit-learn | PyTorch / XGBoost | 论文环境等价性 |
| --- | --- | --- | --- | --- |
| Mousika | 3.10.22 | 1.24.4 / 1.2.2 | 1.13.1+cpu / 未用于此测试 | 兼容性选择；ToN写Python3.6/NumPy1.19.3，等价性Unknown |
| ETC | 3.8.20 | 1.19.5 / 0.23.2 | 未安装 / 1.3.3 | Python/sklearn有notebook与pickle线索；其余为明确选择，不是作者完整环境 |
| LiM | 3.11.18 | 1.26.4 / 1.4.2 | 未安装 / 2.1.1 | 符合README pins；论文写Python3.13.0/XGBoost2.1.2，未恢复 |

各环境保留environment.yml、Conda explicit、pip freeze和工具链版本；pip本地构建URL/可移植性限制明确记录。CUDA包/NCCL被pip间接安装不代表存在GPU或已测CUDA。数据与权重以固定上游SHA、来源、大小、SHA256、许可/访问Unknown及用途区分；未把作者随附旧结果当作本次输出。原始源码固定版本和tracked-file哈希见 `environment/upstream_manifest.json`，四个checkout包含Mousika两分支，均保持干净状态。

四个隔离补丁的适用SHA、原因与实际复验见 `patches/README.md`及各论文子目录：Mousika整值浮点类别解析（运行错误修复）、Mousikav2右支Gini平方项（算法逻辑修改）、ETC众数平票兼容（环境兼容性）、ETC feature末区间位宽（数据处理/编码配置修复）。Mousika算法补丁改变分裂目标，未声称论文等价。ETC原样7776投票项超过固定P4容量5256；两补丁后5256项、全部7776输入与随附表一致，消除360个有效决策差异。但仍有端口差异、任意新模型阈值、时间戳/长度wrap及RF软投票对P4硬投票等未验证边界。

## 下一轮选择依据

1. **优先补齐ETC离线完整评估**：已有可运行旧环境、真实样本和表项对照；下一步依赖完整PCAP/处理文件、三数据集配置、12折与原图表协议，并需解决已列出的离线API/作用域和投票语义差异。
2. **LiM原协议与基线对齐**：需要原4000样本ID/划分/PCAP、TShark版本、ET-BERT/YaTC配置和权重、计时/内存/功率协议；接近或高于论文accuracy不能替代这些证据。
3. **Mousika应用分类路径优先于硬件投入**：补齐ISCX/Bot-IoT处理数据、原环境、LSTM/评估入口；v2 Gini修复应独立做敏感性分析，不能直接套回论文指标。
4. **下一批候选再作分层审计**：Leo/Brain-on-Switch偏在线P4，LINC覆盖增量更新；ET-BERT/YaTC/NetMamba/MH-Net有明显GPU依赖或待核实数据权重。IIsy必须显式选择UNSW网络用例，避免只跑Iris。

以上仅为研究者选择下一轮的证据与建议，本轮未开展采购、联系作者、发布代码或申请专有服务。
