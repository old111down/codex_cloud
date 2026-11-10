"""Independent cached-LFS hash boundary using only local inert transfer fixtures."""
import pytest

from test_download_workflow import TABLES, WEEK, release_fixture  # fixture is deliberately shared


def test_complete_cache_same_length_lfs_corruption_does_not_pass_presence_or_size(release_fixture):
    fixture = release_fixture
    fixture['seed_metadata']()
    destination = fixture['seed_week']()
    request = destination / 'requests.parquet'
    before = request.read_bytes()
    corrupt = bytes([before[0] ^ 1]) + before[1:]
    assert len(corrupt) == len(before) and corrupt != before
    request.write_bytes(corrupt)
    with pytest.raises(ValueError, match='(?i)SHA256|hash'):
        fixture['run']('download_processed_release.py')
    assert request.read_bytes() == corrupt
    assert fixture['requests'] == [], 'Existing mismatch must fail before any replacement transfer'
    for name in TABLES:
        if name != 'requests.parquet':
            assert (destination / name).read_bytes() == fixture['payloads'][name]


def test_selected_destination_and_partial_staging_reuse_both_valid_payloads(release_fixture):
    fixture = release_fixture
    fixture['seed_metadata']()
    destination = fixture['seed_week'](names=['requests.parquet'])
    staging = fixture['seed_week']('staging', names=['sessions.parquet'])
    request_inode = (destination / 'requests.parquet').stat().st_ino
    session_inode = (staging / 'sessions.parquet').stat().st_ino
    fixture['run']('download_processed_release.py')
    assert (destination / 'requests.parquet').stat().st_ino == request_inode
    assert (destination / 'sessions.parquet').stat().st_ino == session_inode
    assert not any(path.endswith(('/processed/requests.parquet', '/processed/sessions.parquet'))
                   for path in fixture['requests'])
    for name, content in fixture['payloads'].items():
        assert (destination / name).read_bytes() == content
