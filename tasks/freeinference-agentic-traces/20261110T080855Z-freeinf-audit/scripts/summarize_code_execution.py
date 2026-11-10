#!/usr/bin/env python3
"""Collect bounded-command metadata without turning exit0 into paper success."""
import datetime as dt
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
records = []
for path in sorted((root / "logs/official_checks").glob("*.json")):
    record = json.loads(path.read_text())
    record["experiment_id"] = path.stem
    record["metadata_path"] = str(path.relative_to(root))
    record["stdout_stderr_path"] = str(path.with_suffix(".log").relative_to(root))
    record["variant"] = ("Isolated patched source" if path.stem == "empty_scope_patch_check"
                         else "Original official source" if path.stem in {"paper_one_week", "paper_all_weeks", "simulation_one_week_guarded", "simulation_small_realdata", "public_tests", "release_help", "readme_make_dry_run", "readme_make_figures_original"}
                         else "Audit helper / validation")
    records.append(record)
now = dt.datetime.now(dt.timezone.utc)
t0 = dt.datetime.fromisoformat("2026-11-10T08:06:28+00:00")
comparison = json.loads((root / "reports/paper_metric_comparison_summary.json").read_text())
worktree = subprocess.check_output(["git", "-C", str(root / "upstream/freeinference_agentic_trace"), "status", "--porcelain"], text=True)
summary = {
    "task_budget_start_utc": t0.isoformat(), "generated_utc": now.isoformat(),
    "elapsed_task_seconds_as_of_generation": (now-t0).total_seconds(),
    "source_commit": "2b795dbf5eac490a7c081906fdce6cc7a184b7ef",
    "source_worktree_clean_verified": worktree == "", "source_modifications": [],
    "environment_ref": "environment/freeinference/runtime_versions.json",
    "environment_changes": "Official dependency constraints in independent Conda; Python path/source copy instead of upstream editable install/.venv",
    "status": "Partially Verified", "no_full_paper_reproduction_claimed": True,
    "commands": records,
    "command_outcomes": {"recorded": len(records), "exit_zero": sum(r["exit_code"] == 0 for r in records),
                         "nonzero": [{"id": r["experiment_id"], "exit_code": r["exit_code"], "timed_out": r.get("timed_out", False)} for r in records if r["exit_code"] != 0]},
    "full_public_processed_data": {"weeks": 16, "official_figure_registry_items_executed": 41,
                                   "fresh_output_files": 88, "nonfinite_numeric_output_count": 0,
                                   "source_copy_files_byte_equal": 115,
                                   "cache_source": "Author-precomputed simulation tables; provenance manifest check passed; no all-week replay rerun"},
    "paper_metric_comparison": comparison,
    "numeric_agreement_limitation": "Selected public-data calculations and author-supplied simulation aggregates, with documented printed precision; not independent ground-truth, inference-system or all-experiment validation",
    "additional_observations": ["Provider D retention curve does not directly corroborate15min median<50% wording; cause Unknown",
                                "Table6 single-call84.5% uses calls as denominator; request-weighted share93.2316%",
                                "Partial-week original plotting exits0 with8NaN comparison metrics when SWE-Bench absent"],
    "full_week_cache_replay": {"status": "Unknown", "executed": True, "week": "2026-08-30",
                               "timeout_seconds": 120, "processes": 1, "audit_address_space_guard_gib": 8,
                               "exit_code": 124, "complete_artifacts": 0,
                               "interpretation": "Not completed within this audit bound; not proof cloud replay is infeasible or algorithm defective"},
    "small_realdata_cache_replay": {"status": "Verified", "not_a_paper_result": True,
                                    "sessions": 3, "requests": 42, "tool_calls": 39,
                                    "block_reads": 539494, "policy_ttl_tally_rows": 52,
                                    "cheaper_reads_rows": 63, "official_cli_exit_code": 0,
                                    "elapsed_seconds": 2.431405076000374,
                                    "provenance": "reports/small_realdata_subset_provenance.json",
                                    "validation": "reports/small_realdata_simulation_validation.json"},
    "patches": [{"path": "patches/0001-report-empty-benchmark-scope.patch",
                 "category": "Runtime output-reporting error fix", "applied_to_upstream": False,
                 "validation": "Missing-SWE subset branch passed in private source copy; full16weeks patch branch not rerun",
                 "equivalence": "Nonempty comparison branch unchanged by inspection; empty populations explicitly skip entire comparison section"}],
    "unverified": ["Original gateway collection and95% session reconstruction validation", "Complete Figure7/Table6b subagent analysis",
                   "Figure16 intent annotation and its accuracy", "Complete fullweek/all16week independent cache replay",
                   "GPU queueing/throughput/KV memory/cost and real provider policies", "Batch-mix and provider-D discrepancy root causes"],
}
(root / "code_execution_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False)+"\n")
print(json.dumps({"output": "code_execution_summary.json", "commands": len(records), "source_clean": not worktree, "status": summary["status"]}))
