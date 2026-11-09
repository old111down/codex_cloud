#!/usr/bin/env python3
"""Compare self-created synthetic checkpoints; no third-party pickle is loaded."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
UP=ROOT/'upstream/et_bert'
sys.path.insert(0,str(UP))
import torch
R=ROOT/'papers/et_bert/runtime-artifacts'
a=torch.load(R/'tiny_synthetic_model.bin',map_location='cpu')
b=torch.load(R/'patched_tiny_synthetic_model.bin',map_location='cpu')
assert set(a)==set(b)
different=[k for k in a if not torch.equal(a[k],b[k])]
assert not different
predictions=(R/'synthetic_predictions.tsv').read_text().splitlines()
assert len(predictions)==3
result={'scope':'Patch changes output location and import resolution only; equivalence verified for this synthetic seeded run, not all future experiments',
        'checkpoint_source':'Both files generated locally in this audit from explicit synthetic TSVs, no external checkpoint deserialized',
        'state_dict_tensor_count':len(a),'all_state_tensors_exactly_equal':not different,
        'synthetic_unlabeled_predictions':predictions,
        'confusion_matrix_created':(R/'patched_tiny_synthetic_model.bin.confusion_matrix').exists(),
        'artifacts':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
                     for p in (R/'tiny_synthetic_model.bin',R/'patched_tiny_synthetic_model.bin',R/'synthetic_predictions.tsv',R/'synthetic_dataset.pt',R/'synthetic_pretrained_model.bin-2')]}
(ROOT/'evidence/et_bert/patch_equivalence.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
