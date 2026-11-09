"""Exercise the exact upstream loader function on one explicit synthetic flow."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import numpy as np
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Subset

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'upstream/pegasus/software'))
from util.data_loader import FlowDataset
src=ROOT/'upstream/pegasus/software/train_net/runmodel.py'
tree=ast.parse(src.read_text())
fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='build_data_loader')
module=ast.Module(body=[fn],type_ignores=[])
ns={'FlowDataset':FlowDataset,'train_test_split':train_test_split,'DataLoader':DataLoader,'Subset':Subset}
exec(compile(module,str(src),'exec'),ns)
path=ROOT/'papers/pegasus/runtime-artifacts/one_synthetic_flow.json'
flow={'label':'emule','len_seq':list(range(40,80)),'ts_seq':[i*.001 for i in range(40)]}
path.write_text(json.dumps([flow])+'\n')
np.random.seed(42)
train,val,full=ns['build_data_loader'](1501,2561,8,str(path),8,SimpleNamespace(dataset='PeerRush',val_ratio=.2),is_train=True,shuffle=False)
t=list(map(int,train.dataset.indices));v=list(map(int,val.dataset.indices))
shared=set()
for a in t:
 for b in v:
  shared.update(set(range(a,a+8))&set(range(b,b+8)))
assert len(full.dataset)==33 and len(shared)>0
result={'scope':'One synthetic flow through original FlowDataset and exact AST-extracted upstream build_data_loader; no training and no real dataset',
        'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'synthetic_flow_count':1,'packet_count':40,'window_size':8,'windows':33,
        'train_windows':len(t),'validation_windows':len(v),'train_starts':t,'validation_starts':v,
        'shared_source_flows':1,'shared_packet_positions':sorted(shared),
        'confirmed_behavior':'The code splits after overlapping-window expansion; a single flow can enter both train and validation.',
        'not_established':'Actual external train/test overlap or impact on paper test metrics is Unknown. Paper says flow-level75/10/15 splits; original files not acquired.'}
(ROOT/'evidence/pegasus/split_grain_diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
