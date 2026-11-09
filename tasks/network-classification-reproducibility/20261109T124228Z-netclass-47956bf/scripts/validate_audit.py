#!/usr/bin/env python3
"""Structural validation only. Scientific evidence still requires human review."""
import csv
import datetime as dt
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]
def require(condition,message):
    if not condition:
        errors.append(message)
def read_json(p):
    try:
        return json.loads(p.read_text())
    except (OSError,ValueError) as e:
        errors.append(f'{p.relative_to(ROOT)}: {e}')
        return None

rows=read_json(ROOT/'catalog/candidates.json') or []
require(len(rows)>=10,'At least ten reviewed candidates required')
require(len({r.get('id') for r in rows})==len(rows),'Duplicate candidate IDs')
mandatory=('id','title','year','venue','doi','paper_url','repository_url','branch',
           'commit_sha','license','last_commit_utc','repository_pushed_at','task',
           'input_unit','labels','datasets','model','deployment','data_public',
           'code_public','gpu_dependency','proprietary_dependency',
           'association_evidence','evidence_files')
for r in rows:
    pid=r.get('id','?')
    for field in mandatory:
        require(field in r and r[field] is not None and r[field]!='',f'{pid}: missing {field}; use Unknown explicitly')
    require(re.fullmatch(r'[0-9a-f]{40}',str(r.get('commit_sha',''))) is not None,f'{pid}: full commit SHA required')
    require(2021<=int(r.get('year',0))<=2026,f'{pid}: outside research years')
    date=r.get('publication_date','Unknown')
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(date)):
        require('2021-11-09'<=date<='2026-11-09',f'{pid}: publication outside scope')
    elif r.get('year') in (2021,2026):
        require(False,f'{pid}: boundary year requires exact publication date evidence')
    require(bool(r.get('association_evidence')) and r.get('association_evidence')!='Unknown',f'{pid}: no association evidence')
    require(r.get('association_status')=='已验证',f'{pid}: association not reviewed')
    for rel in r.get('evidence_files',[]):
        require((ROOT/rel).is_file(),f'{pid}: missing evidence file {rel}')

allowed={'已验证','部分覆盖','缺失','未知','不适用'}
columns={'claim_id','paper_section','claim','code_paths','data_paths','config','entrypoint','executable','status','missing','evidence'}
counts={}
for pid in ('mousika','etc_noms_2024','lim'):
    folder=ROOT/'papers'/pid
    for name in ('metadata.json','coverage_matrix.csv','static_audit.md','reproduction_report.md'):
        require((folder/name).is_file(),f'{pid}: missing {name}')
    path=folder/'coverage_matrix.csv'
    if not path.exists():
        continue
    with path.open(newline='') as f:
        reader=csv.DictReader(f)
        require(columns<=set(reader.fieldnames or []),f'{pid}: missing matrix columns {columns-set(reader.fieldnames or [])}')
        matrix=list(reader)
    counts[pid]=len(matrix)
    require(bool(matrix),f'{pid}: empty coverage matrix')
    ids=[r.get('claim_id') for r in matrix]
    require(len(ids)==len(set(ids)),f'{pid}: duplicate claim IDs')
    for r in matrix:
        require(r.get('status') in allowed,f'{pid}/{r.get("claim_id")}: invalid coverage state {r.get("status")}')
        require(bool(r.get('evidence')),f'{pid}/{r.get("claim_id")}: evidence or explicit Unknown required')
        require(not any('pending execution' in str(v).lower() for v in r.values()),f'{pid}/{r.get("claim_id")}: stale pending execution marker')
        for token in re.findall(r'(?:evidence|environment|logs|papers|patches)/[\w./-]+',r.get('evidence','')):
            token=token.rstrip('.,;')
            require((ROOT/token).exists(),f'{pid}/{r.get("claim_id")}: missing evidence reference {token}')
    env=ROOT/'environment'/pid
    require((env/'environment.yml').exists(),f'{pid}: missing environment.yml')
    require(any(env.glob('*explicit*')),f'{pid}: missing explicit Conda lock or failure record')
    require(any(env.glob('*freeze*')),f'{pid}: missing pip freeze or failure record')
require((ROOT/'reports/cross_paper_report.md').is_file(),'Missing cross-paper report')
require((ROOT/'environment/upstream_manifest.json').is_file(),'Missing upstream manifest')
print(json.dumps({'scope':'structural only; not scientific validation','candidates':len(rows),
                  'coverage_rows':counts,'errors':errors},ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
