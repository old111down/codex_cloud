#!/usr/bin/env python3
"""Probe only a newly unshared network namespace; keep the raw result private."""
import json
import argparse
import os
from pathlib import Path
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent-netns', required=True)
    args = parser.parse_args()
    if os.readlink('/proc/self/ns/net') == args.parent_netns:
        raise RuntimeError('Refusing to modify the recorded parent namespace')
    links = socket.if_nameindex()
    if [name for _, name in links] != ['lo']:
        raise RuntimeError('Refusing a namespace with any interface besides lo')
    record = {'observed_wall_ns': time.time_ns(), 'netns_private': os.readlink('/proc/self/ns/net'),
              'parent_netns_private': args.parent_netns,
              'only_loopback': True, 'steps': []}
    for cmd in [['ip', 'link', 'set', 'lo', 'up'],
                ['tc', 'qdisc', 'replace', 'dev', 'lo', 'root', 'netem', 'delay', '20ms'],
                ['tc', '-j', 'qdisc', 'show', 'dev', 'lo']]:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        record['steps'].append({'argv': cmd, 'exit_code': result.returncode,
                                'stdout': result.stdout, 'stderr': result.stderr})
    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)):
        record['packet_socket'] = 'PASS'
    available = record['steps'][1]['exit_code'] == 0
    if available:
        subprocess.run(['tc', 'qdisc', 'del', 'dev', 'lo', 'root'], capture_output=True, check=True)
    record['netem'] = 'AVAILABLE_REQUIRES_CONTRAST_IMPLEMENTATION' if available else 'BLOCKED'
    path = ROOT / 'private/evidence/reproduce_namespace_probe.json'
    if path.exists():
        raise FileExistsError('refusing to overwrite permission evidence')
    path.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'packet_capture': record['packet_socket'], 'netem': record['netem'],
                      'scope': 'only this child namespace; no host/interface modifications'}))
    # Missing netem is an authorized downgrade, not a reason to skip baseline.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
