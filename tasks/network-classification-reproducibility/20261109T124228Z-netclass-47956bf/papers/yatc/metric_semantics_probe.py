#!/usr/bin/env python3
"""Check exported metric semantics on a deliberately imbalanced synthetic set."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'upstream/yatc'))
import compat_bootstrap
import torch
from torch.utils.data import TensorDataset,DataLoader
from sklearn.metrics import precision_recall_fscore_support
from engine import evaluate
class AlwaysZero(torch.nn.Module):
    def forward(self,x):
        out=torch.zeros(len(x),7);out[:,0]=1;return out
torch.set_num_threads(1)
target=[0,0,0,0,0,0,1,2,3,4]
pred=[0]*len(target)
result=evaluate(DataLoader(TensorDataset(torch.zeros(10,1,40,40),torch.tensor(target)),batch_size=10),AlwaysZero(),torch.device('cpu'))
weighted=precision_recall_fscore_support(target,pred,average='weighted',zero_division=0)
macro=precision_recall_fscore_support(target,pred,average='macro',zero_division=0)
assert abs(result['macro_f1']-weighted[2])<1e-12
assert abs(result['macro_f1']-macro[2])>0.1
record={'scope':'Synthetic metric-name consistency test; no traffic classification accuracy claim',
 'targets':target,'predictions':pred,'reported_macro_pre':result['macro_pre'],'reported_macro_rec':result['macro_rec'],'reported_macro_f1':result['macro_f1'],
 'actual_weighted_precision_recall_f1':list(weighted[:3]),'actual_macro_precision_recall_f1':list(macro[:3]),
 'confirmed':'evaluate stores weighted averages under macro_* keys','paper_uses_mislabeled_values':'Unknown: full paper not obtained'}
(ROOT/'evidence/yatc/metric_semantics.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
