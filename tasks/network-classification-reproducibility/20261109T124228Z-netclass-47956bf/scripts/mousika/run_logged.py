"""Bounded command runner. Arguments: NAME TIMEOUT CWD COMMAND [ARGS...]."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
name, timeout, cwd, *cmd = sys.argv[1:]
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
env = dict(os.environ, OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", PYTHONDONTWRITEBYTECODE="1")
t = time.monotonic()
try:
    proc = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=float(timeout), text=True)
    output, code = proc.stdout, proc.returncode
except subprocess.TimeoutExpired as e:
    output = e.stdout or b""
    if isinstance(output, bytes):
        output = output.decode(errors="replace")
    output += "\nAUDIT_TIMEOUT\n"
    code = 124
end = datetime.datetime.now(datetime.timezone.utc).isoformat()
record = dict(command=cmd, cwd=cwd, start_utc=start, end_utc=end, exit_code=code,
              elapsed_seconds=time.monotonic()-t, timeout_seconds=float(timeout),
              OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
base = ROOT / "logs" / "mousika" / name
base.with_suffix(".json").write_text(json.dumps(record, indent=2)+"\n")
base.with_suffix(".log").write_text(output)
print(json.dumps(record, indent=2))
print(output[-5000:])
sys.exit(code)
