> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Pegasus 追加轮运行与复现报告

**本轮等级R1，仅CPU有限Smoke。** 六类模型有公开实现、P4文本生成器可运行，但真实原数据、原论文checkpoint和原硬件评估未重现；没有达到R2/R3/R4。

## 版本、环境与数据

官方源码master `a73bd327fbf0db2550a9bc1e304b96e0aa550cba`，Apache-2.0，checkout保持pristine。阅读范围为15页公开arXiv v1/作者同SHA副本，Fig1–9/Table1–6；最终ACM403，最终独有修改Unknown，详见静态审计。

独立Conda前缀`.conda/pegasus`，Python3.8.18匹配README；NumPy1.24.3、pandas2.0.3、SciPy1.10.1、sklearn1.3.2匹配源码requirements固定项，matplotlib3.7.5、numba0.58.1等为实际解析版本。Torch在README未固定版本，本轮显式选择官方CPU wheel2.4.1+cpu；无GPU/CUDA。Python构建GCC12.3.0，宿主GCC14.2.0。所有实际版本、environment.yml、resolved yml、Conda explicit和pip freeze在`environment/pegasus/`。Conda freeze含本地构建来源URL的移植限制仍适用。README完整安装recipe没有逐字通过：`conda create-n`缺空格，clone后停在repo根目录而requirements实际在software子目录。本轮实际安装修正命令和工作目录；这些literal失败已补审留日志，不能称原文全部setup通过。

仓库120MB展开（245个blob约113MB），没有安装VM/专有SDK或调用付费服务。对应软件测试CSV/JSON不在仓库；公开PeerRush Drive链接HEAD返回200，但内容为2459字节HTML而非数据附件，没有完成真实测试集下载，不能把链接存在称为数据已取得。原PCAP/split ID/数据许可及校验值Unknown；没有用BMv2的其他pkl/pcap冒充软件原test集。

本轮模型输入为显式合成9×10整数特征、标签0/1/2，seed42，仅检查CPU加载和输出形状。使用作者当前MLP checkpoint（53490字节，SHA256`8d53350a788ff062f0b4f0f2dce1a3c92b543178f4d5812a85d1bf052ca2bfd0`）；作者声明当前权重为重新训练的替代品，不是丢失的论文原权重。静态pickle GLOBALs只有OrderedDict/torch tensor rebuild/FloatStorage，后续harness使用`torch.load(weights_only=True)`，严格state_dict匹配。没有把该有限检查描述为形式化安全证明。输入和模型来源/哈希见`evidence/pegasus/`。

## 实际命令、失败与观察

精确argv、cwd、UTC起止、exit code、stdout/stderr保留于`logs/pegasus/<run_id>.json/.log`。

| run_id | 实际动作 | 结果 |
| --- | --- | --- |
| conda_create | `.tools/miniforge3/bin/conda create -y --override-channels -c conda-forge -p /workspace/traffic-repro-audit/.conda/pegasus python=3.8.18 pip=24.3.1` | exit0 |
| torch_cpu_install | `.conda/pegasus/bin/python -m pip install torch==2.4.1+cpu --index-url https://download.pytorch.org/whl/cpu` | exit0，明确CPU依赖选择 |
| readme_dependencies | cwd=`upstream/pegasus/software`，原样`pip install -r requirements.txt` | exit0；`matplotlib--inline`由pip标准名称规范化接受，不是确认的安装bug |
| readme_cpu_cnnl | 原README示例`python -m quickdemo.cnnLtest --dataset PeerRush --ptpth save/cnnL/PeerRush/CNNL_PeerRush.pt --testpth dataset/PeerRush/redeal_test.json --device cpu` | exit1，缺真实JSON；在失败前已torch.load官方CNN-L checkpoint，未完成真实推理/指标 |
| model_smoke | `.conda/pegasus/bin/python papers/pegasus/model_smoke.py` | exit0；预审MLP替代权重严格加载，输出9×3且有限、log概率归一化 |
| unmodified_mlp_synthetic | 原`quickdemo.mlptest`，仅将testpth指向明确合成CSV、PeerRush权重、device cpu | exit0，打印synthetic macro-F1=0.3485；不作网络结果/论文比较 |
| readme_p4_syntax | cwd=`hardware/p4_syntax`，原`codegen.py mlp16.p4g <隔离输出>/mlp16.p4` | exit0，仅文本生成；未P4编译/包级仿真 |
| split_grain_diagnostic | 原FlowDataset+AST提取未修改`build_data_loader`函数，一条40包合成flow、window8、val_ratio=.2 | exit0；确认窗口切分允许同flow共享训练验证包。不是训练或原外部test泄漏验证 |
| readme_literal_conda_typo | 补审原文`conda create-n Pegasus python=3.8.18` | exit2，子命令不存在；没有创建额外环境 |
| readme_literal_root_requirements | 补审原文clone后repo根目录`pip install -r requirements.txt` | exit1，该工作目录无requirements.txt |

