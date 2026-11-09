> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# LINC 独立复核

复核日期2026-11-09。独立阅读原作者论文Methods/Incremental/Evaluation与编号对象，检查固定SHA `4a44171c84547de885a54e5f1a234640cd8501d4` 的源代码、41行矩阵、运行报告、环境偏差、三个补丁和关键原始日志。**现有证据只支持有限合成组件R1；没有真实流量数据、完整增量流程、P4仿真或硬件结果。** 没有发现将合成100%精度冒充论文复现的表述。

## 覆盖与证据检查

- 41个claim_id唯一，明确引用的本地证据路径均存在。Fig1–9、TableI–III、三任务、四个比较方法、Streaming/P2P/VoIP三次连续更新、受限/全量新数据、time/resource和采样实验均有对应覆盖行；原作者12页版本没有Appendix。
- 公开源码实际提供NN/规则导出、PyTorch规则匹配和一个硬编码Streaming更新；没有将通用helper或UNIV遗留loader计作完整三任务评估。未发现P4源文件/构建/控制器；`Simulator`不被称作软件交换机。
- 论文TableII/III六行是ERG、DAC加四个基线，报告的“六方法”有上下文依据；Fig5则为LINC加四个基线。RATIO=1与“0.05%”说明不一致属可核源事实，但原pickle是否预采样未知。
- Fig8子图(a)/(b)标签为Streaming/P2P，而总caption顺序写反；矩阵按子图标签定位，已提醒原审计代理登记这项内部不一致。Fig9b的up-to85%是跨任务汇总表述，不能据此认定每个数据集都恰为85%。

## 独立可执行检查

实际执行 `papers/linc/independent_checks.py`，独立Conda环境`.conda/linc`，CPU/单线程、无训练。原始命令、UTC时间、stdout/stderr和exit0在 `logs/linc/independent_review_checks.*`；进程1.624秒。结果保存 `independent_checks.json`。

1. 从原始和补丁后的文件分别AST提取原`Switch`类，以同样三条规则穷举全部八个3-bit查询。原版五个default查询被分到rule1，缓存计数`[1,6,1,0]`；补丁后索引零差异，缓存`[1,1,1,5]`。预测类别序列未变化，不能由此声称论文精度下降。
2. 进一步确认**补丁3只修复局部默认缓存，未修完整增量父规则逻辑**。对不匹配规则的新类样本`query111,label3`，补丁后的正确default index为N=3，默认预测0，所以可进入误分类更新。原`update_streaming.py:179`随后执行`positive_samples[ind][str(int(values[ind]))]`；`values`只有N项，执行同一原AST赋值时抛`IndexError: index3 is out of bounds ... size3`。这是条件可达的剩余断点；未完整运行CUDA更新，也未对论文真实数据发生率作推断。已通知原审计代理补入报告，不能把5/8→0/8写成整个增量算法已修复。
3. `_train_epoch`四个batch时`num_batch//10=0`与原始ZeroDivisionError日志一致；该补丁仅改日志间隔，未改optimizer/loss。
4. 检查`RATIO=1`和实际切片代码：若传入1000条新类训练样本将保留1000而非63。此为代码行为，不证明未取得的作者pickle包含多少条。

## 环境和结果边界

原固定SwANLab版本不可解析且官方PyPI精确版本404、NumPy2.0.1/Torch2.0.1+cpu桥失败均有实际日志。明确省略inactive跟踪包、CPU wheel及NumPy1.26.4是环境偏差，未被描述成原始安装成功。数据Baidu请求从本云环境返回403只证明本次访问受阻，不证明全球链接失效或数据不存在。

原NN forward/backward、修复后64/32/32合成训练/规则导出属于R1。合成100%精度、2条规则和小样本耗时不能对照论文137秒、14.31/36.46秒、原分类指标或99.9Gbps。真实数据、63/44/28样本ID/划分、完整三次更新、原权重和全部硬件/资源结果仍Unknown。无需为这次独立复核重跑训练或改动上游。
