> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Pegasus 独立复核

复核日期2026-11-09，由负责YaTC的另一agent完成。已读83行覆盖矩阵、最终metadata/static/reproduction/execution_summary、关键README及软件入口/数据加载/绘图代码，并对照15页作者稿的编号范围与关键方法/实验章节。只复核现存证据，没有重新执行模型、加载pickle、编译P4、启动BMv2或真实硬件。

**结论：限定审计范围内通过。** R1只表示CPU有限模型/文本生成/合成诊断；真实原数据、原权重、软硬件等价和论文性能均Unknown，不能判R2/R3/R4。曾发现的分支main/master笔误及metadata仍称未执行的旧GPU字段已通知并修正；最终记录与实际`master@a73bd327fbf0db2550a9bc1e304b96e0aa550cba`一致。

## 论文、原始权重与文档边界

- 独立SHA256检查确认`paper.pdf`与作者站命名`paper_final.pdf`的文件完全相同，实际均标arXiv:2506.05779v1、15页。公开稿Fig1–9/Table1–6，无Appendix；ACM最终稿403，最终独有修改/编号仍Unknown。没有因作者站文件名含SIGCOMM或final就把它当已验证ACM最终版。
- 按内容检查编号偏移：仓库Figure8画流状态位数/F1，对应作者稿Fig7；Figure9读取ROC JSON，对应Fig8；Figure10a_b_c/10d对应公开稿Fig9精度/吞吐。83行矩阵按版本和内容映射，没有把文件名偏移当成实验不存在。
- `software/README.md`明确承认论文原.pth文件丢失、当前模型重训；这是一条已确认的**作者文档声明**，并不等于本次独立证明丢失历史。顶层README称软件/硬件输出相同，子README又说硬件并非完全相同，绘图README说明直接重画硬件已采集数字。报告没有把这些冲突自动解释成已证实的软件–硬件等价。
- Table5各数据集×八方法的24个macro-F1参照已与原文逐项核对；Table6八模型、Fig7三域×三位宽、Fig8三正常域×六异常类型、Fig9比较/吞吐均有行。baseline完整实现及真实性能缺口保持缺失/部分覆盖。图中或脚本的归档数字不是本轮重新测量。
- 原文§7.1将“accuracy/macro-accuracy”定义为packet-level macro-F1，报告已明确；ISCX正文“seven”却只枚举六名、代码跳过browsing后六类的口径差异也保留为待核问题，未擅自补齐。

## 实际运行范围和审计流程偏差

`independent_review_checks.py`只用标准库检查哈希、日志时序、源顺序、合成输入和已存窗口索引，exit0，原始证据为 `logs/pegasus/independent_review.{json,log}`、`independent_validation.json`。

- MLP checkpoint SHA与静态审查/Smoke JSON一致，合成CSV确有9行、10特征，标签0/1/2各3条。MLP专门静态检查所在retrieve步骤在模型Smoke之前结束；后续harness用`weights_only=True`、strict state_dict匹配、有限9×3输出。0.3485只是原quickdemo对任意合成标签输出的macro-F1，不是网络分类或论文比较。
- **CNN-L顺序确为先加载后补审**：原命令11:26:24Z开始，11:26:26Z因缺JSON退出；文件专门静态检查11:26:38Z。源码先`torch.load(weights_only=False)`反序列化，再构造data loader，最后才`load_state_dict`。故本次失败前已反序列化checkpoint，但尚未应用其state_dict，也没有CNN-L真实推理或指标；不能倒称全部权重预审，不能把事后GLOBAL检查当形式化安全证明。最终报告如实将其列为本审计流程偏差，而非论文或上游运行错误。
- README两项安装问题另有post-hoc原文命令日志：`conda create-n` exit2，仓库根缺requirements文件exit1。实际依赖安装在software子目录成功；报告明确修正语法/cwd，不把原文整套recipe称为逐字通过。
- P4G→P4原入口exit0只证明MLP16文本生成；未有P4编译、包级仿真或真实硬件证据。BMv2仅MLP-B、使用生成包绕过feature extraction，不能据其材料覆盖全部六模型或线速吞吐。

## Validation粒度反例

原`FlowDataset`先把flow展开stride1/window8窗口，原`build_data_loader`再对窗口索引做stratified split。诊断明确使用**一条40包合成flow、val_ratio=.2、seed42**；CLI默认val_ratio=.1，并非本轮的默认参数或原75/10/15数据重建。

已独立由保存的train/validation窗口起点重算：33个窗口索引被分成26/7且窗口索引本身不交叉，但对应原包位置6–38在两侧共享，来源仍是同一flow。这严格证明**该机制允许flow及重叠包跨train/validation**；不证明实际外部train/test文件重叠、不量化原论文test指标偏差，也不把合成反例称为已确认的真实数据泄漏。报告及矩阵保留了这些边界。

上游Git状态为空；没有对作者仓库提交修改。原数据/split与许可、替代权重训练过程、硬件配对输出、真实GPU/CPU吞吐和原SDK兼容仍需后续证据。
