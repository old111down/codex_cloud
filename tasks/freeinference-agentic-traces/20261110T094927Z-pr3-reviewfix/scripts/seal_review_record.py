"""Seal this PR repair record; preserve the prior scientific snapshot fields."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess

REVIEW = Path(__file__).resolve().parents[1]
PRIOR = REVIEW.parent / '20261110T080855Z-freeinf-audit'
REPO = REVIEW.parents[2]
BASE = '34678ab6d88546fcc3d038706a38b41afbbba73d'
COMMENT = 'https://github.com/old111down/codex_cloud/pull/3#issuecomment-6764182774'
BRANCH = 'codex/freeinference-agentic-traces/20261110T080855Z-freeinf-audit'
ALLOWED = {'README.md', 'metadata.json', 'reports/publication_manifest.json',
           'scripts/download_selected_week.py', 'scripts/download_processed_release.py',
           'scripts/export_reviewed_archive.py', 'scripts/review_reproduction_evidence.py'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def original(relative):
    path = (PRIOR / relative).relative_to(REPO).as_posix()
    return subprocess.check_output(['git', '-C', str(REPO), 'show', BASE + ':' + path])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seal-time')
    args = parser.parse_args()
    now = args.seal_time or datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    result = read(REVIEW / 'reports/relocated_regression_summary.json')
    assert result['status'] == 'Verified'
    for name, checksum in result['source_sha256_after'].items():
        assert digest((PRIOR / 'scripts' / name).read_bytes()) == checksum, name
    old_metadata = json.loads(original('metadata.json'))
    current_metadata = read(PRIOR / 'metadata.json')
    assert all(current_metadata[key] == value for key, value in old_metadata.items())
    assert set(current_metadata) - set(old_metadata) == {'post_review_revisions', 'historical_artifact_hash_scope'}
    previous = read(PRIOR / 'reports/publication_manifest.json')
    prefix = PRIOR.relative_to(REPO).as_posix() + '/'
    prior_files = subprocess.check_output(['git', '-C', str(REPO), 'ls-tree', '-r', '--name-only', BASE, '--', prefix], text=True).splitlines()
    frozen = [path[len(prefix):] for path in prior_files if path[len(prefix):] not in ALLOWED]
    assert len(frozen) == 199
    assert all(digest((PRIOR / rel).read_bytes()) == digest(original(rel)) for rel in frozen)

    spec = importlib.util.spec_from_file_location('reviewed_export_rules', PRIOR / 'scripts/export_reviewed_archive.py')
    rules = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rules)
    import re

    def approved_bytes(path):
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        assert len(raw) < 2_000_000 and b'\0' not in raw
        text = raw.decode('utf-8')
        for label, pattern in rules.SECRET_PATTERNS.items():
            assert not re.search(pattern, text), f'Publication pattern rejection: {path.name}:{label}'
        return raw

    changed = []
    entries = []
    # Reject existing unreviewable review artifacts before changing any index.
    for path in REVIEW.rglob('*'):
        if path.is_file():
            approved_bytes(path)
    for entry in previous['files']:
        rel = entry['path']; raw = approved_bytes(PRIOR / rel)
        if rel in ALLOWED and digest(raw) != digest(original(rel)):
            changed.append({'path': rel, 'before_sha256': digest(original(rel)), 'after_sha256': digest(raw)})
        if digest(raw) != entry['published_sha256']:
            assert rel in ALLOWED, rel
            entry = {**entry, 'source_sha256': digest(raw), 'published_sha256': digest(raw), 'bytes': len(raw),
                     'revision_provenance': {'baseline_commit': BASE, 'run_id': REVIEW.name,
                                             'comment_url': COMMENT, 'previous_published_sha256': entry['published_sha256']}}
        entries.append(entry)
    helper = 'scripts/pinned_release_download.py'
    changed.append({'path': helper, 'before_sha256': None, 'after_sha256': digest((PRIOR / helper).read_bytes())})
    if not any(entry['path'] == helper for entry in entries):
        raw = approved_bytes(PRIOR / helper)
        entries.append({'path': helper, 'source_sha256': digest(raw), 'published_sha256': digest(raw),
                        'bytes': len(raw), 'publication_review': 'approved', 'transformations': [],
                        'kind': 'Original pinned-transfer helper added for the PR review correction'})
    previous.update(reviewed_at_utc=now, files=sorted(entries, key=lambda item: item['path']),
                    files_count=len(entries), bytes=sum(entry['bytes'] for entry in entries),
                    revision_review={'run_id': REVIEW.name, 'comment_url': COMMENT, 'baseline_commit': BASE,
                                     'historical_scientific_results_unchanged': True})
    write(PRIOR / 'reports/publication_manifest.json', previous)
    write(REVIEW / 'reports/change_inventory.json', {'baseline_commit': BASE, 'changed_or_added_artifacts': changed,
          'regenerated_index': '../20261110T080855Z-freeinf-audit/reports/publication_manifest.json',
          'immutable_prior_files_verified': len(frozen), 'scientific_status_unchanged': 'Partially Verified'})

    commands = []
    for path in sorted((REVIEW / 'logs').glob('*.json')):
        record = read(path)
        command = record.get('argv', record.get('command'))
        code = record.get('exit_code', record.get('pytest_exit_code'))
        if not isinstance(command, list) or code is None:
            continue
        commands.append({'command': command, 'cwd': record.get('cwd', str(REPO)),
                         'start_time_utc': record.get('start_utc'), 'end_time_utc': record.get('end_utc'),
                         'exit_code': code, 'status': 'Verified' if code == 0 else 'Failed',
                         'scope': 'Process outcome only; baseline intentional failures and runner mistakes are explained in task_report.md',
                         'evidence': [path.relative_to(REVIEW).as_posix(), path.with_suffix('.log').relative_to(REVIEW).as_posix()]})
    commands.sort(key=lambda entry: entry['start_time_utc'] or '')
    lines = ['# 实际执行命令', '', '以下读取本轮保存的命令记录；失败不改写为成功。原版预期失败用于证明缺陷，未重跑论文科学实验。', '']
    for entry in commands:
        lines += [f"## {Path(entry['evidence'][0]).stem}", '', f"UTC：{entry['start_time_utc']} → {entry['end_time_utc']}；exit={entry['exit_code']}。", '',
                  f"[元数据]({entry['evidence'][0]}) / [日志]({entry['evidence'][1]})", '', '```json', json.dumps(entry['command'], ensure_ascii=False), '```', '']
    (REVIEW / 'execution_log.md').write_text('\n'.join(lines))
    count = result['counts']['tests']
    (REVIEW / 'task_report.md').write_text(f'''# PR #3 评审修复报告

本轮三个P2修复及回归状态为 **Verified**，范围限审计工具；首轮论文状态仍为 **Partially Verified**。

Task ID：`{REVIEW.name}`；开始UTC：2026-11-10T09:49:27Z；报告封版UTC：{now}。原研究T0与三小时截止不重置。用户要求续改PR #3，因此保留原分支，新run记录修复关系与验证，不再创建PR或合并。

1. 下载：固定revision元数据自动初始化；selected→full及部分目录经哈希核对后复用。已有完整目录也重新核验；LFS SHA-256、非LFS Git blob及manifest绑定失败时保留证据，不静默覆盖。使用本地小型HTTP惰性字节验证，未重新下载8.37GB。
2. 导出：整批路径/内容验证、净化和扫描拒绝之前不写目标树或两个manifest。通过后staging，逐文件原子替换，公开manifest最后、本地receipt随后；不是所有I/O错误的跨文件事务。
3. 复核：原28项规则保持，任何失败都保存Failed报告并非零退出；缺失/损坏/不可序列化输入同样失败。论文已确认的数值/方法差异保留，不能与一致性失败混淆。

最终独立公开副本迁移回归 **{count}通过、0失败、0错误、0跳过**；移除私有fixture环境覆盖，完整保留仓库目录层级，只复制公开归档和临时夹具。[汇总](reports/relocated_regression_summary.json)、[日志](logs/relocated_regression.log)。默认CLI numbers是明确标注的最小合成片段，不代表完整绘图结果验证；真实旧聚合另行只读复核28项通过，见[saved recheck](reports/saved_evidence_recheck.json)。

原版基线失败、初版/最终成功及独立边界验证分别保存于logs与三个修复说明。根运行器首次flatten目录导致15个定位失败，已保留layout-error记录并修复；先前38项通过是早期scanner版本快照，最终以上述新结果及其源SHA为准。没有把中途失败隐去。

原206个文件中，仅声明的7个文件允许修订；另新增一个下载helper。其余 **199个文件逐字节不变**，含全部82份历史运行日志；原metadata所有字段值保留，只新增修订关系和历史哈希范围。[变更记录](reports/change_inventory.json)、[独立保全](reports/independent_archive_preservation.json)。原始科学结论、模型/数据/上游代码和数值对照不因本轮工具修复而升级。

已知限制：没有重复真实全量网络下载；hardlink要求同文件系统支持；未保证断电/并发导出的全批回滚；secret pattern不是完整安全证明；原论文的私有输入、意图/95%重建验证与全16周缓存独立重算仍Unknown或未完成。

源码基线：`old111down/codex_cloud@{BASE}`；作者版本仍为`2b795dbf5eac490a7c081906fdce6cc7a184b7ef`。实际命令见[execution_log.md](execution_log.md)，详细修复见[README](README.md)，公开范围见[清单](reports/publication_manifest.json)。不上传原始Trace、PCAP、完整第三方源码、环境或凭据。最终上传SHA在PR描述和回复中核对，避免提交自引用。
''')
    finding = lambda description, status, evidence, kind='runtime_observation': {'description': description, 'status': status, 'evidence_type': kind, 'evidence': evidence}
    import pytest
    metadata = {'schema_version': '1.0', 'task_id': REVIEW.name, 'task_name': 'PR3 audit-tool review corrections',
        'task_slug': 'freeinference-agentic-traces', 'run_id': REVIEW.name,
        'archive_repository': 'https://github.com/old111down/codex_cloud',
        'start_time_utc': '2026-11-10T09:49:27Z', 'end_time_utc': now,
        'end_time_scope': 'Report seal; final remote branch/PR-head verification is recorded externally in the PR description',
        'objective': 'Fix the three P2 review comments with failure-path regressions and preserve original scientific evidence',
        'branch': BRANCH, 'branch_policy_exception': 'User explicitly requested updating the existing PR; this new run is a corrective record on that same branch',
        'related_runs': [{'run_id': PRIOR.name, 'relation': 'Corrective PR review; original science status/times and artifacts retained', 'path': str(PRIOR.relative_to(REPO))}],
        'inherited_research_budget': {'original_t0_utc': old_metadata['start_time_utc'], 'deadline_utc': old_metadata['deadline_utc'], 'reset': False},
        'source_repositories': [{'url': 'https://github.com/old111down/codex_cloud', 'branch': BRANCH, 'commit_shas': [BASE], 'version_status': 'Verified'},
                                {'url': 'https://github.com/HarvardMadSys/freeinference_agentic_trace', 'commit_shas': ['2b795dbf5eac490a7c081906fdce6cc7a184b7ef'], 'version_status': 'Verified'}],
        'runtime_environment': {'python': platform.python_version(), 'pytest': pytest.__version__, 'platform': platform.system(),
                                'paper_environment': '../20261110T080855Z-freeinf-audit/environment/freeinference/runtime_versions.json',
                                'new_environment_installed': False, 'new_paper_experiments': False},
        'commands_executed': commands,
        'completed_work': [finding('Three P2 defects corrected and portable relocated regressions pass', 'Verified', ['reports/relocated_regression_summary.json', 'reports/download_fix.md', 'reports/export_fix.md', 'reports/review_status_fix.md']),
                           finding('199 original files and original metadata values preserved', 'Verified', ['reports/independent_archive_preservation.json', 'reports/change_inventory.json'])],
        'failed_experiments': [finding('Original baseline regressions fail as expected; first relocated runner used an incorrect flattened layout', 'Failed', ['logs/', 'reports/relocated_regression_layout_error.json'])],
        'important_findings': [finding('Original scientific results remain Partially Verified; tooling repairs do not validate missing paper claims', 'Verified', ['task_report.md'], 'source_fact')],
        'unverified_claims': [finding('Real clean8.37GB transfer, cross-filesystem hardlink, concurrent/disk-failure export transaction and original unverified paper claims', 'Unknown', ['task_report.md'], 'unverified_question')],
        'artifacts': [{'path': name, 'status': 'Verified', 'sha256': digest((REVIEW / name).read_bytes()), 'publication_review': 'approved'} for name in ['README.md', 'task_report.md', 'execution_log.md', 'reports/change_inventory.json']],
        'publication_review': {'status': 'Verified', 'manifest': 'reports/publication_manifest.json', 'limitations': ['Explicit reviewed text artifacts only; pattern scans are limited evidence']},
        'pull_request_url': 'https://github.com/old111down/codex_cloud/pull/3', 'review_comment_url': COMMENT,
        'final_status': 'Verified', 'final_status_scope': 'The three audit-tool repairs and regression checks only; original paper remains Partially Verified'}
    write(REVIEW / 'metadata.json', metadata)
    manifest_entries = []
    for path in sorted(REVIEW.rglob('*')):
        if not path.is_file() or path == REVIEW / 'reports/publication_manifest.json':
            continue
        assert path.suffix in {'.md', '.py', '.json', '.log', '.csv', '.txt'}
        raw = approved_bytes(path)
        manifest_entries.append({'path': path.relative_to(REVIEW).as_posix(), 'sha256': digest(raw), 'bytes': len(raw), 'publication_review': 'approved'})
    write(REVIEW / 'reports/publication_manifest.json', {'reviewed_at_utc': now, 'status': 'Verified',
          'scope': 'Original repair reports/tests, inspected small logs and aggregate rechecks; no raw data, complete third-party sources, credentials or persistent negative test payloads',
          'files': manifest_entries, 'files_count': len(manifest_entries), 'bytes': sum(item['bytes'] for item in manifest_entries),
          'limitations': ['Manifest excludes itself; scans do not prove absence of every possible sensitive datum', 'Loopback HTTP addresses in test logs are temporary synthetic fixtures']})
    print(json.dumps({'status': 'Verified', 'sealed_utc': now, 'regressions': count, 'prior_files_preserved': len(frozen), 'review_files': len(manifest_entries)}))


if __name__ == '__main__':
    main()
