#!/usr/bin/env python3
"""Fetch/verify the pinned processed release; never fetch the108GB JSONL.

Two transfer workers,5GiB disk reserve, validated partial/complete directory
reuse. Shared helper publishes verified files without overwriting existing
payloads and writes each week's manifest last.
"""
import concurrent.futures
import json
from pathlib import Path
import shutil

from pinned_release_download import PinnedRelease, RESERVE, REV

ROOT = Path(__file__).resolve().parents[1]


def main():
    release = PinnedRelease(ROOT, 'processed_download_records.json')
    remaining = release.remaining_bytes()
    release.check_space(remaining)
    print(json.dumps({'revision': REV, 'weeks': len(release.weeks),
                      'remaining_bytes_including_small_metadata': remaining,
                      'free_bytes': shutil.disk_usage(ROOT).free, 'reserve_bytes': RESERVE}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for _ in pool.map(release.complete_week, release.weeks):
            pass


if __name__ == '__main__':
    main()
