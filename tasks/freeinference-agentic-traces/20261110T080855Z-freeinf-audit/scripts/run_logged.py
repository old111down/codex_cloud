#!/usr/bin/env python3
"""Run a bounded command without a shell; retain combined output and metadata."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--log', required=True, help='Output prefix relative to caller cwd')
p.add_argument('--cwd', default='.')
p.add_argument('--timeout', type=float, default=600)
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args()
cmd = a.command[1:] if a.command[:1] == ['--'] else a.command
if not cmd:
    p.error('missing command')
prefix = Path(a.log).resolve()
prefix.parent.mkdir(parents=True, exist_ok=True)
meta = {'argv': cmd, 'cwd': str(Path(a.cwd).resolve()),
        'start_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'timeout_seconds': a.timeout,
        'resource_environment': {k: os.environ[k] for k in
          ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'CUDA_VISIBLE_DEVICES') if k in os.environ}}
t = time.monotonic()
with prefix.with_suffix('.log').open('w') as f:
    try:
        proc = subprocess.Popen(cmd, cwd=a.cwd, stdout=f, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            meta.update(exit_code=proc.wait(timeout=a.timeout), timed_out=False)
        except subprocess.TimeoutExpired:
            # Bound children of conda/pip as well as the direct parent process.
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            except ProcessLookupError:
                proc.wait()
            meta.update(exit_code=124, timed_out=True)
    except OSError as e:
        f.write(str(e) + '\n')
        meta.update(exit_code=127, error=str(e), timed_out=False)
meta.update(end_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            elapsed_seconds=time.monotonic()-t)
prefix.with_suffix('.json').write_text(json.dumps(meta, indent=2)+'\n')
print(json.dumps(meta, indent=2))
raise SystemExit(meta['exit_code'])
