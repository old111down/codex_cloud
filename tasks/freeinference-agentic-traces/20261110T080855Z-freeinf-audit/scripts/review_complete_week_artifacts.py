#!/usr/bin/env python3
"""Independently compare saved same-week simulation tables, never replay them.

Only counts, hashes, versions and aggregate deltas are emitted; request keys
are used transiently and are never printed or exported.
"""
import argparse
import datetime as dt
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--week',default='2026-06-07_2026-06-13')
p.add_argument('--recomputed',type=Path,default=ROOT/'private/runtime/complete_smallest_week_simulation')
p.add_argument('--output',type=Path,default=ROOT/'reports/independent_full_week_review.json')
p.add_argument('--execution-log',type=Path,help='Saved run_logged command metadata; reads sibling stdout log')
a=p.parse_args()
a.recomputed=a.recomputed.resolve()
reference=ROOT/'upstream/freeinference_agentic_trace/data/v1/simulation'/a.week
fresh=a.recomputed/a.week
source=ROOT/'private/data/release'/a.week
checks=[]
def test(name,value,detail=None):
 checks.append({'check':name,'status':'Verified' if bool(value) else 'Failed','detail':detail})
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
test('fresh_output_week_directory_not_symlink',not fresh.is_symlink())
ancestors=[fresh]+[p for p in fresh.parents if p.is_relative_to(ROOT)]
test('fresh_output_path_no_symlink_components',not any(p.is_symlink() for p in ancestors))
test('fresh_output_not_under_author_reference',not fresh.resolve().is_relative_to(reference.resolve()))
log_path=a.execution_log
if log_path is None:
 label={'2026-06-07_2026-06-13':'simulation_complete_smallest_week','2026-05-31_2026-06-06':'simulation_complete_mixed_scope_week'}.get(a.week)
 if label:log_path=ROOT/'logs/official_checks'/(label+'.json')
execution=None
if log_path is not None and log_path.exists():
 execution=json.loads(log_path.read_text())
 argv=execution['argv']
 position=next(i for i in range(len(argv)-1) if argv[i:i+2]==['-m','simulation'])
 sim_argv=argv[position+2:]
 test('simulation_exit_zero_not_timeout',execution['exit_code']==0 and not execution['timed_out'])
 test('explicit_week_forces_replay','--week' in sim_argv and sim_argv[sim_argv.index('--week')+1]==a.week[:10])
 test('simulation_output_is_fresh_path','--output' in sim_argv and Path(sim_argv[sim_argv.index('--output')+1]).resolve()==a.recomputed.resolve())
 stdout=log_path.with_suffix('.log').read_text()
 test('simulation_printed_completion',a.week in stdout and 'the cache replay and' in stdout)
 lo=dt.datetime.fromisoformat(execution['start_utc']).timestamp();hi=dt.datetime.fromisoformat(execution['end_utc']).timestamp()
 test('output_file_mtimes_within_simulation_window',all(lo<=(fresh/(name+'.parquet')).stat().st_mtime<=hi for name in ['tallies','totals','request_misses','cheaper_reads']))
manifest_sha=sha(source/'manifest.json')
tables=json.loads((source/'tables.json').read_text())
test('tables_bind_current_manifest',tables['manifest_sha256']==manifest_sha)
input_tables={}
for name in ['sessions.parquet','requests.parquet','tool_calls.parquet']:
 h=sha(source/name);rows=pq.read_metadata(source/name).num_rows
 test('input_sha_'+name,h==tables['files'][name]['sha256'])
 test('input_rows_'+name,rows==tables['files'][name]['rows'])
 input_tables[name]={'rows':rows,'sha256':h,'bytes':(source/name).stat().st_size}
