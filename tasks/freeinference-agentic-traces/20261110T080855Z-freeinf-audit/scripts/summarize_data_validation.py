#!/usr/bin/env python3
"""Render source-linked aggregate evidence and a focused Markdown audit report."""
import collections
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA='2b795dbf5eac490a7c081906fdce6cc7a184b7ef'
BASE=f'https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/{SHA}/'

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    j=json.loads((ROOT/'reports/aggregate_stats.json').read_text())
    source=json.loads((ROOT/'reports/data_source_summary.json').read_text())
    anomalies=json.loads((ROOT/'reports/anomaly_and_confounding_aggregates.json').read_text())
    cohort=j['cohort_totals'];top=cohort['top_level'];child=cohort['child']
    expected={'hermes':(3953,43.1),'opencode':(1733,44.2),'pi':(1499,61.2),'eval:swe-bench':(1035,1.8),
      'kilo':(797,8.5),'codex':(763,6.1),'oh-my-pi':(719,17.4),'claude-code':(639,8.9),'copilot':(295,5.8),
      'zcode':(197,9.4),'openclaw':(189,1.0),'cline':(86,1.3),'zoo':(75,.4),'openhands':(22,.1)}
    htokens=collections.Counter()
    for w in j['weeks']:
        for h,totals in w['cohorts']['top_level']['harness_token_sums'].items():htokens[h]+=totals['prompt_tokens']
    comparison=[]
    for h,(n,b) in expected.items():
        actual=j['distributions']['top_level_session_harness'][h];actualb=htokens[h]/1e9
        comparison.append({'harness':h,'paper_sessions':n,'actual_top_level_sessions':actual,'session_count_matches':actual==n,
          'paper_input_tokens_B':b,'actual_top_level_input_tokens':htokens[h],'actual_input_tokens_B':actualb,
          'input_tokens_match_at_paper_one_decimal_B':round(actualb,1)==b,'scope':'All16weeks, top-level sessions, SWE included'})
    write_csv(ROOT/'reports/table1_harness_comparison.csv',comparison)
    checks=[]
    for w in j['weeks']:
        for name,count in w['observations_requiring_review'].items():
            interpretation='Value observation; cause Unknown, not automatic corruption' if name in {'negative_tool_gap_latency','cached_tokens_exceed_provider_prompt','ttft_exceeds_derived_request_duration'} else 'Structural/schema/conditional consistency check'
            checks.append({'week':w['week'],'check':name,'observed_count':count,'status':'Verified: zero exceptions observed' if count==0 else 'Verified observation; interpretation Unknown','interpretation':interpretation,'evidence':'aggregate_stats.json + logs/profile_full_release_final.log'})
    write_csv(ROOT/'reports/quality_checks.csv',checks)
    nulls={}
    for w in j['weeks']:
        for file,meta in w['file_metadata'].items():
            for field,n in meta['nulls_in_read_fields'].items():
                key=(file,field);value=nulls.setdefault(key,{'rows':0,'nulls':0});value['rows']+=meta['rows'];value['nulls']+=n
    write_csv(ROOT/'reports/missingness_summary.csv',[{'table':file,'field':field,**v,'null_fraction':v['nulls']/v['rows'],'scope':'All16weeks; pruned strings/block top-level nulls not read; leaf footer stats in aggregate_stats.json'} for (file,field),v in sorted(nulls.items())])
    harness_table='\n'.join(f"| {r['harness']} | {r['paper_sessions']:,} | {r['actual_top_level_sessions']:,} | {r['actual_input_tokens_B']:.3f} | {r['paper_input_tokens_B']:.1f} |" for r in comparison)
    report=f'''# FreeInference 真实数据与环境验证

公开的全部 **16 周、48 个 Parquet 文件**已实际下载、逐文件 SHA-256 校验并完成分周质量审计。其顶层 Session 口径下的 Table 1 数量与 Token 总量匹配论文公布精度。此结论只覆盖公开数据统计和所列检查；不代表 Session 重建准确率、意图标签、网络流量分类或全部缓存模拟已验证。

## 范围和证据

- 官方代码固定 commit：`{SHA}`。
- HF revision：`{j['dataset_revision']}`，数据许可证 CC-BY-4.0、无需 gated 授权；来源 `https://huggingface.co/datasets/harvardMadsys/freeinference_agentic_trace`。
- 真实文件总量 **{source['bytes']:,} bytes**，没有下载/解压 108GB JSONL，没有复制缓存双份。48 文件的 URL、字节数、SHA-256、行数见 [data_manifest.csv](reports/data_manifest.csv)。每表还与 `tables.json`、其绑定的 `manifest.json` 校验。
- 下载前实测单个1.82GB文件约12MB/s，获得协调后扩展全量；全量新增文件下载 `08:18:52Z–08:25:26Z`、393.67s、2 并发，完成时 free 9,192,960,000 bytes，大于5GiB预留。[原日志](logs/processed_release_download.log)
- 分周批量读取排除 `block_ids`、工具参数/程序字符串，不执行任何 Trace 内容。最终全量审计 `08:27:22Z–08:27:51Z`，exit0，28.89s，最大RSS **{j['max_rss_kib']/1024:.1f} MiB**。[命令与返回码](logs/profile_full_release_final.json) / [输出](logs/profile_full_release_final.log)
- [aggregate_stats.json](reports/aggregate_stats.json) 包含每周 schema、footer、缺失率、键/连接、时间、token、类别分布和交叉计数；[quality_checks.csv](reports/quality_checks.csv) 可逐周复查；[missingness_summary.csv](reports/missingness_summary.csv) 汇总实际读取列的空值。

## Conda 环境和原版依赖

独立环境 `.conda/freeinference`，Python3.12.16、pandas3.1.1、PyArrow26.0.1、Matplotlib3.11.2、tiktoken0.14.0、orjson3.13.0、tree-sitter0.26.0、tree-sitter-bash0.25.1；完整版本见 [runtime_versions.json](environment/freeinference/runtime_versions.json)。Linux6.18.57/glibc2.41；任务资源探测为4CPU/16GiB，无GPU。官方该项目依赖没有PyTorch/CUDA，不需要为本项安装。

按官方 `pyproject.toml` 声明安装依赖，无兼容替换；Conda create exit0、8.46s，pip install exit0、22.53s。代码通过固定源码路径/隔离执行副本导入，没有 editable install 污染上游；本代理检查 `git status --porcelain` 为空。锁文件：[environment.yml](environment/freeinference/environment.yml)、[conda-explicit.txt](environment/freeinference/conda-explicit.txt)、[pip-freeze.txt](environment/freeinference/pip-freeze.txt)。未上传环境目录、第三方源码或原数据。

实际主要命令：

```bash
/workspace/traffic-repro-audit/.tools/miniforge3/bin/conda create -y --override-channels -c conda-forge -p /workspace/freeinference-audit/.conda/freeinference python=3.12 pip
.conda/freeinference/bin/python -m pip install --no-cache-dir -r environment/freeinference/requirements-from-upstream.txt
python scripts/download_selected_week.py
python scripts/download_processed_release.py
.conda/freeinference/bin/python scripts/profile_parquet.py --week 2026-08-30 --verify-checksums --output reports/aggregate_stats_one_week.json
.conda/freeinference/bin/python scripts/profile_parquet.py --verify-checksums --output reports/aggregate_stats.json
.conda/freeinference/bin/python scripts/build_data_dictionary.py
.conda/freeinference/bin/python scripts/build_data_manifest.py
.conda/freeinference/bin/python scripts/audit_aggregate_anomalies.py
```

实际执行用 `scripts/run_logged.py` 包装并设置超时，完整 argv/start/end/exit 在对应 `.json`，原输出在 `.log`。单周最小统计先成功，再扩全量。官方 `make figures` 和缓存模拟的命令/结果由独立运行报告记录，不能以本脚本替代官方算法验证。

## Table 1：先明确统计粒度

论文 Table1/官方 [summary.py]({BASE}paper/metrics/summary.py#L15) 使用顶层 Session population。Parquet 另外公开子代理 Session，直接对所有表行计数会错误地得到“与论文不一致”。

| 指标 | 论文Table1 | 实际顶层口径 | 全部Parquet行口径 | 判断 |
|---|---:|---:|---:|---|
| Sessions | 12,002 | {top['sessions']:,} | {j['totals']['rows']['sessions.parquet']:,} | 顶层精确匹配 |
| Requests | 1,186,582 | {top['requests']:,} | {j['totals']['rows']['requests.parquet']:,} | 顶层精确匹配 |
| Tool calls | 1,213,347 | {top['tool_calls']:,} | {j['totals']['rows']['tool_calls.parquet']:,} | 顶层精确匹配 |
| Input tokens | 209.2B | {top['tokens']['prompt_tokens']:,} | {j['totals']['tokens']['prompt_tokens']:,} | 按论文0.1B精度匹配 |
| Output tokens | 552.5M | {top['tokens']['completion_tokens']:,} | {j['totals']['tokens']['completion_tokens']:,} | 按论文0.1M精度匹配 |
| Cached tokens | 197.1B | {top['tokens']['cache_read_tokens']:,} | {j['totals']['tokens']['cache_read_tokens']:,} | 按论文0.1B精度匹配 |

子代理共 {child['sessions']:,} Sessions / {child['requests']:,} Requests / {child['tool_calls']:,} Tool calls。顶层包含1,035个SWE-Bench会话，人类部分10,967个、13种Harness。全部14类的会话数和Token精度比较见 [table1_harness_comparison.csv](reports/table1_harness_comparison.csv)。

| Harness | 论文Sessions | 实际顶层Sessions | 实际Input B | 论文Input B |
|---|---:|---:|---:|---:|
{harness_table}

## 已确认的结构、时间和缺失性

全部16周schema一致；实际3表38个顶层字段，展开role_tokens另5个子字段。无重复候选主键、无孤儿Request/Tool/子代理、无子代理环、step/call_index均从0连续，ID格式符合公开定义；实际请求时长与TTFT没有负值、没有TTFT大于衍生请求时长的行。所有行的工具latency与官方邻接公式一致。只意味着所列检查未观察到例外，不能据此证明重建关系是真实因果关联。

空值具有条件语义：顶层的父/出生键为null；每个Session第一步link_reason/waited_for/transition为null；非mutation的cause为null；非Shell工具parse_status为null；没有匹配result的outcome/result_tokens可为null；cache计数/TTFT也可能缺失。**缺失缓存计数不等于零**，应遵循 [tokens.py]({BASE}paper/metrics/tokens.py#L19) 的cache-reporting选择。已修正字典中的用户清单：Session start/end、Request turn_index、provider_tokens/mutation、Tool arguments/subagent 属于JSONL派生/嵌套表示，不是同名Parquet列。

`end_ms`来自原日志timestamp；`start_ms=end_ms-(latency_ms or 0)`是 [转换算式]({BASE}export/log_records/fields.py#L174)，并非独立客户端发包时间测量。物理采集事件、历史部署时钟和队列延迟在这份数据里仍Unknown。Completion落在周内而start跨到前一天正常：例如Aug30周4条衍生start在Aug29，不能误报超界损坏。Session自己的JSONL起止为主链request min/max；本审计分别记录主链span和包含descendant的span，不混用。

## 需解释的值观测，而非自动判定损坏

1. **4条负工具gap**：Jun21周两个request batch分别−437/−180ms；Aug30周一个batch含2条call，各−1497ms。工具latency实际为next_request.start−current.end、同batch共享，完全符合源码公式。真实工具执行起止并未采集在此字段；重建/日志时钟/并发等原因Unknown。源码在time_breakdown中把负gap截为0，tool overview单call统计等路径口径需单独识别，不能把四行解释为“真实工具耗时为负”。
2. **4条cache_read_tokens>prompt_tokens**：均在Aug9周、匿名Provider C、minimax-m3，四条总prompt835,640、cache835,703，差63。源字段来自Provider/log usage；供应商计费/报告或归一化语义不可由匿名字母还原，因此不单凭该不等式断言损坏。[anomaly_and_confounding_aggregates.json](reports/anomaly_and_confounding_aggregates.json) 保留无ID聚合证据。官方uncached_tokens截为0、cache ratio部分路径截为1，而token_growth明确保留负uncached，复算须保留该区别。
3. **Provider tokens与role_tokens不同口径**：前三种usage优先日志、fallback response.usage；role_tokens来自o200k_base digest。二者差异不是质量失败。`schema.py`的TOKENIZER注释泛称token counts，但实际 [fields.py]({BASE}export/log_records/fields.py#L154) 与 [paper tokens.py]({BASE}paper/metrics/tokens.py#L1) 明确区分。
4. **Harness方法次序**：论文§3说有UA时使用UA，否则system prompt；当前 [harness.py]({BASE}export/log_records/harness.py#L64) 先匹配前6条system/user消息、最多20K字符的intro phrase，再UA fallback。差异已源码确认；由于公开数据无原文本和UA，影响Unknown。

## 用于分类时的样本选择、泄漏和混杂

公开human agent会话须至少2个user-triggered turn、1个tool turn，SWE只要求tool turn；见 [chains.py]({BASE}export/sessions/chains.py)。这强于只排除single-request API，还会排除单用户turn的多step任务。长会话/用户idle等结论只适用于筛选人口，不宜外推所有Agent调用。

Human顶层Harness最大Hermes3,953个（36.04%），最小OpenHands22个，相差179.68倍。模型使用也不均衡：例如Codex请求60.91%为glm-5.2、Claude Code请求71.08%为deepseek-v4-flash；这些比率为**全部会话含child的request加权**。完整harness/model/provider交叉计数已保存；它证明观测共现，不是因果效应或分类准确率。公开数据无任务意图标签/正文，无法量化Harness与任务语义的混杂。

Session/user/parent/spawn/block IDs禁止当classifier特征；需以账号和整棵子代理家族分组、再做时间/模型/Provider隔离，避免随机Request划分泄漏。Harness/trigger/tool-category等可作应用层监督候选，但它们并非从PCAP直接可见，也不是独立人工真值。Schema中没有包长/方向/IAT、五元组、TLS/H2/H3 stream关联或同步客户端事件，不能直接训练或检验network-only classifier。

全量17种历史模型label中精确`mimo-v2.6-flash`为0，任意包含mimo的label也为0；这只证明此历史公开范围未观察到，不能用于判断当前模型支持或路由。当前支持性应单独查授权可用的实时文档/API。

## Unknown / 尚未完成

- 未验证原始私有日志的完整性、在线采集器历史版本、Session重建95%准确率及其误差分布。
- 未读取/重建108GB JSONL；block_ids值未全量加载，只有schema、footer大小/leaf统计，top-level list缺失率仍Unknown。被裁掉的参数/程序字符串等语义匿名性未独立验证。
- 未复现Create/Extend/Refine/Debug/Explain/Steer/Setup/Other意图标注。公开schema没有intent，无法凭counts重建。
- 未采集任何配对PCAP、未运行模型推理或分类训练；本审计不提供分类性能结论。
- 缓存仿真与图表运行见独立报告；读取预发布simulation结果生成图不等于重新执行仿真。

本数据适于Serving工作负载、应用层结构和额外采集实验的设计。其对网络侧分类的价值是先验和标签机制参考，直接网络监督数据仍需新增同步的客户端请求事件与PCAP。
'''
    (ROOT/'data_validation_report.md').write_text(report)
    quality=report.split('## 已确认的结构、时间和缺失性',1)[1].split('## 用于分类时',1)[0].replace('](reports/','](')
    (ROOT/'reports/quality_findings.md').write_text('''# 数据质量结论\n\n'''+quality+'\n\n完整范围、Table1对比和命令见 [data_validation_report.md](../data_validation_report.md)。\n')
    logs={}
    for name in ['conda_create','official_dependencies_install','selected_requests_download','processed_release_download','profile_one_week','profile_full_release','profile_full_release_final','build_data_dictionary','build_data_manifest','anomaly_and_confounding_audit']:
        p=ROOT/'logs'/f'{name}.json'
        if p.exists():logs[name]=json.loads(p.read_text())
    summary={'status':'Verified data/environment execution; partial paper reproduction evidence only','task_start_utc':'2026-11-10T08:06:28Z','source_commit':SHA,'dataset_revision':j['dataset_revision'],
      'scope':j['scope'],'all_data_bytes':source['bytes'],'cohort_totals':cohort,'identifiers_aggregate':j['identifiers_aggregate'],
      'table1_harness_rows_matching_counts':sum(r['session_count_matches'] for r in comparison),'table1_harness_rows_matching_tokens_at_reported_precision':sum(r['input_tokens_match_at_paper_one_decimal_B'] for r in comparison),
      'observations_requiring_interpretation':{k:v for k,v in j['observations_requiring_review_total'].items() if v},
      'executed_pipeline_logs':logs,'unverified':['Physical historical log instrumentation','Reconstruction accuracy','Intent annotation','Full independent cache simulation','Paired PCAP/network classification'],
      'public_artifacts':['data_dictionary.csv','data_validation_report.md','reports/aggregate_stats.json','reports/aggregate_stats_one_week.json','reports/data_manifest.csv','reports/data_source_summary.json','reports/observed_schemas.json','reports/table1_harness_comparison.csv','reports/quality_checks.csv','reports/missingness_summary.csv','reports/anomaly_and_confounding_aggregates.json','reports/quality_findings.md','environment/freeinference/','scripts/'],
      'privacy':'No raw data/IDs/arguments/program strings/paper fulltext/author code copied into public outputs; only source metadata and aggregate statistics.',
      'experiment_substitutions':'None; own quality scripts complement, never replace official statistical/algorithm execution.'}
    (ROOT/'reports/execution_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'status':'generated','harness_count_matches':sum(r['session_count_matches'] for r in comparison),'harness_token_matches':sum(r['input_tokens_match_at_paper_one_decimal_B'] for r in comparison),'quality_check_rows':len(checks),'missingness_rows':len(nulls)}))

if __name__=='__main__':main()
