#!/usr/bin/env python3
"""Hand-check the pinned public cache implementation on three synthetic reads.

This is a smoke test of official code, not a reproduction of a paper result.
No trace rows, identifiers, prompts, or tool arguments are used.
Run with PYTHONPATH pointing at the unmodified upstream checkout.
"""
import json

import numpy as np

from simulation import block_reads, cache


def main():
    week = block_reads.WeekRequests(
        arrival_s=np.array([0.0, 5.0, 20.0]),
        completion_s=np.array([1.0, 6.0, 21.0]),
        session=np.array([0, 0, 0]),
        step=np.array([0, 1, 2]),
        output_tokens=np.zeros(3),
        in_scope=np.ones(3, dtype=bool),
        session_ids=np.array(["synthetic", "synthetic", "synthetic"]),
        next_step_arrival_s=np.array([5.0, 20.0, np.inf]),
        session_end_s=np.array([21.0, 21.0, 21.0]),
    )
    reads = cache.sort_reads(np.array([64, 64, 64]), np.arange(3), week)
    short = cache.tally(reads, 1.0, "ttl_only", 30.0)
    medium = cache.tally(reads, 10.0, "ttl_only", 30.0)
    infinite = cache.tally(reads, np.inf, "ttl_only", 30.0)
    # First read is always a miss; subsequent gaps are 4s and 14s.
    assert short["hit_tokens"] == 0 and short["miss_tokens"] == 48
    assert medium["hit_tokens"] == 16 and medium["miss_tokens"] == 32
    assert infinite["hit_tokens"] == 32 and infinite["miss_tokens"] == 16
    assert short["reusable_token_seconds"] == 32.0
    assert medium["reusable_token_seconds"] == 240.0
    assert infinite["dead_token_seconds"] == 144.0
    print(json.dumps({"test": "three_synthetic_reads_one_16_token_block",
                      "status": "passed", "not_a_paper_metric": True,
                      "ttl_1s": short, "ttl_10s": medium,
                      "ttl_infinite": infinite}, indent=2))


if __name__ == "__main__":
    main()
