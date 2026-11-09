#!/usr/bin/env python3
"""Independent artifact/metric review; never train or load a pickle/model."""
import ast
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
records={}
prediction_rows={}
for name in ('core_conference','core_conference_time_aligned','core_full'):
    p=ROOT/'evidence/flowrest'/(name+'_predictions.csv')
    rows=list(csv.DictReader(p.open()))
    meta=json.loads((p.parent/(name+'_metrics.json')).read_text())
    prediction_rows[name]=rows
    true=[r['y_true'] for r in rows];pred=[r['y_pred'] for r in rows]
    classes=sorted(set(true)|set(pred))
    supports=Counter(true);pred_counts=Counter(pred)
    correct=Counter(t for t,p in zip(true,pred) if t==p)
    values=[]
    for label in classes:
        precision=correct[label]/pred_counts[label] if pred_counts[label] else 0.0
        recall=correct[label]/supports[label] if supports[label] else 0.0
        f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
        values.append((precision,recall,f1,supports[label]))
    accuracy=sum(correct.values())/len(rows)
    macro=[sum(x[i] for x in values)/len(values) for i in range(3)]
    weighted=[sum(x[i]*x[3] for x in values)/len(rows) for i in range(3)]
    expected=meta['classification_report']
    assert abs(accuracy-meta['accuracy'])<1e-12
    for name2,calculated in [('macro avg',macro),('weighted avg',weighted)]:
        for metric,value in zip(('precision','recall','f1-score'),calculated):
            assert abs(value-expected[name2][metric])<1e-12,(name,name2,metric)
    records[name]={'rows':len(rows),'correct':sum(correct.values()),'accuracy':accuracy,
                   'macro_precision_recall_f1':macro,'weighted_precision_recall_f1':weighted,
                   'prediction_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

a=json.loads((ROOT/'evidence/flowrest/core_conference_metrics.json').read_text())
b=json.loads((ROOT/'evidence/flowrest/core_conference_time_aligned_metrics.json').read_text())
for k in ('train_input_sha256','train_rows','test_rows','model_params','features','classes','tree_nodes','tree_leaves','executed_cells'):
    assert a[k]==b[k],k
arows=prediction_rows['core_conference'];brows=prediction_rows['core_conference_time_aligned']
assert [(r['row_index'],r['y_true']) for r in arows]==[(r['row_index'],r['y_true']) for r in brows]
assert a['test_input_sha256']!=b['test_input_sha256']
script=(ROOT/'papers/flowrest/run_core.py').read_text()
assert "if mode=='conference_time_aligned' and i==20:" in script
assert "for col in ['Flow IAT Min','Flow IAT Max','Flow Duration']" in script
assert "ns['X_test'][col]=ns['X_test'][col]*1000" in script

nbpath=ROOT/'upstream/flowrest/Python/Full_version/Unibs_flowrest_analysis.ipynb'
nb=json.loads(nbpath.read_text())
expected_cells=[i for i,c in enumerate(nb['cells']) if c['cell_type']=='code']
log=(ROOT/'logs/flowrest/original_full_notebook_with_public_data.log').read_text()
actual=[int(x) for x in re.findall(r'Executing original cell (\d+)',log)]
command=json.loads((ROOT/'logs/flowrest/original_full_notebook_with_public_data.json').read_text())
assert expected_cells==actual==list(range(12))
assert command['exit_code']==0
assert hashlib.sha256(nbpath.read_bytes()).hexdigest() in log

generated=ROOT/'papers/flowrest/runtime-artifacts/conference/te_unsw_per_flow_saved_model_16_classes.py'
calls=ast.parse(generated.read_text());invalid=[]
for node in ast.walk(calls):
    if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute) or not isinstance(node.func.value,ast.Name):continue
    table=node.func.value.id
    if table not in ('table_feature1','table_feature6'):continue
    if not node.func.attr.startswith('add_with_'):continue
    feature=1 if table.endswith('1') else 6
    width=3 if feature==1 else 5
    kw={k.arg:ast.literal_eval(k.value) for k in node.keywords}
    start,end=kw[f'feature{feature}_start'],kw[f'feature{feature}_end']
    if not 0<=start<=end<(1<<width):invalid.append([feature,start,end])
assert sorted(invalid)==[[1,7,65535],[6,26,65535]]
p4=(ROOT/'upstream/flowrest/P4/Conference_version/unsw_per_flow_16_classes/unsw_per_flow_16_classes.p4').read_text()
assert 'meta.flow_duration[31:29]: range @name("feature1")' in p4
assert 'meta.flow_iat_max[31:27]: range @name("feature6")' in p4
assert not subprocess.check_output(['git','-C',str(ROOT/'upstream/flowrest'),'status','--porcelain']).strip()

result={'scope':'Independent review of existing artifacts, no retraining, model loading, P4 or packet execution',
        'metrics_recomputed_from_all_predictions':records,
        'sensitivity':{'same_train_hash_model_params_labels_row_indices_seed_tree_sizes':True,
                       'only_harness_data_change':'After original cell20, multiply three X_test time columns1000; verified same common cell list and branch source',
                       'paper_equivalence':'Unknown; physical units and original processing not established'},
        'original_unibs_notebook':{'code_cells':actual,'exit_code':command['exit_code'],'raw_log_matches_notebook_hash':True},
        'generated_range_invalid_intervals':invalid,'upstream_clean':True}
(ROOT/'papers/flowrest/independent_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