sessions=pd.read_parquet(source/'sessions.parquet')
requests=pd.read_parquet(source/'requests.parquet',columns=['session_id','step','completion_tokens'])
top=sessions[sessions.parent_session_id.isna()]
expected_requests=requests[requests.session_id.isin(top.session_id)].copy()
expected_harness=top.set_index('session_id').harness
expected_requests['scope']=expected_requests.session_id.map(expected_harness).map(lambda h:'SWE-Bench' if h=='eval:swe-bench' else 'Agentic')
expected_scopes=set(expected_requests.scope)
TTLS=['1s','10s','30s','1m','5m','10m','15m','30m','1h','3h','6h','1d','none']
POLICIES=['ttl_only','reclaim_mutate','reclaim_dead','reclaim_both']
cohort={'all_sessions':len(sessions),'top_level_sessions':len(top),'child_sessions':len(sessions)-len(top),
        'top_level_harness_counts':{str(k):int(v) for k,v in top.harness.value_counts().items()},
        'all_requests':len(requests),'top_level_requests':len(expected_requests),
        'swe_top_level_sessions':int(top.harness.eq('eval:swe-bench').sum())}
expected_source_files={'tallies.parquet','totals.parquet','request_misses.parquet','cheaper_reads.parquet'}
for label,folder in [('reference',reference),('fresh',fresh)]:
 sources=json.loads((folder/'sources.json').read_text())
 test(label+'_source_file_set',set(sources)==expected_source_files)
 test(label+'_sources_current',all(sources[name]=={'manifest.json':manifest_sha} for name in expected_source_files))
KEYS={'tallies':['scope','policy','ttl'],'totals':['scope'],'request_misses':['scope','session_id','step'],'cheaper_reads':['ttl','read_price_cut']}
results={}
for name,keys in KEYS.items():
 rp,fp=reference/(name+'.parquet'),fresh/(name+'.parquet')
 test(name+'_different_file',not rp.samefile(fp))
 x,y=pd.read_parquet(rp),pd.read_parquet(fp)
 test(name+'_column_set',set(x)==set(y))
 test(name+'_duplicate_keys',not x.duplicated(keys).any() and not y.duplicated(keys).any())
 x=x.set_index(keys).sort_index();y=y.set_index(keys).sort_index()
 test(name+'_keyset',x.index.equals(y.index))
 comparable=x.index.equals(y.index) and set(x)==set(y)
 cols={}
 if comparable:
  for col in x:
   left,right=x[col].to_numpy(),y[col].to_numpy()
   finite=np.isfinite(left)&np.isfinite(right)
   exact=np.array_equal(left,right,equal_nan=False)
   delta=np.abs(left.astype(float)-right.astype(float))
   cols[col]={'dtype_reference':str(left.dtype),'dtype_fresh':str(right.dtype),
              'cells':len(left),'finite_cells':int(finite.sum()),'exact_equal_cells':int(np.sum(left==right)),
              'max_absolute_delta':float(delta.max()) if len(delta) else 0.0,
              'within_atol_1e6_rtol_1e12':bool(np.isclose(left,right,atol=1e-6,rtol=1e-12,equal_nan=False).all())}
   test(name+'_exact_'+col,exact and finite.all())
 if name=='tallies':
  test('tallies_exact_scope_policy_TTL_crossproduct',set(x.index)==set(itertools.product(expected_scopes,POLICIES,TTLS)))
 if name=='cheaper_reads':
  test('cheaper_reads_exact_TTL_price_crossproduct',set(x.index)==set(itertools.product(['5m','15m','none'],[i/20 for i in range(21)])))
 if name=='request_misses':
  original=pd.MultiIndex.from_frame(expected_requests[['scope','session_id','step']]).sort_values()
  released=x.reset_index();observed=pd.MultiIndex.from_frame(released[['scope','session_id','step']]).sort_values()
  test('request_misses_covers_all_top_level_requests_with_correct_scope',original.equals(observed))
 if name=='totals':
  test('totals_exact_scopes',set(x.index)==expected_scopes)
  for scope in expected_scopes:
   selected=expected_requests[expected_requests.scope==scope]
   test('totals_requests_scope_'+scope,int(x.loc[scope,'requests'])==len(selected))
   test('totals_output_scope_'+scope,float(x.loc[scope,'output_tokens'])==float(selected.completion_tokens.fillna(0).sum()))
  test('totals_requests_equal_top_level_input',int(x.requests.sum())==len(expected_requests))
  test('totals_outputs_equal_top_level_input',float(x.output_tokens.sum())==float(expected_requests.completion_tokens.fillna(0).sum()))
 info={}
 for label,path in [('reference',rp),('fresh',fp)]:
  metadata=pq.read_metadata(path);arrow=pq.read_schema(path)
  pandas_meta=json.loads((arrow.metadata or {}).get(b'pandas',b'{}'))
  info[label]={'sha256':sha(path),'bytes':path.stat().st_size,'created_by':metadata.created_by,
               'pandas_version_metadata':pandas_meta.get('pandas_version'),
               'rows':metadata.num_rows,'row_groups':metadata.num_row_groups}
 results[name]={'keys':keys,'keysets_equal':comparable,'columns':cols,**info,
                'byte_equal':info['reference']['sha256']==info['fresh']['sha256']}
