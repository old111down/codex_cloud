# 实际云环境

追加自主审计新增Flowrest、Leo、LINC、ET-BERT、YaTC、Pegasus及Lens诊断前缀，连同原三试点共10个独立Conda环境。Lens只含轻量指标/划分检查依赖，不是主模型环境。原始及兼容环境差异均记录在各子目录；`cloud_status_round2.json`是本轮刷新状态。当前公开open-p4studio的可获取性与历史SDE/硬件权限分开记录，见 `evidence/round2/open_p4studio/audit_note.md`；本轮未构建SDK。

探测原始证据为 `host_probe.json`，时间见该文件；运行态策略见 `cloud_status.json`。本次 executor ID 与用户指定环境一致，状态为 running、observations_current=true、网络策略 enforced/unrestricted。启动策略 `/etc/codex/network-policy.json` 亦已读取；未配置 VPN、secret 或 outbound identity。

- 系统：Debian GNU/Linux 13.6 (trixie)，x86_64；具体内核和编译器见原始探测。
- CPU：虚拟机可见5个逻辑CPU，Intel Xeon Platinum8573C；cgroup `cpu.max=400000 100000`，可用计算配额为4核。可见逻辑核数不等于持续CPU配额。
- 内存：主机报告约17.6GiB；cgroup `memory.max=17179869184`，上限16GiB。无swap。
- 磁盘：初始 `/workspace` 所在overlay总约31.45GiB，可用约29.78GiB；该值会随环境安装变化。
- GPU：`nvidia-smi`、`nvcc` 不存在；`/dev/nvidia*`/`/dev/dri/*` 未发现。没有已证实可用的GPU。CUDA硬件验证为 Unknown/未执行，不从依赖包名推断GPU存在。
- 工具：Git/GCC/G++/pdftotext可用；首次探测无 Conda、p4c、BMv2 simple_switch、TShark、Docker。未安装未经授权的Intel SDE/SDK或真实Tofino硬件。
- 权限：普通 `agent` 用户，`sudo` 命令不存在。普通用户可写工作区、可运行进程和联网；是否具备未测试的内核/硬件特权为 Unknown。没有尝试改变权限或网络规则。
- 网络：GitHub API、Git clone、公开论文端点、Conda/pip下载均有实际成功记录；个别出版方拒绝访问在各论文报告中记录。未枚举/输出凭据值；保持继承代理与TLS验证。

## Conda

初始没有Conda。安装官方 conda-forge Miniforge3 `26.9.4-2` 至 `.tools/miniforge3`，安装器 SHA256 与GitHub官方release API asset digest一致。来源、大小与哈希见 `miniforge_provenance.json`；实际下载与安装命令、退出状态见 `logs/miniforge_*`。此安装为用户目录内的Conda兼容发行版，不修改系统Python。

每篇论文独立使用 `.conda/<id>`。各环境的 `environment.yml`、显式Conda包列表、pip冻结与版本探测保留在对应子目录。Python/PyTorch/CUDA/系统工具版本缺失时明确记录，不从论文描述补齐本地测量。环境选择与论文版本不一致的地方在各论文报告说明。

## 来源重建

`upstream_manifest.json` 记录原始代码仓库固定SHA、实际分支、远端、tracked-file SHA256、Git状态及浅克隆标志。它不声称保存了作者未公开的历史或私有数据。重新拉取依赖网络、上游仍可访问和许可证；本地保存的审计证据可由 `scripts/verify_checksums.py` 独立校验。
