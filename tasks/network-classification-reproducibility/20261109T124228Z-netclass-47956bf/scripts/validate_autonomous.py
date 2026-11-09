#!/usr/bin/env python3
"""Validate extension structure, lineage and log alignment, not scientific truth."""
import csv
import datetime as dt
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
errors=[]
def require(ok,msg):
    if not ok:
        errors.append(msg)
def csv_rows(rel):
    path=ROOT/rel
    require(path.exists(),f'Missing {rel}')
    return list(csv.DictReader(path.open(newline=''))) if path.exists() else []
def references(value,label):
    for token in re.findall(r'(?:evidence|environment|logs|papers|patches|reports)/[\w./-]+',value):
        token=token.rstrip('.,;')
        if '*' in token or token.endswith('/') or token.endswith('.'):
            continue
        require((ROOT/token).exists(),f'{label}: missing reference {token}')

required=['catalog/papers.csv','reports/coverage_matrix.csv','reports/reproduction_results.csv',
          'reports/critical_findings.md','reports/final_audit_report.md','reports/execution_timeline.md',
          'reports/reproduce_next.md']
for rel in required:
    require((ROOT/rel).is_file(),f'Missing requested deliverable {rel}')
papers=csv_rows('catalog/papers.csv')
ids={r['id'] for r in papers}
require(len(ids)==len(papers),'Duplicate paper record IDs')
for r in papers:
    label=r['id']
    for field in ('title','year','venue','repository_url','datasets','model','screening_status','paper_family_id'):
        require(bool(r.get(field)),f'{label}: empty {field}; use Unknown')
    if r.get('association_status')=='已验证':
        require(re.fullmatch(r'[0-9a-f]{40}',r.get('commit_sha','')) is not None,f'{label}: verified association missing full SHA')
        require(r.get('association_evidence') not in ('', 'Unknown'),f'{label}: no association evidence')
    date=r.get('publication_date','Unknown')
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',date) and not r.get('screening_status','').startswith('excluded'):
        require('2021-11-09'<=date<='2026-11-09',f'{label}: date outside scope')
    try:
        files=json.loads(r.get('evidence_files','[]'))
        if isinstance(files,list):
            for rel in files:
                require((ROOT/rel).exists(),f'{label}: absent evidence {rel}')
    except json.JSONDecodeError:
        require(r.get('evidence_files')=='Unknown',f'{label}: invalid evidence_files JSON')

coverage=csv_rows('reports/coverage_matrix.csv')
keys=set()
for row in coverage:
    label=f'{row["paper_id"]}/{row["claim_id"]}'
    key=(row['paper_id'],row['claim_id'])
    require(key not in keys,f'Duplicate claim {label}');keys.add(key)
    require(row['paper_id'] in ids,f'{label}: paper not in catalog')
    require(row.get('status') in {'已验证','部分覆盖','缺失','未知','不适用'},f'{label}: invalid status')
    require((ROOT/row['source_matrix']).is_file(),f'{label}: missing source matrix')
    references(row.get('evidence',''),label)
    require('pending execution' not in str(row).lower(),f'{label}: stale pending marker')
for pid in sorted({r['paper_id'] for r in coverage}):
    env=ROOT/'environment'/pid
    require((env/'environment.yml').is_file(),f'{pid}: missing environment declaration')
    require(any(env.glob('*explicit*')),f'{pid}: missing Conda explicit record')
    require(any(env.glob('*freeze*')),f'{pid}: missing pip freeze')
    require(any(env.glob('runtime*')),f'{pid}: missing runtime version probe')
    require((ROOT/'papers'/pid/'independent_review.md').is_file(),f'{pid}: missing independent review')

runs=csv_rows('reports/reproduction_results.csv')
for r in runs:
    label=f'{r["paper_id"]}/{r["run_id"]}'
    require(r['paper_id'] in ids,f'{label}: not cataloged')
    files=json.loads(r['evidence_files'])
    for rel in files:
        require((ROOT/rel).exists(),f'{label}: missing run evidence {rel}')
    meta_path=ROOT/files[0]
    if meta_path.exists():
        meta=json.loads(meta_path.read_text())
        require(str(meta.get('exit_code'))==r['exit_code'],f'{label}: exit code changed')
        require(json.loads(r['command'])==meta.get('argv',meta.get('command')),f'{label}: command changed')
    require(not str(r['reproduction_level']).startswith(('R3','R4')),f'{label}: unsupported R3/R4 claim needs explicit review')
    require(r['paper_comparable']!='true',f'{label}: unreviewed paper comparability assertion')
    if r['audit_round']=='autonomous_round2':
        start=dt.datetime.fromisoformat(r['start_utc'].replace('Z','+00:00'))
        require(start>=dt.datetime.fromisoformat('2026-11-09T11:06:24+00:00'),f'{label}: inherited run mislabeled new')
        require(start<dt.datetime.fromisoformat('2026-11-09T14:06:24+00:00'),f'{label}: experiment started beyond budget')
manifest_path=ROOT/'environment/upstream_manifest.json'
if manifest_path.exists():
    for r in json.loads(manifest_path.read_text())['repositories']:
        require(not r['git_status_porcelain'],f'{r["id"]}: upstream not pristine')

summary={'scope':'Structure/log lineage only; not a scientific correctness certification',
         'paper_records':len(papers),'coverage_rows':len(coverage),'structured_commands':len(runs),'errors':errors}
print(json.dumps(summary,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
