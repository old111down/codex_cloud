> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Pegasus 静态论文—代码覆盖审计

固定作者仓库`afireswallow/Pegasus@a73bd327fbf0db2550a9bc1e304b96e0aa550cba`（master，Apache-2.0），论文SIGCOMM2025 DOI`10.1145/3718958.3750529`。官方清华研究组Open Source页明确给出该论文及仓库，README精确题名、会议/DOI与Crossref作者列表匹配，非按同名猜测。

## 论文版本边界与完整阅读

已读公开arXiv:2506.05779v1（2025-06-06），15页全部正文、§3–5方法、§6实现、§7.1–7.5全部实验、§8讨论、结论和参考文献；此版本无Appendix。作者madsys官方网站标为`SIGCOMM2025-zhang.pdf`的副本与arXiv下载**SHA256完全一致**（`52e9d6…93d31`），同样只有Fig1–9/Table1–6。ACM最终PDF HEAD403，Tavily亦无法获取，因此最终版独有改动/图表为Unknown，不能因文件名声称已拿到最终定稿。

仓库图名存在一位编号偏移，按内容而非文件名关联：`figure_generation/code/Figure8.py`对应公开稿Fig7（流状态内存/F1），`Figure9.py`对应公开稿Fig8（ROC），`Figure10a_b_c.py/Figure10d.py`对应公开稿Fig9（CPU/GPU比较与吞吐）。保留版本关系；不能把编号差异误认成实验缺失。

## A：代码公开完整性

六种主要模型有对应Python实现和测试/训练/量化/转换入口：MLP、RNN、CNN-B/M/L、AutoEncoder。`hardware/normal_version/`包含六模型P4源，`running_version/`公开CNN-L三类/六类部署与权重转换，`p4_syntax/`有MLP/CNN的Jinja2生成器。代码支持范围明显超过单个README演示，但没有证据证明全部论文任务/配置完整等价。

完整性阻断包括：实际软件CSV/JSON在外部Google Drive，仓库未附该测试集；原论文权重已被作者声明丢失；baseline N3IC/Leo/BoS完整实现/精确训练设置未全部随项目提供；全表数据只在论文/未取得的LaTeX源中，`figure_generation`主要重绘归档结果；CPU/GPU性能采样/多GPU吞吐复验脚本未见。Table5三数据集×八方法的PR/RC/F1、Table6资源、Fig7全部配置、Fig8六攻击×三正常域、Fig9性能均分别列入覆盖矩阵。

## 已确认事实与运行观察

1. **原始权重缺失及文档冲突**：顶层README说软件和硬件输出相同；`software/README.md`又明确原论文.pth文件丢失，当前模型从头重训，并承认软硬件实现不完全相同、可能寄存器冲突或丢包；`figure_generation/README.md`说明原实验数据来自硬件，软件仿真不能重现硬件数据，只绘制已收集结果。作者关于“差异很小”的判断本轮未验证。不能因顶部README声称精确论文结果可复现。
2. **标签定义不一致**：公开论文§7.1写ISCX“seven classes”，却仅列Email/Chat/Streaming/FTP/VoIP/P2P六名。代码`util/data_loader.py`/`bigcnn_data_loader.py`先定义含browsing的七标签映射，再显式跳过browsing，减一后使用六输出类；quickdemo也固定`ISCXVPN→6`。这是一项确认的文本/实现口径差异，是否仅论文笔误及最终版如何描述仍Unknown，不自行补第七类或宣称完成七类评估。
3. **“Accuracy”实际指macro-F1**：§7.1明确将packet-level macro-accuracy定义为各类F1平均值。因此Table5、Fig9和正文的“accuracy”不能解读为传统正确率。脚本常只返回macro-F1；PR/RC具体平均方式/全部原始结果协议需继续核实。
4. **滑窗后切validation**：`FlowDataset`将每个flow展开为stride1、window8的重叠窗口后，`train_net/runmodel.py::build_data_loader`对窗口索引作stratified train_test_split，而非先按flow分组。已用一条40包合成flow、参数`val_ratio=.2`演示33窗口切入train/validation且共享原包；CLI默认为.1，该诊断是机制反例，不是原75/10/15实测。真实外部train/test文件是否重叠、对论文独立test指标影响均Unknown，不能直接指控已确认test泄漏。
5. **CPU有限运行**：software目录中的原requirements安装成功，但README的`conda create-n`拼写和requirements工作目录错误使逐字setup recipe不成立，实际安装修正了命令/目录并留有literal失败日志。README CNN-L CPU命令因缺外部JSON失败。预审MLP替代checkpoint后，原模型类严格load_state_dict及9×10合成输入前向通过，未改quickdemo MLP也可运行；它打印的0.3485只是随机合成标签的macro-F1，不是网络分类结果。P4G→P4文本原入口通过，没有编译/仿真。

## 部署与尚未验证

BMv2只实现MLP-B；其README明确使用生成包来省略feature extraction，不能据此覆盖全部模型、真实原包处理或硬件吞吐。搭建指令依赖sudo/预装VM与第三方系统安装脚本，本轮未运行这些脚本。真实Tofino2、原SDK版本和高端CPU/四V100对照均未获取。当前公开open-p4studio可获得不等于已构建或与论文版本等价。所有硬件资源、吞吐、真实数据PR/RC/F1与原权重等价结论保持Unknown。

审计流程局限另见运行报告：初次CNN-L README命令在该checkpoint文件专门静态预审前已加载它；检查事后补做，实际时间/源hash准确保留，不能倒称预审通过。后续MLP采用已预审文件及`weights_only=True`。
