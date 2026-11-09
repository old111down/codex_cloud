#!/usr/bin/env python3
"""Independent read-only evidence checks. Does not call P4, BFRT, model or SDK APIs."""
import ast,collections,csv,datetime,hashlib,itertools,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2]
P=R/'papers/etc_noms_2024';U=R/'upstream/etc_noms_2024'

def vote_entries(path):
 entries={}
 for call in ast.walk(ast.parse(path.read_text())):
  if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and call.func.value.id=='voting_table' and call.func.attr=='add_with_set_final_class':
   d={k.arg:ast.literal_eval(k.value) for k in call.keywords}
   key=tuple(d['class'+str(i)] for i in range(5))
   assert key not in entries
   entries[key]=d['class_result']
 return entries
bundled=U/'In_switch_ETC/Switch/table_entries.py'
v=vote_entries(bundled);counts=collections.Counter();errors=[]
for key in itertools.product(range(1,7),repeat=5):
 c=collections.Counter(key);mx=max(c.values());winners=[x for x,n in c.items() if n==mx]
 expected=winners[0] if len(winners)==1 else key[0]
 modern=next(x for x in key if x in winners)
 if len(winners)>1:counts['non_unique_mode']+=1
 if modern!=expected:counts['modern_mode_effective_decisions_different']+=1
 if v.get(key,key[0])!=expected:errors.append(key)
 counts['combinations']+=1
with (P/'coverage_matrix.csv').open() as f:rows=list(csv.DictReader(f))
ids=[r['claim_id'] for r in rows]
required=['ALG1-01','ALG1-02','P4-01','P4-02','P4-03','P4-04','P4-05','FIG2-IMA','FIG2-QUIC','FIG2-VPN','FIG3-IMA','FIG3-QUIC','FIG3-VPN','FIG4-A','FIG4-B','FIG4-C','FIG4-D','TABLE2-IMA','TABLE2-QUIC','TABLE2-VPN']+[f'TABLE1-{d}-{m}' for d in ['IMA','QUIC','VPN'] for m in ['RF','XGBoost','P4']]
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read-only static evidence and 7776-combination software vote semantics check. Not SDK execution, table installation, packet simulation or hardware validation.','upstream_sha':subprocess.check_output(['git','-C',str(U),'rev-parse','HEAD'],text=True).strip(),'upstream_status_short':subprocess.check_output(['git','-C',str(U),'status','--short'],text=True),'bundled_table_sha256':hashlib.sha256(bundled.read_bytes()).hexdigest(),'bundled_voting_entry_count':len(v),'voting_table_P4_declared_capacity':5256,'vote_counts':dict(counts),'bundled_vs_unique_mode_plus_P4_default_mismatches':len(errors),'coverage_matrix_rows':len(rows),'required_coverage_ids_missing':sorted(set(required)-set(ids)),'important_limit':'Static declared capacity is not hardware resource usage; equality to bundled entries is not sklearn RF probability-voting equivalence.'}
for label,rel in [('unmodified','runtime-artifacts/generator/table_entries.py'),('patched','runtime-artifacts/patched/In_switch_ETC/Offline_model_preparation/table_entries.py')]:
 p=P/rel
 if p.exists():
  vals=vote_entries(p)
  result[label]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'vote_entries':len(vals),'effective_vote_differences_from_bundled':sum(vals.get(k,k[0])!=v.get(k,k[0]) for k in itertools.product(range(1,7),repeat=5))}
  intervals={i:[] for i in range(4)}
  for node in ast.walk(ast.parse(p.read_text())):
   if not (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name)):
    continue
   name=node.func.value.id
   if name not in ['table_feature'+str(i) for i in range(4)]:
    continue
   i=int(name[-1]);kw={k.arg:ast.literal_eval(k.value) for k in node.keywords}
   intervals[i].append((kw['feature'+str(i)+'_start'],kw['feature'+str(i)+'_end']))
  ranges={}
  for i,values in intervals.items():
   maximum=(1<<[15,16,8,16][i])-1;ordered=sorted(values)
   invalid=[(a,b) for a,b in values if not 0<=a<=b<=maximum]
   discontinuities=[(a,b,c,d) for (a,b),(c,d) in zip(ordered,ordered[1:]) if b+1!=c]
   ranges[str(i)]={'entries':len(values),'key_bits':[15,16,8,16][i],'min_start':min(a for a,b in values),'max_end':max(b for a,b in values),'invalid_intervals':invalid,'gaps_or_overlaps':discontinuities,'covers_full_key_domain':not invalid and not discontinuities and ordered[0][0]==0 and ordered[-1][1]==maximum}
  result[label]['static_feature_ranges']=ranges
(R/'logs/etc_noms_2024/independent_review_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
assert not errors
assert not result['required_coverage_ids_missing']
assert not result['upstream_status_short']
assert result['patched']['effective_vote_differences_from_bundled']==0
assert all(v['covers_full_key_domain'] for v in result['patched']['static_feature_ranges'].values())
