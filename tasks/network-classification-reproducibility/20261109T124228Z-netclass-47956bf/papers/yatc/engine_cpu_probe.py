#!/usr/bin/env python3
"""Expected-failure CPU training probe using the unmodified author engine."""
from pathlib import Path
import sys
from types import SimpleNamespace
import importlib.util
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'upstream/yatc'))
import compat_bootstrap
import torch
from torch.utils.data import DataLoader,TensorDataset
import models_YaTC
if '--patched' in sys.argv:
    path=ROOT/'papers/yatc/runtime-artifacts/cpu_patch/engine.py'
    spec=importlib.util.spec_from_file_location('audit_patched_engine',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    train_one_epoch=module.train_one_epoch
else:
    from engine import train_one_epoch
from util.misc import NativeScalerWithGradNormCount
torch.set_num_threads(1);torch.manual_seed(0)
model=models_YaTC.TraFormer_YaTC(num_classes=7,drop_path_rate=0.0)
loader=DataLoader(TensorDataset(torch.rand(2,1,40,40),torch.tensor([0,1])),batch_size=2)
args=SimpleNamespace(accum_iter=1,warmup_epochs=0,epochs=1,lr=0.001,min_lr=0.001)
optimizer=torch.optim.SGD(model.parameters(),lr=0.001)
train_one_epoch(model,torch.nn.CrossEntropyLoss(),loader,optimizer,torch.device('cpu'),0,NativeScalerWithGradNormCount(),args=args)
