#!/usr/bin/env python3
"""Execute unchanged selected author notebook cells; bounded real-data core test.

Deliberately skips expensive search cells and hardware-result analysis. This is
not execution of the full notebook and does not reproduce paper metrics.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'upstream/etc_noms_2024/In_switch_ETC/Offline_model_preparation'
NOTEBOOK = SOURCE / 'Nims2023_Data_Analysis.ipynb'
OUT = ROOT / 'papers/etc_noms_2024/runtime-artifacts'
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(SOURCE)
notebook = json.loads(NOTEBOOK.read_text())
ns = {'__name__': '__audit_notebook_subset__'}
timings = {}
cells = [0, 1, 2, 4, 6, 10, 11, 12, 14, 15, 18]
for i in cells:
    print('BEGIN ORIGINAL NOTEBOOK CELL', i, flush=True)
    start = time.perf_counter()
    exec(compile(''.join(notebook['cells'][i]['source']), str(NOTEBOOK) + ':cell' + str(i), 'exec'), ns)
    timings[str(i)] = time.perf_counter() - start
    print('END ORIGINAL NOTEBOOK CELL', i, timings[str(i)], flush=True)
from sklearn.metrics import accuracy_score, classification_report
pred = ns['rf_final'].predict(ns['X_test_comp'][ns['selected_feats']])
report = classification_report(ns['y_test'], pred, target_names=ns['classes'], output_dict=True)
result = {
    'scope': 'Original cells subset on bundled real NIMS sample; not full search, CV, packet preprocessing, hardware or paper metric reproduction',
    'notebook_sha256': hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
    'input_sha256': hashlib.sha256((SOURCE / 'NIMS_IMA_sample_data.csv').read_bytes()).hexdigest(),
    'executed_cells': cells,
    'skipped_relevant_cells': {'8': 'Hyperparameter/feature grid search', '13': 'Full compression search', '16': 'Overwrites upstream model', '17': 'Overwrites upstream test data', '20-21': 'Hardware experiment digest data absent'},
    'raw_rows': 1867,
    'filtered_rows': len(ns['data_8_noms_new']),
    'train_rows': len(ns['y_train']),
    'test_rows': len(ns['y_test']),
    'features': ns['selected_feats'],
    'class_order': ns['classes'],
    'split': '75/25 stratified, random_state=42; original notebook cell6',
    'compressed_model_accuracy': accuracy_score(ns['y_test'], pred),
    'compressed_model_classification_report': report,
    'cell_seconds': timings,
}
target = ROOT / 'papers/etc_noms_2024/core_sample_metrics.json'
target.write_text(json.dumps(result, indent=2) + '\n')
import pickle
with (OUT / 'audit_retrained_rf.pkl').open('wb') as f:
    pickle.dump(ns['rf_final'], f)
print(json.dumps(result, indent=2), flush=True)
