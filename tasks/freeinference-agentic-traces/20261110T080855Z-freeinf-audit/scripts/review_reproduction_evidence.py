#!/usr/bin/env python3
"""Read-only consistency review of saved aggregate/runtime evidence.

Only a completed, passing consistency review exits zero. Scientific paper/code
result discrepancies remain evidence, not consistency-check failures. Use
--root and --output to review saved inputs without overwriting prior reports.
No author computation, model, dataset download or original experiment is run.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sys

SCOPE = ('Independent read-only review of saved aggregates, source methods and '
         'execution logs; no author pipeline/model rerun')
STATUSES = {'Verified', 'Partially Verified', 'Failed', 'Unknown'}


def finite_count(value):
    if isinstance(value, float):
        return int(not math.isfinite(value))
    if isinstance(value, dict):
        return sum(finite_count(v) for v in value.values())
    if isinstance(value, list):
        return sum(finite_count(v) for v in value)
    return 0


def complete_week_status(review):
    """Validate the optional saved review and propagate its actual failures."""
    if review.get('status') not in STATUSES:
        raise ValueError('Complete-week review has an invalid or missing status')
    weeks = review.get('weeks')
    if not isinstance(weeks, list) or not weeks:
        raise ValueError('Complete-week review must contain a nonempty weeks list')
    statuses = [review['status']]
    for week in weeks:
        if not isinstance(week, dict) or not isinstance(week.get('week'), str):
            raise ValueError('Complete-week review contains an invalid week record')
        if week.get('status') not in STATUSES:
            raise ValueError('Complete-week review contains an invalid week status')
        counts = week.get('check_counts')
        if not isinstance(counts, dict) or not isinstance(counts.get('Failed'), int) or counts['Failed'] < 0:
            raise ValueError('Complete-week review has invalid failure counts')
        statuses.append(week['status'])
        if counts['Failed'] > 0:
            statuses.append('Failed')
        if 'checks' in week:
            if not isinstance(week['checks'], list):
                raise ValueError('Complete-week review has an invalid checks list')
            for item in week['checks']:
                if not isinstance(item, dict) or item.get('status') not in STATUSES:
                    raise ValueError('Complete-week review contains an invalid check')
                statuses.append(item['status'])
    for status in ('Failed', 'Unknown', 'Partially Verified'):
        if status in statuses:
            return status
    return 'Verified'


def build_report(root, checks):
    # The scientific checks below retain their original populations and rules.
    ROOT = root

    def check(name, actual, expected, scope, evidence):
        checks.append({'check': name, 'status': 'Verified' if actual == expected else 'Failed',
                       'actual': actual, 'expected': expected, 'scope': scope, 'evidence': evidence})

    def read(name):
        def invalid_constant(constant):
            raise ValueError(f'{name}: invalid non-finite JSON constant {constant}')
        value = json.loads((ROOT / name).read_text(), parse_constant=invalid_constant)
        if not isinstance(value, dict):
            raise ValueError(f'{name}: expected a JSON object')
        return value

    stats=read('reports/aggregate_stats.json')
    numbers=read('private/runtime/figures/numbers.json')
    quality=read('reports/paper_all_weeks_numeric_quality.json')
    expected_harness={'claude-code':639,'cline':86,'codex':763,'copilot':295,'eval:swe-bench':1035,
                      'hermes':3953,'kilo':797,'oh-my-pi':719,'openclaw':189,'opencode':1733,
                      'openhands':22,'pi':1499,'zcode':197,'zoo':75}
    check('complete_week_count',stats['scope']['weeks'],16,'public release weeks','reports/aggregate_stats.json')
    check('Table1_top_level_harness_counts',stats['distributions']['top_level_session_harness'],expected_harness,
          'top-level includes SWE-Bench, excludes child sessions','paper Table1 p1; reports/aggregate_stats.json')
    check('Table1_session_count',stats['cohort_totals']['top_level']['sessions'],12002,
          'top-level includes SWE-Bench','paper Table1 p1; reports/aggregate_stats.json')
    check('Table1_request_count',stats['cohort_totals']['top_level']['requests'],1186582,
          'top-level includes SWE-Bench, excludes child requests','paper Table1 p1; reports/aggregate_stats.json')
    check('Table1_tool_call_count',stats['cohort_totals']['top_level']['tool_calls'],1213347,
          'top-level includes SWE-Bench, excludes child tool calls','paper Table1 p1; reports/aggregate_stats.json')
    for field,paper in [('prompt_tokens',209.2),('cache_read_tokens',197.1),('completion_tokens',552.5)]:
        scale=1e6 if field=='completion_tokens' else 1e9
        check('Table1_rounded_'+field,round(stats['cohort_totals']['top_level']['tokens'][field]/scale,1),paper,
              'top-level includes SWE-Bench; rounded at paper precision','paper Table1 p1; reports/aggregate_stats.json')
    for key,file in [('sessions','sessions.parquet'),('requests','requests.parquet'),('tool_calls','tool_calls.parquet')]:
        check('cohorts_partition_'+key,sum(v[key] for v in stats['cohort_totals'].values()),stats['totals']['rows'][file],
              'all published rows=top-level+child','reports/aggregate_stats.json')
    for key,value in stats['totals']['tokens'].items():
        if key.startswith('role_tokens'): continue
        check('cohorts_partition_'+key,sum(v['tokens'][key] for v in stats['cohort_totals'].values()),value,
              'all published token totals=top-level+child','reports/aggregate_stats.json')
    check('stable_account_salt_series',stats['identifiers_aggregate']['consistent_nonnull_salt_series'],True,
          'declared salt series only; not proof of one account per person','reports/aggregate_stats.json')
    check('account_count',stats['identifiers_aggregate']['distinct_pseudonymous_accounts_within_salt_series'],267,
          'distinct pseudonymous accounts, not summed weekly counts','README; reports/aggregate_stats.json')
    check('session_ids_crossweek_unique',stats['identifiers_aggregate']['duplicate_session_ids_across_all_selected_weeks'],0,
          'published session identifiers across selected weeks','reports/aggregate_stats.json')
    for field,expected_sum in [('session_harness',stats['totals']['rows']['sessions.parquet']),
                               ('top_level_session_harness',12002),
                               ('request_harness',stats['totals']['rows']['requests.parquet']),
                               ('tool_category',stats['totals']['rows']['tool_calls.parquet'])]:
        check('distribution_sum_'+field,sum(stats['distributions'][field].values()),expected_sum,
              'aggregate arithmetic only','reports/aggregate_stats.json')
    manifest_checks=[v for w in stats['weeks'] for k,v in w['checks'].items() if 'equal_tables_manifest' in k]
    check('all_48_file_row_and_hash_checks',len(manifest_checks)==96 and all(manifest_checks),True,
          '3tables×16weeks:96 saved row/hash checks against author manifests','reports/aggregate_stats.json')
    check('full_period_numerics_finite',finite_count(numbers),0,
          'author CLI numbers.json only; not proof every plot is semantically correct','private/runtime/figures/numbers.json')
    check('quality_report_agrees',quality['nonfinite_count'],0,
          'independent finite scan agrees with saved validator','reports/paper_all_weeks_numeric_quality.json')
    check('no_explicit_full_period_skips',quality['explicit_not_drawn'],[],
          'registered figure CLI outputs; missing modules still remain missing','reports/paper_all_weeks_numeric_quality.json')
    for field,expected in [('sessions',12002),('requests',1186582),('tool_calls',1213347)]:
        check('author_trace_summary_'+field,numbers['dataset']['trace_summary'][field],expected,
              'author global top-level inventory cross-check','private/runtime/figures/numbers.json')
    negative_batches=sum(w.get('negative_gap_detail_aggregate',{}).get('distinct_request_batches',0) for w in stats['weeks'])
    observations={'all_rows':stats['totals']['rows'],'top_level':stats['cohort_totals']['top_level'],
                  'child':stats['cohort_totals']['child'],
                  'human_top_level_sessions':12002-1035,
                  'negative_tool_gap_call_rows':stats['observations_requiring_review_total']['negative_tool_gap_latency'],
                  'negative_tool_gap_distinct_request_batches':negative_batches,
                  'cached_tokens_exceed_prompt_rows':stats['observations_requiring_review_total']['cached_tokens_exceed_provider_prompt'],
                  'gap_formula_mismatch_rows':stats['observations_requiring_review_total']['tool_gap_disagrees_release_adjacency_formula'],
                  'full_figure_output_nonfinite_values':finite_count(numbers),
                  'one_week_figure_output_nonfinite_values':read('reports/paper_one_week_numeric_quality.json')['nonfinite_count']}
    files=['reports/aggregate_stats.json','reports/paper_all_weeks_numeric_quality.json',
           'reports/paper_one_week_numeric_quality.json','private/runtime/figures/numbers.json',
           'paper_code_coverage.csv','data_dictionary.csv','logs/official_checks/paper_all_weeks.json',
           'logs/official_checks/simulation_one_week_guarded.json','logs/official_checks/simulation_small_realdata.json']
    provenance=[{'path':name,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in files]
    report={'status':'Unknown',
            'review_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'scope':'Independent read-only review of saved aggregates, source methods and execution logs; no author pipeline/model rerun',
            'source_commit':stats['source_commit'],'dataset_revision':stats['dataset_revision'],
            'checks':checks,'check_counts':{s:sum(c['status']==s for c in checks) for s in ['Verified','Failed']},
            'observations':observations,'evidence_files':provenance,
            'important_limits':['Author-supplied cache intermediate tables were redrawn; full sixteen-week cache simulation was not rerun.',
                                'The successful small cache replay uses3selected sessions/42requests, not the full paper population.',
                                'Count consistency is independently checked; raw private-source correctness and semantic label accuracy remain Unknown.',
                                'Full-method and numeric discrepancies are described in independent_reproduction_review.md; finite numbers do not imply paper equality.']}
    full_week_review_path=ROOT/'reports/independent_full_week_review.json'
    if full_week_review_path.exists():
        full_review=read('reports/independent_full_week_review.json')
        report['additional_complete_week_review_status']=complete_week_status(full_review)
        report['additional_complete_week_artifact_reviews']=[{'week':w['week'],'status':w['status'],'check_counts':w['check_counts']} for w in full_review.get('weeks',[])]
    report['commands_executed']=['python scripts/review_reproduction_evidence.py']
    comparison_path=ROOT/'reports/paper_metric_comparison_summary.json'
    if comparison_path.exists():
        report['selected_numeric_claim_comparison']=read('reports/paper_metric_comparison_summary.json')
    report['confirmed_discrepancies']=[
     {'id':'batch_mix','status':'Verified discrepancy','paper_same_percent':71.3,'observed_same_percent':64.01737580122536,'paper_mixed_percent':28.7,'observed_mixed_percent':35.98262419877464,'root_cause':'Unknown'},
     {'id':'batch_width_estimand','status':'Verified semantic discrepancy','single_call_call_share_percent':84.48155264313472,'single_call_request_share_percent':93.23158637717053,'scope':'Human top-level requests with calls; zero-call requests excluded'},
     {'id':'provider_letter_curve','status':'Partially Verified discrepancy','observation':'Public C first point below50% near811.652s;D near2051.923s,while paper describesD after15min','root_cause':'Unknown mapping/filter/version'}]
    report['method_limits']=['Human selection requires2userturns+1toolturn;SWE requires1toolturn only','Harness code uses intro phrase before user-agent,paper describes reversed precedence','No explicitRTT subtraction in public tool-gap path;upstream logged latency preprocessing Unknown','ToolTime/latency uses single-call requests;failures use nonnull outcome']
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1],
                        help='Read saved evidence under this audit root')
    parser.add_argument('--output', type=Path,
                        help='Write a new review report here; default ROOT/reports/independent_reproduction_review.json')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    output = args.output or root / 'reports/independent_reproduction_review.json'
    checks = []
    try:
        report = build_report(root, checks)
        additional = report.get('additional_complete_week_review_status', 'Verified')
        if any(item['status'] == 'Failed' for item in checks) or additional == 'Failed':
            report['status'] = 'Failed'
        else:
            report['status'] = additional
        report['status_detail'] = (
            'Consistency checks passed; unresolved scientific method/result discrepancies remain separate'
            if report['status'] == 'Verified'
            else 'Consistency review did not pass; inspect checks and additional complete-week review status'
        )
        report['input_errors'] = []
        # Validate serialization before publishing a report, including input-derived fields.
        serialized = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        report = {
            'status': 'Failed', 'review_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'scope': SCOPE, 'source_commit': 'Unknown', 'dataset_revision': 'Unknown',
            'checks': checks,
            'check_counts': {status: sum(item['status'] == status for item in checks)
                             for status in ('Verified', 'Failed')},
            'input_errors': [{'type': type(error).__name__, 'message': str(error)}],
            'status_detail': 'Saved evidence is missing, invalid, or unreadable; no passing review is claimed',
        }
        # A malformed input might have placed a non-finite value in a partial check.
        # Keep the failure and diagnostic, omitting unserializable partial values.
        try:
            serialized = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
        except (TypeError, ValueError):
            report['checks'] = []
            report['partial_check_values_omitted'] = True
            serialized = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized)
    except OSError as error:
        print(f'Failed to persist consistency review: {type(error).__name__}: {error}', file=sys.stderr)
        return 1
    print(json.dumps({'status': report['status'], 'checks': report['check_counts'],
                      'input_errors': report['input_errors']}, ensure_ascii=False))
    return 0 if report['status'] == 'Verified' else 1


if __name__ == '__main__':
    raise SystemExit(main())
