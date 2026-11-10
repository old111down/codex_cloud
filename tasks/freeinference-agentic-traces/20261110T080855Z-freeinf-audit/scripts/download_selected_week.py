#!/usr/bin/env python3
"""Download one pinned public Parquet object; never execute or print trace rows."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
info=json.loads((ROOT/'private/evidence/hf_repo.json').read_text())
revision=info['sha']
week='2026-08-30_2026-09-05'
rel=f'release/{week}/processed/requests.parquet'
entry=next(x for x in info['siblings'] if x['rfilename']==rel)
expected_size=entry['size'];expected_hash=entry['lfs']['sha256']
dest=ROOT/'private/data/release'/week/'requests.parquet'
dest.parent.mkdir(parents=True,exist_ok=True)
partial=dest.with_suffix('.parquet.partial')
url=f'https://huggingface.co/datasets/harvardMadsys/freeinference_agentic_trace/resolve/{revision}/{rel}'
free=shutil.disk_usage(dest.parent).free
assert free>=expected_size+5*1024**3,'Insufficient free disk after 5GiB reserve'
start=dt.datetime.now(dt.timezone.utc).isoformat();tic=time.monotonic()
count=0;h=hashlib.sha256();last=0
request=urllib.request.Request(url,headers={'User-Agent':'research-reproducibility-audit'})
try:
    with urllib.request.urlopen(request,timeout=90) as source, partial.open('wb') as output:
        while chunk:=source.read(4*1024**2):
            output.write(chunk);h.update(chunk);count+=len(chunk)
            if count-last>=128*1024**2:
                print(json.dumps({'downloaded_bytes':count,'expected_bytes':expected_size,'elapsed_seconds':round(time.monotonic()-tic,2)}),flush=True)
                last=count
    checksum=h.hexdigest()
    assert count==expected_size,(count,expected_size)
    assert checksum==expected_hash,'Downloaded data hash differs from pinned Hub LFS metadata'
    partial.replace(dest)
    status='Verified'
finally:
    record={'week':week,'revision':revision,'source_url':url,'expected_bytes':expected_size,
            'downloaded_bytes':count,'expected_sha256':expected_hash,'observed_sha256':h.hexdigest(),
            'start_utc':start,'end_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'elapsed_seconds':time.monotonic()-tic,'free_bytes_before':free,
            'status':locals().get('status','Failed'),'scope':'Public Parquet transfer/hash only; no trace rows printed'}
    (ROOT/'private/evidence/requests_download_record.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2),flush=True)
