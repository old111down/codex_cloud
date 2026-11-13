#!/usr/bin/env python3
"""Run one stock, deterministic A2A scenario inside an already created netns.

No upstream source is modified. This wrapper supplies a one-prompt config,
captures task-owned loopback externally, and records an unrelated TCP control.
All raw output, payloads, database, connection identifiers and PCAP stay private.
"""
from __future__ import annotations
import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import yaml

ROOT = Path(__file__).resolve().parents[1]
SHA = 'd055fa68ef4de30b93a8a30838ae51fe3e4b561c'


def anchor():
    a = time.monotonic_ns(); wall = time.time_ns(); b = time.monotonic_ns()
    return {'wall_ns': wall, 'mono_before_ns': a, 'mono_after_ns': b}


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def command(cmd):
    x = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return {'argv': cmd, 'exit_code': x.returncode, 'stdout': x.stdout, 'stderr': x.stderr}


def negative_control():
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 9009)); server.listen(1); server.settimeout(3)
    done = []
    def accept():
        try:
            conn, _ = server.accept()
            with conn:
                conn.recv(1)
            done.append(True)
        except Exception:
            done.append(False)
    thread = threading.Thread(target=accept, daemon=True); thread.start()
    start = anchor()
    with socket.socket() as client:
        client.settimeout(2); client.connect(('127.0.0.1', 9009))
        local, remote = client.getsockname(), client.getpeername()
        client.shutdown(socket.SHUT_WR)
        client.recv(1)
    end = anchor(); thread.join(3); server.close()
    return {'client': {'ip': local[0], 'port': local[1]},
            'server': {'ip': remote[0], 'port': remote[1]},
            'start_wall_ns': start['wall_ns'], 'end_wall_ns': end['wall_ns'],
            'start_anchor': start, 'end_anchor': end, 'success': done == [True]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    p.add_argument('--group', choices=['smoke', 'A'], required=True)
    p.add_argument('--parent-netns', required=True)
    p.add_argument('--task-seed', default='6g-testbed-local-task-v1')
    args = p.parse_args()
    if not args.run_id.replace('_', '').replace('-', '').isalnum():
        p.error('run-id must be a simple synthetic alias')
    actual_ns = os.readlink('/proc/self/ns/net')
    if actual_ns == args.parent_netns or [v[1] for v in socket.if_nameindex()] != ['lo']:
        raise RuntimeError('refusing non-isolated network namespace')
    source = ROOT / 'upstream/6G-Testbed'
    observed_sha = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if observed_sha != SHA:
        raise RuntimeError('upstream commit mismatch')
    if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip():
        raise RuntimeError('upstream checkout is dirty')
    run_dir = ROOT / 'private/runtime' / args.run_id
    run_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    meta = {'schema_version': 'mag-a2a-audit-round-v1', 'run_id': args.run_id, 'group': args.group,
            'source_sha': SHA, 'scenario': 'a2a_single_task_local', 'profile': 'no_emulation',
            'interface': 'lo', 'target_port': 9001, 'negative_port': 9009,
            'connection_policy': 'new_server_and_sdk_session_per_round_card_then_one_task',
            'namespace': actual_ns, 'parent_namespace_differs': True,
            'pcap_path': 'capture.pcap', 'appdb_path': 'app.db', 'process_exit': None,
            'start_anchor': anchor(), 'clock_anchors': [], 'errors': [],
            'capture_provider': 'original_external_AF_PACKET_not_upstream_CaptureController'}
    capture = None
    files = []
    try:
        meta['loopback_up'] = command(['ip', 'link', 'set', 'lo', 'up'])
        if meta['loopback_up']['exit_code']:
            raise RuntimeError('cannot bring up the task-owned child loopback')
        meta['qdisc_before'] = command(['tc', '-j', 'qdisc', 'show', 'dev', 'lo'])
        if meta['qdisc_before']['exit_code']:
            raise RuntimeError('cannot inspect isolated baseline qdisc')
        qdiscs = json.loads(meta['qdisc_before']['stdout'])
        if any(item.get('kind') not in {'noqueue'} for item in qdiscs):
            raise RuntimeError('isolated baseline has a nontrivial qdisc')
        original = yaml.safe_load((source / 'aitestbed/configs/scenarios.yaml').read_text())
        original_profiles = yaml.safe_load((source / 'aitestbed/configs/profiles.yaml').read_text())
        scenario = copy.deepcopy(original['scenarios']['a2a_single_task_local'])
        task = base64.b32encode(hashlib.sha256(args.task_seed.encode()).digest()).decode().rstrip('=')
        scenario['prompts'] = [task]
        defaults = copy.deepcopy(original['defaults'])
        defaults.update(retry_count=0, inter_run_delay_sec=0, inter_prompt_delay_sec=0)
        config = {'scenarios': {'a2a_single_task_local': scenario}, 'defaults': defaults}
        profiles = {'profiles': {'no_emulation': original_profiles['profiles']['no_emulation']}}
        (run_dir / 'scenario.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
        (run_dir / 'profiles.yaml').write_text(yaml.safe_dump(profiles, sort_keys=False))
        meta.update(task_text=task, task_sha256=hashlib.sha256(task.encode()).hexdigest(),
                    task_bytes=len(task.encode()), expected_response_text='echo: ' + task,
                    target_operation='message/send', configuration_changes=['one deterministic synthetic prompt', 'retry_count=0', 'inter_run_delay_sec=0'])
        env = os.environ.copy()
        env.update(PYTHONDONTWRITEBYTECODE='1', NO_PROXY='127.0.0.1,localhost', no_proxy='127.0.0.1,localhost',
                   PYTHONPATH=os.pathsep.join(str(source / x) for x in ['aitestbed', 'netemu/src', 'aiortc-main-clean/src']))
        cap_command = [sys.executable, str(ROOT / 'scripts/packet_capture.py'), '--interface', 'lo',
                       '--ports', '9001,9009', '--parent-netns', args.parent_netns,
                       '--expected-netns', actual_ns,
                       '--output', str(run_dir / 'capture.pcap'), '--meta', str(run_dir / 'capture.json'),
                       '--ready-file', str(run_dir / 'capture.ready'), '--max-seconds', '120']
        meta['capture_command'] = cap_command
        caplog = (run_dir / 'capture.log').open('w'); files.append(caplog)
        capture = subprocess.Popen(cap_command, env=env, cwd=run_dir, stdout=caplog, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 8
        while not (run_dir / 'capture.ready').exists():
            if capture.poll() is not None or time.monotonic() >= deadline:
                raise RuntimeError('collector did not become ready')
            time.sleep(.02)
        meta['negative_control'] = negative_control()
        meta['clock_anchors'].append(anchor())
        app_command = [sys.executable, str(source / 'aitestbed/orchestrator.py'),
                       '--scenario', 'a2a_single_task_local', '--profile', 'no_emulation', '--runs', '1',
                       '--interface', 'lo', '--egress-only', '--no-capture-loopback',
                       '--config', str(run_dir / 'scenario.yaml'), '--profiles', str(run_dir / 'profiles.yaml'),
                       '--db', str(run_dir / 'app.db'), '--report', str(run_dir / 'official_report.json'),
                       '--stop-on-error']
        meta['command'] = app_command
        meta['app_start_anchor'] = anchor()
        with (run_dir / 'application.log').open('w') as log:
            result = subprocess.run(app_command, env=env, cwd=run_dir, stdout=log, stderr=subprocess.STDOUT, timeout=75)
        meta['app_end_anchor'] = anchor(); meta['process_exit'] = result.returncode
        meta['invocation_elapsed_ms'] = (meta['app_end_anchor']['mono_after_ns'] - meta['app_start_anchor']['mono_before_ns']) / 1e6
        meta['clock_anchors'].append(anchor())
        if (run_dir / 'app.db').exists():
            with sqlite3.connect(run_dir / 'app.db') as connection:
                connection.row_factory = sqlite3.Row
                records = [dict(row) for row in connection.execute('SELECT * FROM traffic_logs ORDER BY id')]
            write(run_dir / 'application_records.json', records)
            targets = [row for row in records if row['scenario_id'] == 'a2a_single_task_local' and row['turn_index'] >= 0]
            meta['official_records'] = len(targets)
            meta['app_success'] = result.returncode == 0 and len(targets) == 1 and bool(targets[0]['success'])
            if len(targets) == 1:
                meta['app_session_id'] = targets[0]['session_id']
                meta['official_task_latency_ms'] = targets[0]['latency_sec'] * 1000
        else:
            meta['app_success'] = False; meta['official_records'] = 0
    except Exception as exc:
        meta['errors'].append({'type': type(exc).__name__, 'message': str(exc)})
        meta.setdefault('app_success', False)
    finally:
        # Only our collector PID is signalled. The enclosing unshare invocation
        # is launched in an owned process group by run_logged.py for timeout cleanup.
        if capture is not None:
            if capture.poll() is None:
                time.sleep(.20)
                capture.send_signal(signal.SIGINT)
            try:
                meta['capture_exit'] = capture.wait(timeout=8)
            except subprocess.TimeoutExpired:
                capture.kill(); meta['capture_exit'] = capture.wait(); meta['errors'].append({'type': 'CaptureStopTimeout'})
        for handle in files:
            handle.close()
        meta['qdisc_after'] = command(['tc', '-j', 'qdisc', 'show', 'dev', 'lo'])
        meta['end_anchor'] = anchor(); meta['clock_anchors'].append(meta['end_anchor'])
        meta['status'] = 'completed' if meta.get('app_success') and meta.get('capture_exit') == 0 else 'failed'
        write(run_dir / 'run.json', meta)
    print(json.dumps({'run_id': args.run_id, 'status': meta['status'], 'app_success': meta.get('app_success'),
                      'process_exit': meta['process_exit'], 'capture_exit': meta.get('capture_exit'),
                      'official_records': meta.get('official_records'), 'errors': [item['type'] for item in meta['errors']]}))
    return 0 if meta['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
