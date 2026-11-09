#!/usr/bin/env python3
"""Independent lightweight source/inventory/arithmetic/synthetic-split review; no Lens model imports."""
from pathlib import Path
import json,re,csv,hashlib,datetime,math,subprocess,importlib.util,contextlib,io
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'evidence/round2/modern_search/lens';paper=(E/'paper.txt').read_text()
figures=set(map(int,re.findall(r'Figure\s*(\d+)\s*:',paper)));tables=set(map(int,re.findall(r'Table\s*(\d+)\s*:',paper)))
assert figures==set(range(1,5)),figures
assert tables==set(range(1,18)),tables
rows=list(csv.DictReader((ROOT/'papers/lens/coverage_matrix.csv').open()));assert len(rows)==97
assert len([r for r in rows if r['claim_id'].startswith('CLS-')])==12
assert len([r for r in rows if r['claim_id'].startswith('GEN-')])==35
assert len([r for r in rows if r['claim_id'].startswith('EXT-')])==6
checked=0
for item in json.loads((E/'static/upstream_files.json').read_text()):
 p=ROOT/'upstream/lens'/item['path'];assert p.is_file(),p
 assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],p;checked+=1
# Disjoint point masses P=(1,0),Q=(0,1): standard total variation=1/2 L1=1.
P=[1.,0.];Q=[0.,1.];l1=sum(abs(a-b) for a,b in zip(P,Q));tvd=l1/2;code_tvd=tvd/math.sqrt(2);hd_unnorm=math.sqrt(sum((math.sqrt(a)-math.sqrt(b))**2 for a,b in zip(P,Q)));hellinger=hd_unnorm/math.sqrt(2)
saved=json.loads((ROOT/'papers/lens/metric_split_probe_results.json').read_text())
assert abs(saved['metric']['original_tvd']-code_tvd)<1e-12
assert abs(saved['metric']['original_hd']-hd_unnorm)<1e-12
# Recompute independent synthetic records against the unchanged reference functions, not the main Lens model.
sp=ROOT/'upstream/lens/data_preprocessing/2_split_pcap_by_label.py'
spec=importlib.util.spec_from_file_location('lens_independent_reference_split',sp);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
data=[]
for coarse in (0,1):
 for fine in range(4):
  for record in range(50):
   data.append({'path':f'SYNTHETIC_REVIEW/c{coarse}/f{fine}/r{record}.pcap','label1':f'c{coarse}','label2':f'c{coarse}_f{fine}','label3':f'c{coarse}_f{fine}_app'})
df=pd.DataFrame(data)
with contextlib.redirect_stdout(io.StringIO()):
 c=module.split_dataset_by_label(df,label_column='label1');f=module.split_dataset_to_train_val_test(df,label_column='label2')
pre=set(c['pretrain']['path']);same=set(c['test']['path']);fine_test=set(f['test']['path'])
assert (len(pre),len(same),len(fine_test),len(pre&same),len(pre&fine_test))==(240,32,40,0,22)
result={'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Independent captions/tracked hashes/standard arithmetic and original split functions on synthetic IDs only. No model/tokenizer/real traffic or paper-result reproduction','figure_numbers':sorted(figures),'table_numbers':sorted(tables),'coverage_rows':len(rows),'classification_rows':12,'generation_rows':35,'extension_rows':6,'tracked_source_hashes_verified':checked,'metric_arithmetic':{'standard_TVD':tvd,'code_normalization_TVD':code_tvd,'unnormalized_HD':hd_unnorm,'standard_Hellinger':hellinger,'paper_formula':'No explicit formula found; author convention and Table6 actual-score meaning Unknown'},'synthetic_reference_split':{'records':400,'pretrain':len(pre),'same_coarse_test':len(same),'independent_fine_test':len(fine_test),'same_coarse_overlap':len(pre&same),'cross_task_overlap':len(pre&fine_test),'interpretation':'Possible transductive input exposure in reference pipeline. Does not prove real released artifact overlap or supervised label leakage.'},'upstream_status_porcelain':subprocess.check_output(['git','-C',str(ROOT/'upstream/lens'),'status','--porcelain'],text=True).strip(),'matrix_sha256':hashlib.sha256((ROOT/'papers/lens/coverage_matrix.csv').read_bytes()).hexdigest()}
(ROOT/'papers/lens/independent_review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
