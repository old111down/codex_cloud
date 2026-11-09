#!/usr/bin/env python3
"""Recheck archived LiM predictions with the standard library; no model execution."""
import csv
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def main():
    data = ROOT / 'upstream/lim/cstnet-tls1.3_5_packets.csv'
    predictions = ROOT / 'evidence/lim/predictions.csv'
    metrics = json.loads((ROOT / 'evidence/lim/metrics.json').read_text())
    source = ROOT / 'upstream/lim/xgboost_classifier.py'
    with data.open() as file:
        rows = list(csv.DictReader(file))
    with predictions.open() as file:
        predicted = list(csv.DictReader(file))
    correct = sum(row['true_label'] == row['predicted_label'] for row in predicted)
    assert correct / len(predicted) == metrics['accuracy']
    indices = [int(row['csv_row_zero_based']) for row in predicted]
    assert len(indices) == len(set(indices))
    assert all(rows[index]['label'] == row['true_label'] for index, row in zip(indices, predicted))
    assert hashlib.sha256(data.read_bytes()).hexdigest() == metrics['data_sha256']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == metrics['source_sha256']
    per_class = {}
    for label in sorted({row['true_label'] for row in predicted}):
        tp = sum(row['true_label'] == label and row['predicted_label'] == label for row in predicted)
        fp = sum(row['true_label'] != label and row['predicted_label'] == label for row in predicted)
        fn = sum(row['true_label'] == label and row['predicted_label'] != label for row in predicted)
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn)
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        for key, value in [('precision', precision), ('recall', recall), ('f1-score', f1)]:
            assert abs(value - metrics['classification_report'][label][key]) < 1e-12
        per_class[label] = dict(tp=tp, fp=fp, fn=fn, precision=precision, recall=recall, f1=f1)
    candidates = json.loads((ROOT / 'catalog/offline_candidates.json').read_text())
    paths = [path for row in candidates for path in row['evidence_files']]
    missing = [path for path in paths if not (ROOT / path).is_file()]
    assert not missing
    assert all(row['reproduction_level'] == 'R0' and row['execution_status'].startswith('Unknown') for row in candidates)
    result = dict(
        review_date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        command='python papers/lim/independent_validate.py',
        scope='Independent arithmetic and artifact linkage check; does not rerun classifier or validate original PCAP',
        data_rows=len(rows), test_rows=len(predicted), correct_predictions=correct,
        accuracy=correct / len(predicted), source_sha256=metrics['source_sha256'],
        data_sha256=metrics['data_sha256'], all_true_labels_match_source_rows=True,
        test_row_indices_unique=True, per_class=per_class,
        candidate_records_checked=len(candidates), candidate_evidence_paths_checked=len(paths),
        candidate_evidence_paths_missing=missing, candidate_execution_claims_R0_Unknown=True,
    )
    output = ROOT / 'papers/lim/independent_validation.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'per_class'}, indent=2))

if __name__ == '__main__':
    main()
