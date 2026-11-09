"""CPU smoke of an officially sourced, statically reviewed replacement state_dict."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'upstream/pegasus/software'))
from model.mlpmodel import mlp_lut
torch.set_num_threads(1)
torch.manual_seed(42)
rng=np.random.default_rng(42)
x=rng.integers(0,16,size=(9,10)).astype(np.float32)
y=np.tile(np.arange(3),3)
folder=ROOT/'papers/pegasus/runtime-artifacts'
folder.mkdir(exist_ok=True)
csv=folder/'synthetic_9rows.csv'
np.savetxt(csv,np.column_stack([y,x]),delimiter=',',header=','.join(['label']+[f'f{i}' for i in range(10)]),comments='')
path=ROOT/'upstream/pegasus/software/save/mlp/PeerRush/MLP_PeerRush.pt'
review=json.loads((ROOT/'evidence/pegasus/mlp_weights_static_review.json').read_text())
assert hashlib.sha256(path.read_bytes()).hexdigest()==review['sha256']
state=torch.load(path,map_location='cpu',weights_only=True)
model=mlp_lut(10,32,16,3,torch.device('cpu'),1,2,1)
model.load_state_dict(state,strict=True)
model.eval()
with torch.no_grad():
    out=model(torch.from_numpy(x))
assert tuple(out.shape)==(9,3) and torch.isfinite(out).all()
assert torch.max(torch.abs(torch.logsumexp(out,dim=-1))).item()<1e-5
result={'scope':'Official replacement MLP checkpoint and unmodified model class; synthetic inputs only, no network accuracy or original paper equivalence',
        'weights_sha256':review['sha256'],'input_kind':'synthetic random integers,seed42',
        'input_shape':list(x.shape),'output_shape':list(out.shape),'strict_state_dict_load':True,
        'finite_output':True,'log_probability_normalization_passed':True,
        'synthetic_csv_sha256':hashlib.sha256(csv.read_bytes()).hexdigest(),
        'state_parameter_count':sum(t.numel() for t in state.values()),
        'paper_accuracy':'Unknown','paper_latency':'Unknown','paper_throughput':'Unknown'}
(ROOT/'evidence/pegasus/model_smoke_metrics.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
