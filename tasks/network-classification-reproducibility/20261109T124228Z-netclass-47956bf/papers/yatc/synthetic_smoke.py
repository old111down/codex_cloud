#!/usr/bin/env python3
"""Synthetic PCAP and full factory-model CPU smoke; no paper metric claims."""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'upstream/yatc'))
import compat_bootstrap
import numpy as np
import torch
import models_YaTC
from data_process import read_MFR_bytes, MFR_generator
from scapy.all import IP,TCP,Raw,wrpcap
from PIL import Image

torch.set_num_threads(1)
torch.manual_seed(0)
np.random.seed(0)
out=ROOT/'papers/yatc/runtime-artifacts/synthetic'
(out/'pcaps/train/synthetic_a').mkdir(parents=True,exist_ok=True)
(out/'pcaps/test/synthetic_a').mkdir(parents=True,exist_ok=True)
packets=[IP(src='192.0.2.1',dst='198.51.100.2')/TCP(sport=12345,dport=443)/Raw(b'example-payload-'+bytes([i])) for i in range(3)]
pcap=out/'pcaps/train/synthetic_a/fixture.pcap'
wrpcap(str(pcap),packets)
data=bytes.fromhex(read_MFR_bytes(str(pcap)))
assert len(data)==1600
assert data[:80]==bytes(packets[0])[:40]+bytes(40)
assert data[12:20]==bytes([192,0,2,1,198,51,100,2])
assert data[20:24]==bytes([0x30,0x39,0x01,0xbb])
assert data[960:]==bytes(640)  # last two missing packets zero padded
MFR_generator(str(out/'pcaps'),str(out/'matrices'))
matrix=np.asarray(Image.open(out/'matrices/train/synthetic_a/fixture.png'))
assert matrix.shape==(40,40) and matrix.tobytes()==data

x=torch.rand(2,1,40,40)*2-1
t=time.perf_counter()
mae=models_YaTC.MAE_YaTC()
loss,pred,mask=mae(x,mask_ratio=0.9)
assert loss.isfinite() and pred.shape==(2,400,4) and mask.shape==(2,400)
loss.backward()
mae_seconds=time.perf_counter()-t
classifier=models_YaTC.TraFormer_YaTC(num_classes=7,drop_path_rate=0.0)
optimizer=torch.optim.SGD(classifier.parameters(),lr=1e-3)
before=classifier.head.weight.detach().clone()
t=time.perf_counter()
logits=classifier(x)
ce=torch.nn.functional.cross_entropy(logits,torch.tensor([0,1]))
optimizer.zero_grad();ce.backward();optimizer.step()
assert logits.shape==(2,7) and ce.isfinite()
delta=float((classifier.head.weight-before).abs().max())
assert delta>0
result={'input_kind':'synthetic','scope':'Unmodified full MAE_YaTC and TraFormer_YaTC factories plus original PCAP→MFR functions; import aliases applied in audit bootstrap only; random initialization, not pretrained or real traffic',
 'torch_version':torch.__version__,'input_shape':list(x.shape),'input_sha256':hashlib.sha256(x.numpy().tobytes()).hexdigest(),
 'synthetic_pcap_sha256':hashlib.sha256(pcap.read_bytes()).hexdigest(),'synthetic_mfr_sha256':hashlib.sha256(data).hexdigest(),
 'mae_parameters':sum(p.numel() for p in mae.parameters()),'classifier_parameters':sum(p.numel() for p in classifier.parameters()),
 'mae_loss':float(loss.detach()),'mae_pred_shape':list(pred.shape),'masked_patch_counts':mask.sum(dim=1).tolist(),
 'classification_logits_shape':list(logits.shape),'synthetic_cross_entropy':float(ce.detach()),'head_weight_max_change':delta,
 'pcap_contains_ip_and_ports_after_representation':True,'packet_count_in_fixture':3,'zero_padded_packet_slots':2,
 'mae_forward_backward_seconds':mae_seconds,'classifier_step_seconds':time.perf_counter()-t,
 'limitations':['Synthetic figures are smoke outputs, not Accuracy/F1 or paper performance','Default mask_ratio0.9 keeps int(400*(1-0.9))=39 patches due float truncation','No original dataset, labels, splits or checkpoint loaded','Whole-function walltime is not controlled inference latency measurement']}
(ROOT/'evidence/yatc/synthetic_smoke_metrics.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
