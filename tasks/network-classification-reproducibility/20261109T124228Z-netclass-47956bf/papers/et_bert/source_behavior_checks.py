#!/usr/bin/env python3
"""Bounded original-function probes with declared synthetic/mock boundaries."""
import ast
import binascii
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
UP=ROOT/'upstream/et_bert'
OUT=ROOT/'papers/et_bert/runtime-artifacts/behavior'
OUT.mkdir(parents=True,exist_ok=True)
import numpy as np
import scapy.all as scapy
from sklearn.model_selection import StratifiedShuffleSplit

def original_functions(path,names,namespace):
    tree=ast.parse(path.read_text())
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(selected)==len(names)
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),namespace)
    return namespace

# A real PCAP container with wholly synthetic packets; mock only flowcontainer's direction output.
packet=scapy.Ether(dst='aa:bb:cc:dd:ee:ff',src='00:11:22:33:44:55')/scapy.IP(src='10.0.0.1',dst='10.0.0.2')/scapy.TCP(sport=1234,dport=443)/scapy.Raw(bytes(range(64)))
pcap=OUT/'synthetic.pcap'
scapy.wrpcap(str(pcap),[packet,packet.copy()])
ns={'scapy':scapy,'binascii':binascii,'extract':lambda path:{'synthetic':SimpleNamespace(ip_lengths=[118,118])},
    'word_dir':str(OUT)+os.sep,'word_name':'burst.txt'}
original_functions(UP/'data_process/dataset_generation.py',{'cut','bigram_generation','get_burst_feature','get_feature_packet'},ns)
(OUT/'burst.txt').unlink(missing_ok=True)
ns['get_burst_feature'](str(pcap),64)
burst=(OUT/'burst.txt').read_text()
fine=ns['get_feature_packet'](str(pcap),128)[0]
assert burst.split()[0]=='aabb'
assert fine.split()[0]!='aabb'

# Execute the original split function; feed synthetic packet rows with known session IDs.
samples=[[f'class{c}-session{s}-packet{p}' for s in range(10) for p in range(8)] for c in range(2)]
ys=[[c]*80 for c in range(2)]
def collect(model,xd,yd,xtrain,xtest,xvalid,ytrain,ytest,yvalid):
    return {'train':xtrain,'test':xtest,'valid':xvalid},{'train':ytrain,'test':ytest,'valid':yvalid}
ns2={'np':np,'os':os,'StratifiedShuffleSplit':StratifiedShuffleSplit,'_category':2,
     'dataset_save_path':str(OUT/'split')+os.sep,'dataset_dir':str(OUT),
     'pcap_path':'synthetic','samples':[80,80],'features':['payload'],'dataset_level':'packet',
     'dataset_generation':SimpleNamespace(generation=lambda *a,**kw:([samples],ys)),
     'models_deal':collect}
(OUT/'split').mkdir(exist_ok=True)
original_functions(UP/'data_process/main.py',{'dataset_extract'},ns2)
xd,yd=ns2['dataset_extract'](['pre-train'])
groups={k:{s.rsplit('-packet',1)[0] for s in v} for k,v in xd.items()}
overlap={'train_test':len(groups['train']&groups['test']),
         'train_valid':len(groups['train']&groups['valid']),
         'test_valid':len(groups['test']&groups['valid'])}
assert overlap['train_test']>0
result={
 'scope':'Original source functions with synthetic inputs; not evidence that the paper train/test actually overlapped',
 'header_behavior':{'function':'data_process/dataset_generation.py:get_burst_feature',
                    'mock_boundary':'flowcontainer.extract only; direction lengths supplied as [+118,+118]',
                    'input_pcap_sha256':hashlib.sha256(pcap.read_bytes()).hexdigest(),
                    'input_ethernet_destination':'aa:bb:cc:dd:ee:ff',
                    'pretraining_first_token':burst.split()[0],
                    'fine_tuning_first_token_after_fixed_38_byte_slice':fine.split()[0],
                    'confirmed':'This BURST helper retains frame headers; alternate vocab_process.preprocess strips first38bytes. Which branch generated the paper corpus is Unknown.'},
 'split_behavior':{'function':'data_process/main.py:dataset_extract',
                   'mock_boundary':'dataset_generation.generation returns160 synthetic packet rows from20 known sessions; models_deal collects arrays after original splitting',
                   'split_sizes':{k:len(v) for k,v in xd.items()},'session_overlap_counts':overlap,
                   'confirmed':'Default code stratifies packet rows without session groups; same-session packet rows can cross splits.',
                   'not_established':'Actual published dataset train/test leakage, its magnitude, or effects on paper scores remain Unknown.'}}
(ROOT/'evidence/et_bert/source_behavior_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
