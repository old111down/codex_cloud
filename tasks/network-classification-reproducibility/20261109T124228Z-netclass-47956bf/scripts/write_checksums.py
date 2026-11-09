#!/usr/bin/env python3
"""Seal reviewed audit files. Run intentionally after review, not as a repair."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED=('evidence/checksums.json','logs/repository_validation.',
          'logs/checksums_verification.','logs/autonomous/checksum_verification')
paths=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().split('\0')
rows=[]
for rel in sorted(set(paths)):
    if not rel or any(rel==x or rel.startswith(x) for x in EXCLUDED):
        continue
    p=ROOT/rel
    if p.is_file():
        rows.append({'path':rel,'bytes':p.stat().st_size,
                     'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
out={'sealed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
     'scope':'Reviewed Git-visible audit files; ignores upstream/environment binaries and self-referential validation output',
     'excluded':list(EXCLUDED),'files':rows}
(ROOT/'evidence/checksums.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(f'Sealed {len(rows)} audit files')
