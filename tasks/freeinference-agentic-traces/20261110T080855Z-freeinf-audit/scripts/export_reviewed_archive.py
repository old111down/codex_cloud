"""Export only this run's explicit reviewed allowlist; keep originals untouched."""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def sha(data):
    return hashlib.sha256(data).hexdigest()
def main():
    info = json.loads((ROOT / "run_info.json").read_text())
    target = Path(info["public_worktree"]) / info["public_run_path"]
    target.mkdir(parents=True, exist_ok=True)
    paths = set(json.loads((ROOT / "reports/data_publication_review.json").read_text())["safe_file_allowlist"])
    paths.update(json.loads((ROOT / "research_notes/code_coverage_and_runtime/publication_allowlist.json").read_text())["files"])
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
scripts/alignment/check_public_gateway_metadata.py scripts/alignment/match_intervals.py scripts/alignment/synthetic_checks.py
logs/alignment_public_http_checks.json logs/alignment_synthetic_checks.json logs/alignment_synthetic_checks.log""".split())
    for optional in ["reports/checkpoints.json", "reports/remote_verification.json", "reports/final_validation.json", "reports/archive_startup_verification.json", "reports/pull_request_receipt.json", "logs/archive_checkpoint.json", "logs/archive_checkpoint.log", "logs/archive_scientific.json", "logs/archive_scientific.log", "logs/archive_final.json", "logs/archive_final.log"]:
        if (ROOT / optional).exists():
            paths.add(optional)
    entries = []
    issues = []
    for rel in sorted(paths):
        part = Path(rel)
        if part.is_absolute() or ".." in part.parts or part.parts[0] in {"private", "upstream", ".conda", ".git"}:
            raise ValueError(f"Forbidden allowlist path: {rel}")
        src = ROOT / rel
        if src.is_symlink() or not src.is_file():
            raise ValueError(f"Missing or symlink: {rel}")
        raw = src.read_bytes()
        if len(raw) > 2_000_000 or b"\0" in raw:
            raise ValueError(f"Unreviewed large/binary file: {rel}")
        content = raw.decode("utf-8")
        changes = []
        if rel == "environment/freeinference/pip-freeze.txt":
            pattern = r"(?m)^packaging @ file://.*$"
            if re.search(pattern, content):
                content = re.sub(pattern, "packaging==26.3", content)
                content = "# Public export: Conda build-machine file URL replaced by observed packaging==26.3; original retained privately.\n" + content
                changes.append("Replaced packaging Conda build-machine file URL with installed version26.3; no experiment change")
        # Actual credential-shaped values, not harmless mentions of header/field names.
        for label, pattern in {
            "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            "github_token": r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b",
            "api_secret": r"\bsk-[A-Za-z0-9_-]{20,}\b",
            "signed_url": r"[?&](?:X-Amz-Signature|X-Goog-Signature|Signature|access_token)=[A-Za-z0-9%_-]{12,}",
            "url_credentials": r"https?://[^\s/@:]+:[^\s/@]+@",
            "ssh_public_or_private": r"\bssh-(?:rsa|ed25519) [A-Za-z0-9+/]{40,}",
            "raw_uuid": r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        }.items():
            if re.search(pattern, content):
                issues.append({"path": rel, "pattern": label})
        out = content.encode()
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(out)
        entries.append({"path": rel, "source_sha256": sha(raw), "published_sha256": sha(out), "bytes": len(out),
                        "publication_review": "sanitized" if changes else "approved", "transformations": changes,
                        "kind": "Original audit analysis/metadata/script, inspected log, environment declaration or necessary patch"})
    if issues:
        raise ValueError(f"Publication scan rejected: {issues}")
    # Manifest is an inventory of other files; no impossible self-hash assertion.
    manifest = {"reviewed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "Verified",
                "scope": "Explicit allowlist with topical content review and root pattern/path/size/binary checks; no complete third-party source/data",
                "limitations": ["Pattern scan is not a proof of absence of every possible sensitive datum", "Manifest excludes its own self-hash", "Aggregate methods do not establish original collection correctness"],
                "files": entries, "files_count": len(entries), "bytes": sum(x["bytes"] for x in entries), "scan_issues": issues,
                "withheld": "reports/withheld_artifacts.md"}
    (target / "reports/publication_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "reports/publication_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"files": len(entries), "bytes": manifest["bytes"], "scan_issues": issues, "target": str(target)}))
if __name__ == "__main__":
    main()
