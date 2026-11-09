#!/usr/bin/env python3
"""Independent static/artifact check. No model or pickle deserialization."""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'evidence/pegasus'
UP=ROOT/'upstream/pegasus'
def j(path):return json.loads((ROOT/path).read_text())
def stamp(s):return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
mlp=j('evidence/pegasus/mlp_weights_static_review.json')
cnnl=j('evidence/pegasus/cnnl_weights_static_review.json')
smoke=j('evidence/pegasus/model_smoke_metrics.json')
for record in (mlp,cnnl):
    p=ROOT/record['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256']
assert smoke['weights_sha256']==mlp['sha256']
assert smoke['strict_state_dict_load'] and smoke['finite_output'] and smoke['log_probability_normalization_passed']
assert smoke['input_shape']==[9,10] and smoke['output_shape']==[9,3]
fixture=ROOT/'papers/pegasus/runtime-artifacts/synthetic_9rows.csv'
assert hashlib.sha256(fixture.read_bytes()).hexdigest()==smoke['synthetic_csv_sha256']
with fixture.open() as f:rows=list(csv.reader(f))
assert len(rows)==10 and len(rows[0])==11
assert sorted(int(float(r[0])) for r in rows[1:])==[0,0,0,1,1,1,2,2,2]

original=j('logs/pegasus/readme_cpu_cnnl.json')
assert original['exit_code']==1
assert stamp(cnnl['reviewed_at_utc'])>stamp(original['end_utc'])
src=(UP/'software/quickdemo/cnnLtest.py').read_text()
assert src.index('weight = torch.load(')<src.index('test_loader = build_data_loader(')<src.index('model.load_state_dict(weight)')
original_error=(ROOT/'logs/pegasus/readme_cpu_cnnl.log').read_text()
assert 'FileNotFoundError' in original_error and 'redeal_test.json' in original_error
retrieval=j('logs/pegasus/retrieve_evidence.json')
model_run=j('logs/pegasus/model_smoke.json')
assert stamp(retrieval['end_utc'])<stamp(model_run['start_utc'])
assert model_run['exit_code']==0
assert j('logs/pegasus/unmodified_mlp_synthetic.json')['exit_code']==0

paper_sha=hashlib.sha256((E/'paper.pdf').read_bytes()).hexdigest()
assert paper_sha==hashlib.sha256((E/'paper_final.pdf').read_bytes()).hexdigest()
text=(E/'paper.txt').read_text()
assert 'arXiv:2506.05779v1' in text and text.count('\f')==15
assert 'macro-accuracy' in text and 'average F1-score' in text
assert '75% of the flows' in text and '10% for validation' in text
assert '15% for testing' in text
root_readme=(UP/'README.md').read_text()
software_readme=(UP/'software/README.md').read_text()
assert 'software and hardware outputs are identical' in root_readme
assert 'original .pth files used in the paper were lost' in software_readme
assert 'not fully identical to the software simulation' in software_readme
assert 'max_bits_per_flow' in (UP/'figure_generation/code/Figure8.py').read_text()
assert 'load_roc_data' in (UP/'figure_generation/code/Figure9.py').read_text()
assert 'GPU/CPU' in (UP/'figure_generation/code/Figure10a_b_c.py').read_text()
assert 'Throughput (samples/s)' in (UP/'figure_generation/code/Figure10d.py').read_text()

split=j('evidence/pegasus/split_grain_diagnostic.json')
t=set(split['train_starts']);v=set(split['validation_starts'])
assert t.isdisjoint(v) and t|v==set(range(33))
tp={i for start in t for i in range(start,start+8)}
vp={i for start in v for i in range(start,start+8)}
assert sorted(tp&vp)==split['shared_packet_positions']
assert split['synthetic_flow_count']==1 and split['shared_source_flows']==1
assert not subprocess.check_output(['git','-C',str(UP),'status','--porcelain']).strip()
result={'scope':'Independent static/artifact review only; no repeated inference, unpickle, training, P4 simulation or hardware',
        'paper_sha256':paper_sha,'author_copy_pages':15,
        'paper_and_named_final_file_are_same_arxiv_v1':True,
        'final_ACM_layout_verified':False,
        'replacement_MLP_weight_and_synthetic_fixture_hashes_match':True,
        'synthetic_fixture_rows':9,
        'original_CNNL_deserialized_weight_before_failed_data_loading':True,
        'CNNL_state_dict_not_applied_before_failure':True,
        'CNNL_review_happened_after_original_run':True,
        'MLP_review_harness_finished_before_model_smoke':True,
        'overlapping_window_split_counterexample_packet_intersection':sorted(tp&vp),
        'diagnostic_val_ratio':0.2,'upstream_CLI_default_val_ratio':0.1,
        'paper_accuracy_means_packet_macro_F1':True,
        'figure_numbering_by_content':{'artifact8':'author7 storage','artifact9':'author8 ROC','artifact10':'author9 comparison/throughput'},
        'upstream_clean':True,
        'limitations':['No real traffic metrics','No paper original checkpoint recovery','No verified hardware/software equivalence','No actual train/test leak established']}
(ROOT/'papers/pegasus/independent_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
