> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Flowrest 论文—代码静态审计

审计日2026-11-09；固定作者仓库 `nds-group/Flowrest@13a527cfc0cac523b9f4be9a9366738bcdd3d5db`，main。论文原版INFOCOM2023 DOI `10.1109/INFOCOM53939.2023.10229100` 与2025期刊扩展 DOI `10.1109/TON.2025.3564465` 为同一paper family，不重复计独立研究。两版结论均直接链接该GitHub，README精确题名/作者/DOI和IMDEA作者稿链接形成交叉证据。API未提供许可证，未发现LICENSE/COPYING，许可为Unknown。

## 阅读范围与全部用例

已读INFOCOM作者版全部10页，重点§III架构/实现、§III-E建模、§IV实验；编号对象为Fig1–7、TableI，无编号Algorithm/Appendix。已读ToN作者版18页，重点§III总流程、§IV硬件模型/模拟器、§V实现、§VI设置/评价、§VII所有实验；编号对象为Fig1–10、TableI–VI，无编号Algorithm/Appendix。原始接受稿的最终出版排版差异及单独supplement为Unknown。

INFOCOM有三数据源、四个难度用例：UNSW-IoT16/26类设备识别、UNIBS8类服务分类、CICIDS2017 Friday二类检测。期刊扩展改为五数据集：UNSW26、UNIBS8、CICIDS2、IoT23十四类bot、ToN-IoT十类攻击，并新增模拟器、三额外模型映射、五基线、按流长度归一化的packet评分、资源代价模型选择及延迟测量。全部编号对象和重要实验在83行 `coverage_matrix.csv` 按版本分别登记，不把README新增IoT23/ToN-IoT归入原会议版。

## 实际公开资产

整个仓库只有3个notebook、2个model-to-table脚本、1个full-version UNIBS控制器、3个P4主程序和includes、3个保存RF模型、设备MAC标签表及README示意图。conference目录仅提供UNSW16 per-packet/per-flow；full目录仅提供UNIBS8。没有给出CICIDS、UNSW26、IoT23、ToN-IoT的处理数据、任务配置、P4变体或完整评估程序。README认为相同方法可用于其他用例，这不能代替该用例的实现和复现实验。

作者README公开Box派生train/test文件可按文件名直链下载；本轮取得UNSW16与UNIBS四个CSV，来源、大小、时间、SHA256在 `evidence/flowrest/downloaded_data_manifest.json`。最初目录/DAV列举失败后直链成功，不把初始401解释为数据最终不可获得。原始PCAP→CSV的特征/时间单位/日期映射代码仍缺失。

## 已确认的代码问题

1. **训练/测试时间变换不对称**：conference flow notebook cell17将训练FlowIATMin/Max/Duration乘1000；cell20及prepare_test没有相同变换。公开CSV按原单元跑得Accuracy0.645647、MacroF1=0.402694；仅对测试同三列乘1000的审计敏感性条件升至0.987031/0.919989。这是运行观察和单因素证据；CSV真实单位、作者原实验如何处理、哪种条件等价于论文仍Unknown，不把改善认定为论文复现。
2. **F1阈值量纲**：get_fewest_features的score来自f1_score，范围0–1；analyze_models_features调用阈值99。完美合成分类F1=1时也返回None，而阈值0.99可返回特征子集。反例与日志保留；函数返回值在某些调用中被忽略，不能据此推断全部训练都会崩溃。
3. **测试集用于选择**：conference模型/特征/时间位压缩搜索持续在X_test/y_test上评估、择优；full UNIBS grid也据test score排序。未见独立验证集或外层交叉验证。代码路径确认，导致最终指标乐观偏差的大小未测，为Unknown；不能仅据此宣布已证明数据泄漏或论文结论无效。
4. **原样generator成功不代表表项可装载**：conference生成器exit0，但将全部末区间上界设65535。固定P4的FlowDuration键只有[31:29]三位、FlowIATMax只有[31:27]五位；输出末区间分别7..65535、26..65535越界。AST对照已执行；实际BFRT会拒绝、截断还是报何种错误未测试。
5. **full保存模型与generator接口不配套**：full模型内嵌sklearn0.23.2，未保存feature_names_in_；脚本强制读取该属性。原始脚本先因YOUR_TRAINED_MODEL.pkl占位失败，将原模型只复制到预期文件名后实测AttributeError。没有改源代码或静默发明特征顺序。
6. **硬件约束参数占位**：prune_model的MaxTen=0且注明真实限制confidential，只打印ERROR，不约束/拒绝模型。部署所需准确限制Unknown，不能把本地RF训练成功理解为硬件可部署。

## 重要缺失

- ToN §IV-C专用流管理模拟器、CRC16参数/entries/timeout/digest10ms扫参实现缺失，Fig5与Fig7无法由公开仓库重放。
- ToN Eq1的TCAM代价/alpha0.5模型选择器缺失；UNIBS notebook只排序macro/weighted指标，无TCAM输入或资源统计。
- ToN §VI-D要求packet预测按1/flowLength加权；未见sample_weight/流长度归一化路径，因此不能复现packet-vs-flow公平比较协议。
- 额外pForest/Soter/Mousika/NetBeacon适配与多映射P4实现、全部baseline配置、Fig9 flow-length绘图、资源/延迟评估脚本或原始输出缺失。README外链到其他作者仓库不等于本实验的适配实现公开。
- 原始SDE9.7.0/P4Insight环境、Tofino硬件和网络负载未验证。当前public open-p4studio的可获取性不等于历史版本/本源码兼容性，本轮未拉取/构建它。

## 证据边界

源码hash清单为 `evidence/flowrest/source_manifest.json`，notebook cell完整文本用于定位（不是新的作者实现）。数据审计中的跨日FlowID字符串重合不能单独证明同一会话泄漏：原日期/会话映射缺失，需进一步核验。本轮只确认两个公开派生CSV组件可运行，完整论文全部任务实现未公开齐全，所有原论文硬件及可比精度结论保持Unknown。
