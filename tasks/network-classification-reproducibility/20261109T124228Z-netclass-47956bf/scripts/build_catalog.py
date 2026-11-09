#!/usr/bin/env python3
"""Normalize reviewed source records without inventing missing metadata."""
import csv
import datetime as dt
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FIELDS=['id','title','year','publication_date','venue','doi','paper_url','repository_url',
        'branch','commit_sha','license','last_commit_utc','repository_pushed_at',
        'repository_updated_at','task','input_unit','labels','datasets','model',
        'deployment','data_public','code_public','gpu_dependency','proprietary_dependency',
        'association_status','association_evidence','evidence_files','reproduction_level','unknowns']
rows=[]
for name in ('offline_candidates.json','network_candidates.json'):
    path=ROOT/'catalog'/name
    if not path.exists():
        raise SystemExit(f'Missing reviewed input: {path}')
    for r in json.loads(path.read_text()):
        r=dict(r)
        r['association_status']='已验证'
        r['source_record']=str(path.relative_to(ROOT))
        rows.append(r)
for pid in ('mousika','etc_noms_2024','lim'):
    path=ROOT/'papers'/pid/'metadata.json'
    r=json.loads(path.read_text())
    r['id']=pid
    r['last_commit_utc']=r.get('last_commit_utc',r.get('commit_utc',r.get('commit_time',r.get('commit_date','Unknown'))))
    r['repository_pushed_at']=r.get('repository_pushed_at',r.get('github_pushed_at',r.get('repository_api_pushed_at','Unknown')))
    r['repository_updated_at']=r.get('repository_updated_at',r.get('github_updated_at',r.get('repository_api_updated_at','Unknown')))
    r['gpu_dependency']=r.get('gpu_dependency',r.get('gpu_required_for_lim','Unknown'))
    r['proprietary_dependency']=r.get('proprietary_dependency',r.get('proprietary_hardware_software',r.get('proprietary_hardware_required','Unknown')))
    r['association_status']='已验证'
    r['evidence_files']=[str(path.relative_to(ROOT))]+[
        str(p.relative_to(ROOT)) for p in sorted((ROOT/'evidence'/pid).glob('*'))
        if p.is_file() and p.suffix in ('.pdf','.txt','.json','.md')]
    r['source_record']=str(path.relative_to(ROOT))
    rows.append(r)
rows.sort(key=lambda r:(int(r['year']),r['id']))
out=[]
for r in rows:
    value=r.get('last_commit_utc','Unknown')
    if isinstance(value,str) and value!='Unknown':
        try:
            r['last_commit_utc']=dt.datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(dt.timezone.utc).isoformat().replace('+00:00','Z')
        except ValueError:
            pass
    # Preserve reviewed extra fields and make every required catalog field explicit.
    record={k:r.get(k,'Unknown') for k in FIELDS}
    record.update({k:v for k,v in r.items() if k not in record})
    out.append(record)
(ROOT/'catalog/candidates.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (ROOT/'catalog/candidates.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS)
    w.writeheader()
    for r in out:
        w.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r[k],(list,dict)) else r[k] for k in FIELDS})
print(f'Wrote {len(out)} reviewed candidates')
