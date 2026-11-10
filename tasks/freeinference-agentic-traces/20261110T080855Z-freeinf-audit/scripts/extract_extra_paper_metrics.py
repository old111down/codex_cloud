#!/usr/bin/env python3
"""Aggregate only metrics not serialized by the official figure CLI.

Uses the official gap/token functions and their exact eligibility rules.
Reads selected columns, keeps all IDs/rows private, and emits aggregate values.
"""
import argparse
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from paper.metrics import gaps, tokens
from paper.prefix_caching import reuse
from release import population, reader

p = argparse.ArgumentParser()
p.add_argument("--release", type=Path, required=True)
p.add_argument("--output", type=Path, required=True)
a = p.parse_args()
frames, swe_sessions = [], 0
weeks = reader.week_directories(a.release)
columns = ["session_id", "step", "start_ms", "end_ms", "waited_for", "provider", "prompt_tokens", "completion_tokens", "cache_read_tokens"]
for week in weeks:
    sessions = pq.read_table(week / "sessions.parquet").to_pandas()
    top = sessions[sessions.parent_session_id.isna()]
    swe_sessions += int((top.harness == population.BENCHMARK_HARNESS).sum())
    top_agentic = top[top.harness != population.BENCHMARK_HARNESS]
    requests = pq.read_table(week / "requests.parquet", columns=columns).to_pandas()
    frames.append(requests.merge(top_agentic[["session_id", "user_id"]], on="session_id", how="inner"))
requests = pd.concat(frames, ignore_index=True).sort_values(["session_id", "step"], ignore_index=True)
eligible = requests[tokens.is_cache_reporting(requests) & (requests.prompt_tokens > 0)]
token_denominator = eligible.prompt_tokens.sum() + eligible.completion_tokens.fillna(0).sum()
rows = gaps.gap_rows(requests)
hit_rows = rows.dropna(subset=["hit_ratio"])
bin_summary = {name: {"requests": len(values), "mean": float(values.mean()), "median": float(values.median())}
               for name, label, _, _ in gaps.GAP_BINS
               for values in [hit_rows.hit_ratio[hit_rows.gap_bin == label]] if len(values)}
idle_rows = gaps.idle_gap_rows(requests)
counts = idle_rows.provider.value_counts()
largest = counts[counts >= reuse.MIN_IDLE_GAPS_PER_PROVIDER].index[:reuse.PROVIDERS_DRAWN]
provider_points = {provider: gaps.retention_points(idle_rows[idle_rows.provider == provider]).to_dict(orient="records")
                   for provider in sorted(largest)}
result = {"weeks": len(weeks), "scope": "Top-level human Agentic sessions, benchmark excluded",
          "swe_sessions": swe_sessions, "cache_reporting_requests": len(eligible),
          "cached_token_share_percent": float(100 * eligible.cache_read_tokens.sum() / token_denominator),
          "cached_token_share_denominator": "sum(prompt_tokens + completion_tokens.fillna(0)) on cache-reported prompt>0 human rows",
          "gap_p90_seconds": {key: float(rows.gap_s[rows.cause == label].quantile(0.9)) for key, label in gaps.CAUSE_NAMES.items()},
          "hit_ratio_by_gap_bin": bin_summary,
          "provider_retention_points": provider_points,
          "method": "Official paper.metrics.gaps.gap_rows and paper.metrics.tokens.is_cache_reporting; column-pruned public Parquet",
          "not_a_network_packet_measurement": True}
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
print(json.dumps(result, indent=2, allow_nan=False))
