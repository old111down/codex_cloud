#!/usr/bin/env python3
"""Validate conservation/monotonicity of the official real-subset cache replay."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from simulation import cache

root = Path(__file__).resolve().parents[1]
week = "2026-08-30_2026-09-05"
data = root / "private/runtime/small_realdata_release" / week
sim = root / "private/runtime/small_realdata_simulation" / week
tables = {name: pd.read_parquet(sim / f"{name}.parquet") for name in ("tallies", "totals", "cheaper_reads")}
tallies, totals, model = tables["tallies"], tables["totals"], tables["cheaper_reads"]
lists = pq.read_table(data / "requests.parquet", columns=["block_ids"])["block_ids"].combine_chunks()
blocks = lists.values.to_numpy()
input_block_tokens = len(blocks) * cache.BLOCK_TOKENS
first_read_tokens = len(np.unique(blocks)) * cache.BLOCK_TOKENS
assert len(tallies) == 4 * 13
assert ((tallies.hit_tokens + tallies.miss_tokens) == input_block_tokens).all()
none = tallies[(tallies.policy == "ttl_only") & (tallies.ttl == "none")].iloc[0]
assert none.miss_tokens == first_read_tokens
order = [name for name, _ in cache.TTLS]
for policy in cache.POLICIES:
    rows = tallies[tallies.policy == policy].set_index("ttl").loc[order]
    assert (np.diff(rows.hit_tokens) >= 0).all()
baseline = model[model.read_price_cut == 0]
assert np.allclose(baseline.today_prefilled_tokens, baseline.prefilled_tokens)
assert np.allclose(baseline.today_cached_tokens, baseline.cached_tokens)
assert (model.skipped_reductions <= model.reductions).all()
report = {"status": "Verified", "not_a_paper_result": True, "scope": "3audit-selected sessions/42requests only",
          "checks": ["52policy/TTL tallies", "hit+miss conserves input block tokens",
                     "infinite-TTL first reads equal distinct blocks", "hits monotone withTTL for each policy",
                     "cheaper-reads zero-price-cut baseline unchanged", "skipped reductions bounded"],
          "tally_rows": len(tallies), "cheaper_reads_rows": len(model),
          "input_block_tokens": input_block_tokens, "distinct_block_first_read_tokens": first_read_tokens,
          "ttl_infinite_hit_tokens": int(none.hit_tokens), "ttl_infinite_miss_tokens": int(none.miss_tokens),
          "accounting_totals": totals.to_dict(orient="records")}
(root / "reports/small_realdata_simulation_validation.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
print(json.dumps(report, indent=2, allow_nan=False))
