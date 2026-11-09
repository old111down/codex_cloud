#!/usr/bin/env python3
"""Independent bounded source counterexamples; no NN training or paper data."""
import ast
import itertools
import json
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn

ROOT=Path(__file__).resolve().parents[2]
paths={'original':ROOT/'upstream/linc/linc/simulator.py',
       'patched':ROOT/'papers/linc/runtime-artifacts/patched/linc/simulator.py'}
keys=np.array([[0,0,0],[0,0,1],[0,1,0]],dtype=np.float32)
masks=np.ones_like(keys)
values=np.array([0,1,0],dtype=np.int64)
scores=np.array([1,2,3],dtype=np.float32)
queries=torch.tensor(list(itertools.product([0.,1.],repeat=3)))
expected=[0,1,2,3,3,3,3,3]
out={'scope':'Independent synthetic source-function checks, no original dataset/NN/P4 execution','checks':{}}
for name,path in paths.items():
    tree=ast.parse(path.read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Switch')
    ns={'torch':torch,'nn':nn}
    exec(compile(ast.Module(body=[cls],type_ignores=[]),str(path),'exec'),ns)
    switch=ns['Switch'](3,keys,masks,values,scores,num_classes=3)
    pred,index=switch(queries,torch.zeros(8,dtype=torch.long),cache=True,return_key=True)
    mismatch=sum(a!=b for a,b in zip(index.tolist(),expected))
    assert mismatch==(5 if name=='original' else 0)
    out['checks'][name]={'indices':index.tolist(),'mismatches':mismatch,
                         'cache_counts':[sum(len(v) for v in d.values()) for d in switch.allocate_samples],
                         'predictions':pred.tolist()}
    if name=='patched':
        default_index=int(index[-1])
        # Execute exactly the first assignment in the original update loop.
        upd=ast.parse((ROOT/'upstream/linc/update_streaming.py').read_text())
        main=next(n for n in upd.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        loop=next(n for n in main.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='ind')
        stmt=loop.body[0]
        assert stmt.lineno==179
        namespace={'positive_samples':switch.allocate_samples,'ind':default_index,'values':values}
        error=None
        try:
            exec(compile(ast.Module(body=[stmt],type_ignores=[]),'update_streaming.py:179','exec'),namespace)
        except IndexError as e:
            error=str(e)
        assert error is not None
        out['patched_incremental_boundary']={
            'query':[1,1,1],'true_new_label':3,'predicted_default_label':int(pred[-1]),
            'corrected_default_index':default_index,'values_length':len(values),
            'source_statement':'update_streaming.py:179 pos_X = positive_samples[ind][str(int(values[ind]))]',
            'error_type':'IndexError','error':error,
            'interpretation':'Local default-bucket fix needs corresponding incremental-parent/default-entry handling; current full update cannot be declared repaired.'}
assert 4//10==0
out['small_batch_modulus']={'batches':4,'original_modulus':4//10,'zero_division_confirmed_in_existing_log':'logs/linc/train_small_original.log'}
out['sample_ratio']={'source':'update_streaming.py:27,45-47','RATIO':1,
                    'selected_if1000_new_samples':int(1000*1),'not_hard_limited_to63':True,
                    'unknown':'Actual downloaded pickle may already be subsampled; it was not acquired.'}
(ROOT/'papers/linc/independent_checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
