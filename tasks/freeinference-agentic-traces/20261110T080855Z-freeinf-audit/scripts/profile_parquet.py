#!/usr/bin/env python3
"""Bounded, aggregate-only quality audit of the official public Parquet release.

Reads one week at a time and prunes block_ids and tool argument/program strings.
Never emits session/user IDs or raw rows. No trace content is executed. Real
list-of-block data is not materialized; footer sizes are recorded instead.
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import resource
import time

os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('ARROW_NUM_THREADS','2')
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]
REV='bb26cf72c9c20f2b05f765d88548156a74d3c253'
SHA='2b795dbf5eac490a7c081906fdce6cc7a184b7ef'
FILES=['sessions.parquet','requests.parquet','tool_calls.parquet']
EXCLUDE={'requests.parquet':{'block_ids','tool_definition_names'},'tool_calls.parquet':{'arguments_skeleton','programs','name'}}
EXPECTED={'sessions.parquet':6,'requests.parquet':21,'tool_calls.parquet':11}

def hash_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while b:=f.read(16*1024**2):h.update(b)
    return h.hexdigest()

def dist(series):
    return {str(k):int(v) for k,v in series.fillna('<null>').value_counts(dropna=False).sort_index().items()}

def quant(series):
    x=pd.to_numeric(series,errors='coerce').dropna()
    if not len(x):return {'n':0}
    return {'n':len(x),'sum':int(x.sum()),'min':float(x.min()),'p25':float(x.quantile(.25)),
            'median':float(x.median()),'p75':float(x.quantile(.75)), 'p90':float(x.quantile(.9)),
            'p95':float(x.quantile(.95)),'p99':float(x.quantile(.99)),'max':float(x.max())}

def crosstab(a,b):
    return [{'left':str(x),'right':str(y),'count':int(n)} for (x,y),n in pd.DataFrame({'a':a,'b':b}).fillna('<null>').value_counts().sort_index().items()]

def key_index(frame,columns):
    return pd.MultiIndex.from_frame(frame[columns])

def footer(path):
    f=pq.ParquetFile(path); m=f.metadata
    groups=[]
    for i in range(m.num_row_groups):
        rg=m.row_group(i)
        groups.append({'row_group':i,'rows':rg.num_rows,'uncompressed_bytes':rg.total_byte_size,
                       'block_ids_uncompressed_bytes':sum(rg.column(j).total_uncompressed_size for j in range(rg.num_columns) if rg.column(j).path_in_schema.startswith('block_ids'))})
    null_footer={}
    for j in range(m.row_group(0).num_columns):
        leaves=[m.row_group(i).column(j) for i in range(m.num_row_groups)]
        null_footer[leaves[0].path_in_schema]=sum(x.statistics.null_count for x in leaves) if all(x.statistics and x.statistics.has_null_count for x in leaves) else None
    return f,{'rows':m.num_rows,'row_groups':groups,'schema':str(f.schema_arrow),'top_level_fields':len(f.schema_arrow),'footer_arrow_schema_matches_column_count':len(f.schema_arrow)==EXPECTED[path.name],
              'footer_leaf_null_counts':null_footer,'footer_null_interpretation':'List leaf nulls conflate absent/empty lists and null elements; not a measured top-level list null count.'}

def audit_week(path,verify):
    name=path.name; started=dt.datetime.now(dt.timezone.utc).isoformat()
    manifest=json.loads((path/'manifest.json').read_text()); tables=json.loads((path/'tables.json').read_text())
    assert manifest['format_version']==1
    assert hash_file(path/'manifest.json')==tables['manifest_sha256']
    checks={}; frames={}; meta={}; checksums={}
    for file in FILES:
        f,meta[file]=footer(path/file)
        expected=tables['files'][file]
        checks[f'{file}:rows_equal_tables_manifest']=meta[file]['rows']==expected['rows']
        if verify:
            checksums[file]=hash_file(path/file)
            checks[f'{file}:sha256_equal_tables_manifest']=checksums[file]==expected['sha256']
        columns=[c for c in f.schema_arrow.names if c not in EXCLUDE.get(file,set())]
        # Batches keep the large block column pruned at the Parquet scan itself.
        arrow=pa.Table.from_batches(list(f.iter_batches(batch_size=8192,columns=columns,use_threads=False)))
        frames[file]=arrow.flatten().to_pandas()
        meta[file]['nulls_in_read_fields']={c:int(frames[file][c].isna().sum()) for c in frames[file]}
        meta[file]['pruned_columns']=sorted(EXCLUDE.get(file,set()))
    s,r,t=(frames[f] for f in FILES)
    checks['session_id_unique']=not bool(s.session_id.duplicated().any())
    checks['request_session_step_unique']=not bool(r.duplicated(['session_id','step']).any())
    checks['tool_session_step_index_unique']=not bool(t.duplicated(['session_id','step','call_index']).any())
    violations={
      'duplicate_session_keys':int(s.session_id.duplicated().sum()),
      'duplicate_request_keys':int(r.duplicated(['session_id','step']).sum()),
      'duplicate_tool_keys':int(t.duplicated(['session_id','step','call_index']).sum()),
      'requests_without_session':int((~r.session_id.isin(s.session_id)).sum()),
      'tools_without_request':int((~key_index(t,['session_id','step']).isin(key_index(r,['session_id','step']))).sum()),
      'sessions_without_request':int((~s.session_id.isin(r.session_id)).sum()),
      'children_without_parent_session':int((s.parent_session_id.notna()&~s.parent_session_id.isin(s.session_id)).sum()),
      'negative_request_duration':int((r.end_ms<r.start_ms).sum()),
      'negative_ttft':int((r.ttft_ms<0).sum()),
      'ttft_exceeds_derived_request_duration':int((r.ttft_ms>(r.end_ms-r.start_ms)).sum()),
      'negative_tool_gap_latency':int((t.latency_ms<0).sum()),
      'negative_prompt_tokens':int((r.prompt_tokens<0).sum()),
      'negative_completion_tokens':int((r.completion_tokens<0).sum()),
      'negative_cached_tokens':int((r.cache_read_tokens<0).sum()),
      'cached_tokens_exceed_provider_prompt':int((r.cache_read_tokens>r.prompt_tokens).sum()),
      'cause_present_without_mutation':int((r.cause.notna()&r.transition.ne('mutation')).sum()),
      'mutation_without_cause':int((r.transition.eq('mutation')&r.cause.isna()).sum()),
      'step_zero_with_link_reason':int((r.step.eq(0)&r.link_reason.notna()).sum()),
      'nonzero_step_without_link_reason':int((r.step.gt(0)&r.link_reason.isna()).sum()),
      'negative_request_step':int((r.step<0).sum()),
      'negative_call_index':int((t.call_index<0).sum()),
      'invalid_session_id_hex_format':int((~s.session_id.str.fullmatch('[0-9a-f]{32}',na=False)).sum()),
      'invalid_user_id_hex_format_nonnull':int((s.user_id.notna()&~s.user_id.str.fullmatch('[0-9a-f]{16}',na=False)).sum()),
    }
    enums={'step_trigger':{'user','tool'},'waited_for':{'user','tool','ask_user_tool','subagent'},
        'link_reason':{'tool_call_id','assistant_message'},'finish_reason':{'stop','length','tool_calls','content_filter','other'},
        'transition':{'append','mutation','switch'},'cause':{'compaction','tool_definitions','system_prompt','dropped_turns','injection','tool_result','other'}}
    for col,allowed in enums.items():violations['unknown_enum_'+col]=int((r[col].notna()&~r[col].isin(allowed)).sum())
    step_groups=r.groupby('session_id').step.agg(['min','max','count','nunique'])
    violations['noncontiguous_session_steps']=int(((step_groups['min']!=0)|(step_groups['max']+1!=step_groups['nunique'])|(step_groups['count']!=step_groups['nunique'])).sum())
    calls=t.groupby(['session_id','step']).call_index.agg(['min','max','nunique','count'])
    violations['noncontiguous_call_indexes']=int(((calls['min']!=0)|(calls['max']+1!=calls['nunique'])|(calls['count']!=calls['nunique'])).sum())
    child=s[s.parent_session_id.notna()].copy()
    ckeys=child[['parent_session_id','spawned_by_step','spawned_by_call_index']].rename(columns={'parent_session_id':'session_id','spawned_by_step':'step','spawned_by_call_index':'call_index'})
    violations['children_without_spawning_tool_key']=int((~key_index(ckeys,['session_id','step','call_index']).isin(key_index(t,['session_id','step','call_index']))).sum())
    violations['multiple_children_for_one_spawn_key']=int(ckeys.duplicated().sum())
    violations['top_level_with_spawn_fields']=int((s.parent_session_id.isna()&(s.spawned_by_step.notna()|s.spawned_by_call_index.notna())).sum())
    violations['child_missing_spawn_field']=int((child.spawned_by_step.isna()|child.spawned_by_call_index.isna()).sum())
    parents=dict(zip(child.session_id,child.parent_session_id)); cycles=0
    for k in parents:
        seen=set();curr=k
        while curr in parents:
            if curr in seen:cycles+=1;break
            seen.add(curr);curr=parents[curr]
    violations['children_with_cyclic_ancestry']=cycles
    ordered=r.sort_values(['session_id','step'])
    next_start=ordered.groupby('session_id').start_ms.shift(-1)
    next_wait=ordered.groupby('session_id').waited_for.shift(-1)
    expected_gaps=(next_start-ordered.end_ms).where(next_wait.isin({'tool','ask_user_tool','subagent'}))
    expected=ordered[['session_id','step']].assign(expected_gap=expected_gaps)
    compared=t.merge(expected,on=['session_id','step'],validate='many_to_one')
    mismatch=~(compared.latency_ms.eq(compared.expected_gap)|(compared.latency_ms.isna()&compared.expected_gap.isna()))
    violations['tool_gap_disagrees_release_adjacency_formula']=int(mismatch.sum())
    negative_calls=t[t.latency_ms<0]
    negative_gap_observation={'call_rows':len(negative_calls),'distinct_request_batches':len(negative_calls[['session_id','step']].drop_duplicates()),'gap_values_ms_counts':{str(int(k)):int(v) for k,v in negative_calls.latency_ms.value_counts().sort_index().items()},
        'explanation':'Formula consistency checked, underlying timing/linkage/instrumentation cause Unknown; these are inferred inter-request gaps, not independently measured tool execution durations.'}
    for k,v in violations.items():checks[k+':zero']=v==0
    # These observations require semantic interpretation; TTFT and tool gaps are
    # source log measurements/derivations, not independently measured network time.
    start=pd.Timestamp(name[:10],tz='UTC');end=start+pd.Timedelta(days=7)
    lo=int(start.timestamp()*1000);hi=int(end.timestamp()*1000)
    time_stats={
       'unit':'milliseconds since Unix epoch; source-definition checked, scale observed',
       'start_min_utc':pd.to_datetime(r.start_ms.min(),unit='ms',utc=True).isoformat(),
       'end_max_utc':pd.to_datetime(r.end_ms.max(),unit='ms',utc=True).isoformat(),
       'completion_outside_named_utc_week':int(((r.end_ms<lo)|(r.end_ms>=hi)).sum()),
       'derived_start_before_week':int((r.start_ms<lo).sum()),
       'duration_ms':quant(r.end_ms-r.start_ms),'ttft_ms':quant(r.ttft_ms),
       'tool_shared_gap_latency_ms':quant(t.latency_ms)}
    rs=r.merge(s[['session_id','harness','parent_session_id']],on='session_id',how='left',validate='many_to_one')
    ts=t.merge(s[['session_id','harness','parent_session_id']],on='session_id',how='left',validate='many_to_one')
    cohorts={}
    for label,mask in [('top_level',s.parent_session_id.isna()),('child',s.parent_session_id.notna())]:
        selected_s=s[mask];selected_r=rs[rs.parent_session_id.isna() if label=='top_level' else rs.parent_session_id.notna()]
        selected_t=ts[ts.parent_session_id.isna() if label=='top_level' else ts.parent_session_id.notna()]
        cohorts[label]={'sessions':len(selected_s),'requests':len(selected_r),'tool_calls':len(selected_t),
            'tokens':{k:int(selected_r[k].sum()) for k in ['prompt_tokens','completion_tokens','cache_read_tokens']},
            'harness_token_sums':selected_r.groupby('harness')[['prompt_tokens','completion_tokens','cache_read_tokens']].sum().astype('int64').to_dict('index')}
    span=r.groupby('session_id').agg(start_ms=('start_ms','min'),end_ms=('end_ms','max'),steps=('step','size'))
    span=span.join(s.set_index('session_id')[['harness','parent_session_id']])
    # Descendant-inclusive top-level elapsed spans are separately retained. No
    # claim that an externally observed task spans only mainchain requests.
    root_for={k:k for k in s.session_id}
    for k in root_for:
        cur=k;seen=set()
        while cur in parents and cur not in seen:seen.add(cur);cur=parents[cur]
        root_for[k]=cur
    span['root_session']=span.index.map(root_for)
    root_span=span.groupby('root_session').agg(start_ms=('start_ms','min'),end_ms=('end_ms','max'))
    spans={'mainchain_all_sessions_ms':quant(span.end_ms-span.start_ms),
           'mainchain_top_level_sessions_ms':quant((span.end_ms-span.start_ms)[span.parent_session_id.isna()]),
           'top_level_including_descendants_ms':quant(root_span.end_ms-root_span.start_ms)}
    role_cols=[c for c in r.columns if c.startswith('role_tokens.')]
    tokens={c:quant(r[c]) for c in ['prompt_tokens','completion_tokens','cache_read_tokens']+role_cols}
    role_sum=r[role_cols].sum(axis=1)
    tokens['provider_prompt_differs_o200k_role_sum_rows']=int((r.prompt_tokens!=role_sum).sum())
    distributions={
      'session_harness':dist(s.harness),'top_level_session_harness':dist(s.loc[s.parent_session_id.isna(),'harness']),
      'request_harness':dist(rs.harness),'request_model':dist(r.model),'request_provider':dist(r.provider),
      'request_stream':dist(r.stream),'step_trigger':dist(r.step_trigger),'waited_for':dist(r.waited_for),
      'link_reason':dist(r.link_reason),'finish_reason':dist(r.finish_reason),'transition':dist(r.transition),'mutation_cause':dist(r.cause),
      'tool_category':dist(t.category),'tool_parse_status':dist(t.parse_status),'tool_outcome':dist(t.outcome),
    }
    session_models=r.groupby('session_id').model.nunique()
    model_switch_steps=r.sort_values(['session_id','step']).groupby('session_id').model.transform(lambda x:x.ne(x.shift()).astype(int)).sum()-r.session_id.nunique()
    cross={'harness_by_model_requests':crosstab(rs.harness,rs.model),
           'model_by_provider_requests':crosstab(r.model,r.provider),
           'harness_by_provider_requests':crosstab(rs.harness,rs.provider)}
    harness_tokens=rs.groupby('harness')[['prompt_tokens','completion_tokens','cache_read_tokens']].sum().astype('int64').to_dict('index')
    observed={'week':name,'started_utc':started,'ended_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'rows':{file:meta[file]['rows'] for file in FILES},'users_within_week':int(s.user_id.nunique()),
      'top_level_sessions':int(s.parent_session_id.isna().sum()),'child_sessions':len(child),
      'sessions_using_multiple_models':int((session_models>1).sum()),'adjacent_model_switch_steps':int(model_switch_steps),
      'users_with_multiple_harnesses':int((s.groupby('user_id').harness.nunique()>1).sum()),
      'checks':checks,'observations_requiring_review':violations,'file_metadata':meta,
      'negative_gap_detail_aggregate':negative_gap_observation,
      'time':time_stats,'session_spans':spans,'tokens':tokens,'distributions':distributions,
      'confounding_crosstabs':cross,'harness_token_sums':harness_tokens,'cohorts':cohorts,
      'ttft_nonnull_fraction':float(r.ttft_ms.notna().mean()),'hashes':checksums,
      'known_limits':['Raw source events and physical timestamp meaning cannot be independently validated from public aggregates.',
        'block_ids not read; their schema/footer byte sizes only were checked.',
        'Arguments, program labels, raw tool names and tool definition strings were pruned; their semantic anonymity was not audited.',
        'No semantic intent labels or wire packet/flow measurements exist in observed schema.',
        'Pseudonymous account IDs are stable within a salt series, but one account is not necessarily one person.',
        'Labels harness/tool-category/mutation are inferred/exported metadata, not independently labeled intent ground truth.']}
    return observed

def sum_counters(weeks,key):
    result={}
    for w in weeks:
        for category,counts in w[key].items():
            target=result.setdefault(category,collections.Counter());target.update(counts)
    return {k:dict(sorted(v.items())) for k,v in result.items()}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--release',type=Path,default=ROOT/'private/data/release')
    parser.add_argument('--week',action='append');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--verify-checksums',action='store_true')
    args=parser.parse_args();start=dt.datetime.now(dt.timezone.utc).isoformat();tic=time.monotonic()
    paths=sorted(p for p in args.release.iterdir() if (p/'manifest.json').exists() and (not args.week or p.name[:10] in args.week))
    assert paths,'No selected complete week'
    results=[]
    for path in paths:
        print(json.dumps({'event':'start_week','week':path.name}),flush=True)
        w=audit_week(path,args.verify_checksums);results.append(w)
        print(json.dumps({'event':'completed_week','week':path.name,'rows':w['rows'],'nonzero_observations':{k:v for k,v in w['observations_requiring_review'].items() if v}}),flush=True)
    totals={f:sum(w['rows'][f] for w in results) for f in FILES}
    tokens={k:sum(w['tokens'][k]['sum'] for w in results) for k in ['prompt_tokens','completion_tokens','cache_read_tokens']+[f'role_tokens.{k}' for k in ['system','user','assistant','tool','tool_definitions']]}
    violations={k:sum(w['observations_requiring_review'][k] for w in results) for k in results[0]['observations_requiring_review']}
    # Cross-week pseudonymous account linkage is counted only with a consistent
    # declared salt series. Hashes are held privately and never emitted.
    salt_series={json.loads((p/'manifest.json').read_text()).get('salt_series') for p in paths}
    users=set();sessions=[]
    for p in paths:
        ss=pq.read_table(p/'sessions.parquet',columns=['session_id','user_id'])
        users.update(x for x in ss['user_id'].to_pylist() if x is not None)
        sessions.extend(ss['session_id'].to_pylist())
    identifiers={'consistent_nonnull_salt_series':len(salt_series)==1 and None not in salt_series,
        'distinct_pseudonymous_accounts_within_salt_series':len(users) if len(salt_series)==1 and None not in salt_series else None,
        'duplicate_session_ids_across_all_selected_weeks':len(sessions)-len(set(sessions)),
        'meaning':'Account pseudonyms, not verified individual people; underlying raw identities unavailable.'}
    # Cross-tabs are public label count sums.
    cross={}
    for name in results[0]['confounding_crosstabs']:
        c=collections.Counter()
        for w in results:
            for row in w['confounding_crosstabs'][name]:c[(row['left'],row['right'])]+=row['count']
        cross[name]=[{'left':k[0],'right':k[1],'count':n} for k,n in sorted(c.items())]
    result={'status':'Verified execution; scope-limited descriptive and relational audit, not full paper reproduction',
      'source_commit':SHA,'dataset_revision':REV,'start_utc':start,'end_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'elapsed_seconds':time.monotonic()-tic,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'scope':{'weeks':len(results),'week_names':[w['week'] for w in results],'block_ids_values_read':False},
      'totals':{'rows':totals,'top_level_sessions':sum(w['top_level_sessions'] for w in results),'child_sessions':sum(w['child_sessions'] for w in results),'tokens':tokens},
      'identifiers_aggregate':identifiers,'observations_requiring_review_total':violations,'distributions':sum_counters(results,'distributions'),
      'confounding_crosstabs':cross,'weeks':results}
    result['cohort_totals']={label:{k:sum(w['cohorts'][label][k] for w in results) for k in ['sessions','requests','tool_calls']} for label in ['top_level','child']}
    for label,target in result['cohort_totals'].items():
        target['tokens']={k:sum(w['cohorts'][label]['tokens'][k] for w in results) for k in ['prompt_tokens','completion_tokens','cache_read_tokens']}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'event':'finished','weeks':len(results),'rows':totals,'elapsed_seconds':result['elapsed_seconds'],'max_rss_kib':result['max_rss_kib']}),flush=True)

if __name__=='__main__':main()
