#!/usr/bin/env python3
"""Exercise the isolated empty-scope fix; upstream must remain pristine.

Set PYTHONPATH to the private patched paper package and original upstream.
"""
import json
from pathlib import Path

from paper import benchmark_vs_production, inputs
from release import reader

root = Path(__file__).resolve().parents[1]
release_path = root / "private/runtime/release_one_week"
release = reader.load(release_path)
result = benchmark_vs_production.draw(
    inputs.Inputs(release=release, release_directory=release_path,
                  simulation_directory=root / "upstream/freeinference_agentic_trace/data/v1/simulation"),
    root / "private/runtime/empty_scope_patch_figures",
)
assert len(result) == 7
assert all(item.get("drawn") == "no: SWE-Bench scope has no requests" for item in result.values())
output = root / "reports/empty_scope_patch_result.json"
output.write_text(json.dumps({"status": "Verified", "scope": "One-week missing-SWE branch only",
                             "not_a_paper_result": True, "section_numbers": result}, indent=2, allow_nan=False)+"\n")
print(json.dumps({"status": "passed", "explicitly_skipped_items": len(result),
                  "original_code_modified": False}, indent=2))
