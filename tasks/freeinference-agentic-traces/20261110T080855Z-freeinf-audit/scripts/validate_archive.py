"""Validate the published text snapshot and evidence links, not paper accuracy."""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit
import jsonschema

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--finished", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.run_directory.resolve()
    data = json.loads((root / "metadata.json").read_text())
    schema = json.loads(args.schema.read_text())
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(data)
    start = datetime.fromisoformat(data["start_time_utc"].replace("Z", "+00:00"))
    deadline = datetime.fromisoformat(data["deadline_utc"].replace("Z", "+00:00"))
    assert start.utcoffset().total_seconds() == 0
    if args.finished:
        assert data["end_time_utc"] and data["pull_request_url"]
    if data["end_time_utc"]:
        end = datetime.fromisoformat(data["end_time_utc"].replace("Z", "+00:00"))
        assert start <= end <= deadline and end.utcoffset().total_seconds() == 0
    required = "paper_analysis.md architecture.md data_dictionary.csv session_reconstruction.md paper_code_coverage.csv reproduction_report.md trace_pcap_alignment.md mvp_experiment_plan.md research_opportunities.md execution_timeline.md README.md metadata.json task_report.md execution_log.md".split()
    assert all((root / p).is_file() for p in required)
    manifest = json.loads((root / "reports/publication_manifest.json").read_text())
    expected = {x["path"]: x for x in manifest["files"]}
    csv_counts = {}; counts = {"json": 0, "python_syntax": 0, "markdown": 0}; total = 0
    for path in root.rglob("*"):
        assert not path.is_symlink(), str(path)
        if not path.is_file():
            continue
        total += 1
        rel = path.relative_to(root).as_posix()
        assert path.suffix in {".md", ".csv", ".json", ".txt", ".yml", ".py", ".log", ".patch"}
        raw = path.read_bytes(); text = raw.decode("utf-8")
        assert b"\x00" not in raw and len(raw) < 2_000_000
        if rel != "reports/publication_manifest.json":
            assert rel in expected, f"Not explicitly allowed: {rel}"
            assert hashlib.sha256(raw).hexdigest() == expected[rel]["published_sha256"], rel
        if path.suffix == ".json":
            # Strictly reject the Python JSON extension NaN/Infinity.
            json.loads(text, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            counts["json"] += 1
        if path.suffix == ".py":
            ast.parse(text, str(path)); counts["python_syntax"] += 1
        if path.suffix == ".csv":
            rows = list(csv.reader(text.splitlines()))
            assert rows and all(len(x) == len(rows[0]) for x in rows)
            csv_counts[rel] = len(rows) - 1
        if path.suffix == ".md":
            counts["markdown"] += 1
            for dest in re.findall(r"\]\(([^)]+)\)", text):
                dest = dest.split(' "')[0].strip("<>")
                u = urlsplit(dest)
                if u.scheme or dest.startswith("#"):
                    continue
                assert (path.parent / unquote(u.path)).exists(), (rel, dest)
    assert total == len(expected) + 1
    assert csv_counts["data_dictionary.csv"] == 68
    assert csv_counts["paper_code_coverage.csv"] == 58
    assert csv_counts["paper_metric_comparison.csv"] == 73
    result = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "status": "Verified",
              "scope": "Public snapshot syntax/schema/UTC/files/relative links/manifest hashes only; not scientific validation or remote upload proof",
              "files": total, "manifest_entries": len(expected), "counts": counts, "csv_rows": csv_counts,
              "required_artifacts_present": len(required), "strict_json": True, "relative_links": "all present",
              "publication_hashes": "all match", "finished_record_required": args.finished}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
