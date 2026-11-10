#!/usr/bin/env python3
"""Fetch/revalidate one pinned request table, including clean-root bootstrap.

This minimal transfer probe is not a complete reader-compatible week. Run
download_processed_release.py afterwards to complete all tables privately.
"""
from pathlib import Path

from pinned_release_download import PinnedRelease

ROOT = Path(__file__).resolve().parents[1]
WEEK = '2026-08-30_2026-09-05'


def main():
    release = PinnedRelease(ROOT, 'selected_download_records.json')
    release.fetch(release.rel(WEEK, 'requests.parquet'),
                  ROOT / 'private/data/release' / WEEK / 'requests.parquet')


if __name__ == '__main__':
    main()
