#!/usr/bin/env python3
import json,hashlib
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];out={}
for mode,files in [('full',['unibs2009_train_3_pkt.csv','unibs2009_test_3_pkt.csv']),('conference',['rf3_train.csv','rf3_test.csv'])]:
 ds=[]
 for f in files:
  p=ROOT/'papers/flowrest/runtime-artifacts'/mode/f;d=pd.read_csv(p)
  ds.append(d)
  out[f]={'rows':len(d),'columns':list(d.columns),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'null_cells':int(d.isna().sum().sum()),'exact_duplicate_rows':int(d.duplicated().sum()),'flow_id_unique':int(d['Flow ID'].nunique()),'label_counts':d['Label'].value_counts().to_dict() if 'Label' in d else 'Unknown','time_quantiles':{c:{str(k):float(v) for k,v in d[c].quantile([0,.5,.9,1]).items()} for c in ['Flow Duration','Flow IAT Min','Flow IAT Max']}}
 out[mode+'_split_checks']={'same_flow_id_strings_across_train_test':len(set(ds[0]['Flow ID'])&set(ds[1]['Flow ID'])),'interpretation':'Flow IDs can recur on different days; raw dates/session provenance absent. This count alone is not confirmed train-test leakage.'}
(ROOT/'evidence/flowrest/data_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:({'rows':v['rows'],'null_cells':v['null_cells'],'exact_duplicate_rows':v['exact_duplicate_rows']} if 'rows' in v else v) for k,v in out.items()},indent=2))
