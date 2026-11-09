"""Independent numerical counterexample; patch changes algorithm behavior."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
UP = ROOT/"upstream/mousika-v2/Distillation"
sys.path.insert(0,str(UP))
from SoftTree import SoftTreeClassifier

X=np.array([[0,0],[0,0],[0,0],[0,1],[1,0],[1,1],[1,1],[1,1]])
labels=np.array([0,0,0,1,0,1,1,1])
y=np.eye(2)[labels]

def reference_scores():
    scores=[]
    for feat in range(X.shape[1]):
        score=0.0
        for val in [0,1]:
            node=y[X[:,feat]==val]
            probs=node.mean(axis=0)
            score-=len(node)/len(y)*(1-float(probs@probs))
        scores.append(score)
    return scores

def observed(cls):
    model=cls(class_num=2,n_features="all",min_sample_leaf=1)
    model.features_attr=["d","d"]
    rows=model._SoftTreeClassifier__split_pair(X,y,[0,1])
    return [float(rows[rows[:,1]==feat][0,0]) for feat in range(2)]

ref=reference_scores()
original=observed(SoftTreeClassifier)
assert not np.allclose(original,ref), (original,ref)
with tempfile.TemporaryDirectory(prefix="mousika-v2-gini-") as temp:
    dest=Path(temp)/"Distillation"
    shutil.copytree(UP,dest,ignore=shutil.ignore_patterns("__pycache__"))
    subprocess.run(["patch","--binary","-p1","-i",str(ROOT/"patches/mousika/0002-v2-correct-right-branch-gini.patch")],cwd=temp,check=True)
    spec=importlib.util.spec_from_file_location("patched_softtree",dest/"SoftTree.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    patched=observed(module.SoftTreeClassifier)
    assert np.allclose(patched,ref), (patched,ref)
print(json.dumps({"kind":"algorithm_logic_counterexample","input_X":X.tolist(),
                  "labels":labels.tolist(),"reference_negative_weighted_gini":ref,
                  "original_scores":original,"patched_scores":patched,
                  "original_disagrees_with_paper_Gini_equation":True,
                  "patch_matches_independent_equation_on_this_input":True,
                  "paper_metric_equivalence":"Unknown"},indent=2))
