#!/usr/bin/env python3
"""Fetch the pinned public processed release, never the 108GB JSONL.

Two workers; atomic whole-week publication into the reader's release directory.
Private data only. Hash/size validation uses the pinned HF sibling metadata and
the release's tables.json. No rows or signed redirect URLs are logged.
"""
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REV = 'bb26cf72c9c20f2b05f765d88548156a74d3c253'
metadata_path=ROOT / 'private/evidence/hf_repo.json'
if not metadata_path.exists():
    metadata_path.parent.mkdir(parents=True,exist_ok=True)
    metadata_url=f'https://huggingface.co/api/datasets/harvardMadsys/freeinference_agentic_trace/revision/{REV}?blobs=true'
    with urllib.request.urlopen(metadata_url,timeout=60) as response:
        metadata_path.write_bytes(response.read())
INFO = json.loads(metadata_path.read_text())
assert INFO['sha']==REV,'Metadata must be for the pinned dataset revision'
BASE = f'https://huggingface.co/datasets/harvardMadsys/freeinference_agentic_trace/resolve/{REV}/'
ENTRIES = {x['rfilename']: x for x in INFO['siblings']}
WEEKS = sorted({p.split('/')[1] for p in ENTRIES if p.endswith('/processed/requests.parquet')})
RESERVE = 5 * 1024**3
LOCK = threading.Lock()
RECORDS = []
OUT = ROOT / 'private/evidence/processed_download_records.json'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(16*1024**2): h.update(b)
    return h.hexdigest()

def fetch(rel, dest):
    e=ENTRIES[rel]; expected=e['size']; expected_sha=e.get('lfs',{}).get('sha256')
    started=dt.datetime.now(dt.timezone.utc).isoformat(); tic=time.monotonic()
    if dest.exists():
        actual=sha(dest)
        assert dest.stat().st_size==expected and (not expected_sha or actual==expected_sha)
        return actual
    assert shutil.disk_usage(ROOT).free >= RESERVE+expected, '5GiB reserve would be exceeded'
    partial=dest.with_suffix(dest.suffix+'.partial'); dest.parent.mkdir(parents=True,exist_ok=True)
    count=0; h=hashlib.sha256()
    with urllib.request.urlopen(urllib.request.Request(BASE+rel,headers={'User-Agent':'research-reproducibility-audit'}),timeout=120) as src, partial.open('wb') as target:
        while b:=src.read(4*1024**2):
            target.write(b); h.update(b); count+=len(b)
            if count%(256*1024**2)<len(b):
                assert shutil.disk_usage(ROOT).free>=RESERVE,'5GiB reserve reached'
    assert count==expected,'byte count mismatch'
    actual=h.hexdigest()
    assert not expected_sha or actual==expected_sha,'pinned LFS SHA mismatch'
    partial.replace(dest)
    rec={'source_url':BASE+rel,'revision':REV,'file':rel,'bytes':count,'sha256':actual,
         'expected_sha256':expected_sha,'start_utc':started,'end_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
         'elapsed_seconds':round(time.monotonic()-tic,3),'status':'Verified'}
    with LOCK:
        RECORDS.append(rec); OUT.write_text(json.dumps(RECORDS,indent=2)+'\n')
        print(json.dumps({'file':rel,'bytes':count,'sha256':actual,'elapsed_seconds':rec['elapsed_seconds'],'status':'Verified'}),flush=True)
    return actual

def week(week):
    dest=ROOT/'private/data/release'/week
    if dest.exists() and all((dest/n).exists() for n in ['manifest.json','tables.json','requests.parquet','sessions.parquet','tool_calls.parquet']):
        print(json.dumps({'week':week,'status':'already present; initially verified by selected-week downloader'}),flush=True)
        return
    staging=ROOT/'private/data/staging'/week
    for name in ['manifest.json','tables.json','sessions.parquet','tool_calls.parquet','requests.parquet']:
        rel=f'release/{week}/'+(name if name=='manifest.json' else f'processed/{name}')
        fetch(rel,staging/name)
    tables=json.loads((staging/'tables.json').read_text())
    assert sha(staging/'manifest.json')==tables['manifest_sha256']
    for name, facts in tables['files'].items(): assert sha(staging/name)==facts['sha256']
    staging.replace(dest)
    print(json.dumps({'week':week,'status':'complete; atomically published','free_bytes':shutil.disk_usage(ROOT).free}),flush=True)

if __name__=='__main__':
    remaining=sum(e['size'] for p,e in ENTRIES.items() if '/processed/' in p and p.endswith('.parquet') and not (ROOT/'private/data/release'/p.split('/')[1]/p.split('/')[-1]).exists())
    assert shutil.disk_usage(ROOT).free>=remaining+RESERVE,'Full release plan exceeds disk reserve'
    print(json.dumps({'revision':REV,'weeks':len(WEEKS),'remaining_parquet_bytes':remaining,'free_bytes':shutil.disk_usage(ROOT).free,'reserve_bytes':RESERVE}),flush=True)
    with cf.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(week,WEEKS): pass
