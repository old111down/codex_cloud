#!/usr/bin/env python3
"""Create an explicitly audit-derived tiny public-data subset for cache smoke.

Select at most three complete top-level sessions, each with3–32 requests and
no spawned children, wholly present in the first request row group. Selection
is deterministic in released session-key order. IDs and rows remain private.
This is not the original week, and its cache statistics cannot reproduce the
paper. It exists to exercise the unchanged full simulator within a small budget.
"""
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from release import reader

root = Path(__file__).resolve().parents[1]
source = root / "private/data/release/2026-08-30_2026-09-05"
output = root / "private/runtime/small_realdata_release" / source.name
output.mkdir(parents=True, exist_ok=True)
reader.check_week(source)
sessions = pq.read_table(source / "sessions.parquet")
requests_file = pq.ParquetFile(source / "requests.parquet")
keys = requests_file.read(columns=["session_id"]).to_pandas()["session_id"]
counts = keys.value_counts()
first_group_keys = set(requests_file.read_row_group(0, columns=["session_id"])["session_id"].to_pylist())
parents = set(x for x in sessions["parent_session_id"].to_pylist() if x is not None)
top_level = set(sessions.filter(pc.is_null(sessions["parent_session_id"]))["session_id"].to_pylist())
eligible = sorted(s for s in first_group_keys & top_level - parents if 3 <= counts[s] <= 32)
# A boundary session may extend to the next row group; exclude it explicitly.
first_counts = requests_file.read_row_group(0, columns=["session_id"]).to_pandas()["session_id"].value_counts()
selected = [s for s in eligible if first_counts[s] == counts[s]][:3]
assert selected, "No complete eligible session in first row group"
chosen = pa.array(selected, type=pa.string())
whole_group = requests_file.read_row_group(0)
requests = whole_group.filter(pc.is_in(whole_group["session_id"], value_set=chosen))
del whole_group
session_subset = sessions.filter(pc.is_in(sessions["session_id"], value_set=chosen))
tools = pq.read_table(source / "tool_calls.parquet")
tools = tools.filter(pc.is_in(tools["session_id"], value_set=chosen))
tables = {"sessions.parquet": session_subset, "requests.parquet": requests,
          "tool_calls.parquet": tools}
original_record = json.loads((source / "tables.json").read_text())
manifest = {"format_version": 1, "week": source.name, "files": {},
            "audit_derived_subset": True, "not_original_paper_population": True,
            "source_manifest_sha256": reader.file_sha256(source / "manifest.json"),
            "source_requests_sha256": original_record["files"]["requests.parquet"]["sha256"],
            "selection": "first3complete top-level childless sessions in first rowgroup with3–32requests, sorted released key"}
(output / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
record = {"manifest_sha256": reader.file_sha256(output / "manifest.json"), "files": {}}
for name, table in tables.items():
    path = output / name
    pq.write_table(table, path)
    record["files"][name] = {"bytes": path.stat().st_size, "sha256": reader.file_sha256(path), "rows": len(table)}
(output / "tables.json").write_text(json.dumps(record, indent=2)+"\n")
reader.check_week(output)
summary = {"audit_derived_subset": True, "not_a_paper_result": True,
           "source_requests_sha256": manifest["source_requests_sha256"],
           "selection": manifest["selection"], "counts": {name: facts["rows"] for name, facts in record["files"].items()},
           "data_bytes": sum(facts["bytes"] for facts in record["files"].values()),
           "source_first_rowgroup_uncompressed_bytes": requests_file.metadata.row_group(0).total_byte_size,
           "subset_block_reads": len(requests["block_ids"].combine_chunks().values),
           "checksums": {name: facts["sha256"] for name, facts in record["files"].items()}}
(root / "reports/small_realdata_subset_provenance.json").write_text(json.dumps(summary, indent=2)+"\n")
print(json.dumps(summary, indent=2))
