> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# LINC 论文—代码覆盖静态审计

固定源码为 `haolinyan/LINC main@4a44171c84547de885a54e5f1a234640cd8501d4`。原论文p2脚注直接链接仓库；README精确题名及作者托管PDF匹配，关联已验证。全文为12页IEEE PDFExpress作者版，§III框架、§IV方法、§V增量、§VI全部评估及参考文献已读。编号对象为Fig1–9、TableI–III；此版本无Appendix、Algorithm、Listing，外部补充材料情况Unknown。

## 公开实现的边界

仓库实现了自定义NNU、NN训练、从训练样本生成/合并规则、PyTorch张量规则匹配，以及一次ISCX三类→四类Streaming更新。它没有提供论文主要任务的完整可运行实验材料：

- `train_nn.py`默认六类、96bit，`train_nn_c3.py`保留标签0/1/2；`update_streaming.py`只硬编码原标签4映射到新标签3。缺P2P/VoIP连续更新入口、六方法对齐比较、比率扫描和TableII/III聚合脚本。修改参数或代码自行补出后两次更新不等于作者已经公开完整实现。
- `LINCDataset`只读取外部pickle的train/val/test键；从PCAP提取TableI字段、位展开、标签映射和划分的生产流程缺失。`linc/mousika_utils.py`确有遗留UNIV CSV loader，路径为不存在的`Dataset/univ/`，但未接入完整LINC三任务训练/评估；不把它的存在解释为UNIV实验已可复现。UNSW没有专用配置/数据处理入口。
- Fig5–7、Fig9b的三任务/全部基线、预算和采样消融未有相应成套配置/日志或绘图聚合；自定义模型组件不能替代这些实验。`linc/mousika.py`用于局部更新的RF/SoftTree helper也不是完整Mousikav2基线复现。
- 无`.p4`文件、P4构建配置、控制器、交换机安装脚本或原始硬件测量。`linc/simulator.py`是PyTorch规则匹配器，不能算BMv2/Tofino包级仿真。今日部分SDK可能公开，但本仓库没有可审计的P4程序和历史配置，本轮也没有安装兼容SDK或使用硬件。
- 论文训练环境Python3.9/PyTorch1.12.0/TeslaM60与requirements中的Torch2.0.1不同；论文称T最佳0.5–0.6，脚本默认T=0.2219338905926658。完整超参数搜索、原样本ID、会话独立性、原始随机拆分来源Unknown。代码训练seed2023和更新seed0可见，不能补齐未知论文协议。

## 已确认的问题及证据边界

1. **原始依赖安装失败**：`swanlab==0.3.16`在当前索引无匹配发行，官方PyPI精确版本端点也404。原始pip命令退出1。默认实验跟踪分支未开启，审计明确省略该inactive包；不将此环境称作原版依赖安装成功。
2. **NumPy桥接失败**：声明的NumPy2.0.1搭配官方Torch2.0.1+cpu，实际`torch.from_numpy`报`Numpy is not available`及`_ARRAY_API`警告。明确降至1.26.4后有限测试成功，原freeze/失败日志保存。这是本次CPU构建条件下的事实，不自动外推所有平台。
3. **小batch训练崩溃**：`linc/model.py:265`用`num_batch//10`作模数；四个batch时在首步优化后抛ZeroDivisionError。隔离补丁只修日志间隔。
4. **默认子空间分配错误**：`Switch.scores`形状是(1,N)，`linc/simulator.py:58`却用`len(self.scores)=1`标记未匹配样本。三规则、穷举八个3bit查询时，五个未匹配样本均被写入rule1缓存，保留default bucket3为空。分类默认标签仍为0，所以这不证明论文accuracy降低；它直接证明缓存/增量分区在该可达输入条件下出错。补丁改为N后局部反例通过；独立probe进一步确认`update_streaming.py:179`直接访问`values[N]`会越界。对未匹配的新类样本这是可达的后续IndexError，不是完整增量修复。完整GPU更新和真实数据影响仍未验证。
5. **样本比例说明不一致**：`update_streaming.py:27`为`RATIO=1 #0.05% of new dat`，实际取全部已加载新类train/val，不强制63条。原pickle未获取，因此其自身是否预先只含63样本为Unknown，不能据此断言作者实验实际用了全部原始数据。
6. **Fig8标签顺序不一致**：面板(a/b/c)分别标Streaming/P2P/VoIP，但总caption括号内顺序写P2P/Streaming/VoIP。矩阵按面板标记，原始输出与作者意图Unknown，不擅自交换实验曲线。
7. **CPU支持不完整**：NN主训练选择CPU fallback，但`generate_rules`、`Simulator`与增量脚本硬编码CUDA。补丁仅使导出/张量模拟器可在CPU跑小合成输入，不声称完整Streaming/P2P/VoIP已迁移。

41行 `coverage_matrix.csv`覆盖全部编号对象、三任务、三次增量、部分/全部新数据、四基线、时间、硬件及采样声明。覆盖状态只表达证据/实现范围。已确认事实、实际运行、未验证问题分别以源代码、日志与Unknown标记，不据README声称完整实现。
