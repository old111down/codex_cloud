"""Bounded audit harness; every input here is synthetic, not network traffic."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np
import torch
from torch.utils.data import Dataset

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument('stage', choices=['network', 'train', 'subspace'])
p.add_argument('--patched', action='store_true')
a = p.parse_args()
source = ROOT / ('papers/linc/runtime-artifacts/patched' if a.patched else 'upstream/linc')
sys.path.insert(0, str(source))
from linc.model import EnsembleNNModel, LINCModel
from linc.simulator import Switch

torch.set_num_threads(1)
torch.manual_seed(2023)
np.random.seed(2023)
result = {'scope':'synthetic CPU component test only; no paper metric comparison',
          'stage':a.stage,'patched':a.patched,'source':str(source),
          'torch':torch.__version__,'numpy':np.__version__,'cuda_available':torch.cuda.is_available()}
if a.stage == 'network':
    model=EnsembleNNModel(2,96,4,0.6,2)
    x=torch.randint(0,2,(32,96)).float()*2-1
    y=torch.arange(32)%2
    logits,loss=model.loss(x,y)
    loss.backward()
    assert logits.shape==(32,2) and torch.isfinite(loss)
    result.update(shape=list(logits.shape),loss=float(loss.detach()),
                  parameters=sum(v.numel() for v in model.parameters()),
                  input_sha256=hashlib.sha256(x.numpy().tobytes()).hexdigest())
elif a.stage == 'train':
    class Synthetic(Dataset):
        def __init__(self,data_path,split=1,key='train'):
            seed={'train':1,'val':2,'test':3}[key]
            n=64 if key=='train' else 32
            rng=np.random.default_rng(seed)
            self.X=rng.integers(0,2,(n,8)).astype(np.float32)[::split]
            self.y=self.X[:,0].astype(np.int64)
        def __len__(self):return len(self.y)
        def __getitem__(self,i):return self.X[i]*2-1,self.y[i]
    out=ROOT/'papers/linc/runtime-artifacts'/('synthetic-patched' if a.patched else 'synthetic-original')
    trainer=LINCModel(Synthetic,num_classes=2,in_features=8,k=2,T=0.6,E=2,
                      batch_size=16,num_epochs=1,save_dir=str(out),data=None)
    trainer.train()
    acc,rules=trainer.export(split=1)
    result.update(synthetic_test_accuracy_percent=float(acc),rules=int(rules),
                  train_rows=64,val_rows=32,test_rows=32,epochs=1,features=8,
                  seed=2023,training_wall_seconds=trainer.training_dur,
                  conversion_wall_seconds=trainer.conversion_dur)
elif a.stage == 'subspace':
    keys=np.array([[0,0,0],[0,0,1],[0,1,0]],dtype=np.float32)
    masks=np.ones_like(keys)
    values=np.array([0,1,0],dtype=np.int64)
    scores=np.array([1,2,3],dtype=np.float32)
    switch=Switch(3,keys,masks,values,scores,num_classes=2)
    queries=torch.tensor(list(itertools.product([0.,1.],repeat=3)))
    labels=torch.zeros(8,dtype=torch.int64)
    pred,index=switch(queries,labels,cache=True,return_key=True)
    expected=[]
    for q in queries.numpy():
        match=np.where(np.all(keys==q,axis=1))[0]
        expected.append(int(match[np.argmax(scores[match])]) if len(match) else len(keys))
    actual=index.tolist()
    result.update(expected_subspace_indices=expected,actual_subspace_indices=actual,
                  predictions=pred.tolist(),rules=len(keys),all_inputs=8,
                  mismatches=sum(x!=y for x,y in zip(actual,expected)),
                  cache_counts=[sum(len(v) for v in z.values()) for z in switch.allocate_samples])
    print(json.dumps(result,indent=2))
    (ROOT/'evidence/linc'/('subspace_patched.json' if a.patched else 'subspace_original.json')).write_text(json.dumps(result,indent=2)+'\n')
    assert actual==expected,'Unmatched samples must map to the reserved default subspace, not rule1'
    raise SystemExit(0)
print(json.dumps(result,indent=2))
(ROOT/'evidence/linc'/f'{a.stage}_{"patched" if a.patched else "original"}.json').write_text(json.dumps(result,indent=2)+'\n')
