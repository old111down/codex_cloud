#!/usr/bin/env python3
"""Compare request versus call weighting on the same complete public population."""
import argparse
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from release import population, reader

p = argparse.ArgumentParser()
p.add_argument("--release", type=Path, required=True)
p.add_argument("--output", type=Path, required=True)
a = p.parse_args()
frames = []
weeks = reader.find_weeks(a.release, None)
for week in weeks:
    sessions = pq.read_table(week / "sessions.parquet", columns=["session_id", "parent_session_id", "harness"]).to_pandas()
    selected = sessions[sessions.parent_session_id.isna() & (sessions.harness != population.BENCHMARK_HARNESS)]
    calls = pq.read_table(week / "tool_calls.parquet", columns=["session_id", "step", "category"]).to_pandas()
    frames.append(calls[calls.session_id.isin(selected.session_id)])
calls = pd.concat(frames, ignore_index=True)
grouped = calls.groupby(["session_id", "step"])
width = grouped.size()
categories = grouped.category.nunique()
batched = width > 1
same = categories == 1
request_weighted = float(100 * same[batched].mean())
call_weighted = float(100 * width[batched & same].sum() / width[batched].sum())
result = {"weeks": len(weeks), "scope": "all16weeks, top-level human sessions, benchmark excluded",
          "tool_calls": len(calls), "requests_with_calls": len(width), "batched_requests": int(batched.sum()),
          "same_category_batch_share_percent": {"request_weighted": request_weighted, "call_weighted": call_weighted},
          "single_call_request_share_percent": float(100 * (width == 1).mean()),
          "single_call_call_share_percent": float(100 * width[width == 1].sum() / width.sum()),
          "interpretation": "Two different estimands on identical records; neither weighting is inherently invalid. Paper wording/table and code must identify which is intended.",
          "sources": "paper/metrics/tools.py batching_profile:width.map on calls versus batches.groupby requests"}
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
print(json.dumps(result, indent=2, allow_nan=False))
