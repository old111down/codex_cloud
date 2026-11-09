#!/usr/bin/env python3
"""Execute unchanged upstream source, capture its in-memory test outputs.
This second run adds observation only, not a paper-equivalent sample selection.
"""
import os, runpy, json, hashlib, pathlib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
root = pathlib.Path(__file__).resolve().parents[2]
up = root / 'upstream/lim'
source = up / 'xgboost_classifier.py'
os.chdir(up)
g = runpy.run_path(str(source), run_name='__main__')
_, test_idx = train_test_split(np.arange(len(g['df'])), test_size=0.2, random_state=42)
assert np.array_equal(g['y_encoded'][test_idx], g['y_test'])
out = pd.DataFrame({'csv_row_zero_based': test_idx, 'true_label':g['y_test_decoded'],
                    'predicted_label':g['y_pred_decoded']})
ev = root / 'evidence/lim'
out.to_csv(ev / 'predictions.csv', index=False)
metrics = {'method':'runpy executes upstream source verbatim; capture after completion',
 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'data_sha256':hashlib.sha256((up/'cstnet-tls1.3_5_packets.csv').read_bytes()).hexdigest(),
 'rows':len(g['df']), 'training_rows':len(g['y_train']), 'test_rows':len(g['y_test']),
 'accuracy':accuracy_score(g['y_test_decoded'],g['y_pred_decoded']),
 'classification_report':classification_report(g['y_test_decoded'],g['y_pred_decoded'],output_dict=True),
 'paper_equivalence':'Unknown: sample selection, balance, versions and original split differ or unavailable',
 'source_modified':False, 'weights_saved':False}
(ev/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
print('AUDIT_CAPTURE_METRICS='+json.dumps(metrics))
