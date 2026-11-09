"""Bounded original RF→soft-label→BDT functions on identified UNIV CSV prefixes.

This deliberately is not the full paper split, balance, data preparation or metric.
"""
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile

import numpy as np
import pandas as pd
from imblearn.under_sampling import RandomUnderSampler

ROOT=Path(__file__).resolve().parents[2]
UP=ROOT/"upstream/mousika/Distillation"
sys.path.insert(0,str(UP))
from bdt_test import produce_soft_labels
from SoftTree import SoftTreeClassifier

drop=["srcPort","dstPort","protocol","ip_ihl","ip_tos","ip_flags","ip_ttl","tcp_dataofs",
      "tcp_flag","tcp_window","udp_len","length"]
drop += [f"{side}Addr{i}" for side in ["src","dst"] for i in range(1,5)]
archive=UP/"Dataset/univ.zip"
with zipfile.ZipFile(archive) as z:
    with z.open("univ/univ1-1.csv") as src:
        train=pd.read_csv(src,nrows=512).drop(columns=drop).to_numpy()
    with z.open("univ/univ1-2.csv") as src:
        test=pd.read_csv(src,nrows=256).drop(columns=drop).to_numpy()
X,y=RandomUnderSampler(random_state=5).fit_resample(train[:,:-1],train[:,-1])
train=np.column_stack([X,y])
# Upstream load_data permutes after under-sampling. Fix the initial audit harness
# omission; use an explicit harness seed, unlike upstream's unseeded permutation.
train=np.random.default_rng(5).permutation(train)
assert set(np.unique(train[:,-1]))=={0,1}, np.unique(train[:,-1])
start=time.monotonic()
soft=produce_soft_labels(train,round_num=1,fold_num=2,k=0,model="rf")
assert soft.shape==(len(train),2)
assert np.allclose(soft.sum(axis=1),1)
tree=SoftTreeClassifier(n_features="all",min_sample_leaf=5)
tree.fit(train[:,:-1],soft,["d"]*X.shape[1])
prediction=tree.predict(test[:,:-1])
assert len(prediction)==len(test)
print(json.dumps({"kind":"real_data_prefix_component_smoke","task":"flow-size prediction",
 "training_prefix_rows":512,"test_prefix_rows":256,"balanced_training_rows":len(train),
 "binary_features":X.shape[1],"labels":[0,1],"predictions":len(prediction),
 "training_input_sha256":hashlib.sha256(train.tobytes()).hexdigest(),
 "test_input_sha256":hashlib.sha256(test.tobytes()).hexdigest(),
 "elapsed_seconds":time.monotonic()-start,
 "test_prefix_accuracy":float(np.mean(prediction==test[:,-1])),
 "full_paper_equivalence":"Unknown; arbitrary small prefixes, full split and raw preprocessing not restored",
 "paper_accuracy_reproduced":False,"traffic_application_classification_reproduced":False},indent=2))
