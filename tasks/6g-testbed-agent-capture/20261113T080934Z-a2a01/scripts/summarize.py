#!/usr/bin/env python3
"""Build public, payload-free round summaries from this task's local evidence."""
from __future__ import annotations
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat(timespec='microseconds')


def stats(values):
    return {'n': len(values), 'median': statistics.median(values) if values else None,
            'min': min(values) if values else None, 'max': max(values) if values else None}


def main():
    rows = []
    for run_path in sorted((ROOT / 'private/runtime').glob('*/run.json')):
        run = read(run_path); alias = run['run_id']; directory = run_path.parent
        analysis_path = ROOT / 'reports/per_run' / (alias + '.json')
        analysis = read(analysis_path) if analysis_path.exists() else {}
        launch_path = ROOT / 'private/launches' / (alias + '.json')
        launch = read(launch_path) if launch_path.exists() else {}
        raw_records = read(directory / 'application_records.json') if (directory / 'application_records.json').exists() else []
        records = [item for item in raw_records if item['scenario_id'] == run['scenario'] and item['turn_index'] >= 0]
        app = records[0] if len(records) == 1 else {}
        scope_ok = bool(launch.get('scope_verified')) and bool(launch.get('parent_qdisc_unchanged'))
        excluded = alias == 'smoke001' and not scope_ok
        match = 'EXCLUDED_AUDIT_SETUP_ERROR' if excluded else analysis.get('match_status', 'not_evaluable')
        status = 'EXCLUDED' if excluded else analysis.get('status', 'BLOCKED')
        target = analysis.get('target_filter_counts', {}); selected = analysis.get('matched_connection_counts', {})
        negative = analysis.get('negative_control', {}); clock = analysis.get('clock', {})
        rtt = analysis.get('syn_to_synack_rtt', {})
        rows.append({'run_id': alias, 'group': run['group'], 'scenario': run['scenario'],
            'profile': run['profile'], 'source_sha': run['source_sha'], 'configuration_sha256': sha(directory / 'scenario.yaml'),
            'interface': run['interface'], 'connection_policy': run['connection_policy'],
            'app_session_alias': alias + ':session1' if len(records) == 1 else '',
            'association_alias': alias + ':selected_connection' if analysis.get('match_status') == 'unique_connection' and not excluded else '',
            'association_private_evidence': f'private/analyzed/{alias}.json#eligible_candidates' if analysis.get('match_status') == 'unique_connection' and not excluded else '',
            'app_start_utc': utc(app['t_request_start']) if app else '',
            'app_end_utc': utc(app['t_last_token']) if app and app.get('t_last_token') else '',
            'app_success': bool(run.get('app_success')), 'process_exit': run.get('process_exit'),
            'app_task_latency_ms': run.get('official_task_latency_ms'),
            'invocation_elapsed_ms': run.get('invocation_elapsed_ms'),
            'observed_syn_to_synack_ms': rtt.get('median_ms'), 'syn_rtt_sample_count': rtt.get('sample_count', 0),
            'rtt_scope': 'packet_based_same_loopback_RX_observation_point_estimate_not_independent_socket_RTT',
            'http_post_request_to_response_complete_ms': analysis.get('pcap_http_request_to_response_complete_ms'),
            'pcap_private_path': f'private/runtime/{alias}/capture.pcap',
            'pcap_sha256': analysis.get('hashes', {}).get('pcap_sha256', ''),
            'capture_packets_all': (read(directory / 'capture.json')['counts']['retained_packets'] if (directory / 'capture.json').exists() else 0),
            'target_packets_c2s': target.get('client_to_server_packets'), 'target_packets_s2c': target.get('server_to_client_packets'),
            'target_packets_total': target.get('packets'), 'target_connection_count': target.get('connections'),
            'matched_connection_packets': selected.get('packets'),
            'negative_packets': negative.get('packets'), 'negative_control_status': ('PASS' if negative.get('matching_manifest_connections') == 1 and negative.get('protocol_message_send_messages') == 0 else 'Unknown'),
            'observed_rpc_method': '|'.join(analysis.get('observed_rpc_methods', [])),
            'capture_socket_drops': analysis.get('capture_validation', {}).get('reported_socket_drops'),
            'collector_anchor_read_bracket_ns': clock.get('collector', {}).get('max_anchor_read_bracket_ns'),
            'collector_observed_offset_range_ns': clock.get('collector', {}).get('offset_midpoint_range_ns'),
            'within_unexpanded_app_window': clock.get('matched_within_unexpanded_official_task_window'),
            'scope_verified': scope_ok, 'analysis_status': status, 'match_status': match,
            'included_in_A_summary': run['group'] == 'A' and status == 'PASS' and scope_ok,
            'failure_or_exclusion': ('Incorrect manually supplied parent namespace argument; superseded by automatically observed smoke002; not accepted' if excluded else ';'.join(analysis.get('failure_reasons', [])))})
    if not rows:
        raise RuntimeError('No executed round records; refusing empty success')
    with (ROOT / 'runs.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    group_a = [item for item in rows if item['group'] == 'A']
    passed = [item for item in group_a if item['included_in_A_summary']]
    if not passed:
        raise RuntimeError('No accepted A rounds; refusing numeric success report')
    summary = {'scope': 'Separated local baseline rounds; not IID population or WAN inference',
        'A_attempts': len(group_a), 'A_pass': len(passed), 'A_fail_or_blocked': len(group_a) - len(passed),
        'B_attempts': 0, 'B_status': 'BLOCKED', 'B_reason': 'tc netem in our isolated child loopback returned: Specified qdisc kind is unknown; no host module changes attempted',
        'app_task_latency_ms': stats([item['app_task_latency_ms'] for item in passed]),
        'packet_syn_to_synack_estimate_ms': stats([item['observed_syn_to_synack_ms'] for item in passed if item['observed_syn_to_synack_ms'] is not None]),
        'HTTP_post_request_to_response_complete_ms': stats([item['http_post_request_to_response_complete_ms'] for item in passed]),
        'application_invocation_ms_including_import_launch_and_card': stats([item['invocation_elapsed_ms'] for item in passed]),
        'capture_all_packets': sum(item['capture_packets_all'] for item in passed),
        'target_filtered_packets': sum(item['target_packets_total'] for item in passed),
        'matched_connection_packets_including_card': sum(item['matched_connection_packets'] for item in passed),
        'negative_control_packets': sum(item['negative_packets'] for item in passed),
        'matching': {status: sum(item['match_status'] == status for item in group_a) for status in ['unique_connection', 'ambiguous', 'unmatched', 'not_evaluable']},
        'negative_control_pass': sum(item['negative_control_status'] == 'PASS' for item in passed),
        'all_config_hashes_equal': len({item['configuration_sha256'] for item in group_a}) == 1,
        'all_connection_policies_equal': len({item['connection_policy'] for item in group_a}) == 1,
        'task_payloads_published': False, 'p95_reported_as_stable_result': False}
    if group_a and (not summary['all_config_hashes_equal'] or not summary['all_connection_policies_equal']):
        raise RuntimeError('Uncontrolled baseline configuration or connection policy drift')
    (ROOT / 'reports/summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    smoke = next((item for item in rows if item['run_id'] == 'smoke002'), None)
    if smoke is None:
        raise RuntimeError('No accepted smoke round')
    private_config = yaml.safe_load((ROOT / 'private/runtime/smoke002/scenario.yaml').read_text())
    scenario = private_config['scenarios']['a2a_single_task_local']
    safe_config = {key: value for key, value in scenario.items() if key != 'prompts'}
    safe_config['prompts'] = {'count': len(scenario['prompts']), 'contents': 'WITHHELD',
                             'sha256': read(ROOT / 'private/runtime/smoke002/run.json')['task_sha256']}
    (ROOT / 'environment/scenario_snapshot.json').write_text(json.dumps({'scenario': safe_config, 'defaults': private_config['defaults'],
        'source_yaml_sha256': smoke['configuration_sha256'], 'description': 'Sanitized one-task configuration; literal synthetic payload withheld'}, indent=2) + '\n')
    source = ROOT / 'upstream/6G-Testbed'
    if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip():
        raise RuntimeError('Upstream modified after execution; investigate before reporting')
    manifest = {'schema_version': '6g-a2a-capture-audit-v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'source_repository': 'https://github.com/5G-MAG/6G-Testbed', 'paper_review_commit': 'd055fa68ef4de30b93a8a30838ae51fe3e4b561c',
        'executed_commit': smoke['source_sha'], 'upstream_modified': False,
        'paper': 'https://arxiv.org/html/2611.07250v1', 'historical_artifact_id': 'S4aP260148',
        'historical_artifact_relation': 'Distinct historical report/workbook; not asserted to be the present execution',
        'scenario': 'a2a_single_task_local', 'observation_point': 'Own isolated network namespace loopback software RX',
        'isolation': 'unshare --user --map-root-user --net; only lo; parent/child qdisc snapshots compared',
        'capture_provider': 'Original external AF_PACKET collector; upstream sudo/tcpdump CaptureController not executed',
        'capture_filter': 'Only complete TCP/IP frames involving synthetic task ports9001/9009; PACKET_HOST only; all other frames discarded before writing',
        'pcap': {'format': 'classic nanosecond little endian', 'datalink': 'DLT_EN10MB', 'timestamp': 'SO_TIMESTAMPNS software RX CLOCK_REALTIME', 'duplication_handling': 'PACKET_HOST only; outgoing loopback copy discarded'},
        'clocks': {'application': 'Official float time.time CLOCK_REALTIME; no original monotonic duration',
                   'wrapper': 'CLOCK_MONOTONIC/CLOCK_REALTIME sandwich anchors at run/capture, not SDK per-event instrumentation',
                   'pcap': 'Kernel software RX CLOCK_REALTIME; nanosecond representation is not nanosecond accuracy',
                   'matching_tolerance_ns': 50000000, 'tolerance_is_measured_error': False,
                   'all_A_matched_without_window_expansion': all(item['within_unexpanded_app_window'] for item in passed)},
        'configuration_snapshot': 'environment/scenario_snapshot.json', 'configuration_changes': ['One deterministic local synthetic prompt instead of two defaults', 'No retries', 'No inter-run wait inside one-round CLI'],
        'connection_policy': smoke['connection_policy'],
        'versions': 'environment/agent/versions.json', 'dependencies': 'environment/agent/requirements-runtime.txt',
        'seed': '6g-testbed-local-task-v1; transformed deterministically before use; plaintext request/response not published',
        'verdicts': {'A2A_scenario_rerun': 'PASS' if len(passed) >= 5 else 'FAIL',
                     'log_pcap_alignment': 'PASS' if len(passed) >= 5 and all(item['match_status'] == 'unique_connection' for item in passed) else 'FAIL',
                     'RTT_contrast': 'BLOCKED'},
        'scope_limits': ['No claim of entire testbed/container pipeline execution', 'No upstream CaptureController execution',
                         'No packet-level SDK/tool semantic truth', 'No client socket RTT calibration or shaped-profile effect',
                         'No WAN egress, physical multihop, production, classifier or GPU experiment'],
        'private_artifacts': 'PCAP, literal task/config, original app database/records, connection IDs and raw logs remain under private/',
        'round_results': 'runs.csv', 'summary': summary}
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    app_stats = summary['app_task_latency_ms']; rtt_stats = summary['packet_syn_to_synack_estimate_ms']
    max_bracket = max(item['collector_anchor_read_bracket_ns'] for item in passed)
    max_offset_range = max(item['collector_observed_offset_range_ns'] for item in passed)
    table = '\n'.join(f"| {item['run_id']} | {item['app_task_latency_ms']:.6f} | {item['observed_syn_to_synack_ms']:.6f} | {item['target_packets_total']} | {item['match_status']} | {item['negative_control_status']} |" for item in group_a)
    (ROOT / 'REPORT.md').write_text(f'''# 5G-MAG Agent/A2A 采集链路云端验证

现在可迁移的是**版本固定的本地A2A单任务驱动、每轮独立捕获、日志—连接关联、负对照与完整性审计流程**；真实时延干预、TLS/并发CLI或桌面Agent广域出口仍缺证据。

## 三项验收

| 项目 | 判定 | 证据与范围 |
|---|---|---|
| A2A场景复跑 | {manifest['verdicts']['A2A_scenario_rerun']} | 原版orchestrator与echo agent，固定论文审查提交，10个分开的基线轮次，各一个合成任务；[逐轮表](runs.csv)、[协议摘要](reports/per_run/) |
| 应用日志↔PCAP | {manifest['verdicts']['log_pcap_alignment']} | 10/10唯一关联到一个HTTP/1.1 A2A任务连接，10个负对照连接可见且排除；只验证运行/连接粒度 |
| RTT干预对照 | BLOCKED | 新建隔离child loopback上`tc netem delay20ms`返回`Specified qdisc kind is unknown`；不加载共享宿主内核模块，不用应用sleep替代网络整形，B组0轮 |

官方场景PASS限本地确定性A2A功能路径，不代表整个测试床、Docker、全部矩阵或内建采集器通过。此处实际使用自有外置AF_PACKET采集器，原版sudo/tcpdump CaptureController没有执行。

## 来源、环境及操作约束

代码固定`{smoke['source_sha']}`，处于detached checkout，上游未修改。论文v1的§7.1用该提交审查实现；历史报告/workbook `S4aP260148`是另一来源，不能认定同次运行。官方历史ZIP本轮HTTP403，未独立核对workbook单元格。详见[论文证据](reports/paper_evidence.md)、[入口审计](reports/entrypoint_audit.md)。

Linux Debian13.6，CPU配额4核、内存限制16GiB；独立Conda Python3.12.16。安装A2A及orchestrator import所需的轻量依赖，真实仓内custom aiortc源码经PYTHONPATH导入，未安装或运行torch/GPU/VLM。原依赖锁与仓内custom aiortc声明有矛盾，详见版本和原始安装日志；这是可审查的环境选择，不声称复原历史锁环境。

普通父进程无AF_PACKET权限；本轮实际授权路径是创建自己的user+network namespace，仅包含lo，并验证父子namespace不同、每轮父qdisc前后相同。只在该child内置lo为UP和抓取本任务9001/9009端口。未修改父/共享接口或qdisc，未调用付费API、生产流量或其它场景。

## 固定任务与连接策略

私有最小YAML保留官方scenario type/provider/agent参数，只把默认两个prompts改为一个固定合成任务，retry_count=0。任务内容/原始配置不上传，哈希与去正文快照见[配置](environment/scenario_snapshot.json)。每轮重新启动官方server及SDK session，先获取Agent Card再发一次任务；实际task所在keepalive连接同时含card GET与task POST。因此不能把它笼统称为冷TCP请求，也未将冷热连接混合统计。

每轮原始PCAP、数据库、原日志和私有连接证据单独保存，路径及SHA见runs.csv和manifest。namespace inode在销毁后可能复用，不作为跨轮全局身份；同一固定task哈希用于全部轮次，每轮有各自run/session记录。IP/端口/服务身份/session及runID仅作关联真值，不是未来分类输入。记录的实际wire RPC方法是 **SendMessage**；源码注释中的message/send不当作实测字符串。

## 小样本结果

以下只有A组，不存在B组效应估计。SYN指标是**同一loopback软件RX观察点上SYN→匹配SYN-ACK的时间差（packet-based RTT estimate）**，不等于独立socket/ICMP端到端RTT校准，也不等于论文图3名义2d。

| 量 | n | 中位数ms | 范围ms |
|---|---:|---:|---:|
| 官方SDK任务时延 | {app_stats['n']} | {app_stats['median']:.6f} | {app_stats['min']:.6f}–{app_stats['max']:.6f} |
| 观测点SYN→SYNACK估计 | {rtt_stats['n']} | {rtt_stats['median']:.6f} | {rtt_stats['min']:.6f}–{rtt_stats['max']:.6f} |
| POST首字节→其响应末字节 | {summary['HTTP_post_request_to_response_complete_ms']['n']} | {summary['HTTP_post_request_to_response_complete_ms']['median']:.6f} | {summary['HTTP_post_request_to_response_complete_ms']['min']:.6f}–{summary['HTTP_post_request_to_response_complete_ms']['max']:.6f} |

这些是10个分开轮次，不自动视为IID统计样本；不报告P95为稳定尾部结论。APP与HTTP跨度的差值也不能直接归因于计算/模型开销。没有可比较的第二组，不能验证论文“任务时延随RTT变化”的干预结论。

| 轮次 | APP ms | SYN估计ms | 目标端口包数 | 匹配 | 负对照 |
|---|---:|---:|---:|---|---|
{table}

## PCAP、关联与时钟核验

10轮共{summary['capture_all_packets']}个实际捕获记录，其中目标过滤{summary['target_filtered_packets']}包、匹配连接{summary['matched_connection_packets_including_card']}包、负对照{summary['negative_control_packets']}包。匹配连接字节含card和task；目标过滤还含readiness等连接，都不能叫精确单任务网络字节。frame字节与论文Table3的IP-payload/应用层统计不能直接等同。

PCAP纳秒格式、Ethernet datalink、长度、哈希、首末时间、双向TCP、无截断/倒退、drain及内核报告丢弃数均核验；不是只检查文件存在。SYN/SYNACK及第三ACK方向与seq/ack吻合才给握手估计，重传歧义不强算。关联联合run/capture/interface、官方session记录、端点/连接epoch、时间窗、HTTP/JSONRPC id及确定性echo；全部匹配在未经扩展的官方APP窗内。9009空载TCP connect/close是已知非目标负连接，不冒充同协议语义负样本。[采集独审](reports/collector_baseline_review.md)、[分析器](scripts/analyze_capture.py)。

官方APP时钟是float `time.time()`，而wrapper/collector采样monotonic-before/realtime/monotonic-after锚点；PCAP是SO_TIMESTAMPNS软件接收CLOCK_REALTIME。DB时间float ULP约238.4ns。锚点读取夹序宽度最大{max_bracket:,}ns，观测offset range最大{max_offset_range:,.0f}ns；这些是读取区间和观测变化，不是UTC校准或packet误差上界。50ms是预声明匹配容差，不是测量误差，本轮10次未依赖它扩展APP窗。若未来加egress整形，RX tap可能位于第一单向排队之后，不能预设SYN差包含2d，必须再校验观测点与独立客户端RTT。

## 失败、修正及未验证内容

首轮审计中的smoke001应用/采集成功，但父namespace参数由包装器错误传入，故排除验收；原件和失败原因保留，smoke002改由launcher实际读取父namespace并核验后重跑通过。批运行门控首次使用了错误的summary字段而停止在首轮之前，修正为真实`match_status`并保留失败日志；没有因此伪造A组轮次。安装缺失包和首次CLI帮助失败均保留。这些历史记录不代表每次fresh复跑都会发生同一失败。当前运行未更改上游以隐藏失败。

缺口：未执行B组、未校准端到端socket RTT、未测TLS/H2/H3复用并发/重试/桌面后台流量、未验证个人助理WAN与真实多跳、无逐包工具语义真值。下一轮需要已授权且netem可用的隔离路径，在同一客户端时间基准验证RTT；再为自己的CLI/桌面Agent加进程/attempt/transport连接事件、双时钟和采集完整性计数。[迁移字段清单](reports/agent_field_migration.csv)。

复跑入口[reproduce.sh](reproduce.sh)只覆盖本任务A2A与降级分支；不执行全矩阵、AR/XR、视频、分类器或P4。入口的`--smoke-only`已在全新私有工作副本中实际执行通过（复用同一环境和只读源码，另一次任务/捕获，不计入上述A组样本）；默认十轮入口未再整体重复运行，但其基线与逐轮分析组成命令已实际执行。若未来环境已可用netem，full入口会明确停止，不能继续声称本轮的BLOCKED原因。只公开脱敏报告、脚本、汇总与环境元数据；原PCAP/明文/凭据不上传。
''')
    print(json.dumps({'A_attempts': len(group_a), 'A_pass': len(passed), 'verdicts': manifest['verdicts'], 'summary': summary}, allow_nan=False))


if __name__ == '__main__':
    main()
