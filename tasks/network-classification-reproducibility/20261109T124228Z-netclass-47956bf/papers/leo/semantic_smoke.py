"""Bounded source-code diagnostic; not P4 compilation, simulation, or paper evaluation."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'upstream/leo/leo-generator'
sys.path.insert(0,str(SRC))
import leo_ctrlplane as author

out=ROOT/'papers/leo/runtime-artifacts/smoke'
out.mkdir(parents=True,exist_ok=True)
results=[]
for a in range(3):
    X=np.array([[a],[a+1]],dtype=np.int64)
    y=np.array([0,1])
    model=DecisionTreeClassifier(max_depth=1,criterion='entropy',random_state=42).fit(X,y)
    text=export_text(model,feature_names=['feature_0'])
    path=out/f'tree_{a}.txt'
    path.write_text(text)
    reconstructed=author.build_tree_from_file(path)
    c=reconstructed.root.constraint
    probes=np.arange(6).reshape(-1,1)
    reference=model.predict(probes).tolist()
    # Pinned P4/template uses 16-bit f + (-constraint), MSB=1 for the left branch.
    # These small non-negative probes avoid signed-subtraction overflow ambiguity.
    author_semantics=[reconstructed.root.left.label if ((int(x)-c)&0xffff)&0x8000 else reconstructed.root.right.label for x in probes[:,0]]
    results.append({'input_sha256':hashlib.sha256(X.tobytes()+y.tobytes()).hexdigest(),
                    'export_text':text,'sklearn_threshold':float(model.tree_.threshold[0]),
                    'parsed_constraint':c,'probes':probes[:,0].tolist(),
                    'sklearn_predictions':reference,'generated_predicate_predictions':author_semantics,
                    'mismatching_probes':[int(x) for x,r,p in zip(probes[:,0],reference,author_semantics) if r!=p]})
assert results[0]['parsed_constraint']==0
assert results[0]['mismatching_probes']==[0]
assert results[1]['mismatching_probes']==[]
assert results[2]['mismatching_probes']==[2]
result={'scope':'Synthetic 2-point CART stumps, original text parser, and Python evaluation of pinned P4 arithmetic; not executed P4 or network data',
        'source_sha256':hashlib.sha256((SRC/'leo_ctrlplane.py').read_bytes()).hexdigest(),
        'counterexample_confirmed':True,'cases':results}
(ROOT/'evidence/leo/threshold_counterexample.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
