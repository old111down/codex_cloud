> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# YaTC 静态代码覆盖审计（论文全文受阻）

**范围：完整公开代码已读，完整论文—实验覆盖为Unknown。** 官方AAAI文章页可读，明确关联仓库并声称五个真实流量数据集；其PDF经两个公开OJS下载/浏览路由均HTTP403，独立网页工具返回BotStopper Access Denied，Tavily PDF提取失败。作者GitHub、OpenAlex/Semantic Scholar所列开放版本和公开搜索未找到另一份可核实作者全文。未绕过访问防护，未用别的论文补齐原文。

因此，Method、Implementation、Evaluation、Appendix的完整阅读与编号图表清单本轮**不能完成**；其编号、全部实验及原论文指标均Unknown。矩阵中的README用例不是伪造的论文章节，也不能证明五个数据集均被公开实现。论文关联和已读源码/实际运行仍可审计。

## 版本与关联

论文 *Yet Another Traffic Classifier: A Masked Autoencoder Based Traffic Transformer with Multi-Level Flow Representation*，AAAI2023，DOI `10.1609/aaai.v37i4.25674`。官方文章页直接给GitHub；作者项目README精确题名、作者与会议匹配，作者iZRJ个人GitHub还保留项目fork。固定官方 `NSSL-SJTU/YaTC` 的 `main@a220b75f8365acaf63dbac7df87aaaa357698b85`，提交2024-04-29T17:05:07Z，无许可证文件/API许可为null（Unknown）。源文件SHA/函数边界在 `evidence/yatc/source_manifest.json`。

## 代码路径和缺失环节

- `data_process.py:16–44`从**已分流**PCAP读前5包，每包保留/补齐80字节IPv4+运输层header、240字节payload；少于5包补零，`MFR_generator:46–60`生成40×40 PNG。未提供原始抓包→flow sessionization、采样/训练测试拆分或标签映射生成器；输入要求外部已有train/test/class目录。无CLI/main，函数需外部调用。
- `models_YaTC.py:16–93`为packet/flow attention和共享Transformer blocks；`MaskedAutoencoder:96–299`实现随机mask、编码解码和MSE重建；工厂`MAE_YaTC:303–308`/`TraFormer_YaTC:312–316`给出4层192维encoder和2层128维decoder配置。
- `pre-train.py`提供150000-step默认入口，`fine-tune.py`提供预训练权重加载、分类头替换、训练与评估。README列四个数据目录：ISCXVPN2016(7)、ISCXTor2016(8)、USTC-TFC2016(20)、CICIoT2022(10)，而官方摘要称五数据集，完整第五用例身份及配置为Unknown。默认入口只示范VPN，其他数据集需人工改data_path/nb_classes，没有逐实验配置清单。
- 数据和预训练checkpoint通过作者Google Drive链接外置。本轮取得了显示`YaTC_datasets.zip`/`YaTC_pretrained_model.pth`的公开landing页，但**没有下载文件**；内容完整性、文件大小、分流规则、split/seed、校验值和许可均Unknown。文件预览页存在不等于下载与评估已通过。
- `fine-tune.py:152`用ImageFolder按目录排序得到标签；原实验标签映射/已发布数据内文件清单不在Git中。train/test独立性、时间/设备/应用级泄漏与原数据预训练重叠均Unknown。

## 已确认代码行为与实际问题

1. README指定torch1.9.0/timm0.3.2/Python3.8等组合在本次新环境中有两项导入失败：SummaryWriter依赖的`distutils.version`未加载，旧timm依赖的`torch._six.container_abcs`不存在。原始失败日志保留；别名兼容后仅进入下一阶段，不算完整运行成功。原作者未锁定的setuptools/tensorboard等版本为Unknown，不能据此断言原作者环境从来无法运行。
2. `engine.py:66,148`无条件CUDA同步；传入CPU也失败。原始engine单batch在148行实测失败；隔离补丁后通过。
3. `engine.py:209`计算`average='weighted'`，但222–224行以`macro_pre/macro_rec/macro_f1`导出。合成10条反例的导出`macro_f1=0.45`，实际macro F1=0.15，weighted F1=0.45。**这证实键名与计算语义不符，论文是否也错用/错标指标仍Unknown**。
4. `data_process.py:20–23`保留IP header与TCP/UDP端口，没有本地mask/anonymize步骤。合成PCAP确证src/dst IP与sport/dport字节进入MFR。外部原PCAP可能已匿名化，因此这只是输入表示及潜在捷径风险；**未证实真实数据泄漏**。
5. `models_YaTC.py:209`的`int(L*(1-mask_ratio))`在L=400、ratio=0.9时为39，实际mask361/400，已测。这是有限精度/截断行为，不据此断言论文结果有实质偏差。
6. `fine-tune.py:299–332`在每个epoch对`data_path/test`评估，追踪并打印Max Accuracy/Max F1，入口未区分独立validation目录。**每轮用test评估/显示max是静态事实；论文是否选取该max、是否存在实际测试集选择偏差为Unknown**。不能单凭该循环指控论文发生泄漏。
7. 同一fine-tune循环只创建`log_stats`字典，未调用`save_model`或将该字典写文件；训练后仅有内存模型和stdout。`--eval`有意跳过`--finetune`初始化，只有`--resume`会经`misc.load_model`加载checkpoint。它是需明确的运行接口/归档缺口，不能将未指定resume的随机模型评估当预训练模型结果。

所有源码位置均针对固定SHA。CPU Smoke仅涵盖随机初始化完整工厂模型和合成PCAP；原始预训练、真实下游数据、few-label实验、基线、原指标、吞吐和硬件配置仍Unknown。P4/专有交换机部署不适用于此仓库。
