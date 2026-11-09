#!/usr/bin/env python3
"""Precisely evaluate the original loss combiner, without training replacements."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import torch

ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'upstream/et_bert/uer/trainer.py'
tree=ast.parse(source.read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='BertTrainer')
fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward_propagation')
ns={}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),ns)
state=SimpleNamespace(total_loss=0.0,total_loss_mlm=0.0,total_loss_sp=0.0,
                      total_correct_mlm=0,total_correct_sp=0,total_denominator=0.0,
                      total_instances=0,accumulation_steps=1)
mlm=torch.tensor(10.0,requires_grad=True)
sp=torch.tensor(2.0,requires_grad=True)
def model(src,tgt,seg):
    return mlm,sp,torch.tensor(0),torch.tensor(0),torch.tensor(1.0)
src=torch.zeros((2,4),dtype=torch.long)
actual=ns['forward_propagation'](state,(src,src,torch.zeros(2,dtype=torch.long),src),model)
actual.backward()
assert abs(actual.item()-3.0)<1e-6
assert abs(mlm.grad.item()-0.1)<1e-6
assert abs(sp.grad.item()-1.0)<1e-6
out={'scope':'Exact original BertTrainer.forward_propagation combiner with supplied loss tensors; synthetic numeric probe, no paper experiment',
     'source':'uer/trainer.py:179','paper_reference':'arXiv2202.06335v2 §3.3 Eq(4): L=L_MBM+L_SBP',
     'input_loss_mlm':10.0,'input_loss_sp':2.0,'accumulation_steps':1,
     'paper_equation_value':12.0,'actual_original_code_value':actual.item(),
     'gradient_wrt_mlm':mlm.grad.item(),'gradient_wrt_sp':sp.grad.item(),
     'confirmed':'Pinned implementation uses relative MBM weight0.1, SBP weight1.0.',
     'unknown':'Whether original 2022 reported experiments used this implementation, and impact on paper metrics.'}
(ROOT/'evidence/et_bert/loss_equation_probe.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
