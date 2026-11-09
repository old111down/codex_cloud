> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Leo 静态代码覆盖审计

审计对象为 NSDI2024 *Leo: Online ML-based Traffic Classification at Multi-Terabit Line Rate*，固定 `Purdue-ISL/Leo@bd9fb79b8e0bd79b4922f3ca1ada88b9ee69eff2`，MIT。论文首页脚注直接链接作者仓库，README题名、作者和USENIX引用匹配。全文20个PDF页面（1页USENIX封面+印刷页1573–1591），Methods§4、Implementation§5、Analysis§6、Evaluation§7及Appendix A.1–A.3均已阅读。Fig1–23、Table1–2全部列入矩阵；没有只检查README第一个生成器。

## 已确认的实现范围

- `leo-generator/` 有SRAM/TCAM P4生成器、树文本解析和BFRT控制面命令生成器，支持树深、子树大小、feature数及TCAM叶数上限。`leo/` 有资源模型、feature位宽预算枚举器、固定P4和1M流示例；`iisy/`有固定P4、理论资源计算与最坏feature表分割程序。它们提供了重要机制，不等于论文全部评估已经自动化。
- 两个`dataset-simulation/dataset-processor-*.py`包含数据清理、候选switch feature列表、标签合并、75/25分层切分、entropy/class_weight balanced CART、RFE、按类F1/macro-F1与结果导出。训练数据未随仓库提供。主程序固定十组配置，不能直接覆盖论文全部Leo/Leo-NT/IIsy/pForest对照和所有硬件配置；论文图表重绘脚本、编译批量结果及真实测试床原始数据未提供。
- 自动feature extraction不属于生成器已实现范围：README明确要求用户自己填入stateful register/feature赋值标记。`leo-1m-flows.p4`只给一种五特征示例，不是Table2全部四种配置的可重建处理链。

## 已确认问题与证据

1. **树阈值整数转换失真**：`leo_ctrlplane.py:34–47`将sklearn的`<=0.50`阈值`round`成0；`generate_rule_commands`编码`(-constraint)&0xffff`，P4模板用16位加法并检查MSB，实际是`f<constraint`。原始CART两点样本的输入0因此得到相反类别。阈值2.5同样出错，1.5恰好正确。已执行反例见`evidence/leo/threshold_counterexample.json`、`logs/leo/threshold_counterexample.*`，原控制命令生成出的`constraint=0`也保留。此结论是源代码与受限数值反例，不声称已观测真实交换机或论文数据上全部错误。
2. **16位差值符号不是全unsigned16域的比较器**：对可表示输入65535和小阈值，`(f-c)&0xffff`最高位为1，会被当作左分支，和原树不一致。`evidence/leo/integer_domain_counterexamples.json`/同名诊断日志保留。实际数据中该域输入的频率及论文结果影响为Unknown。没有用Python谓词诊断冒充P4包级仿真。
3. **runtime transient控制面不完整**：§4.5描述双树、原子active-tree切换；生成器虽接受`--transient`，`leo_ctrlplane_gen:399ff`直接输出“Disabled transient control plane support for now...”，没有对应完整更新事务。本轮原样命令确认该输出，不能据flag存在就宣称动态无不一致更新已复现。
4. **数据/协议差异**：README的目录树把CICIDS文件放在UNSW目录、UNSW文件放在CICIDS目录，与实际脚本读取路径相反。NB15脚本先合并官方train/test CSV再重新随机划分，默认`bin_threshold=3000`做多类，而主文§7.2是二类；函数有`-1`二类逻辑但无默认相应运行配置。切分和CART未设置random_state，每配置重新划分，原始折分/会话ID未知。不能把重新合并视为已确认训练测试泄漏；它确实改变官方split，论文也明确使用75/25。
5. **完整评估缺口**：没有原始CSV/PCAP、所有baseline训练与硬件编译配置、数字化Fig11–23结果、流状态离散化的全数据处理、tcpreplay/控制CPU推理服务/时间戳收集脚本。未证实完整原实验可执行。

## 版本和当前SDK状态

原论文用SDE9.11.1。2026年当前README明确新增open-p4studio链接，不能笼统把所有Tofino SDK说成始终不可公开获取。父审计保存的`evidence/round2/open_p4studio/`核实现在存在公开编译器/软件模型；实际硬件BSP/Serdes/P4Insight及历史版本等价性另有边界。本轮未安装/编译该SDK，无真实Tofino。公开源码可获得不意味着构建、仿真或硬件性能已验证。

静态代码覆盖状态与执行等级分开；全部论文F1、500ns/500×、深度/资源/1M流硬件结果仍为Unknown。详见矩阵与运行报告。
