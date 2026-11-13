#!/usr/bin/env python3
"""Observe the real parent namespace and launch only our isolated round."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def qdiscs():
    result = subprocess.run(['tc', '-j', 'qdisc', 'show'], capture_output=True, text=True, timeout=5)
    return {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--group', choices=['smoke', 'A'], required=True)
    args = parser.parse_args()
    if not args.run_id.replace('_', '').replace('-', '').isalnum():
        raise ValueError('unsafe run alias')
    parent = os.readlink('/proc/self/ns/net')
    before = qdiscs()
    path = ROOT / 'private/launches' / (args.run_id + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError('refusing to overwrite a launch record')
    command = ['unshare', '--user', '--map-root-user', '--net', sys.executable,
               str(ROOT / 'scripts/run_isolated_round.py'), '--run-id', args.run_id,
               '--group', args.group, '--parent-netns', parent]
    env = os.environ.copy(); env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = {'run_id': args.run_id, 'observed_parent_netns': parent, 'command': command,
              'start_wall_ns': time.time_ns(), 'parent_qdisc_before': before}
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, timeout=100)
        record['child_exit'] = result.returncode
        run_dir = ROOT / 'private/runtime' / args.run_id
        run = json.loads((run_dir / 'run.json').read_text())
        capture = json.loads((run_dir / 'capture.json').read_text())
        record['scope_verified'] = (run['namespace'] != parent
            and capture['namespace_scope']['recorded_parent_netns'] == parent
            and capture['namespace_scope']['netns'] == run['namespace'])
    except Exception as error:
        record.update(child_exit=1, scope_verified=False, error_type=type(error).__name__, error=str(error))
    record['parent_qdisc_after'] = qdiscs()
    record['parent_qdisc_unchanged'] = (before['exit_code'] == 0
        and record['parent_qdisc_after'] == before)
    record['end_wall_ns'] = time.time_ns()
    path.write_text(json.dumps(record, indent=2) + '\n')
    ok = record['child_exit'] == 0 and record['scope_verified'] and record['parent_qdisc_unchanged']
    print(json.dumps({'run_id': args.run_id, 'launch_verified': ok,
                     'scope_verified': record['scope_verified'],
                     'parent_qdisc_unchanged': record['parent_qdisc_unchanged']}))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
