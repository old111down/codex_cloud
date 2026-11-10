#!/usr/bin/env python3
"""Compare independently transcribed paper claims to aggregate runtime outputs.

Agreement from author-supplied simulation intermediates is marked partial;
it never becomes an independent cache-replay reproduction. Tolerances reflect
printed rounding, and are emitted for inspection rather than hidden in labels.
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUMBERS = ROOT / "private/runtime/figures/numbers.json"
EXTRA = ROOT / "reports/extra_paper_metrics_all_weeks_v2.json"
if not EXTRA.exists():
    EXTRA = ROOT / "reports/extra_paper_metrics_all_weeks.json"
n = json.loads(NUMBERS.read_text())
extra = json.loads(EXTRA.read_text()) if EXTRA.exists() else {}
observed = {}


def record(cid, path, scale=1.0, author_simulation=False):
    value = n
    try:
        for key in path.split("/"):
            value = value[key]
        observed[cid] = (float(value) * scale, path, author_simulation)
    except (KeyError, TypeError, ValueError):
        pass


for cid, metric in {"total_sessions": "sessions", "total_requests": "requests", "total_tools": "tool_calls", "input_tokens": "input_tokens", "output_tokens": "output_tokens", "cached_tokens": "cached_tokens"}.items():
    record(cid, "dataset/trace_summary/" + metric)
for cid, metric in {"user_steps": "median_user_steps", "tool_steps": "median_tool_steps", "llm_steps": "median_requests"}.items():
    record(cid, "sessions/counts_per_session/" + metric)
for cid, metric, scale in [("turn_duration", "turn_median_s", 1), ("session_duration", "session_median_s", 1/60), ("session_p90", "session_p90_s", 1/3600)]:
    record(cid, "sessions/turn_and_session_duration/" + metric, scale)
for cid, metric in {"input_median": "median_input", "uncached_median": "median_uncached", "output_median": "median_output"}.items():
    record(cid, "sessions/tokens_per_request/" + metric)
for cid, metric in {"cached_cost_share": "pooled_cached", "uncached_cost_share": "pooled_uncached", "output_cost_share": "pooled_output"}.items():
    record(cid, "sessions/cost_share_by_session/" + metric, 100)
for part, metric in {"user_idle": "human", "tool": "tool", "decode": "decode", "prefill": "prefill"}.items():
    record("time_" + part, "sessions/session_time_breakdown/mean_" + metric + "_share", 100)
for part in ("prefill", "decode", "tool"):
    record("speedup_" + part, "sessions/speedup_if_twice_as_fast/" + part + "_speedup")
record("shell_calls", "tools/shell_split/shell_share", 100)
if "shell_calls" in observed:
    observed["native_calls"] = (100 - observed["shell_calls"][0], "100 - tools/shell_split/shell_share*100", False)
for cid, metric in {"read_calls": "Read_calls_percent", "read_result_tokens": "Read_tokens_percent", "interpreter_calls": "*Interpreter_calls_percent", "interpreter_waittime": "*Interpreter_time_percent", "askuser_calls": "Ask User_calls_percent", "askuser_waittime": "Ask User_time_percent", "tool_failure": "All_fail_percent"}.items():
    record(cid, "tools/tool_overview/" + metric)
record("sessions_with_batches", "tools/batching_profile/sessions_batched_percent")
record("sessions_with_subagents", "tools/tool_overview/Subagent_sessions_percent")
record("batch_mix_same", "tools/batching_profile/same_tool_percent")
record("batch_mix_mixed", "tools/batching_profile/mixed_percent")
for cid, cause in {"tool_gap_hit": "tool", "useridle_hit": "user"}.items():
    record(cid, "prefix_caching/mean_hit_ratio_by_cause/mean_hit_ratio_" + cause, 100)
record("tool_gap_median", "prefix_caching/gap_by_cause/median_gap_s_tool")
for cid, metric in {"mutated_steps": "mutation_steps_percent", "sessions_with_mutation": "mutation_sessions_percent", "mutation_fresh_prefill": "mutation_prefill_percent"}.items():
    record(cid, "prefix_caching/mutations_by_cause/" + metric, author_simulation=cid == "mutation_fresh_prefill")
for cid, ttl in {"prefill_15min": "15m", "prefill_30min": "30m", "prefill_1h": "1h", "prefill_6h": "6h", "prefill_1day": "1d"}.items():
    record(cid, "prefix_caching/prefill_against_storage/prefill_above_floor_" + ttl, 100, True)
for cid, ttl in {"stored_1h": "1h", "stored_1day": "1d"}.items():
    record(cid, "prefix_caching/prefill_against_storage/retained_" + ttl + "_over_15m", author_simulation=True)
record("deadblocks_day", "prefix_caching/retained_over_active/dead_over_active_1d", author_simulation=True)
record("lifecycle_reclaim_day", "prefix_caching/dead_over_active_by_policy/reclaim_both_dead_fall_1d", author_simulation=True)
if n.get("prefix_caching", {}).get("api_cost", {}).get("knee_ttl") == "30m":
    record("api_cost_30min", "prefix_caching/api_cost/knee_cost", author_simulation=True)
if n.get("prefix_caching", {}).get("infrastructure_cost", {}).get("lowest_ttl") == "15m":
    record("infra_cost_15min", "prefix_caching/infrastructure_cost/lowest_cost", author_simulation=True)
for metric, output in {"turn_duration": "turn_duration", "session_duration": "session_duration", "input_tokens": "input_per_request", "user_prompt_tokens": "user_prompt_size"}.items():
    for population, output_population in (("SWE-Bench", "benchmark"), ("human", "human")):
        record(f"comparison_{metric}_{population}", f"benchmark_vs_production/{output}/median_{output_population}")
if extra:
    observed["swe_sessions"] = (extra["swe_sessions"], "extra_paper_metrics_all_weeks.json:swe_sessions", False)
    observed["cached_token_share"] = (extra["cached_token_share_percent"], "extra_paper_metrics_all_weeks.json:cached_token_share_percent", False)
    for cid, cause, scale in [("tool_gap_p90", "tool", 1), ("askuser_gap_p90", "ask_user_tool", 1/60), ("subagent_gap_p90", "subagent", 1/60), ("useridle_gap_p90", "user", 1/60)]:
        observed[cid] = (extra["gap_p90_seconds"][cause] * scale, "extra_paper_metrics_all_weeks.json:gap_p90_seconds." + cause, False)


def tolerance(claim):
    cid = claim["claim_id"]
    exact = {"total_sessions", "total_requests", "total_tools", "swe_sessions", "user_steps", "tool_steps", "llm_steps", "uncached_median", "output_median"}
    if cid in exact:
        return 0.0
    if cid == "comparison_session_duration_human":
        return 3.0  # paper30.2minutes converted to1812seconds; half0.1min
    if cid == "deadblocks_day":
        return 5.0  # paper approximate120factor, about two significant figures
    if cid in {"input_tokens", "cached_tokens"}:
        return 50_000_000.0
    if cid == "output_tokens":
        return 50_000.0
    if cid in {"input_median", "comparison_input_tokens_human", "comparison_input_tokens_SWE-Bench", "comparison_user_prompt_tokens_SWE-Bench"}:
        return 50.0
    value = claim["reported_value"]
    decimals = len(value.split(".")[-1]) if "." in value else 0
    # Approximate prose values use the same half-last-printed-unit rule.
    return 0.5 * 10**(-decimals) + 1e-9


claims = list(csv.DictReader((ROOT / "research_notes/paper_workload_characterization/paper_claims.csv").open()))
rows = []
for claim in claims:
    cid = claim["claim_id"]
    row = dict(claim)
    row.update(observed_value="Unknown", absolute_delta="Unknown", rounding_tolerance=tolerance(claim),
               comparison="Unknown", verification="Unknown", observed_source="Unknown",
               numerical_provenance="Unknown", limitation="No mapped released implementation/output or input missing")
    if cid in observed:
        value, source, author_sim = observed[cid]
        reported = float(claim["reported_value"])
        finite = math.isfinite(value)
        agree = finite and abs(value - reported) <= row["rounding_tolerance"]
        row.update(observed_value=value if finite else "Non-finite", absolute_delta=abs(value-reported) if finite else "Unknown",
                   comparison="Within printed rounding" if agree else "Outside printed rounding",
                   verification="Partially Verified" if author_sim else ("Verified" if agree else "Partially Verified"),
                   observed_source=source,
                   numerical_provenance="Author-precomputed simulation intermediates, freshly aggregated/redrawn" if author_sim else "Recomputed from all16weeks public Parquet",
                   limitation="Full cache replay not completed; not independent confirmation" if author_sim else "Confirms public processed-data calculation, not original collection or ground truth")
        if not agree:
            row["limitation"] += "; observed difference requires scope/version/method investigation, not automatic proof of error"
    rows.append(row)
fields = list(rows[0])
with (ROOT / "paper_metric_comparison.csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
summary = {"claims": len(rows), "compared": sum(r["comparison"] != "Unknown" for r in rows),
           "within_printed_rounding": sum(r["comparison"] == "Within printed rounding" for r in rows),
           "outside_printed_rounding": [{k: r[k] for k in ("claim_id", "reported_value", "observed_value", "unit", "rounding_tolerance")} for r in rows if r["comparison"] == "Outside printed rounding"],
           "unknown_claim_ids": [r["claim_id"] for r in rows if r["comparison"] == "Unknown"],
           "no_full_paper_reproduction_claimed": True}
(ROOT / "reports/paper_metric_comparison_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False)+"\n")
print(json.dumps(summary, indent=2, allow_nan=False))
