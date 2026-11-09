#!/usr/bin/env python3
"""Limited original-function and author-artifact smoke; all inputs synthetic."""
import hashlib,json,pickle,ast,collections
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.metrics import accuracy_score
ROOT=Path(__file__).resolve().parents[2];UP=ROOT/'upstream/flowrest'; E=ROOT/'evidence/flowrest'
notebook=UP/'Python/Conference_version/unsw_iot_per_flow_16_classes.ipynb'
x=json.loads(notebook.read_text());ns={}
for i in (0,4,5,6,7,8,9,10,11,12,13,14):
 exec(compile(''.join(x['cells'][i]['source']),str(notebook)+'#cell'+str(i),'exec'),ns)
rng=np.random.RandomState(42)
X=pd.DataFrame({'f0':np.r_[np.zeros(24),np.ones(24)],'f1':rng.randint(0,10,48)})
y=np.r_[np.zeros(24,dtype=int),np.ones(24,dtype=int)]
importance=pd.DataFrame({0:[1.0,0.0]},index=X.columns)
ret=ns['get_fewest_features']([None,3,3],importance,X,y,X,y,99,'macro')
assert ret is None
ret_fixed_parameter=ns['get_fewest_features']([None,3,3],importance,X,y,X,y,0.99,'macro')
assert ret_fixed_parameter is not None and ret_fixed_parameter[1]==1.0
model=ns['fit_final_model'](X.columns,[None,3,3],X,y)
assert np.array_equal(model.predict(X),y)
artifact=UP/'Python/Conference_version/unsw_per_flow_saved_model_16_classes.sav'
# Provenance/hash and static opcode review are in pickle_static_review.json before this run.
with artifact.open('rb') as f:author_model=pickle.load(f)
features=list(author_model.feature_names_in_)
values=np.column_stack([rng.randint(0,m+1,32) for m in (65535,7,1500,65535,1500,65535,31)])
frame=pd.DataFrame(values,columns=features)
pred=author_model.predict(frame)
assert len(pred)==32 and set(pred)<=set(author_model.classes_)
result={'scope':'Synthetic data and author saved-model loading only; no real traffic dataset or paper metric validation',
 'notebook_sha256':hashlib.sha256(notebook.read_bytes()).hexdigest(),
 'synthetic_fit':{'rows':len(X),'sha256':hashlib.sha256(X.to_numpy().tobytes()+y.tobytes()).hexdigest(),'predictions_equal_labels':True,'accuracy':float(accuracy_score(y,model.predict(X))),'not_paper_metric':True},
 'feature_threshold_counterexample':{'upstream_call_threshold':99,'actual_score_range':[0,1],'perfect_score':1.0,'upstream_return':None,'threshold_0_99_returns_feature_subset':True,'scope':'Parameter counterexample; upstream unchanged'},
 'author_model':{'sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'features':features,'classes':[int(v) for v in author_model.classes_],'n_estimators':len(author_model.estimators_),'tree_nodes':[int(t.tree_.node_count) for t in author_model.estimators_],'tree_leaves':[int(t.tree_.n_leaves) for t in author_model.estimators_],'synthetic_input_rows':32,'input_sha256':hashlib.sha256(values.tobytes()).hexdigest(),'predictions':[int(v) for v in pred]}}
(E/'smoke_metrics.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
