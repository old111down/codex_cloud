"""Regression checks for review exit/status propagation, using saved aggregates.

Default fixtures copy public archived aggregates, CSVs and logs. Since full
CLI numbers were withheld from the public archive, only dataset.trace_summary
is synthesized from the saved top-level counts, explicitly as a regression
fixture (not validation of figure values). An explicit FREEINFERENCE_EVIDENCE_ROOT
override can use the real saved CLI aggregates. Every subprocess runs an exact
script copy in a temporary directory; historical scientific artifacts are never changed.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

TASKS = Path(__file__).resolve().parents[2]
PUBLIC_RUN = TASKS / '20261110T080855Z-freeinf-audit'
TARGET = Path(os.environ.get('FREEINFERENCE_REVIEW_SCRIPT', str(PUBLIC_RUN / 'scripts/review_reproduction_evidence.py')))
EVIDENCE_ROOT = Path(os.environ.get('FREEINFERENCE_EVIDENCE_ROOT', str(PUBLIC_RUN)))
FILES = [
    'reports/aggregate_stats.json', 'reports/paper_all_weeks_numeric_quality.json',
    'reports/paper_one_week_numeric_quality.json',
    'paper_code_coverage.csv', 'data_dictionary.csv', 'logs/official_checks/paper_all_weeks.json',
    'logs/official_checks/simulation_one_week_guarded.json',
    'logs/official_checks/simulation_small_realdata.json',
    'reports/independent_full_week_review.json', 'reports/paper_metric_comparison_summary.json',
]


@pytest.fixture(scope='session')
def saved_aggregates(tmp_path_factory):
    target = tmp_path_factory.mktemp('saved_aggregate_inputs')
    for name in FILES:
        source = EVIDENCE_ROOT / name
        assert source.is_file(), f'Required saved aggregate fixture is unavailable: {name}'
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    numbers = target / 'private/runtime/figures/numbers.json'
    numbers.parent.mkdir(parents=True)
    if 'FREEINFERENCE_EVIDENCE_ROOT' in os.environ:
        source = EVIDENCE_ROOT / 'private/runtime/figures/numbers.json'
        assert source.is_file(), 'Explicit saved-evidence override requires its real CLI aggregate file'
        shutil.copyfile(source, numbers)
    else:
        top = json.loads((target / 'reports/aggregate_stats.json').read_text())['cohort_totals']['top_level']
        numbers.write_text(json.dumps({
            '_regression_fixture': {
                'synthetic': True,
                'scope': 'Minimal CLI dataset.trace_summary only; not full figure-output validation',
                'derived_from': 'Public aggregate_stats.json cohort_totals.top_level',
            },
            'dataset': {'trace_summary': {name: top[name] for name in ('sessions', 'requests', 'tool_calls')}},
        }, allow_nan=False))
    return target


@pytest.fixture
def audit_root(tmp_path, saved_aggregates):
    target = tmp_path / 'audit'
    shutil.copytree(saved_aggregates, target)
    script = target / 'scripts/review_reproduction_evidence.py'
    script.parent.mkdir()
    shutil.copyfile(TARGET, script)
    assert script.read_bytes() == TARGET.read_bytes()
    return target


def change_json(root, name, transform):
    path = root / name
    value = json.loads(path.read_text())
    transform(value)
    path.write_text(json.dumps(value, allow_nan=False))


def invoke(root):
    output = root / 'reports/independent_reproduction_review.json'
    assert not output.exists()
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    result = subprocess.run(
        [sys.executable, str(root / 'scripts/review_reproduction_evidence.py'),
         '--root', str(root), '--output', str(output)],
        cwd=root, env=env, capture_output=True, text=True, timeout=30,
    )
    return result, output


def assert_failed(result, output):
    assert result.returncode != 0, 'A failed consistency review must exit nonzero'
    assert output.is_file(), 'Failure must persist a machine-readable report before exit'
    report = json.loads(output.read_text())
    assert report['status'] == 'Failed'
    return report


def test_public_saved_aggregates_with_minimal_cli_fragment_pass(audit_root):
    result, output = invoke(audit_root)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text())
    assert report['status'].startswith('Verified')
    assert report['check_counts'] == {'Verified': 28, 'Failed': 0}


def test_request_count_failure_is_reported(audit_root):
    change_json(audit_root, 'reports/aggregate_stats.json',
                lambda value: value['cohort_totals']['top_level'].__setitem__('requests', 1186581))
    result, output = invoke(audit_root)
    report = assert_failed(result, output)
    failures = {row['check'] for row in report['checks'] if row['status'] == 'Failed'}
    assert {'Table1_request_count', 'cohorts_partition_requests'} <= failures
    assert report['check_counts']['Failed'] >= 2


def test_manifest_boolean_failure_is_reported(audit_root):
    def mutate(value):
        value['weeks'][0]['checks']['requests.parquet:sha256_equal_tables_manifest'] = False
    change_json(audit_root, 'reports/aggregate_stats.json', mutate)
    result, output = invoke(audit_root)
    report = assert_failed(result, output)
    assert any(row['check'] == 'all_48_file_row_and_hash_checks' and row['status'] == 'Failed'
               for row in report['checks'])


def test_multiple_failures_are_retained(audit_root):
    def mutate(value):
        value['cohort_totals']['top_level']['requests'] -= 1
        value['weeks'][0]['checks']['requests.parquet:sha256_equal_tables_manifest'] = False
    change_json(audit_root, 'reports/aggregate_stats.json', mutate)
    report = assert_failed(*invoke(audit_root))
    assert report['check_counts']['Failed'] >= 3
    assert len(report['checks']) == 28


@pytest.mark.parametrize('level', ['root', 'week', 'check_counts'])
def test_additional_week_failure_propagates(audit_root, level):
    def mutate(value):
        if level == 'root':
            value['status'] = 'Failed'
        elif level == 'week':
            value['weeks'][0]['status'] = 'Failed'
        else:
            value['weeks'][0]['check_counts']['Failed'] = 1
    change_json(audit_root, 'reports/independent_full_week_review.json', mutate)
    report = assert_failed(*invoke(audit_root))
    assert report['check_counts']['Failed'] == 0, 'Base checks are still valid; do not rewrite them'
    assert report['additional_complete_week_artifact_reviews']


def test_missing_input_writes_failure_report(audit_root):
    (audit_root / 'reports/aggregate_stats.json').unlink()
    report = assert_failed(*invoke(audit_root))
    assert report['input_errors']


def test_malformed_input_writes_failure_report(audit_root):
    (audit_root / 'private/runtime/figures/numbers.json').write_text('{"dataset":')
    report = assert_failed(*invoke(audit_root))
    assert report['input_errors']


def test_invalid_structure_writes_failure_report(audit_root):
    (audit_root / 'reports/paper_all_weeks_numeric_quality.json').write_text('[]')
    report = assert_failed(*invoke(audit_root))
    assert report['input_errors']


def test_paper_discrepancies_do_not_fail_consistency(audit_root):
    change_json(audit_root, 'reports/paper_metric_comparison_summary.json',
                lambda value: value.__setitem__('outside_printed_rounding', [
                    {'claim_id': 'batch_mix_same', 'reported_value': 71.3, 'observed_value': 64.0174}
                ]))
    result, output = invoke(audit_root)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text())
    assert report['status'].startswith('Verified')
    assert report['selected_numeric_claim_comparison']['outside_printed_rounding']
    assert report['confirmed_discrepancies']