report={'status':'Verified' if all(c['status']=='Verified' for c in checks) else 'Failed',
        'review_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'week':a.week,
        'scope':'Independent read-only direct Parquet artifact comparison; no simulation rerun',
        'source_commit':'2b795dbf5eac490a7c081906fdce6cc7a184b7ef',
        'source_manifest_sha256':manifest_sha,'input_tables':input_tables,'cohort':cohort,'checks':checks,
        'execution_evidence':None if execution is None else {'path':str(log_path.relative_to(ROOT)),'sha256':sha(log_path),'start_utc':execution['start_utc'],'end_utc':execution['end_utc'],'elapsed_seconds':execution['elapsed_seconds'],'exit_code':execution['exit_code']},
        'paths':{'fresh_output_relative':str(fresh.relative_to(ROOT)),'author_reference_relative':str(reference.relative_to(ROOT)),'fresh_output_is_symlink':fresh.is_symlink()},
        'check_counts':{s:sum(c['status']==s for c in checks) for s in ['Verified','Failed']},'tables':results,
        'request_keys_or_rows_emitted':0,
        'interpretation':'All compared numeric cells are checked exact before discussing float tolerance. Different Parquet hashes indicate byte-level differences, not automatically semantic differences.',
        'limitations':['This complete week only; no promotion of sixteen-week cache claims.',
                       'Matches the author model on public processed inputs, not physical provider caches or original private log truth.',
                       'Source hash binding does not independently validate sampling, session reconstruction or labels.']}
previous=[]
if a.output.exists():
 old=json.loads(a.output.read_text())
 previous=old.get('weeks',[old] if 'week' in old else [])
weeks=[w for w in previous if w.get('week')!=a.week]+[report]
weeks.sort(key=lambda w:w['week'])
combined={'status':'Verified' if all(w['status']=='Verified' for w in weeks) else 'Failed',
          'review_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
          'scope':'Independent artifact checks on specifically listed complete weeks only; no full-period simulation claim',
          'source_commit':report['source_commit'],'weeks':weeks,
          'all_sixteen_week_cache_claims':'Partially Verified; author intermediates aggregated/redrawn, not all weeks replayed',
          'request_keys_or_rows_emitted':0,
          'static_model_boundary':{
            'status':'Verified source implementation; impact Unknown',
            'claim':'The public caller chain forwards one release salt unchanged into token-only block hashing; cache identity is shared block hash within a scope, without explicit model/provider/account namespace.',
            'source_commit':report['source_commit'],
            'evidence_paths':['export/paths.py:24','export/__main__.py:48','export/build_steps.py:89','export/request_inputs/digests.py:54','export/request_inputs/digests.py:83','export/request_inputs/digests.py:115','export/request_inputs/digests.py:140','export/release/requests_table.py:197','simulation/block_reads.py:23','simulation/cache.py:70','simulation/simulate.py:26'],
            'interpretation':'An idealized reuse model, not validation of physical model/provider/tenant cache sharing; no claim of algorithm error.',
            'unknowns':['Historical private pipeline equivalence','Real deployment isolation','Cross-namespace common-prefix frequency','Effect on reported metrics'],
            'salt_value_read_or_emitted':False}}
a.output.write_text(json.dumps(combined,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
print(json.dumps({'status':report['status'],'week':a.week,'checks':report['check_counts'],'cohort':cohort,
                  'byte_equal':{k:v['byte_equal'] for k,v in results.items()},'maximum_absolute_delta':max(m['max_absolute_delta'] for v in results.values() for m in v['columns'].values())}))
raise SystemExit(report['status']!='Verified')