上述运行限制线程为1，保持PYTHONDONTWRITEBYTECODE，不改原始源码。没有运行会申请管理员权限的BMv2/VM安装脚本。raw读取/导出命令也保留来源与环境清单。

**审计流程偏差如实记录**：CNN-L命令11:26:24Z启动，11:26:26Z因缺JSON退出；该checkpoint专门静态pickle审查在11:26:38Z才完成，属于先加载后补审，违反本仓库预审顺序。`cnnl_weights_static_review.json`包含实际时间、hash和准确说明；补审仅见已知tensor/storage/OrderedDict GLOBALs，不能倒称预审或安全证明。后续MLP已在11:25:00–05的retrieve_evidence步骤中预审，并用受限loader。审计自写首次inline检索harness还曾有IndentationError，解析即失败、未运行fetch/model，原错误在`retrieval_harness_initial_failure.log`，不能归咎上游。

## 论文结果的可比性

| 论文指标/用例 | 原文参照 | 本轮可比实测 |
| --- | --- | --- |
| Table5 MLP-B PeerRush macro-F1 |0.8823|Unknown；0.3485是合成标签功能输出，不可比较 |
| Table5 RNN/CNN-B/M/L三数据集PR/RC/F1 |公开稿有全部列值，CNN-L F1=0.9966/0.9380/0.9872|Unknown，未取得原test数据/原权重 |
| Fig7流状态位宽与F1、Table6 SRAM/TCAM/Bus |公开稿硬件值|Unknown，P4文本生成不能代替硬件测量 |
| Fig8三正常域×六攻击AUC |平均AUC约0.950/0.894/0.990|Unknown，未运行AutoEncoder真实混合攻击测试 |
| Fig9 CPU/GPU精度与吞吐 |平均约1.08% macro-F1损失、CPU3800×/GPU600×吞吐增益|Unknown，无原硬件/四V100与计时协议；源码中重画归档数字不算新实验 |

公开论文的“accuracy/macro-accuracy”明确定义为packet-level macro-F1，不能解读为传统Accuracy。ISCX“seven”文本/六类源码、原权重丢失、软硬件文档冲突及validation粒度均已单列证据；它们不自动证明原论文数据上的具体误差。source/method/metric等价性的未验证部分保持Unknown。

## 分层结论

- A公开完整性：六模型训练/测试/转换、标准P4、CNN-L部署和MLP-B BMv2均有对应代码，但全部实验/原数据/原权重/性能协议未完整公开或取得；不判为完整论文可执行。
- B运行：独立CPU环境、原样MLP合成输入和P4G生成器可运行；真实README CNN-L测试被数据缺失阻断。R1。
- C论文结果：全部真实Accuracy/PR/RC/F1/AUC/模型规模对齐、原始split/seed、性能/资源指标未验证。无R2以上结论。
- P4模型文本生成已通过；P4编译、BMv2运行、真实Tofino均未完成。公开SDK与原授权硬件/toolchain仍需单独规划。
- 没有修复或改写上游模型。下一轮应先获取作者原始测试文件和明确six/seven类定义、替代权重训练过程、原硬件结果来源；再以flow分组验证训练/validation/test独立性，并对全部模型做软件–P4逐输入对照。
