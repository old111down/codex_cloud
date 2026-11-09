#!/usr/bin/env python3
"""Download only named public CSVs from the repository's public share URL."""
from pathlib import Path
from urllib.request import urlopen
import hashlib,json,datetime,time
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'papers/flowrest/runtime-artifacts'
files=[('full','unibs2009_train_3_pkt.csv'),('full','unibs2009_test_3_pkt.csv'),('conference','rf3_train.csv'),('conference','rf3_test.csv')]
log=[]
for folder,name in files:
 u='https://box.networks.imdea.org/s/xV7P5bunjxbiSh1/download?path=%2F&files='+name;p=OUT/folder/name
 item={'url':u,'path':str(p.relative_to(ROOT)),'source':'Author repository README public train/test share','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with urlopen(u,timeout=60) as r, p.open('wb') as f:
   item['http_status']=r.status
   while True:
    chunk=r.read(1024*1024)
    if not chunk:break
    f.write(chunk)
  item.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),content_preview=p.read_text()[:180])
 except Exception as e:item['error']=str(e)
 item['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();log.append(item);print(json.dumps(item),flush=True)
 (ROOT/'evidence/flowrest/downloaded_data_manifest.json').write_text(json.dumps(log,indent=2)+'\n')
