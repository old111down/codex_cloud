#!/usr/bin/env python3
"""Aggregate reviewed records and actual logs; never create experiment results."""
import csv
import datetime as dt
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
T0='2026-11-09T11:06:24+00:00'
UNKNOWN='Unknown'

def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default

def packed(value):
    return json.dumps(value,ensure_ascii=False) if isinstance(value,(list,dict,bool)) else value

def table(path, fields, rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        w.writeheader()
        for row in rows:
            w.writerow({k:packed(row.get(k,UNKNOWN)) for k in fields})

def valid(value):
    return value is not None and value!='' and value!='Unknown'

def canonical_key(r):
    doi=str(r.get('doi','')).lower().removeprefix('https://doi.org/').strip()
    if doi.startswith('10.'):
        return 'doi:'+doi
    # Titles, not repository names: the same repository can implement several papers.
    title=re.sub(r'\W+','',str(r.get('title','')).lower())
    return 'title:'+title if title else 'id:'+str(r.get('id'))

def normalize(r,source):
    r=dict(r)
    r['id']=r.get('id',r.get('paper_id',Path(source).parent.name))
    r.setdefault('paper_family_id',r['id'])
    r.setdefault('association_status','已验证' if source=='catalog/candidates.json' else UNKNOWN)
    r.setdefault('screening_status','included_verified' if r['association_status']=='已验证' else 'included_unverified')
    r.setdefault('scope_category','network_traffic_classification')
    r.setdefault('priority','P0' if str(r.get('year','')) in ('2024','2025','2026') else 'P1')
    r.setdefault('related_versions',r.get('extended_paper',r.get('journal_extension',[])))
    r.setdefault('reproduction_level','R0 (catalog only; execution Unknown)')
    r.setdefault('last_commit_utc',r.get('commit_utc',r.get('commit_time',r.get('commit_date',UNKNOWN))))
    r.setdefault('repository_pushed_at',r.get('github_pushed_at',r.get('repository_api_pushed_at',UNKNOWN)))
    r.setdefault('gpu_dependency',r.get('gpu_required_for_lim',UNKNOWN))
    r.setdefault('proprietary_dependency',r.get('proprietary_hardware_software',r.get('proprietary_hardware_required',UNKNOWN)))
    r['source_records']=[source]
    return r

sources=[ROOT/'catalog/candidates.json']+sorted((ROOT/'catalog/round2').glob('*.json'))
records=[]
by_key={}
for path in sources:
    obj=read(path,[])
    if isinstance(obj,dict):
        obj=obj.get('papers',obj.get('records',[obj]))
    if not isinstance(obj,list):
        continue
    for row in obj:
        if not isinstance(row,dict) or not row.get('title'):
            continue
        r=normalize(row,str(path.relative_to(ROOT)))
        key=canonical_key(r)
        if key in by_key:
            prior=by_key[key]
            prior['source_records']+=r['source_records']
            # Preserve first reviewed identity; fill genuinely absent values only.
            for k,v in r.items():
                if not valid(prior.get(k)) and valid(v):
                    prior[k]=v
        else:
            by_key[key]=r
            records.append(r)

# Detailed audit metadata supersedes its old candidate-stage runtime description.
metadata={}
for path in sorted((ROOT/'papers').glob('*/metadata.json')):
    obj=read(path,{})
    pid=path.parent.name
    metadata[pid]=obj
    match=next((r for r in records if r['id']==pid or canonical_key(r)==canonical_key(obj)),None)
    if match is None:
        match=normalize(dict(obj,id=pid),str(path.relative_to(ROOT)))
        records.append(match)
    else:
        for key,value in obj.items():
            if valid(value) and key not in ('id','paper_id','source_records'):
                match[key]=value
        match['source_records'].append(str(path.relative_to(ROOT)))
    match['static_audit_path']=f'papers/{pid}/static_audit.md'
    match['coverage_matrix_path']=f'papers/{pid}/coverage_matrix.csv'
    match['reproduction_report_path']=f'papers/{pid}/reproduction_report.md'
    match['scope_category']=match.get('scope_category','network_traffic_classification')
    if 'association_status' not in obj and obj.get('association_evidence'):
        match['association_status']='已验证'
    if match.get('association_status')=='已验证' and match.get('screening_status')=='included_unverified':
        match['screening_status']='included_verified'

assessments=read(ROOT/'reports/audit_assessments.json',{})
for r in records:
    if r['id'] in assessments:
        r.update(assessments[r['id']])
    value=r.get('last_commit_utc',UNKNOWN)
    if isinstance(value,str) and value!=UNKNOWN:
        try:
            r['last_commit_utc']=dt.datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(dt.timezone.utc).isoformat().replace('+00:00','Z')
        except ValueError:
            pass
records.sort(key=lambda r:(str(r.get('year',UNKNOWN)),str(r['id'])))
for r in records:
    r.setdefault('A_code_coverage','Unknown; see detailed matrix if audited')
    r.setdefault('B_execution',r.get('reproduction_level',UNKNOWN))
    r.setdefault('C_paper_result_reproduction','Unknown; no complete R3/R4 validation established')
(ROOT/'catalog/papers.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
paper_fields=['id','paper_family_id','title','year','year_basis','first_publication_year',
              'publication_date','audited_version_date','date_basis','priority_basis','venue','doi','paper_url',
              'repository_url','branch','commit_sha','license','last_commit_utc','repository_pushed_at',
              'datasets','task','input_unit','labels','model','deployment','scope_category','priority',
              'screening_status','association_status','association_evidence','data_public','code_public',
              'gpu_dependency','proprietary_dependency','related_versions','A_code_coverage','B_execution',
              'C_paper_result_reproduction','static_audit_path','coverage_matrix_path',
              'reproduction_report_path','evidence_files','unknowns','source_records']
table(ROOT/'catalog/papers.csv',paper_fields,records)
by_id={r['id']:r for r in records}

coverage=[]
for path in sorted((ROOT/'papers').glob('*/coverage_matrix.csv')):
    pid=path.parent.name
    record=by_id.get(pid,{})
    with path.open(newline='') as f:
        for row in csv.DictReader(f):
            row.update(paper_id=pid,paper_family_id=record.get('paper_family_id',pid),
                       audit_round='inherited_round1' if pid in ('mousika','etc_noms_2024','lim') else 'autonomous_round2',
                       source_matrix=str(path.relative_to(ROOT)))
            coverage.append(row)
coverage_fields=['paper_id','paper_family_id','audit_round','claim_id','paper_section','claim',
                 'code_paths','data_paths','config','entrypoint','executable','status','missing','evidence','source_matrix']
table(ROOT/'reports/coverage_matrix.csv',coverage_fields,coverage)

run_overrides={}
for path in sorted((ROOT/'papers').glob('*/execution_summary.json')):
    obj=read(path,{})
    entries=obj.get('runs',[]) if isinstance(obj,dict) else obj
    if isinstance(entries,dict):
        entries=[dict(v,run_id=k) for k,v in entries.items()]
    for r in entries:
        rid=str(r.get('run_id',r.get('id',''))).removesuffix('.json').removesuffix('.log').split('/')[-1]
        run_overrides[(path.parent.name,rid)]=dict(r,summary_source=str(path.relative_to(ROOT)))

runs=[]
for path in sorted((ROOT/'logs').glob('*/*.json')):
    obj=read(path,{})
    if not isinstance(obj,dict) or not ('argv' in obj or 'command' in obj) or 'exit_code' not in obj:
        continue
    pid=path.parent.name
    if pid not in metadata:
        continue
    rid=path.stem
    override=run_overrides.get((pid,rid),{})
    start=obj.get('start_utc',obj.get('started_utc',UNKNOWN))
    try:
        round_name='autonomous_round2' if dt.datetime.fromisoformat(start.replace('Z','+00:00'))>=dt.datetime.fromisoformat(T0) else 'inherited_round1'
    except (ValueError,TypeError):
        round_name='Unknown'
    logfile=path.with_suffix('.log')
    output=logfile.read_text(errors='replace') if logfile.exists() else ''
    failure='Not applicable' if obj['exit_code']==0 else next((x.strip() for x in reversed(output.splitlines()) if x.strip()),'Unknown; see original log')
    name=rid.lower()
    phase='setup' if any(x in name for x in ('conda','install','dependency')) else 'source_acquisition' if any(x in name for x in ('clone','download')) else 'patch_management' if any(x in name for x in ('patch1_apply','patch1_check','patch2_apply','patch2_check','patch3_apply','patch3_check','patch_apply','patch_check')) else 'probe' if 'probe' in name else 'patch_validation' if any(x in name for x in ('patch','counterexample','validation')) else 'smoke' if 'smoke' in name else 'execution'
    metrics={}
    # Exit 0 alone cannot establish even an algorithm smoke test (e.g. empty CSV,
    # a disabled controller generator, or applying a patch).
    level='R0 (command completion/failed attempt only; no algorithm validation inferred)'
    input_kind='Unknown'
    if pid=='lim' and rid in ('readme_classifier','core_capture') and obj['exit_code']==0:
        metrics=read(ROOT/'evidence/lim/metrics.json',{})
        level='R2 (author CSV core only)';input_kind='real_author_derived_CSV'
    elif pid=='etc_noms_2024' and rid=='notebook_subset' and obj['exit_code']==0:
        metrics=read(ROOT/'papers/etc_noms_2024/core_sample_metrics.json',{})
        level='R2 (NIMS sample core only)';input_kind='real_author_derived_CSV'
    elif pid=='mousika' and rid=='real_subset_smoke' and obj['exit_code']==0:
        metrics=json.loads(output)
        level='R2 (UNIV prefix component only; paper overall R1)';input_kind='real_author_derived_CSV_prefix'
    elif 'synthetic' in name:
        input_kind='synthetic'
    if pid=='mousika' and rid in ('synthetic_smoke_scoped','readme_rule2entry','parser_patch_smoke','v2_gini_counterexample') and obj['exit_code']==0:
        level='R1 (bounded component only)'
    if pid=='lim' and rid=='synthetic_smoke' and obj['exit_code']==0:
        level='R1 (synthetic dependency/fit smoke only)'
    if pid=='lim' and rid=='readme_preprocess':
        failure='Exit 0 but header-only CSV; no real PCAP processed'
        metrics={'output_rows':0};input_kind='none'
    if pid=='etc_noms_2024' and rid in ('model_generation','model_generation_patched','model_generation_patched_v2','table_validation_v2') and obj['exit_code']==0:
        level='R1 (software generator/entry comparison only; not P4 execution)'
    reason=override.get('failure_reason',failure)
    if not reason:
        reason='Not applicable' if obj['exit_code']==0 else 'Unknown; consult original log'
    row={'run_id':rid,'paper_id':pid,'paper_family_id':by_id.get(pid,{}).get('paper_family_id',pid),
         'audit_round':round_name,'phase':override.get('phase',phase),
         'start_utc':start,'end_utc':obj.get('end_utc',obj.get('ended_utc',UNKNOWN)),
         'elapsed_seconds':obj.get('elapsed_seconds',UNKNOWN),'cwd':obj.get('cwd',UNKNOWN),
         'command':obj.get('argv',obj.get('command',UNKNOWN)),
         'exit_code':obj['exit_code'],'execution_status':'command_exit_0' if obj['exit_code']==0 else 'command_failed',
         'input_kind':override.get('input_kind',input_kind),'metrics':override.get('metrics',metrics or UNKNOWN),
         'reproduction_level':override.get('level',level),
         'paper_comparable':override.get('paper_comparable',False),
         'failure_reason':reason,
         'limitations':override.get('limitations','Command exit status is not scientific equivalence; see per-paper report'),
         'evidence_files':[str(path.relative_to(ROOT)),str(logfile.relative_to(ROOT))]}
    if override.get('summary_source'):
        row['evidence_files'].append(override['summary_source'])
    row['evidence_files']+=override.get('evidence_files',[])
    runs.append(row)
run_fields=['paper_id','paper_family_id','run_id','audit_round','phase','start_utc','end_utc',
            'elapsed_seconds','cwd','command','exit_code','execution_status','input_kind','metrics',
            'reproduction_level','paper_comparable','failure_reason','limitations','evidence_files']
table(ROOT/'reports/reproduction_results.csv',run_fields,runs)
included=[r for r in records if not str(r.get('screening_status','')).startswith('excluded')]
verified_included=[r for r in included if r['association_status']=='已验证']
summary={'screened_records':len(records),'paper_families':len({r['paper_family_id'] for r in records}),
         'included_paper_families':len({r['paper_family_id'] for r in included}),
         'verified_included_paper_families':len({r['paper_family_id'] for r in verified_included}),
         'association_verified_records':sum(r['association_status']=='已验证' for r in records),
         'static_audits':len(list((ROOT/'papers').glob('*/coverage_matrix.csv'))),
         'coverage_rows':len(coverage),'command_records':len(runs),
         'new_round_command_records':sum(r['audit_round']=='autonomous_round2' for r in runs),
         'new_round_runtime_attempt_projects':sorted({r['paper_id'] for r in runs if r['audit_round']=='autonomous_round2' and r['phase'] not in ('setup','probe','source_acquisition','patch_management')}),
         'new_round_successful_algorithm_test_projects':sorted({r['paper_id'] for r in runs if r['audit_round']=='autonomous_round2' and r['exit_code']==0 and str(r['reproduction_level']).startswith(('R1','R2'))})}
(ROOT/'reports/aggregate_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
