"""Synthetic CPU component smoke; does not reproduce a paper metric."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
UP = ROOT / "upstream" / "mousika"
sys.path.insert(0, str(UP / "Distillation"))
from Tree import TreeClassifier
from SoftTree import SoftTreeClassifier

spec = importlib.util.spec_from_file_location("rule2entry", UP / "rule2entry/code/rule2entry.py")
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)

# Four binary feature vectors, repeated eight times; label is first input bit.
X = np.tile(np.array([[0,0], [0,1], [1,0], [1,1]]), (8,1))
y = X[:,0]
soft = np.column_stack([1-y, y]).astype(float)
tests = {}
for cls, labels in [(TreeClassifier,y), (SoftTreeClassifier,soft)]:
    model = cls(n_features="all", min_sample_leaf=1)
    model.fit(X, labels, ["d", "d"])
    predicted = np.asarray(model.predict(X))
    assert np.array_equal(predicted, y), (cls.__name__, predicted)
    with tempfile.TemporaryDirectory() as d:
        rule = Path(d) / "rules.txt"
        model.show_tree(str(rule))
        try:
            rows = converter.Rule2Binary().parse_file(rule)
        except ValueError as exc:
            # Retain the original failed run and expose the narrower passing scope.
            # TreeClassifier serializes categorical labels as e.g. '1.0'; parser uses int().
            if cls is TreeClassifier and "invalid literal for int()" in str(exc):
                tests[cls.__name__] = {"n_synthetic_samples":len(X), "predictions_equal_labels":True,
                    "exported_rules_match_synthetic_vectors":False,
                    "known_integration_failure":str(exc)}
                continue
            raise
        assert rows
        for x, expected in zip(X, y):
            bits = int(x[0]) << 111 | int(x[1]) << 110
            matches = [label for mask,value,label in rows if bits & mask == value]
            assert matches == [int(expected)], (x.tolist(), matches)
    tests[cls.__name__] = {"n_synthetic_samples": len(X), "predictions_equal_labels": True,
                           "exported_rules_match_synthetic_vectors": True}

bundled = []
for rule in sorted((UP / "rule2entry/output/rule_tree/univ").glob("*.txt")):
    rows = converter.Rule2Binary().parse_file(rule)
    existing = UP / "rule2entry/output/ternary_entry/univ" / rule.name
    expected_rows = converter.Rule2Binary().load_ternary(existing)
    assert rows == expected_rows, rule.name
    bundled.append({"path":str(rule.relative_to(ROOT)), "rules":len(rows),
                    "sha256":hashlib.sha256(rule.read_bytes()).hexdigest(),
                    "equals_bundled_ternary":True})
print(json.dumps({"kind":"synthetic_component_smoke", "tests":tests,
                  "bundled_rule_conversion":bundled, "paper_accuracy":"Unknown",
                  "P4_compilation":"not run", "hardware":"not run"}, indent=2))
