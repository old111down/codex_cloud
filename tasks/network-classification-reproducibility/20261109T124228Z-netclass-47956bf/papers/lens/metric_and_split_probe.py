#!/usr/bin/env python3
"""Bounded original-function probes on synthetic inputs; not a Lens model test."""
import importlib.util
import hashlib,json,math,pathlib,platform
import numpy as np
import pandas as pd
import scipy,sklearn
ROOT=pathlib.Path(__file__).resolve().parents[2]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
mp=ROOT/'upstream/lens/src/lens/utils/metric.py'
sp=ROOT/'upstream/lens/data_preprocessing/2_split_pcap_by_label.py'
metric=load('audit_original_lens_metric',mp)
jsd,tvd,hd=metric.cal_jsd_tvd_hd(['a','a'],['b','b'])
# Standard total-variation = sup_A |P(A)-Q(A)| = 1/2 L1(P-Q).
standard_tvd=1.0
assert np.isclose(tvd,1/math.sqrt(2)) and not np.isclose(tvd,standard_tvd)
# Same distribution control: all metrics must be zero.
control=metric.cal_jsd_tvd_hd(['a','b'],['b','a'])
assert np.allclose(control,[0,0,0])
split=load('audit_original_lens_split',sp)
records=[]
for c in range(2):
 for f in range(4):
  for i in range(50):records.append({'path':f'SYNTHETIC/coarse{c}/fine{c}_{f}/flow{i}.pcap','label1':f'coarse{c}','label2':f'fine{c}_{f}','label3':f'app{c}_{f}'})
df=pd.DataFrame(records)
coarse=split.split_dataset_by_label(df,label_column='label1')
fine=split.split_dataset_to_train_val_test(df,label_column='label2')
pt=set(coarse['pretrain']['path']);same_test=set(coarse['test']['path']);fine_test=set(fine['test']['path']);overlap=sorted(pt&fine_test)
assert not(pt&same_test)
assert overlap
result={
 'scope':'Original metric and reference split functions, synthetic inputs only. No Lens model/tokenizer/real traffic, no paper result reproduction.',
 'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'scikit_learn':sklearn.__version__},
 'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [mp,sp]},
 'metric':{'inputs':'two disjoint empirical point-mass distributions','original_jsd_nats':float(jsd),'original_tvd':float(tvd),'common_standard_tvd':standard_tvd,'original_hd':float(hd),'common_standard_hellinger':1.0,'same_distribution_control':list(map(float,control)),'interpretation':'Code uses a nonstandard normalization relative to common TVD/Hellinger definitions. Paper does not supply a formula. Could be intentional author convention; Table6 predictions/absolute metric impact remain Unknown.'},
 'reference_split':{'synthetic_flow_records':len(df),'coarse_pretrain_rows':len(pt),'same_coarse_protocol_test_rows':len(same_test),'same_coarse_protocol_pretrain_test_overlap':len(pt&same_test),'independent_fine_protocol_test_rows':len(fine_test),'coarse_pretrain_fine_test_overlap':len(overlap),'example_synthetic_ids':overlap[:8],'interpretation':'The reference pipeline can expose downstream test inputs in coarse pretraining when independent granular-task manifests share source records. This is transductive input exposure, not proof of supervised label leakage; actual released artifacts and paper protocol disjointness remain Unknown.'},
 'upstream_modified':False
}
p=ROOT/'papers/lens/metric_split_probe_results.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
