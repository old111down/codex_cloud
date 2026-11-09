"""Small independent loss-combiner and static-artifact checks; no model run."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
import torch

ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'upstream/et_bert/uer/trainer.py'
tree=ast.parse(source.read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='BertTrainer')
fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward_propagation')
ns={}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),ns)
state=SimpleNamespace(total_loss=0.,total_loss_mlm=0.,total_loss_sp=0.,
 total_correct_mlm=0,total_correct_sp=0,total_denominator=0.,total_instances=0,
 accumulation_steps=2)
a=torch.tensor(7.,requires_grad=True)
b=torch.tensor(3.,requires_grad=True)
model=lambda *_:(a,b,torch.tensor(0),torch.tensor(0),torch.tensor(1.))
zeros=torch.zeros((2,4),dtype=torch.long)
loss=ns['forward_propagation'](state,(zeros,zeros,torch.zeros(2),zeros),model)
loss.backward()
assert abs(loss.item()-1.85)<1e-6
assert abs(a.grad.item()-.05)<1e-6 and abs(b.grad.item()-.5)<1e-6
history=json.loads((ROOT/'evidence/et_bert/loss_history.json').read_text())
for record in history['historical_snapshots']:
    text=subprocess.check_output(['git','-C',str(ROOT/'upstream/et_bert'),'show',record['sha']+':uer/trainer.py'],text=True)
    for expression in record['loss_combiner']:
        assert expression['code'] in text
rows=list(csv.DictReader((ROOT/'papers/et_bert/coverage_matrix.csv').open()))
assert len(rows)==69
required=['FIG1','FIG2','FIG3','FEWSHOT-40%','TSNE-ET-BERT','DATA-ios','DATA-android',
 'DATA-ustc','DATA-vpn_service','DATA-vpn_app','DATA-tor','DATA-tls13',
 'ABL-no_mbm','ABL-no_sbp','ABL-cf','RANDOMNESS-AES-GCM']
ids={r['claim_id'] for r in rows}
assert set(required)<=ids
missing=[]
for row in rows:
    for path in re.findall(r'(?:evidence|logs|papers|environment|patches)/[\w./-]+',row['evidence']):
        path=path.rstrip('.,;')
        if not (ROOT/path).exists():missing.append((row['claim_id'],path))
assert not missing,missing
assert subprocess.check_output(['git','-C',str(ROOT/'upstream/et_bert'),'status','--porcelain'],text=True).strip()==''
out={'scope':'Independent exact-original-function synthetic loss probe plus static matrix/history checks; no model retraining',
 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'loss_probe':{'loss_mlm':7.,'loss_sp':3.,'accumulation_steps':2,'actual':loss.item(),
               'grad_mlm':a.grad.item(),'grad_sp':b.grad.item(),'expected_combiner':'(0.1*mlm+sp)/2'},
 'history_snapshots_checked':len(history['historical_snapshots']),
 'matrix_rows':len(rows),'matrix_sha256':hashlib.sha256((ROOT/'papers/et_bert/coverage_matrix.csv').read_bytes()).hexdigest(),
 'evidence_references_missing':missing,'upstream_clean':True,
 'not_established':['Exact code used for paper2022 experiments','Full objective reduction equivalence beyond the supplied loss tensors','Any real-network dataset metric or inference performance']}
(ROOT/'papers/et_bert/independent_review_checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
