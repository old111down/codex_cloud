#!/usr/bin/env python3
"""Export an explicitly reviewed batch only after every candidate passes checks.

No discovery, experiment execution, Git operations, credential access or network.
The reviewer pins each payload's hash in an exact allowlist. The manifest itself
is separately scanned and copied, and its hash is returned in the receipt.
"""
import argparse
import hashlib
import ipaddress
import json
from pathlib import Path, PurePosixPath
import re
import sys

MAX_BYTES = 262144
SUFFIXES = {'.md', '.json', '.csv', '.txt', '.yml', '.yaml', '.py', '.sh', '.log'}
RULES = {
    'uuid': re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'),
    'namespace_inode': re.compile(r'\b(?:net|user|mnt|pid|ipc|uts|cgroup):\[[0-9]+\]'),
    'private_key': re.compile(r'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----'),
    'provider_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})\b'),
    'credential_assignment': re.compile(r'(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|authorization)\s*[:=]\s*[\"\x27]?(?:bearer\s+)?[A-Za-z0-9_+/.-]{16,}'),
    'local_url': re.compile('(?i)(?:' + 'file' + r'://|https?://(?:localhost|[^\s/]+\.(?:internal|local))\b)'),
}
IPV4 = re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative(value):
    p = PurePosixPath(value)
    if not value or p.is_absolute() or '..' in p.parts or any(x in {'.git', '__pycache__', 'private', 'upstream'} for x in p.parts):
        raise ValueError('unsafe export path: ' + value)
    if p.suffix not in SUFFIXES:
        raise ValueError('unapproved file type: ' + value)
    return p


def scan(name, data):
    relative(name)
    if len(data) > MAX_BYTES or b'\0' in data:
        raise ValueError('oversized or binary candidate: ' + name)
    content = data.decode('utf-8')
    for label, pattern in RULES.items():
        if pattern.search(content):
            raise ValueError('manual review required: ' + label + ' in ' + name)
    for match in IPV4.finditer(content):
        try:
            address = ipaddress.ip_address(match.group())
        except ValueError:
            continue
        # This audit explicitly reviews fixed synthetic loopback configuration.
        if str(address) not in {'127.0.0.1', '0.0.0.0'}:
            raise ValueError('manual review required: IPv4 in ' + name)
    # Literal IPv6 loopback is synthetic; all other IPv6 address-like runs fail.
    for token in re.findall(r'(?<![A-Za-z0-9_])[0-9A-Fa-f:]{4,}(?![A-Za-z0-9_])', content):
        if ':' not in token:
            continue
        try:
            address = ipaddress.ip_address(token)
        except ValueError:
            continue
        if str(address) != '::1':
            raise ValueError('manual review required: IPv6 in ' + name)
    if name.endswith('.json'):
        json.loads(content)
    return {'path': name, 'bytes': len(data), 'sha256': digest(data), 'scan': 'PASS'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', required=True, type=Path)
    p.add_argument('--destination', required=True, type=Path)
    p.add_argument('--write', action='store_true')
    args = p.parse_args()
    stage = args.stage.resolve(strict=True)
    manifest_path = stage / 'allowedfiles.json'
    manifest_data = manifest_path.read_bytes()
    manifest = json.loads(manifest_data)
    expected_destination = Path(manifest['destination']).resolve()
    destination = args.destination.resolve()
    if destination != expected_destination or destination == stage or stage in destination.parents:
        raise ValueError('destination does not match reviewed run')
    if manifest['review_status'] != 'approved':
        raise ValueError('batch is not approved')
    buffered = []
    receipt = []
    names = set()
    for entry in manifest['files']:
        name = entry['path']; relative(name)
        if name == 'allowedfiles.json' or name in names:
            raise ValueError('duplicate or recursive manifest entry')
        names.add(name)
        path = stage.joinpath(*PurePosixPath(name).parts)
        if any(parent.is_symlink() for parent in (path, *path.parents) if parent == stage or stage in parent.parents):
            raise ValueError('source contains a symlink')
        if path.is_symlink() or path.resolve().parent != stage.joinpath(*PurePosixPath(name).parent.parts).resolve() or stage not in path.resolve().parents:
            raise ValueError('symlink or escaping path')
        data = path.read_bytes()
        if entry['review'] not in {'approved', 'sanitized'} or entry.get('content_inspected') is not True:
            raise ValueError('missing content inspection: ' + name)
        if digest(data) != entry['sha256'] or len(data) != entry['bytes']:
            raise ValueError('candidate changed after review: ' + name)
        receipt.append(scan(name, data)); buffered.append((name, data, entry.get('executable', False)))
    receipt.append(scan('allowedfiles.json', manifest_data))
    buffered.append(('allowedfiles.json', manifest_data, False))
    # Complete all destination checks before the first public mkdir/write.
    for name, data, executable in buffered:
        target = destination / name
        if any(parent.is_symlink() for parent in (target, *target.parents)):
            raise ValueError('destination contains a symlink')
        if any(parent.exists() and not parent.is_dir() for parent in target.parents):
            raise ValueError('destination ancestor is not a directory')
        if target.exists() and target.read_bytes() != data:
            if not manifest.get('allow_refresh_same_run', False):
                raise FileExistsError('refusing to overwrite different evidence')
    if args.write:
        for name, data, executable in buffered:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o755 if executable else 0o644)
    print(json.dumps({'status': 'PASS', 'mode': 'write' if args.write else 'scan-only', 'files': receipt}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        raise SystemExit(1)
