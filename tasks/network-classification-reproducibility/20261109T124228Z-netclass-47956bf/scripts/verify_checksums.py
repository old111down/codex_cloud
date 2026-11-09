#!/usr/bin/env python3
"""Verify audit evidence against the saved manifest. No network requests."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/'evidence/checksums.json'
if not manifest.exists():
    raise SystemExit('Missing evidence/checksums.json')
rows=json.loads(manifest.read_text())['files']
errors=[]
for r in rows:
    p=ROOT/r['path']
    if not p.is_file():
        errors.append(f'Missing: {r["path"]}')
    elif p.stat().st_size!=r['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:
        errors.append(f'Checksum mismatch: {r["path"]}')
for e in errors:
    print(e,file=sys.stderr)
print(f'Checked {len(rows)} files; {len(errors)} errors')
raise SystemExit(bool(errors))
