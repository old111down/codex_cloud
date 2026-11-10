#!/usr/bin/env python3
"""Reject non-finite numeric summaries even when the plotting CLI exits zero."""
import argparse
import json
import math
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("numbers", type=Path)
p.add_argument("--output", type=Path)
a = p.parse_args()
nonfinite, skipped = [], []


def walk(value, path):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "drawn" and isinstance(item, str) and item.startswith("no:"):
                skipped.append({"path": ".".join(path), "reason": item})
            walk(item, path + [str(key)])
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, path + [str(index)])
    elif isinstance(value, float) and not math.isfinite(value):
        nonfinite.append(".".join(path))


walk(json.loads(a.numbers.read_text()), [])
report = {"input": str(a.numbers), "nonfinite_count": len(nonfinite),
          "nonfinite_paths": nonfinite, "explicit_not_drawn": skipped,
          "status": "Failed" if nonfinite else "Verified",
          "scope": "Numerical output quality only; not proof of paper-result equality"}
if a.output:
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
print(json.dumps(report, indent=2, allow_nan=False))
raise SystemExit(bool(nonfinite))
