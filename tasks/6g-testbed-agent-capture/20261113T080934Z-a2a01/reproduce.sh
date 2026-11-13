#!/usr/bin/env bash
# Use a fresh PRIVATE working copy of this audit directory, never an archive run.
set -euo pipefail
MODE="${1:-full}"
if [[ "$MODE" != full && "$MODE" != --smoke-only ]]; then echo 'Usage: reproduce.sh [--smoke-only]' >&2; exit 2; fi
TASK_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$TASK_ROOT"
for tool in git ip tc unshare python3 readlink; do command -v "$tool" >/dev/null; done
if [[ "$(uname -s)" != Linux ]]; then echo 'BLOCKED: Linux is required.' >&2; exit 2; fi
if [[ -d private/runtime/smoke002 ]]; then
  echo 'Refusing to overwrite evidence: use a fresh private working copy.' >&2; exit 2
fi
mkdir -p private/evidence private/runtime private/analyzed environment/agent reports/per_run logs
export PYTHONDONTWRITEBYTECODE=1
AUDIT_PYTHON="${AUDIT_PYTHON:-$TASK_ROOT/.conda/agent/bin/python}"
if [[ ! -x "$AUDIT_PYTHON" ]]; then
  AUDIT_CONDA_EXE="${AUDIT_CONDA_EXE:-$(command -v conda || true)}"
  if [[ -z "$AUDIT_CONDA_EXE" ]]; then
    echo 'BLOCKED: provide Conda or AUDIT_PYTHON pointing to an independent Python3.12 environment.' >&2; exit 2
  fi
  "$AUDIT_CONDA_EXE" create -y --override-channels -c conda-forge -p "$TASK_ROOT/.conda/agent" python=3.12 pip
fi
"$AUDIT_PYTHON" -m pip install --no-cache-dir --only-binary=:all: -r environment/agent/requirements-runtime.txt
SOURCE="$TASK_ROOT/upstream/6G-Testbed"
SHA=d055fa68ef4de30b93a8a30838ae51fe3e4b561c
if [[ ! -d "$SOURCE/.git" ]]; then
  mkdir -p upstream
  git clone --filter=blob:none https://github.com/5G-MAG/6G-Testbed.git "$SOURCE"
  git -C "$SOURCE" checkout --detach "$SHA"
fi
[[ "$(git -C "$SOURCE" rev-parse HEAD)" == "$SHA" ]]
[[ -z "$(git -C "$SOURCE" status --porcelain)" ]]
# Permissions are exercised only by the child namespace. No sudo, modprobe,
# host networking, shared-interface capture, or shared qdisc mutation is used.
PARENT_NETNS="$(readlink /proc/self/ns/net)"
python3 scripts/run_logged.py --log logs/reproduce_permission_probe --timeout 20 -- \
  unshare --user --map-root-user --net "$AUDIT_PYTHON" scripts/probe_namespace.py --parent-netns "$PARENT_NETNS"
if [[ "$MODE" == full ]]; then
  "$AUDIT_PYTHON" -c 'import json; d=json.load(open("private/evidence/reproduce_namespace_probe.json")); assert d["netem"]=="BLOCKED", "Environment changed: netem is available. This entry reproduces the audited downgraded baseline only; design and validate a new delay contrast instead of claiming the old BLOCKED reason."'
fi
"$AUDIT_PYTHON" scripts/launch_round.py --run-id smoke002 --group smoke
"$AUDIT_PYTHON" scripts/analyze_capture.py --run-dir private/runtime/smoke002 \
  --private-output private/analyzed/smoke002.json --summary-output reports/per_run/smoke002.json
if [[ "$MODE" == --smoke-only ]]; then
  echo 'Smoke-only integration check completed; no A/B comparison or baseline sample estimate generated.'
  exit 0
fi
"$AUDIT_PYTHON" scripts/run_baseline.py --rounds 10
for number in {1..10}; do
  printf -v alias 'A%03d' "$number"
  "$AUDIT_PYTHON" scripts/analyze_capture.py --run-dir "private/runtime/$alias" \
    --private-output "private/analyzed/$alias.json" --summary-output "reports/per_run/$alias.json"
done
"$AUDIT_PYTHON" scripts/summarize.py
echo 'Read REPORT.md, manifest.json and runs.csv. Do not publish private/. RTT contrast remains BLOCKED when the probe reports unavailable netem.'
