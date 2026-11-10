"""Run the review regressions in a relocated copy of public artifacts only.

No private dataset, HF metadata or saved figure file is copied. Temporary HTTP
fixtures and negative credential markers are created/removed by the tests.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

REVIEW = Path(__file__).resolve().parents[1]
PRIOR = REVIEW.parent / '20261110T080855Z-freeinf-audit'
SCRIPTS = ['download_selected_week.py', 'download_processed_release.py',
           'pinned_release_download.py', 'export_reviewed_archive.py',
           'review_reproduction_evidence.py']


def hashes():
    return {name: hashlib.sha256((PRIOR / 'scripts' / name).read_bytes()).hexdigest()
            for name in SCRIPTS}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', default=sys.executable)
    args = parser.parse_args()
    before = hashes()
    record = {'start_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Relocated public checkout plus inert local fixtures; no original paper/data/model rerun',
              'source_sha256_before': before}
    output = REVIEW / 'reports/relocated_regression_summary.json'
    log = REVIEW / 'logs/relocated_regression.log'
    output.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix='pr3-public-regression-') as folder:
            work = Path(folder)
            task_parent = work / 'tasks/freeinference-agentic-traces'
            task_parent.mkdir(parents=True)
            for source in (PRIOR, REVIEW):
                shutil.copytree(source, task_parent / source.name,
                                ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
            tests = [task_parent / REVIEW.name / 'scripts' / name for name in (
                'test_download_workflow.py', 'test_export_safety.py', 'test_review_status.py',
                'test_independent_download_cache.py', 'test_independent_export_boundaries.py')]
            command = [args.python, '-m', 'pytest', '-p', 'no:cacheprovider', '-q',
                       *(str(path) for path in tests), '--junitxml=' + str(work / 'results.xml')]
            env = os.environ.copy()
            env.pop('FREEINFERENCE_EVIDENCE_ROOT', None)
            env.pop('FREEINFERENCE_REVIEW_SCRIPT', None)
            env['PYTHONDONTWRITEBYTECODE'] = '1'
            record.update(argv=command, cwd=str(work), private_fixture_overrides_removed=True)
            result = subprocess.run(command, cwd=work, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
            log.write_text(result.stdout)
            record['pytest_exit_code'] = result.returncode
            xml = ET.parse(work / 'results.xml')
            suites = list(xml.getroot().iter('testsuite'))
            record['counts'] = {field: sum(int(item.get(field, '0')) for item in suites)
                                for field in ('tests', 'failures', 'errors', 'skipped')}
            record['source_sha256_after'] = hashes()
            count = record['counts']
            passed = (result.returncode == 0 and count['tests'] > 0
                      and count['failures'] == count['errors'] == count['skipped'] == 0
                      and record['source_sha256_after'] == before)
            record['status'] = 'Verified' if passed else 'Failed'
    except (OSError, ValueError, ET.ParseError, subprocess.TimeoutExpired) as error:
        record.update(status='Failed', error_type=type(error).__name__, error=str(error))
    record['end_utc'] = datetime.now(timezone.utc).isoformat()
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    (REVIEW / 'logs/relocated_regression.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: record[key] for key in ('status', 'counts', 'end_utc') if key in record}))
    return 0 if record['status'] == 'Verified' else 1


if __name__ == '__main__':
    raise SystemExit(main())
