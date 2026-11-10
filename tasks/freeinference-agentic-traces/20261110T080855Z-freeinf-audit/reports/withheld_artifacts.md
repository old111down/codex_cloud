# 未公开归档的证据

私有原件留在本轮工作区，不因公开导出而删除或修改。此表不承诺工作区永久存续；长期复核请从所列官方固定来源重新获取。

| 私有类别 | 保留理由 | 公开替代证据 |
|---|---|---|
| `private/data/` 的48个Parquet及下载manifest原件 | 用户要求不上传原始数据；可能含假名身份、工具参数 | HF revision、逐文件来源/大小/SHA-256、聚合统计 |
| `upstream/` 完整第三方Git仓库及私有执行副本 | 不默认复制第三方源码/历史 | 官方URL、fullSHA、文件hash、必要小补丁 |
| PDF、pdftotext全文、源码/HTML/API响应副本 | 不默认再发布完整论文和第三方内容 | 来源URL、获取时间、SHA-256、原创分析与短必要引用 |
| 实际小子集、simulation原始block/request产物 | 仍属原始数据或行级派生，含ID | 确定性选择规则、输入/派生hash、聚合守恒检查 |
| 绘图PNG/PDF及未逐项审查中间表 | 避免二进制或行级第三方数据误上传 | 数值对照、程序入口、聚合结果及实际日志 |
| 未筛选原始平台/终端状态 | 可能含云实例/主机、身份信息 | 去标识的host_summary及命令执行元数据 |
| 完整Conda安装目录、缓存 | 大型且含不适合Git内容 | environment.yml、explicit、freeze、版本 |

没有保存或上传推理凭据；没有发出模型推理，没有抓取Agent PCAP。公开 `pip-freeze.txt` 中若发现Conda构建机的本地file URL，仅转换为已实际确认的包版本；原件保留，逐文件变换记入publication manifest。该导出变换不是实验依赖替换。
