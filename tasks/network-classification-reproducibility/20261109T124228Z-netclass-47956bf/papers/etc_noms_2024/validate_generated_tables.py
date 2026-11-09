#!/usr/bin/env python3
"""Compare generated RF table entries without calling BFRT or hardware APIs."""
import ast
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
paths = {
    'bundled': ROOT / 'upstream/etc_noms_2024/In_switch_ETC/Switch/table_entries.py',
    'unmodified': ROOT / 'papers/etc_noms_2024/runtime-artifacts/generator/table_entries.py',
    'patched': ROOT / 'papers/etc_noms_2024/runtime-artifacts/patched/In_switch_ETC/Offline_model_preparation/table_entries.py',
}
def read(path):
    entries = {}
    votes = {}
    for call in ast.walk(ast.parse(path.read_text())):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
            continue
        if not call.func.attr.startswith('add_with_') or not isinstance(call.func.value, ast.Name):
            continue
        name = call.func.value.id
        kwargs = {k.arg: ast.literal_eval(k.value) for k in call.keywords}
        canonical = tuple(sorted(kwargs.items()))
        entries.setdefault(name, set()).add(canonical)
        if name == 'voting_table':
            key = tuple(kwargs['class' + str(i)] for i in range(5))
            assert key not in votes
            votes[key] = kwargs['class_result']
    return entries, votes
data = {k: read(p) for k, p in paths.items()}
bundled, bv = data['bundled']
unmodified, uv = data['unmodified']
patched, pv = data['patched']
comparison = {}
for name in sorted(set(bundled) | set(patched)):
    missing = bundled.get(name, set()) - patched.get(name, set())
    extra = patched.get(name, set()) - bundled.get(name, set())
    comparison[name] = {'bundled_count': len(bundled.get(name, set())), 'patched_count': len(patched.get(name, set())), 'missing': len(missing), 'extra': len(extra)}
    assert not missing and not extra, (name, 'table mismatch')
effective_differences = []
for key in itertools.product(range(1, 7), repeat=5):
    # P4 set_default_result uses class0 for absent voting entries.
    b = bv.get(key, key[0])
    u = uv.get(key, key[0])
    p = pv.get(key, key[0])
    assert b == p
    if b != u:
        effective_differences.append({'tree_classes': key, 'bundled': b, 'unmodified': u})
result = {
    'scope': 'Exhaustive 6^5 software vote comparison and exact canonical generated add_with entry-set comparison; no BFRT calls, P4 compilation, or packet simulation',
    'sha256': {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()},
    'vote_counts': {'bundled': len(bv), 'unmodified': len(uv), 'patched': len(pv)},
    'p4_voting_table_declared_size': 5256,
    'unmodified_exceeds_p4_declared_size': len(uv) > 5256,
    'patched_table_entry_sets_equal_bundled': True,
    'all_vote_inputs_tested': 6 ** 5,
    'unmodified_effective_decision_differences': len(effective_differences),
    'difference_examples': effective_differences[:5],
    'per_table_comparison': comparison,
    'deployment_configuration_difference_remaining': 'Generator configures cages1,5; bundled script also configures cage9. No port change made in patch.',
}
(ROOT / 'papers/etc_noms_2024/table_validation_metrics.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
