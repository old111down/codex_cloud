#!/usr/bin/env python3
"""Run a command and retain Linux wait4 resource usage without system time(1).

ru_maxrss is the kernel's maximum RSS statistic for the waited process/children,
not a time-synchronized sum of all worker RSS and not GPU memory. An outer
run_logged.py process enforces the wall-clock/process-group timeout.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument("--output", type=Path, required=True)
p.add_argument("command", nargs=argparse.REMAINDER)
a = p.parse_args()
command = a.command[1:] if a.command[:1] == ["--"] else a.command
if not command:
    p.error("missing command")
start = time.monotonic()
started_utc = dt.datetime.now(dt.timezone.utc).isoformat()
process = subprocess.Popen(command)
_, wait_status, usage = os.wait4(process.pid, 0)
process.returncode = os.waitstatus_to_exitcode(wait_status)
report = {"argv": command, "start_utc": started_utc,
          "end_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
          "elapsed_seconds": time.monotonic()-start, "exit_code": process.returncode,
          "user_cpu_seconds": usage.ru_utime, "system_cpu_seconds": usage.ru_stime,
          "max_rss_kib_linux_wait4": usage.ru_maxrss,
          "max_rss_semantics": "Linux wait4 maximum RSS statistic, largest resident set; not concurrent sum of parent and worker RSS",
          "major_page_faults": usage.ru_majflt, "minor_page_faults": usage.ru_minflt,
          "voluntary_context_switches": usage.ru_nvcsw, "involuntary_context_switches": usage.ru_nivcsw,
          "input_blocks": usage.ru_inblock, "output_blocks": usage.ru_oublock}
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(report, indent=2)+"\n")
print(json.dumps({"resource_usage": str(a.output), "elapsed_seconds": report["elapsed_seconds"],
                  "max_rss_kib_linux_wait4": usage.ru_maxrss, "exit_code": process.returncode}))
raise SystemExit(process.returncode if process.returncode >= 0 else 128-process.returncode)
