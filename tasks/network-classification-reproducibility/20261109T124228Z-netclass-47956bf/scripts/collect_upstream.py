#!/usr/bin/env python3
"""Snapshot repository identity and tracked-file hashes, without modifying upstream."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
def git(p, *args):
    return subprocess.check_output(['git', '-C', str(p), *args], text=True).strip()

result = {'observed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'repositories': []}
for p in sorted((ROOT/'upstream').iterdir()):
    if not (p/'.git').exists():
        continue
    files = []
    paths = subprocess.check_output(['git','-C',str(p),'ls-files','-z']).decode().split('\0')
    for rel in paths:
        if not rel:
            continue
        q = p/rel
        if q.is_file():
            files.append({'path':rel,'bytes':q.stat().st_size,
                          'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
    result['repositories'].append({
        'id':p.name, 'remote':git(p,'remote','get-url','origin'),
        'branch':git(p,'branch','--show-current') or 'detached',
        'commit_sha':git(p,'rev-parse','HEAD'),
        'commit_utc':git(p,'show','-s','--format=%cI','HEAD'),
        'is_shallow':git(p,'rev-parse','--is-shallow-repository'),
        'git_status_porcelain':git(p,'status','--porcelain'),
        'refs':git(p,'show-ref'), 'tracked_files':files})
dest=ROOT/'environment/upstream_manifest.json'
dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(f'{len(result["repositories"])} repositories -> {dest}')
