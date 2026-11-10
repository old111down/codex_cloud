"""End-to-end download regression fixtures: no real data or external network.

The original scripts are copied into a temporary, otherwise clean run directory.
A local HTTP server represents a single pinned official release with inert bytes;
only urllib's host transport is redirected. Hashes/manifest binding remain real.
"""
import collections
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import runpy
import shutil
import threading
import urllib.parse
import urllib.request

import pytest

SOURCE = Path(__file__).resolve().parents[2] / '20261110T080855Z-freeinf-audit/scripts'
REV = 'bb26cf72c9c20f2b05f765d88548156a74d3c253'
WEEK = '2026-08-30_2026-09-05'
TABLES = ('sessions.parquet', 'requests.parquet', 'tool_calls.parquet')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


@pytest.fixture
def release_fixture(tmp_path, monkeypatch):
    root = tmp_path / 'audit'
    (root / 'scripts').mkdir(parents=True)
    for name in ('download_selected_week.py', 'download_processed_release.py', 'pinned_release_download.py'):
        if (SOURCE / name).exists():
            shutil.copy2(SOURCE / name, root / 'scripts' / name)
    monkeypatch.syspath_prepend(str(root / 'scripts'))
    payloads = {name: ('inert-fixture-' + name).encode() for name in TABLES}
    payloads['manifest.json'] = json.dumps({'format_version': 1, 'week': WEEK, 'files': {}}).encode()
    binding = {'manifest_sha256': sha(payloads['manifest.json']),
               'files': {name: {'sha256': sha(payloads[name]), 'rows': 2} for name in TABLES}}
    payloads['tables.json'] = json.dumps(binding).encode()
    requests = []
    state = {'payloads': payloads, 'requests': requests, 'root': root, 'binding': binding}

    def metadata():
        siblings = []
        for name, body in payloads.items():
            rel = f'release/{WEEK}/' + (name if name == 'manifest.json' else 'processed/' + name)
            e = {'rfilename': rel, 'size': len(body), 'blobId': git_blob(body)}
            if name in TABLES:
                e['lfs'] = {'sha256': sha(body), 'size': len(body)}
            siblings.append(e)
        return {'sha': REV, 'siblings': siblings}

    state['metadata'] = metadata

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            api = f'/api/datasets/harvardMadsys/freeinference_agentic_trace/revision/{REV}?blobs=true'
            prefix = f'/datasets/harvardMadsys/freeinference_agentic_trace/resolve/{REV}/release/{WEEK}/'
            if self.path == api:
                body = json.dumps(metadata()).encode()
            elif self.path.startswith(prefix):
                name = self.path[len(prefix):].removeprefix('processed/')
                if name not in payloads:
                    self.send_error(404)
                    return
                body = payloads[name]
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    real_urlopen = urllib.request.urlopen

    def transport(request, *args, **kwargs):
        url = request.full_url if isinstance(request, urllib.request.Request) else request
        parsed = urllib.parse.urlsplit(url)
        assert parsed.hostname == 'huggingface.co', 'Test refused non-fixture external network'
        target = f'http://127.0.0.1:{server.server_port}{parsed.path}'
        if parsed.query:
            target += '?' + parsed.query
        return real_urlopen(target, *args, **kwargs)

    monkeypatch.setattr(urllib.request, 'urlopen', transport)
    usage = collections.namedtuple('usage', 'total used free')
    monkeypatch.setattr(shutil, 'disk_usage', lambda _: usage(100 * 1024**3, 10 * 1024**3, 90 * 1024**3))

    def seed_metadata():
        p = root / 'private/evidence/hf_repo.json'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(metadata()))

    def seed_week(where='release', names=None):
        p = root / 'private/data' / where / WEEK
        p.mkdir(parents=True, exist_ok=True)
        for name in names or payloads:
            (p / name).write_bytes(payloads[name])
        return p

    def run(name):
        return runpy.run_path(str(root / 'scripts' / name), run_name='__main__')

    state.update(seed_metadata=seed_metadata, seed_week=seed_week, run=run)
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def assert_complete(f):
    dest = f['root'] / 'private/data/release' / WEEK
    for name, payload in f['payloads'].items():
        assert (dest / name).read_bytes() == payload


def test_selected_bootstraps_pinned_metadata_from_clean_directory(release_fixture):
    f = release_fixture
    f['run']('download_selected_week.py')
    assert json.loads((f['root'] / 'private/evidence/hf_repo.json').read_text())['sha'] == REV
    assert (f['root'] / 'private/data/release' / WEEK / 'requests.parquet').read_bytes() == f['payloads']['requests.parquet']
    assert any('/api/datasets/' in p for p in f['requests'])


def test_full_bootstraps_clean_directory(release_fixture):
    f = release_fixture
    f['run']('download_processed_release.py')
    assert_complete(f)


