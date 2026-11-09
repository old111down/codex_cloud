#!/usr/bin/env python3
"""Restore only pinned public sources; never run upstream programs or overwrite files."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--only', nargs='*', help='Manifest repository IDs; default all')
a=p.parse_args()
rows=json.loads((ROOT/'environment/upstream_manifest.json').read_text())['repositories']
for r in rows:
    if a.only and r['id'] not in a.only:
        continue
    dest=ROOT/'upstream'/r['id']
    if dest.exists():
        raise SystemExit(f'Refusing to overwrite {dest}; use a fresh audit checkout')
    subprocess.run(['git','clone','--no-checkout',r['remote'],str(dest)],check=True)
    subprocess.run(['git','-C',str(dest),'checkout','--detach',r['commit_sha']],check=True)
