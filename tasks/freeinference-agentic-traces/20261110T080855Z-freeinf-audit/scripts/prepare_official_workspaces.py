#!/usr/bin/env python3
"""Prepare private original/patch workspaces without altering the pinned clone.

Data, author simulation files and generated figures are linked externally.
The only copied third-party material is source/configuration, kept private.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA = "2b795dbf5eac490a7c081906fdce6cc7a184b7ef"
p = argparse.ArgumentParser()
p.add_argument("--empty-scope-patch", action="store_true")
a = p.parse_args()
source = ROOT / "upstream/freeinference_agentic_trace"
runtime = ROOT / "private/runtime"
work = runtime / "readme_workspace"
sha = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
assert sha == EXPECTED_SHA
work.mkdir(parents=True, exist_ok=True)
copied = []
for package in ("release", "paper", "simulation", "export"):
    shutil.copytree(source / package, work / package, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    copied.extend(path.relative_to(source) for path in (source / package).rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc")
for name in ("Makefile", "pyproject.toml", "README.md"):
    shutil.copy2(source / name, work / name)
    copied.append(Path(name))
assert all((work / name).read_bytes() == (source / name).read_bytes() for name in copied)
(work / "data/v1").mkdir(parents=True, exist_ok=True)
(work / "figures").mkdir(exist_ok=True)
(runtime / "figures").mkdir(exist_ok=True)
links = [(ROOT / "private/data/release", work / "data/v1/release"),
         (source / "data/v1/simulation", work / "data/v1/simulation"),
         (runtime / "figures", work / "figures/v1")]
for target, link in links:
    if link.is_symlink():
        assert link.resolve() == target.resolve()
    elif link.exists():
        raise RuntimeError(f"Refusing to replace existing non-symlink: {link}")
    else:
        link.symlink_to(target, target_is_directory=True)
report = {"copied_original_source_files_verified_byte_equal": len(copied), "patched_files": 0,
          "source_commit": sha, "data_and_output_paths": "external symlinks under private/runtime; no upstream changes",
          "purpose": "Controlled original Make figures target with independent Conda PYTHON override"}
(ROOT / "reports/readme_workspace_provenance.json").write_text(json.dumps(report, indent=2)+"\n")
if a.empty_scope_patch:
    compat = runtime / "empty_scope_patch_source"
    shutil.copytree(source / "paper", compat / "paper", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    subprocess.run(["patch", "--batch", "-p1", "--directory", str(compat),
                    "--input", str(ROOT / "patches/0001-report-empty-benchmark-scope.patch")], check=True)
print(json.dumps(report, indent=2))
