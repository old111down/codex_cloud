"""Export only this run's explicit reviewed allowlist; keep originals untouched."""
from __future__ import annotations
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 2_000_000
MANIFEST = Path("reports/publication_manifest.json")
SECRET_PATTERNS = {
    "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "github_token": r"(?<![A-Za-z0-9])(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})(?![A-Za-z0-9])",
    "api_secret": r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}(?![A-Za-z0-9])",
    "signed_url": r"[?&](?:X-Amz-Signature|X-Goog-Signature|Signature|access_token)=[A-Za-z0-9%_-]{12,}",
    "url_credentials": r"https?://[^\s/@:]+:[^\s/@]+@",
    "ssh_public_or_private": r"\bssh-(?:rsa|ed25519) [A-Za-z0-9+/]{40,}",
    "raw_uuid": r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative_path(value):
    """Reject normalization/escape tricks before using an allowlist or run path."""
    if (not isinstance(value, str) or not value or "\\" in value
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
            or any(part in {"", ".", "..", "private", "upstream", ".conda", ".git"} for part in value.split("/"))
            or Path(value).is_absolute() or PureWindowsPath(value).drive):
        raise ValueError("Forbidden relative publication path")
    # A filename is also public metadata. Do not echo a rejected secret-shaped name.
    if any(re.search(pattern, value) for pattern in SECRET_PATTERNS.values()):
        raise ValueError("Publication scan rejected: sensitive path metadata")
    return Path(value)


def absolute_path(value):
    if not isinstance(value, (str, Path)):
        raise ValueError("Publication root must be an absolute local directory")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Publication root must be an absolute local directory")
    return path


def check_existing_path(path, *, directory):
    """Read-only check, including every existing ancestor; never follows links."""
    current = Path(path.anchor)
    for index, component in enumerate(path.parts[1:], 1):
        current /= component
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return False
        if stat.S_ISLNK(mode):
            raise ValueError("Symlink in publication source/destination path")
        is_directory = index < len(path.parts)-1 or directory
        if not (stat.S_ISDIR(mode) if is_directory else stat.S_ISREG(mode)):
            raise ValueError("Unexpected file type in publication path")
    return True


@contextmanager
def directory_fd(path, *, create=False):
    """Anchor all traversal to directories opened with O_NOFOLLOW (Linux)."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            if create:
                try:
                    os.mkdir(component, mode=0o755, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


@contextmanager
def relative_directory_fd(base_fd, parts, *, create=False):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.dup(base_fd)
    try:
        for component in parts:
            if create:
                try:
                    os.mkdir(component, mode=0o755, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def read_source(root, relative):
    try:
        with directory_fd(root) as root_fd, relative_directory_fd(root_fd, relative.parts[:-1]) as parent_fd:
            fd = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd)
            with os.fdopen(fd, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError("Source is not a regular file")
                raw = stream.read(MAX_FILE_BYTES+1)
    except OSError as error:
        raise ValueError(f"Missing or unsafe source: {relative}") from error
    if len(raw) > MAX_FILE_BYTES or b"\0" in raw:
        raise ValueError(f"Unreviewed large/binary file: {relative}")
    try:
        return raw, raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"Non-UTF8 source: {relative}") from error


def read_json(root, relative):
    _, content = read_source(root, relative_path(relative))
    value = json.loads(content)
    if not isinstance(value, dict):
        raise ValueError("Publication metadata must be a JSON object")
    return value


def path_list(value):
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("Reviewed allowlist must be a list of relative path strings")
    return value


def reviewed_paths(root):
    paths = set(path_list(read_json(root, "reports/data_publication_review.json")["safe_file_allowlist"]))
    paths.update(path_list(read_json(root, "research_notes/code_coverage_and_runtime/publication_allowlist.json")["files"]))
    # These are original reports/scripts reviewed by the root and topical reviewers.
    paths.update("""README.md task_report.md reproduction_report.md critical_findings.md metadata.json execution_timeline.md execution_log.md
