#!/usr/bin/env python3
"""Select the smallest complete verified week without subsampling any rows."""
import json
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

root = Path(__file__).resolve().parents[1]
facts = []
for directory in sorted((root / "private/data/release").iterdir()):
    path = directory / "requests.parquet"
    if not path.exists():
        continue
    parquet = pq.ParquetFile(path)
    maximum, total = 0, 0
    for index in range(parquet.metadata.num_row_groups):
        group = parquet.metadata.row_group(index)
        for column_index in range(group.num_columns):
            column = group.column(column_index)
            if column.path_in_schema.startswith("block_ids."):
                maximum = max(maximum, column.total_uncompressed_size)
                total += column.total_uncompressed_size
    sessions = pq.read_table(directory / "sessions.parquet", columns=["harness", "parent_session_id"]).to_pandas()
    top = sessions[sessions.parent_session_id.isna()]
    facts.append({"week": directory.name, "requests_bytes": path.stat().st_size,
                  "request_rows": parquet.metadata.num_rows, "request_row_groups": parquet.metadata.num_row_groups,
                  "block_ids_uncompressed_bytes": total, "max_rowgroup_block_ids_uncompressed_bytes": maximum,
                  "all_session_rows": len(sessions), "top_level_sessions": len(top),
                  "child_sessions": len(sessions)-len(top), "top_level_harness_counts": dict(Counter(top.harness))})
facts.sort(key=lambda item: item["requests_bytes"])
assert len(facts) == 16
report = {"selection_rule": "Minimum complete public requests.parquet compressed bytes among all16 verified weeks; no row/session subsampling",
          "selected_week": facts[0]["week"], "weeks_by_size": facts,
          "scope_note": "Official simulator selects top-level Agentic and SWE-Bench separately; child rows remain input but excluded from standalone scope counts"}
mixed = [item for item in facts if item["top_level_harness_counts"].get("eval:swe-bench", 0) > 0
         and item["top_level_harness_counts"].get("eval:swe-bench", 0) < item["top_level_sessions"]]
report["selected_smallest_mixed_scope_week"] = mixed[0]["week"]
report["mixed_scope_selection_rule"] = "Minimum complete requests.parquet compressed bytes among verified weeks containing both top-level human and SWE-Bench sessions"
(root / "reports/full_week_replay_selection.json").write_text(json.dumps(report, indent=2)+"\n")
print(json.dumps({"selected": facts[0], "next_two": facts[1:3]}, indent=2))
