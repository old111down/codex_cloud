#!/usr/bin/env python3
"""Pinned HF transfers: verify existing files, no-clobber publish, private data.

Partial weeks reuse verified payloads via hardlinks without a second large copy.
Only verified files are published, with manifest last. Failed unique .partial
transfers remain private for diagnosis; existing mismatches are never replaced.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import threading
import time
import urllib.request

REV = 'bb26cf72c9c20f2b05f765d88548156a74d3c253'
REPO = 'harvardMadsys/freeinference_agentic_trace'
BASE = f'https://huggingface.co/datasets/{REPO}/resolve/{REV}/'
METADATA_URL = f'https://huggingface.co/api/datasets/{REPO}/revision/{REV}?blobs=true'
RESERVE = 5 * 1024**3
TABLES = ('sessions.parquet', 'requests.parquet', 'tool_calls.parquet')
WEEK_FILES = TABLES + ('tables.json', 'manifest.json')


class DownloadError(ValueError):
    """Mismatching input or insufficient resources; retain existing evidence."""


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        while block := source.read(16 * 1024**2):
            h.update(block)
    return h.hexdigest()


def publish_new(temp, destination):
    """Atomic no-clobber file publication on the same private filesystem."""
    os.link(temp, destination)
    temp.unlink()


class PinnedRelease:
    def __init__(self, root, record_name):
        self.root = Path(root)
        self.lock = threading.Lock()
        self.write_lock = threading.Lock()
        self.record_path = self.root / 'private/evidence' / record_name
        self.record_path.parent.mkdir(parents=True, exist_ok=True)
        self.records = json.loads(self.record_path.read_text()) if self.record_path.exists() else []
        if not isinstance(self.records, list):
            raise DownloadError('Existing transfer history is not a list; preserve for review')
        path = self.root / 'private/evidence/hf_repo.json'
        if not path.exists():
            self.check_space()
            request = urllib.request.Request(METADATA_URL, headers={'User-Agent': 'research-reproducibility-audit'})
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
            self.check_revision(json.loads(raw))
            self.check_space(len(raw))
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.hf-metadata-', delete=False) as target:
                temp = Path(target.name)
                target.write(raw)
            try:
                publish_new(temp, path)
            except FileExistsError:
                temp.unlink()
        self.info = json.loads(path.read_text())
        self.check_revision(self.info)
        self.entries = {entry['rfilename']: entry for entry in self.info['siblings']}
        self.weeks = sorted({m.group(1) for name in self.entries
                             if (m := re.fullmatch(r'release/(\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2})/processed/requests\.parquet', name))})
        if not self.weeks:
            raise DownloadError('Pinned metadata has no processed release weeks')

    @staticmethod
    def check_revision(info):
        if info.get('sha') != REV:
            raise DownloadError('Metadata revision does not match the pinned revision')
        if not isinstance(info.get('siblings'), list):
            raise DownloadError('Pinned metadata lacks the file list')

    def rel(self, week, name):
        if week not in self.weeks or name not in WEEK_FILES:
            raise DownloadError('Unknown pinned release week/file')
        return f'release/{week}/' + (name if name == 'manifest.json' else f'processed/{name}')

    def check_space(self, needed=0):
        if shutil.disk_usage(self.root).free < RESERVE + needed:
            raise DownloadError('Insufficient disk after mandatory 5GiB reserve')

    def verify(self, rel, path):
        entry = self.entries[rel]
        if path.is_symlink() or not path.is_file():
            raise DownloadError(f'Existing {path.name} is not a regular private file')
        size = path.stat().st_size
        if size != entry['size']:
            raise DownloadError(f'Existing {path.name} size mismatch; refusing overwrite')
        h = hashlib.sha256()
        git = hashlib.sha1(b'blob ' + str(size).encode() + b'\0')
        with path.open('rb') as source:
            while block := source.read(16 * 1024**2):
                h.update(block)
                git.update(block)
        if entry.get('lfs'):
            if h.hexdigest() != entry['lfs'].get('sha256'):
                raise DownloadError(f'Existing {path.name} LFS SHA256 mismatch; refusing overwrite')
        elif not entry.get('blobId') or git.hexdigest() != entry['blobId']:
            raise DownloadError(f'Existing {path.name} Git blob SHA1 mismatch; refusing overwrite')
        return h.hexdigest()

    def fetch(self, rel, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        entry = self.entries[rel]
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        tic = time.monotonic()
        if destination.exists() or destination.is_symlink():
            checksum = self.verify(rel, destination)
            status = 'Verified existing file; reused without transfer'
        else:
            self.check_space(entry['size'])
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f'.{destination.name}.download-', suffix='.partial', delete=False) as target:
                temp = Path(target.name)
                count = 0
                request = urllib.request.Request(BASE + rel, headers={'User-Agent': 'research-reproducibility-audit'})
                with urllib.request.urlopen(request, timeout=120) as source:
                    while block := source.read(4 * 1024**2):
                        count += len(block)
                        if count > entry['size']:
                            raise DownloadError('HTTP response exceeds pinned file size; not published')
                        with self.write_lock:
                            self.check_space(len(block))
                            target.write(block)
                            target.flush()
            checksum = self.verify(rel, temp)
            try:
                publish_new(temp, destination)
            except FileExistsError:
                checksum = self.verify(rel, destination)
                temp.unlink()
            status = 'Verified downloaded file'
        record = {'file': rel, 'source_url': BASE + rel, 'revision': REV,
                  'bytes': entry['size'], 'sha256': checksum,
                  'expected_lfs_sha256': entry.get('lfs', {}).get('sha256'),
                  'expected_git_blob_sha1': None if entry.get('lfs') else entry.get('blobId'),
                  'start_utc': started, 'end_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                  'elapsed_seconds': round(time.monotonic() - tic, 3), 'status': status}
        with self.lock:
            self.records.append(record)
            self.record_path.write_text(json.dumps(self.records, indent=2) + '\n')
            print(json.dumps(record), flush=True)
        return checksum

    def verify_week(self, directory, week):
        for name in WEEK_FILES:
            self.verify(self.rel(week, name), directory / name)
        manifest = directory / 'manifest.json'
        tables = json.loads((directory / 'tables.json').read_text())
        if json.loads(manifest.read_text()).get('format_version') != 1:
            raise DownloadError('Unsupported release manifest format')
        if tables.get('manifest_sha256') != sha256(manifest):
            raise DownloadError('tables.json manifest binding mismatch')
        if set(tables.get('files', {})) != set(TABLES):
            raise DownloadError('tables.json file set mismatch')
        for name in TABLES:
            if sha256(directory / name) != tables['files'][name].get('sha256'):
                raise DownloadError(f'{name} tables.json SHA256 mismatch')

    def remaining_bytes(self):
        return sum(self.entries[self.rel(week, name)]['size']
                   for week in self.weeks for name in WEEK_FILES
                   if not (self.root / 'private/data/release' / week / name).exists()
                   and not (self.root / 'private/data/staging' / week / name).exists())

    def complete_week(self, week):
        destination = self.root / 'private/data/release' / week
        staging = self.root / 'private/data/staging' / week
        # Check all existing committed leaves before any object transfer.
        for directory in (destination, staging):
            if directory.is_symlink():
                raise DownloadError('Release/staging directory symlink is not allowed')
            for name in WEEK_FILES:
                path = directory / name
                if path.exists() or path.is_symlink():
                    self.verify(self.rel(week, name), path)
        if all((destination / name).is_file() for name in WEEK_FILES):
            self.verify_week(destination, week)
            print(json.dumps({'week': week, 'status': 'Verified complete week; reused without transfer'}), flush=True)
            return
        staging.mkdir(parents=True, exist_ok=True)
        for name in WEEK_FILES:
            existing, staged = destination / name, staging / name
            if existing.exists() and not staged.exists():
                os.link(existing, staged)
            self.fetch(self.rel(week, name), staged)
        self.verify_week(staging, week)
        destination.mkdir(parents=True, exist_ok=True)
        # File links are no-clobber and the manifest is the last marker.
        for name in WEEK_FILES:
            try:
                os.link(staging / name, destination / name)
            except FileExistsError:
                self.verify(self.rel(week, name), destination / name)
        self.verify_week(destination, week)
        for name in WEEK_FILES:
            (staging / name).unlink()
        if not any(staging.iterdir()):
            staging.rmdir()
        print(json.dumps({'week': week, 'status': 'Verified complete week; manifest published last',
                          'free_bytes': shutil.disk_usage(self.root).free}), flush=True)
