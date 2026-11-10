# 来源清单

## 范围

检索日期为 2026-11-10，时区 Asia/Shanghai。范围为 AI Agent 网络流量测量、应用或任务级分类、MCP/A2A 通信的网络可观测性。本批仅纳入有可追溯原始证据的公开文献，AR/XR 归其他项目管理。

## 检索记录

| 来源 | 原样检索式 | 结果 |
| --- | --- | --- |
| 学术检索 | `AI agent network traffic measurement encrypted agentic application traffic classification packet traces arxiv network MCP A2A 2025 2026` | 用于发现网络测量与分类候选 |
| 学术检索 | `MCP A2A agent network observability communication measurement packet capture empirical arxiv agentic Internet 2026` | 找到 A2A 元数据实证研究及远程 MCP 生态测量候选 |
| Tavily，arXiv 域名限定 | `A2A MCP communication graph passive metadata multi-agent traffic measurement task classification Dangol` | 成功，找到 2606.07150 的题录和全文版本 |
| Tavily，arXiv 域名限定 | `AI 智能体网络流量测量 任务分类 A2A MCP 可观测性 arXiv` | 成功，用于补查协议互操作方向 |
| Zotero 只读题名查询 | `Communication-Graph Metadata in Autonomous Agent Interoperability` | 可查，本次题名无命中 |

两篇进入本批详细筛选。检索片段只用于发现候选，笔记的事实依据来自版本固定的全文 PDF。

## 候选、纳入与获取

| 作品标识 | 获取与覆盖 | 处理及理由 |
| --- | --- | --- |
| arXiv:2606.07150v3，DOI 10.48550/arXiv.2606.07150 | v3 PDF 实际 GET HTTP 200，886,254 字节。全文文本探针 23 页、99,572 字符，核看第 10、11、18、19 页。原 PDF 保存在本机试跑目录。 | 纳入全文。论文给出 A2A 工作流元数据、分类与留出对照，以及 MCP Streamable HTTP 的合成验证。题录评论中的 22 页与本次探针的 23 个物理页分别保留。 [题录](https://arxiv.org/abs/2606.07150v3) · [全文](https://arxiv.org/pdf/2606.07150v3) |
| arXiv:2609.19100v1，DOI 10.48550/arXiv.2609.19100 | 只阅读官方题录和摘要。官网列有公开 PDF，本批未下载第二篇全文。 | 保留摘要候选。关注远程 MCP 部署与观察范围，可补充基础设施视角，和本轮的任务级流量分类口径不同。 [官方题录和摘要](https://arxiv.org/abs/2609.19100v1) |

## 真实版本对照

同一 arXiv 基础 ID 和 DOI 在官方历史中有 v2（2026-06-13）及 v3（2026-06-17）。v2 PDF 也实际 GET HTTP 200，750,369 字节，解析为 18 页，SHA-256 与 v3 不同。v2 用于版本识别对照，v3 是本轮全文笔记的证据版本。v2 不计为第二篇作品。[v2 题录](https://arxiv.org/abs/2606.07150v2) · [v3 版本历史](https://arxiv.org/abs/2606.07150v3)
