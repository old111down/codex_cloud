"""Extra isolated reviewer-status boundary probes; no science pipeline rerun.

The default fixture uses public saved aggregates and an explicitly synthetic
minimal CLI numbers object, not private full-figure output. An explicit
FREEINFERENCE_EVIDENCE_ROOT may select already-existing private saved evidence.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TASKS = Path(__file__).resolve().parents[2]
TARGET = TASKS / '20261110T080855Z-freeinf-audit/scripts/review_reproduction_evidence.py'
SOURCE = Path(os.environ.get('FREEINFERENCE_EVIDENCE_ROOT', str(TASKS / '20261110T080855Z-freeinf-audit')))
FILES = [
    'reports/aggregate_stats.json', 'reports/paper_all_weeks_numeric_quality.json',
    'reports/paper_one_week_numeric_quality.json', 'private/runtime/figures/numbers.json',
    'paper_code_coverage.csv', 'data_dictionary.csv', 'logs/official_checks/paper_all_weeks.json',
    'logs/official_checks/simulation_one_week_guarded.json',
    'logs/official_checks/simulation_small_realdata.json',
    'reports/independent_full_week_review.json', 'reports/paper_metric_comparison_summary.json',
]


def mutate_json(root, name, transform):
    path = root / name
    value = json.loads(path.read_text())
    transform(value)
    path.write_text(json.dumps(value, allow_nan=False))


def main():
    results = []
    cases = [('nested_failure', 'Failed'), ('unknown_review', 'Unknown'),
             ('partial_review', 'Partially Verified'), ('nonfinite_constant', 'Failed'),
             ('numeric_overflow', 'Failed')]
    for name, expected in cases:
        with tempfile.TemporaryDirectory(prefix='independent-review-') as tmp:
            root = Path(tmp)
            for relative in FILES:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                if relative == 'private/runtime/figures/numbers.json' and not (SOURCE / relative).exists():
                    if 'FREEINFERENCE_EVIDENCE_ROOT' in os.environ:
                        raise FileNotFoundError('Explicit saved-evidence root lacks its CLI numbers file')
                    # Status/serialization fixture only; this does not stand in
                    # for independently recomputed full scientific figures.
                    stats = json.loads((SOURCE / 'reports/aggregate_stats.json').read_text())
                    totals = stats['cohort_totals']['top_level']
                    destination.write_text(json.dumps({'dataset': {'trace_summary': {
                        key: totals[key] for key in ('sessions', 'requests', 'tool_calls')}}}))
                else:
                    shutil.copyfile(SOURCE / relative, destination)
            script = root / 'scripts/review_reproduction_evidence.py'
            script.parent.mkdir()
            shutil.copyfile(TARGET, script)
            if name == 'nested_failure':
                def change(value):
                    value['weeks'][0]['checks'][0]['status'] = 'Failed'
                mutate_json(root, 'reports/independent_full_week_review.json', change)
            elif name in ('unknown_review', 'partial_review'):
                mutate_json(root, 'reports/independent_full_week_review.json',
                            lambda value: value.__setitem__('status', expected))
            elif name == 'nonfinite_constant':
                (root / 'private/runtime/figures/numbers.json').write_text('{"dataset": NaN}')
            else:
                path = root / 'reports/aggregate_stats.json'
                value = json.loads(path.read_text())
                value['cohort_totals']['top_level']['tokens']['prompt_tokens'] = 'OVERFLOW_SENTINEL'
                path.write_text(json.dumps(value).replace('"OVERFLOW_SENTINEL"', '1e309'))
            output = root / 'review.json'
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            run = subprocess.run([sys.executable, str(script), '--root', str(root),
                                  '--output', str(output)], capture_output=True, text=True,
                                 env=env, timeout=30)
            report = json.loads(output.read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
            assert run.returncode != 0 and report['status'] == expected, name
            if name == 'nested_failure':
                assert report['check_counts'] == {'Verified': 28, 'Failed': 0}
                assert report['additional_complete_week_review_status'] == 'Failed'
            if name in ('nonfinite_constant', 'numeric_overflow'):
                assert report['input_errors'], name
            results.append({'case': name, 'expected_status': expected, 'status': report['status'],
                            'exit_code': run.returncode, 'strict_json_saved': True,
                            'partial_values_omitted': report.get('partial_check_values_omitted', False)})
    print(json.dumps({'target_script_sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
                      'scope': 'Temporary public aggregate copies and explicit minimal synthetic CLI numbers unless available; no science rerun',
                      'minimal_synthetic_numbers_fixture': not (SOURCE / 'private/runtime/figures/numbers.json').exists(),
                      'cases': results, 'passed': len(results)}, indent=2))


if __name__ == '__main__':
    main()