def test_selected_then_full_and_idempotent_reuse(release_fixture):
    f = release_fixture
    f['seed_metadata']()  # Separates the original partial-directory bug from bootstrap.
    f['run']('download_selected_week.py')
    selected = f['root'] / 'private/data/release' / WEEK / 'requests.parquet'
    inode = selected.stat().st_ino
    f['run']('download_processed_release.py')
    assert_complete(f)
    assert selected.stat().st_ino == inode, 'Existing verified file must be reused'
    before = list(f['requests'])
    f['run']('download_selected_week.py')
    f['run']('download_processed_release.py')
    assert f['requests'] == before, 'Idempotent rerun must verify locally without HTTP transfers'
    assert sum(p.endswith('/processed/requests.parquet') for p in before) == 1


def test_verified_partial_staging_is_reused(release_fixture):
    f = release_fixture
    f['seed_metadata']()
    f['seed_week']('staging', ['requests.parquet'])
    f['run']('download_processed_release.py')
    assert_complete(f)
    assert not any(p.endswith('/processed/requests.parquet') for p in f['requests'])


def test_complete_but_corrupt_destination_is_rejected_and_preserved(release_fixture):
    f = release_fixture
    f['seed_metadata']()
    dest = f['seed_week']()
    corrupted = b'corrupt-existing-data'
    (dest / 'requests.parquet').write_bytes(corrupted)
    with pytest.raises((ValueError, AssertionError), match='(?i)hash|checksum|size|mismatch|differs'):
        f['run']('download_processed_release.py')
    assert (dest / 'requests.parquet').read_bytes() == corrupted
    assert f['requests'] == []


def test_selected_refuses_to_overwrite_mismatching_existing_data(release_fixture):
    f = release_fixture
    f['seed_metadata']()
    dest = f['seed_week'](names=['requests.parquet'])
    corrupted = b'keep-this-unmatched-data'
    (dest / 'requests.parquet').write_bytes(corrupted)
    with pytest.raises((ValueError, AssertionError), match='(?i)hash|checksum|size|mismatch|differs'):
        f['run']('download_selected_week.py')
    assert (dest / 'requests.parquet').read_bytes() == corrupted
    assert f['requests'] == []


def test_corrupt_staging_is_rejected_without_overwrite(release_fixture):
    f = release_fixture
    f['seed_metadata']()
    stage = f['seed_week']('staging', ['requests.parquet'])
    corrupted = b'unmatched-staging-data'
    (stage / 'requests.parquet').write_bytes(corrupted)
    with pytest.raises((ValueError, AssertionError), match='(?i)hash|checksum|size|mismatch|differs'):
        f['run']('download_processed_release.py')
    assert (stage / 'requests.parquet').read_bytes() == corrupted


def test_manifest_binding_is_verified_even_when_every_file_hash_matches(release_fixture):
    f = release_fixture
    f['binding']['manifest_sha256'] = '0' * 64
    f['payloads']['tables.json'] = json.dumps(f['binding']).encode()
    f['seed_metadata']()
    f['seed_week']()
    with pytest.raises((ValueError, AssertionError), match='(?i)manifest'):
        f['run']('download_processed_release.py')


def test_cached_metadata_with_wrong_revision_is_rejected(release_fixture):
    f = release_fixture
    f['seed_metadata']()
    p = f['root'] / 'private/evidence/hf_repo.json'
    data = json.loads(p.read_text())
    data['sha'] = '0' * 40
    p.write_text(json.dumps(data))
    with pytest.raises((ValueError, AssertionError), match='(?i)revision|pinned'):
        f['run']('download_selected_week.py')
    assert f['requests'] == []


def test_inadequate_reserve_fails_before_object_transfer(release_fixture, monkeypatch):
    f = release_fixture
    f['seed_metadata']()
    usage = collections.namedtuple('usage', 'total used free')
    monkeypatch.setattr(shutil, 'disk_usage', lambda _: usage(10 * 1024**3, 9 * 1024**3, 1024**3))
    with pytest.raises((ValueError, AssertionError), match='(?i)reserve|disk|GiB'):
        f['run']('download_processed_release.py')
    assert f['requests'] == []


def test_same_length_non_lfs_metadata_corruption_is_detected(release_fixture):
    f = release_fixture
    f['seed_metadata']()
    dest = f['seed_week']()
    original = (dest / 'tables.json').read_bytes()
    # Keep byte length and JSON syntax: file size alone cannot detect this.
    altered = original.replace(b'"rows": 2', b'"rows": 3', 1)
    assert len(altered) == len(original) and altered != original
    (dest / 'tables.json').write_bytes(altered)
    with pytest.raises((ValueError, AssertionError), match='(?i)blob|SHA1|hash'):
        f['run']('download_processed_release.py')
    assert (dest / 'tables.json').read_bytes() == altered
    assert f['requests'] == []


def test_bad_http_payload_is_not_published(release_fixture):
    f = release_fixture
    f['seed_metadata']()
    body = f['payloads']['requests.parquet']
    f['payloads']['requests.parquet'] = b'X' * len(body)
    with pytest.raises((ValueError, AssertionError), match='(?i)SHA256|hash|mismatch'):
        f['run']('download_selected_week.py')
    dest = f['root'] / 'private/data/release' / WEEK
    assert not (dest / 'requests.parquet').exists()
    assert any(dest.glob('*.partial')), 'Unpublished failed transfer remains private'
