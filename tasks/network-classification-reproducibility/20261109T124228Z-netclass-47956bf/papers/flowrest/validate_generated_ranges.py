#!/usr/bin/env python3
"""Inspect generated BFRT calls statically; do not call BFRT or execute the generated script."""
import ast,json,collections,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'papers/flowrest/runtime-artifacts/conference/te_unsw_per_flow_saved_model_16_classes.py'
source=p.read_text();tree=ast.parse(source)
counts=collections.Counter();ranges=collections.defaultdict(list)
for c in ast.walk(tree):
 if not isinstance(c,ast.Call) or not isinstance(c.func,ast.Attribute) or not isinstance(c.func.value,ast.Name):continue
 if not c.func.attr.startswith('add_with_'):continue
 name=c.func.value.id;counts[name]+=1
 if name.startswith('table_feature'):
  i=int(name.removeprefix('table_feature'));kw={x.arg:ast.literal_eval(x.value) for x in c.keywords}
  ranges[i].append((kw['feature'+str(i)+'_start'],kw['feature'+str(i)+'_end']))
widths=[16,3,16,16,16,16,5];checks={};bad=[]
for i,rs in ranges.items():
 maxv=2**widths[i]-1;invalid=[v for v in rs if not(0<=v[0]<=v[1]<=maxv)]
 checks['feature'+str(i)]={'bits':widths[i],'entries':len(rs),'domain_max':maxv,'invalid_intervals':invalid}
 bad.extend((i,a,b) for a,b in invalid)
assert bad==[(1,7,65535),(6,26,65535)],bad
out={'scope':'Static AST inspection of original generated calls vs pinned P4 key declarations. Not P4 compilation, BFRT load, or packet simulation',
 'generated_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'generated_bytes':p.stat().st_size,'generated_lines':len(source.splitlines()),'call_counts':dict(counts),'feature_ranges':checks,'invalid_interval_count':len(bad),'p4_evidence':'P4/Conference_version/unsw_per_flow_16_classes/unsw_per_flow_16_classes.p4:316-355',
 'conclusion':'Original generator exits0 but produces two out-of-width terminal intervals; hardware load behavior untested'}
(ROOT/'evidence/flowrest/generated_table_validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
