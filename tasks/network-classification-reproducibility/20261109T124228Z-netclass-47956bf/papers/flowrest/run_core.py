#!/usr/bin/env python3
"""Run selected untouched author notebook cells on public author CSVs; omit searches/saves/hardware."""
import os,json,sys,hashlib,time
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import accuracy_score,classification_report
ROOT=Path(__file__).resolve().parents[2];mode=sys.argv[1]
if hasattr(os,'sched_getaffinity'):
 available=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,set(available[:2]));print('cpu_affinity',sorted(os.sched_getaffinity(0)),flush=True)
if mode=='full':
 name='Full_version/Unibs_flowrest_analysis.ipynb';cells=[0,1,2,3,8,9];skip={4:'Full grid search',5:'grid result analysis',6:'grid ranking display',7:'grid feature display',10:'model display',11:'save model'}
else:
 name='Conference_version/unsw_iot_per_flow_16_classes.ipynb';cells=[0,1,2,4,5,6,7,8,9,10,11,12,13,14,17,20,23,26,27,29];skip={22:'feature/depth/tree search',24:'compression grid',28:'pruning grid',30:'overwrite saved model'}
p=ROOT/'upstream/flowrest/Python'/name;nb=json.loads(p.read_text());ns={'__name__':'__audit_core__'};seconds={}
for i in cells:
 print('Executing untouched cell',i,flush=True);t=time.monotonic();exec(compile(''.join(nb['cells'][i]['source']),str(p)+'#cell'+str(i),'exec'),ns);seconds[str(i)]=time.monotonic()-t
 if mode=='conference_time_aligned' and i==20:
  for col in ['Flow IAT Min','Flow IAT Max','Flow Duration']:ns['X_test'][col]=ns['X_test'][col]*1000
  print('AUDIT SENSITIVITY ONLY: X_test time columns multiplied1000 to match train transform',flush=True)
if mode=='full':model=ns['model'];report=ns['class_report'];Xtr=ns['X_train'][ns['select_feats']];Xte=ns['X_test'][ns['select_feats']];ytr=ns['y_train'];yte=ns['y_test'];pred=ns['y_pred']
else:model=ns['final_10_3_29_27_model'];report=ns['cl_report_29_27_full'];Xtr=ns['X_train_comp_29_27'];Xte=ns['X_test_comp_29_27'];ytr=ns['y_train'];yte=ns['y_test'];pred=model.predict(Xte)
out={'scope':'Selected original notebook cells on public author derived CSV; not full original processing, searches, hardware evaluation or paper-metric reproduction', 'mode':mode,'variant':('Data-processing sensitivity: test time features multiplied1000; not assumed paper equivalent' if mode=='conference_time_aligned' else 'original selected cells'),'notebook_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'executed_cells':cells,'skipped_cells':skip,'train_rows':len(Xtr),'test_rows':len(Xte),'features':list(Xtr.columns),'classes':ns['classes'],'model_params':model.get_params(),'tree_nodes':[int(t.tree_.node_count) for t in model.estimators_],'tree_leaves':[int(t.tree_.n_leaves) for t in model.estimators_],'accuracy':float(accuracy_score(yte,pred)),'classification_report':report,'cell_seconds':seconds,'train_input_sha256':hashlib.sha256(pd.util.hash_pandas_object(Xtr,index=True).values.tobytes()).hexdigest(),'test_input_sha256':hashlib.sha256(pd.util.hash_pandas_object(Xte,index=True).values.tobytes()).hexdigest()}
(ROOT/'evidence/flowrest'/('core_'+mode+'_metrics.json')).write_text(json.dumps(out,indent=2,default=str)+'\n');print(json.dumps(out,indent=2,default=str))
pd.DataFrame({'row_index':Xte.index,'y_true':np.asarray(yte),'y_pred':np.asarray(pred)}).to_csv(ROOT/'evidence/flowrest'/('core_'+mode+'_predictions.csv'),index=False)
