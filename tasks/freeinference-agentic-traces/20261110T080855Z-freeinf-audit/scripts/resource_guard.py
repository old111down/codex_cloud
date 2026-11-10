#!/usr/bin/env python3
"""Apply an audit-only virtual-address-space limit before executing a command.

An allocation failure under this guard is a resource observation, not evidence
of a defect in the target algorithm. Children inherit the guard.
"""
import argparse
import os
import resource

p = argparse.ArgumentParser()
p.add_argument("--address-space-gib", type=float, default=8)
p.add_argument("command", nargs=argparse.REMAINDER)
a = p.parse_args()
command = a.command[1:] if a.command[:1] == ["--"] else a.command
if not command:
    p.error("missing command")
limit = int(a.address_space_gib * 1024**3)
resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
os.execvp(command[0], command)
