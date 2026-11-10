#!/usr/bin/env python3
"""Compare freshly replayed full-week artifacts to the author's same-week files.

Request-miss keys and rows remain private. Only aggregate model tables and
comparison summaries are emitted; Parquet byte equality is reported separately
from logical numerical equality because writer/library versions may differ.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from release import reader
from simulation import block_reads, cache, cheaper_reads

ROOT = Path(__file__).resolve().parents[1]
SHA = "2b795dbf5eac490a7c081906fdce6cc7a184b7ef"
p = argparse.ArgumentParser()
p.add_argument("--week", required=True, help="Full week directory name, Sunday_Saturday")
p.add_argument("--recomputed", type=Path, required=True, help="Fresh simulation root")
p.add_argument("--reference", type=Path, default=ROOT / "upstream/freeinference_agentic_trace/data/v1/simulation")
p.add_argument("--output", type=Path, required=True, help="Public comparison JSON; a sibling CSV holds aggregate cells")
a = p.parse_args()
KEYS = {"tallies": ["scope", "policy", "ttl"], "totals": ["scope"],
        "request_misses": ["scope", "session_id", "step"],
        "cheaper_reads": ["ttl", "read_price_cut"]}
ATOL, RTOL = 1e-6, 1e-12
source_week = ROOT / "private/data/release" / a.week
reader.check_week(source_week)
files, cells = {}, []
for table, keys in KEYS.items():
    ref_path, fresh_path = a.reference / a.week / f"{table}.parquet", a.recomputed / a.week / f"{table}.parquet"
    ref, fresh = pd.read_parquet(ref_path), pd.read_parquet(fresh_path)
    result = {"reference_rows": len(ref), "recomputed_rows": len(fresh),
              "reference_sha256": reader.file_sha256(ref_path), "recomputed_sha256": reader.file_sha256(fresh_path),
              "reference_bytes": ref_path.stat().st_size, "recomputed_bytes": fresh_path.stat().st_size,
              "columns_equal": set(ref.columns) == set(fresh.columns),
              "reference_duplicate_keys": int(ref.duplicated(keys).sum()),
              "recomputed_duplicate_keys": int(fresh.duplicated(keys).sum()), "metrics": {}}
    result["original_row_key_order_equal"] = ref[keys].equals(fresh[keys])
    def footer(path):
        file = pq.ParquetFile(path)
        metadata = file.metadata
        pandas_metadata = json.loads((file.schema_arrow.metadata or {}).get(b"pandas", b"{}"))
        codecs = sorted({metadata.row_group(i).column(j).compression
                         for i in range(metadata.num_row_groups)
                         for j in range(metadata.row_group(i).num_columns)})
        return {"created_by": metadata.created_by, "parquet_format_version": metadata.format_version,
                "row_groups": metadata.num_row_groups, "compression_codecs": codecs,
                "pandas_version": pandas_metadata.get("pandas_version"),
                "pandas_metadata_creator": pandas_metadata.get("creator")}
    result["reference_footer"] = footer(ref_path)
    result["recomputed_footer"] = footer(fresh_path)
    result["byte_equal"] = result["reference_sha256"] == result["recomputed_sha256"]
    ref, fresh = ref.set_index(keys).sort_index(), fresh.set_index(keys).sort_index()
    result["keysets_equal"] = ref.index.equals(fresh.index)
    valid = result["columns_equal"] and result["keysets_equal"] and result["reference_duplicate_keys"] == result["recomputed_duplicate_keys"] == 0
    if valid:
        for metric in ref.columns:
            x, y = ref[metric].to_numpy(), fresh[metric].to_numpy()
            integer = pd.api.types.is_integer_dtype(x.dtype) and pd.api.types.is_integer_dtype(y.dtype)
            finite = np.isfinite(x) & np.isfinite(y)
            delta = np.abs(y.astype(float)-x.astype(float))
            close = (x == y) if integer else np.isclose(x, y, rtol=RTOL, atol=ATOL, equal_nan=False)
            close &= finite
            result["metrics"][metric] = {"integer_exact_comparison": integer,
                "cells": len(x), "exact_equal_cells": int((x == y).sum()),
                "within_tolerance_cells": int(close.sum()), "nonfinite_cells": int((~finite).sum()),
                "max_absolute_delta": float(delta[finite].max()) if finite.any() else None,
                "max_relative_delta_with_denominator_floor1": float((delta[finite]/np.maximum(np.abs(x[finite]), 1)).max()) if finite.any() else None,
                "status": "Verified" if close.all() else "Failed"}
            if table != "request_misses":
                for key, original, new, difference, ok in zip(ref.index, x, y, delta, close):
                    key = key if isinstance(key, tuple) else (key,)
                    cell = dict(table=table, scope="", policy="", ttl="", read_price_cut="")
                    cell.update(dict(zip(keys, key)))
                    cell.update(metric=metric, reference_value=original.item() if isinstance(original, np.generic) else original,
                                recomputed_value=new.item() if isinstance(new, np.generic) else new,
                                absolute_delta=float(difference), comparison="Verified" if ok else "Failed",
                                rule="integer exact" if integer else f"abs<= {ATOL} + {RTOL}*abs(reference)")
                    cells.append(cell)
        valid = all(item["status"] == "Verified" for item in result["metrics"].values())
    result["status"] = "Verified" if valid else "Failed"
    files[table] = result

ref_sources = json.loads((a.reference / a.week / "sources.json").read_text())
fresh_sources = json.loads((a.recomputed / a.week / "sources.json").read_text())
current = {"manifest.json": reader.file_sha256(source_week / "manifest.json")}
sources_match = ref_sources == fresh_sources and all(value == current for value in fresh_sources.values())
report = {"status": "Verified" if all(f["status"] == "Verified" for f in files.values()) and sources_match else "Failed",
    "week": a.week, "entire_week_no_subsampling": True, "source_commit": SHA,
    "source_manifest_sha256": current["manifest.json"], "input_tables_record_sha256": reader.file_sha256(source_week / "tables.json"),
    "configuration": {"partitions": block_reads.PARTITIONS, "block_tokens": cache.BLOCK_TOKENS,
                      "ttls": [name for name, _ in cache.TTLS], "policies": list(cache.POLICIES),
                      "cheaper_reads_ttls": [name for name, _ in cheaper_reads.COMPARED_TTLS],
                      "price_cut_steps": cheaper_reads.PRICE_CUT_STEPS,
                      "forced_compaction_tokens": cheaper_reads.FORCED_COMPACTION_TOKENS,
                      "processes": 1, "audit_address_space_guard_gib": 8},
    "float_tolerance": {"atol": ATOL, "rtol": RTOL}, "integer_rule": "exact equality",
    "source_manifests_equal_and_current": sources_match, "tables": files,
    "public_aggregate_cells": len(cells), "request_level_rows_emitted": 0,
    "scope_limitation": "Independent replay verification of this complete week only; all16week paper simulation metrics remain Partially Verified unless separately replayed. This is a model replay, not GPU/hardware or provider-cache validation."}
report["serialization_note"] = "Parquet byte equality and logical equality are distinct. Writer/pandas versions and codecs are recorded; unequal bytes alone do not demonstrate different numerical results. Cause of every byte difference was not reverse-engineered."
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
with a.output.with_suffix(".csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(cells[0]))
    writer.writeheader()
    writer.writerows(cells)
print(json.dumps(report, indent=2, allow_nan=False))
raise SystemExit(report["status"] != "Verified")
