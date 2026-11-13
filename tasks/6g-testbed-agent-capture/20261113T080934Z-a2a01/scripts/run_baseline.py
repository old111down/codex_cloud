#!/usr/bin/env python3
"""Run ten independent baseline rounds after an accepted functional smoke."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rounds', type=int, default=10)
    parser.add_argument('--prefix', default='A')
    args = parser.parse_args()
    if not 5 <= args.rounds <= 10 or not args.prefix.isalnum():
        parser.error('5–10 rounds and an alphanumeric alias prefix required')
    smoke = json.loads((ROOT / 'reports/per_run/smoke002.json').read_text())
    if (smoke.get('status') != 'PASS' or smoke.get('match_status') != 'unique_connection'
            or not all(smoke.get('checks', {}).values())):
        raise RuntimeError('accepted smoke alignment must pass before baseline')
    outcomes = []
    for i in range(1, args.rounds + 1):
        alias = f'{args.prefix}{i:03d}'
        cmd = [sys.executable, str(ROOT / 'scripts/run_logged.py'), '--log', str(ROOT / 'logs' / alias),
               '--cwd', str(ROOT), '--timeout', '110', '--', sys.executable,
               str(ROOT / 'scripts/launch_round.py'), '--run-id', alias, '--group', 'A']
        start = time.time_ns()
        result = subprocess.run(cmd, cwd=ROOT, timeout=120)
        outcomes.append({'run_id': alias, 'launch_exit': result.returncode,
                         'start_wall_ns': start, 'end_wall_ns': time.time_ns()})
        (ROOT / 'private/runtime/baseline_execution.json').write_text(json.dumps(outcomes, indent=2) + '\n')
        print(json.dumps({'round': alias, 'launch_exit': result.returncode}), flush=True)
    return 0 if all(item['launch_exit'] == 0 for item in outcomes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