paper_analysis.md architecture.md session_reconstruction.md label_mechanisms.csv research_opportunities.md related_work_comparison.csv
trace_pcap_alignment.md mvp_experiment_plan.md environment/host_summary.json environment/source_provenance.json environment/archive_tools_versions.json
environment/freeinference/pip-freeze.txt reports/withheld_artifacts.md reports/reproduction_results.csv reports/data_publication_review.json
reports/alignment_evidence.csv reports/independent_paper_review.md reports/independent_paper_review.json
reports/independent_reproduction_review.md reports/independent_reproduction_review.json
reports/independent_full_week_review.md reports/independent_full_week_review.json
reports/independent_alignment_review.md reports/independent_alignment_review.json reports/request_acceptance_review.md
reports/final_archive_review.md reports/final_archive_review.json
research_notes/paper_workload_characterization/notes.md research_notes/paper_workload_characterization/inventory.json research_notes/paper_workload_characterization/paper_claims.csv
research_notes/session_collection_and_labels/notes.md research_notes/trace_pcap_alignment_mvp/notes.md
research_notes/related_agent_measurement_work/notes.md research_notes/related_agent_measurement_work/source_manifest.json
research_notes/code_coverage_and_runtime/publication_allowlist.json
scripts/run_logged.py scripts/review_reproduction_evidence.py scripts/review_complete_week_artifacts.py scripts/build_task_record.py scripts/export_reviewed_archive.py scripts/validate_archive.py
scripts/pinned_release_download.py
scripts/alignment/check_public_gateway_metadata.py scripts/alignment/match_intervals.py scripts/alignment/synthetic_checks.py
logs/alignment_public_http_checks.json logs/alignment_synthetic_checks.json logs/alignment_synthetic_checks.log""".split())
    for optional in ["reports/checkpoints.json", "reports/remote_verification.json", "reports/final_validation.json", "reports/archive_startup_verification.json", "reports/pull_request_receipt.json", "logs/archive_checkpoint.json", "logs/archive_checkpoint.log", "logs/archive_scientific.json", "logs/archive_scientific.log", "logs/archive_final.json", "logs/archive_final.log"]:
        if (root / optional).exists() or (root / optional).is_symlink():
            paths.add(optional)
    return paths


def check_destinations(root, public_root, target, paths):
    if not check_existing_path(public_root, directory=True):
        raise ValueError("Public worktree must already exist")
    if target.is_relative_to(root) or root.is_relative_to(target):
        raise ValueError("Publication source and target trees must not overlap")
    check_existing_path(target, directory=True)
    for relative in [*paths, MANIFEST]:
        check_existing_path(target / relative, directory=False)
    # This is a regenerable local receipt, updated only after successful publication.
    check_existing_path(root / MANIFEST, directory=False)


def write_staged(stage_fd, relative, data):
    with relative_directory_fd(stage_fd, relative.parts[:-1], create=True) as parent_fd:
        fd = os.open(relative.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=parent_fd)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())


def check_leaf(parent_fd, name):
    try:
        mode = os.stat(name, dir_fd=parent_fd, follow_symlinks=False).st_mode
    except FileNotFoundError:
        return
    if not stat.S_ISREG(mode):
        raise ValueError("Unsafe destination leaf")


def replace_staged(stage_fd, target_fd, relative):
    with relative_directory_fd(stage_fd, relative.parts[:-1]) as source_parent, relative_directory_fd(target_fd, relative.parts[:-1], create=True) as target_parent:
        check_leaf(target_parent, relative.name)
        os.replace(relative.name, relative.name, src_dir_fd=source_parent, dst_dir_fd=target_parent)


def update_source_receipt(root, data):
    with directory_fd(root / MANIFEST.parent) as parent_fd:
        check_leaf(parent_fd, MANIFEST.name)
        temporary = ".publication-manifest-" + secrets.token_hex(12)
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=parent_fd)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, MANIFEST.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        finally:
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except FileNotFoundError:
                pass


def publish(root, public_root, target, prepared, manifest_data):
    """Stage the complete validated batch, then replace files; public receipt last.

    Per-file replacement is atomic. A disk/process failure during the publish
    phase can still leave a partially updated batch; this is not a filesystem
    transaction or a concurrent-export locking protocol.
    """
    with directory_fd(public_root) as public_fd:
        stage_name = ".reviewed-export-" + secrets.token_hex(12)
        os.mkdir(stage_name, mode=0o700, dir_fd=public_fd)
        try:
            stage_fd = os.open(stage_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=public_fd)
            try:
                for relative, data in prepared:
                    write_staged(stage_fd, relative, data)
                write_staged(stage_fd, MANIFEST, manifest_data)
                # Recheck immediately before publication; descriptor traversal
                # below also refuses symlink ancestors if a path changes later.
                check_destinations(root, public_root, target, [relative for relative, _ in prepared])
                with directory_fd(target, create=True) as target_fd:
                    for relative, _ in prepared:
                        replace_staged(stage_fd, target_fd, relative)
                    replace_staged(stage_fd, target_fd, MANIFEST)
                update_source_receipt(root, manifest_data)
            finally:
                os.close(stage_fd)
        finally:
            shutil.rmtree(stage_name, dir_fd=public_fd)


def main():
    # Phase 1 is read-only for both trees: validate every input, sanitize in
    # memory, scan the final bytes and public paths, and preflight destinations.
    root = absolute_path(ROOT)
    if not check_existing_path(root, directory=True):
        raise ValueError("Source root must already exist")
    info = read_json(root, "run_info.json")
    public_root = absolute_path(info["public_worktree"])
    target = public_root / relative_path(info["public_run_path"])
    paths = [relative_path(relative) for relative in sorted(reviewed_paths(root))]
    if MANIFEST in paths:
        raise ValueError("Publication manifest is generated, not an allowlisted input")
    entries = []
    issues = []
    prepared = []
    for part in paths:
        rel = part.as_posix()
        raw, content = read_source(root, part)
        changes = []
        if rel == "environment/freeinference/pip-freeze.txt":
            pattern = r"(?m)^packaging @ file://.*$"
            if re.search(pattern, content):
                content = re.sub(pattern, "packaging==26.3", content)
                content = "# Public export: Conda build-machine file URL replaced by observed packaging==26.3; original retained privately.\n" + content
                changes.append("Replaced packaging Conda build-machine file URL with installed version26.3; no experiment change")
        # Actual credential-shaped values, not harmless mentions of header/field names.
        for label, pattern in SECRET_PATTERNS.items():
            if re.search(pattern, content):
                issues.append({"path": rel, "pattern": label})
        out = content.encode()
        if len(out) > MAX_FILE_BYTES:
            raise ValueError(f"Sanitized export exceeds reviewed file-size limit: {rel}")
        prepared.append((part, out))
        entries.append({"path": rel, "source_sha256": sha(raw), "published_sha256": sha(out), "bytes": len(out),
                        "publication_review": "sanitized" if changes else "approved", "transformations": changes,
                        "kind": "Original audit analysis/metadata/script, inspected log, environment declaration or necessary patch"})
    if issues:
        raise ValueError(f"Publication scan rejected: {issues}")
    check_destinations(root, public_root, target, paths)
    # Manifest is an inventory of other files; no impossible self-hash assertion.
    manifest = {"reviewed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "Verified",
                "scope": "Explicit allowlist with topical content review and root pattern/path/size/binary checks; no complete third-party source/data",
                "limitations": ["Pattern scan is not a proof of absence of every possible sensitive datum", "Manifest excludes its own self-hash", "Aggregate methods do not establish original collection correctness"],
                "files": entries, "files_count": len(entries), "bytes": sum(x["bytes"] for x in entries), "scan_issues": issues,
                "withheld": "reports/withheld_artifacts.md"}
    # Phase 2 starts only once the entire batch passed. Original evidence is
    # unchanged; only the regenerable source receipt is updated after success.
    manifest_data = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    publish(root, public_root, target, prepared, manifest_data)
    print(json.dumps({"files": len(entries), "bytes": manifest["bytes"], "scan_issues": issues, "target": str(target)}))
if __name__ == "__main__":
    main()
