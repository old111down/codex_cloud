> Public filtered copy of the retained local audit. Source-relative artifact IDs may refer to withheld material; see [publication/source ledger](../../reports/source_reference_index.md). Publication omissions do not mean an experiment or paper artifact was missing. Scientific values below are unchanged.

# Mousika 论文—代码静态审计

审计日期：2026-11-09。已阅读全文：INFOCOM 2022 的 10 页原文及 ToN 扩展的 14 页作者稿；方法、实现、评估、局限性均纳入。两份全文均没有附录正文，另行补充材料是否存在为 **Unknown**。最初 IEEE 返回登录页是历史检索失败，随后已从共同作者 Qing Li 主页明确链接的作者站合法取得全文，当前不存在全文访问阻断。

## 版本与关联

- 原论文：*Mousika: Enable General In-Network Intelligence in Programmable Switches by Knowledge Distillation*，INFOCOM 2022，DOI `10.1109/INFOCOM48880.2022.9796936`。
- 扩展：*Empowering In-Network Classification in Programmable Switches by Binary Decision Tree and Knowledge Distillation*，首次在线发表 2023-06-21，最终卷期 ToN 32(1), 2024，DOI `10.1109/TNET.2023.3287091`。
- 原文结论（PDF p9）与扩展摘要（PDF p1）均明确给出 `https://github.com/xgr19/Mousika`。作者主页也列出精确题名；不是同名仓库推断。
- `main`: `76c9db9b4200a7c591bd1e9476ba5ab44a467512`；`Mousikav2`: `3326869d4c1f25768a9304a2df672e82f38972f9`。两处 checkout 均保持 pristine。分支用途见各自 README。
- 无 LICENSE 文件；GitHub API `license:null`。**许可证 Unknown**，公开可访问不等于已获开源许可证授权。

## 全部用例与编号对象

完整 82 行记录见 `coverage_matrix.csv`，逐项注明论文版次、页码/章节、源码行、数据、配置、入口和阻断。INFOCOM 的 Fig1–10、Table I、Algorithm1、Listing1–2 全覆盖；ToN 的 Fig1–18、Table I、Algorithm1、Listing1–2 也独立覆盖。原论文与扩展的图号没有混用。

两版共有三个任务，输入都是包头字段（协议、TTL、包长、端口等）所展开的位，排除 IP/MAC 和校验和：

| 用例 | 论文数据/标签 | main 实际供应 | v2 实际供应 |
|---|---|---|---|
| 流大小预测 | UNIV1；属于流大小前20%流的包为 elephant，其余 mice | 一个ZIP内两个预处理CSV（train/test，各含连续/位特征）、RF→BDT示例和文本规则 | 仅 UNIV CSV loader；Dataset 未提供 |
| 应用流量分类 | ISCX；Email、Chat、Streaming、File Transfer、VoIP、P2P | 无 ISCX loader、预处理数据、配置、运行器 | 同样缺失，且默认 class_num=2 不能直接覆盖六类 |
| 恶意流量检测 | Bot-IoT；合法/恶意（DDoS、扫描等） | 无该数据/loader/配置 | 同样缺失 |

因此，README 的 UNIV 演示不能代表另外两个论文用例已经覆盖；流大小预测也不能代替应用流量分类结果。

INFOCOM IV-A 要求按日期和五元组划分且训练/测试无重叠；`utils.split_train_test` 有五元组分组代码，但当前 `load_data` 直接读预拆分 CSV，缺原始抓包→CSV及日期划分证据。ToN VII-A 改为外层五折交叉验证；v2 的 `KFold(2)` 只用于生成软标签，不是论文五折评估。没有外层五折运行器、网格搜索结果或全量参数配置。

INFOCOM 评估教师为 RF、GRU、LSTM；main 只提供 RF 和 GRU 路径，未提供 LSTM 类。ToN 扩展还包括 GBDT、MLP，但 `--teacher gbdt/mlp` 都仍调用硬编码 RF；NN `select_model` 固定返回 GRU，LSTM 需改源码才能选。Deep Packet/SAM 对比（ToN Fig18）、规模扫描（Fig17）、IIsy/Planter/pForest 基线均无对应完整实验代码，已单列，不能由默认 RF 演示推定覆盖。

## P4 分层

1. 模型/规则生成：main 的 Tree/SoftTree 与 RF 软标签函数存在；仅做了小规模 CPU 功能验证。
2. 规则转 ternary：五份作者规则重新转换，与作者提供的五份 ternary 文件逐条一致；这是编码验证。
3. P4 构建：`flowcontrol.p4` 用 TNA/T2NA；`common/headers.p4` 与 `common/util.p4` 不在仓库。是否可从特定 SDE 示例环境取得完全匹配版本为 Unknown。本环境没有 `p4c`/SDE。
4. 软件仿真：无 BMv2 target/config/packet replay harness，未执行；TNA 源码不能直接认定能在 BMv2 编译。
5. 真硬件：原文要求 EdgeCore Wedge100BF-65X 与 Keysight XGS12-SDL；扩展还包括 H3C S9850-32H、OpenMesh BF-48×6Z。均未获得或执行。40/100Gbps、零丢包、纳秒延迟、TCAM/SRAM/VLIW/阶段数结果全部未验证。

控制面 `entry2dataplane.py:60` 的路径字符串有多余起始单引号，默认 `iscx/univ_gru.txt` 也与实际仅有 UNIV round 文件不匹配。其 PTF/BFRT 导入依赖 SDE；未将静态发现描述为硬件运行验证。

## 缺陷与补丁

- **运行错误修复**：main Tree 导出的整值标签为 `1.0` 等，converter 的 `int(token)` 抛 ValueError。原始失败日志保留；补丁仅接受有限整值十进制标签，拒绝小数/NaN/Infinity，五份现有规则输出未变化。见 `patches/mousika/0001-accept-integral-decimal-class-labels.patch`。
- **算法逻辑修改**：v2 `SoftTree.py:85` 右分支 Gini 累积类样本总量未平方，偏离论文 Eq5。8 行独立反例给出参考负加权Gini `[-0.375,0]`，原版为 `[-0.5625,-0.375]`，补丁为 `[-0.375,0]`。见 `0002-v2-correct-right-branch-gini.patch`。它改变候选分裂评分，可能改变树、精度、规则数和训练成本，不能声称与作者实验等价。

两项补丁均只应用于临时源副本测试，未应用到 upstream。其他已知缺口未静默修改。

## 可追溯证据

- 论文获取与 SHA256：`evidence/mousika/access_research/downloads.json`、两份 `*_verification.json`、`qing_li_homepage.html`。
- 全文阅读与对象清单：同目录 `infocom_inventory.md`、`ton_inventory.md`、两份 `*.txt`。
- 源码全清单与哈希：`evidence/mousika/source_manifest.json`；数据校验/来源/行数：`data_manifest.json`。
- 仓库 API 时间/许可：`evidence/mousika/repo_api.json`；源码行号均以固定 SHA 为准。
