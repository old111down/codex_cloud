> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Leo 独立复核

2026-11-09 UTC，固定 `Purdue-ISL/Leo@bd9fb79b8e0bd79b4922f3ca1ada88b9ee69eff2`。独立检查报告、44行矩阵、论文编号caption和关键§4.3/§4.5/§5/Appendix文本、原parser/生成器/templates、诊断harness与原日志。没有新增训练、P4编译、包级仿真或真实硬件运行。

## 范围与结论

未发现最终报告在本次检查范围内的实质夸大。当前只支持**CPU环境、文本生成和资源公式的有限R1**；真实数据训练、原论文指标、编译可行性、线速/时延/硬件资源结果均未验证。

独立从原论文文本重新提取caption，确认Fig1–23与Table1–2全部存在，并在矩阵中找到全部对应编号。Appendix A.1–A.2的分析/证明及A.3.1–A.3.3的feature数、逐类F1、特征预算/延迟额外实验均有覆盖项。该检查核实inventory，不是独立验证数学证明、重建图中数值或执行所有实验。

## 数值语义核对

- 原`leo_ctrlplane.py:34–47`使用Python `round`将导出阈值0.5/1.5/2.5变为0/2/2；原生成器347行编码负约束，template执行16位加法并提取32768位，匹配严格`f<c`的局部符号谓词。独立按归档小整数probes重算：阈值0.5在x=0失配，2.5在x=2失配，1.5这一例没有失配，与JSON一致。小非负probes避免了溢出问题，因此这是独立于全域问题的round/严格边界诊断。
- 对完整unsigned16输入域，源码`FEATURE_WIDTH16`允许65535。以constraint2为例，`(65535−2)&65535=65533`，MSB=1，符号判断会走left，而65535≤原2.5为false。该反例只证明指定bit-vector条件的缺陷，不证明原论文数据里存在该值、更不代表已经在交换机观察到错误；实际频率与论文精度影响仍Unknown。
- 上述数值检查为Python/标准库算术，不能称P4软件交换机仿真。完整树映射、其他条件符号、量化域与实际P4执行未独立验证。

## 运行和SDK边界

- `readme_ctrlplane`原日志明确打印`Disabled transient control plane support for now...`。报告把它作为自动更新缺口，而非将exit0或`--transient`参数视为双树原子更新成功，处理正确。
- SRAM P4生成器exit0只说明产生文本；资源模型511条目是公式输出。没有bf-p4c、真实P4编译/包级测试/硬件测量日志，报告也未作相应成功声明。
- 报告已更正SDK描述：2026当前README有公开open-p4studio链接，历史SDE9.11.1未取得/当前公开SDK未兼容构建验证/真实Tofino硬件缺失是三个独立问题。未笼统宣称Tofino SDK始终不可公开获取。
- 数据集官方split合并后重划分、缺random_state等描述有源码证据；报告未将“合并再切分”直接判为已确认泄漏，符合证据边界。

17个原始tracked文件的SHA256均与source_manifest相符，上游Git状态为空。纯数值重算、caption清单和矩阵hash在 `independent_review.json`。审查工具首次将列表格式manifest当字典而失败，已修正遍历；这属于审计辅助脚本格式处理，不是上游失败或诊断结论变化。
