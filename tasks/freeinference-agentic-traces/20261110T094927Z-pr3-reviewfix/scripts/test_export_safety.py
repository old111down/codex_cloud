"""End-to-end publication invariants using disposable, synthetic source trees.

No credential-shaped fixture is stored in this file or printed. The only test
marker is assembled at runtime inside TemporaryDirectory and removed on exit.
The fixed required-path declaration supplies fixture boilerplate only; all
security assertions inspect observable filesystem state, not implementation.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[4]
EXPORTER = Path(os.environ.get("AUDIT_EXPORTER_UNDER_TEST", REPOSITORY / "tasks/freeinference-agentic-traces/20261110T080855Z-freeinf-audit/scripts/export_reviewed_archive.py"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(root):
    """Hash contents without allowing failed assertions to disclose fixtures."""
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[relative] = ("symlink", os.readlink(path))
        elif path.is_dir():
            result[relative] = ("directory",)
        else:
            result[relative] = ("file", digest(path.read_bytes()))
    return result


def required_paths():
    tree = ast.parse(EXPORTER.read_text())
    declarations = [node.value for node in ast.walk(tree)
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and "README.md task_report.md" in node.value
                    and "scripts/validate_archive.py" in node.value]
    if len(declarations) != 1:
        raise AssertionError("Expected one fixed reviewed-path declaration")
    return declarations[0].split()


class Fixture:
    def __init__(self, root, existing=True):
        self.root = root
        self.source = root / "source"
        self.public = root / "public"
        self.target = self.public / "tasks/run"
        self.source.mkdir()
        self.public.mkdir()
        for relative in required_paths():
            self.write(relative, "Reviewed audit text.\n")
        self.allow([])
        self.write("reports/publication_manifest.json", '{"previous_source_receipt":true}\n')
        self.write("run_info.json", json.dumps({"public_worktree": str(self.public), "public_run_path": "tasks/run"}))
        if existing:
            (self.target / "reports").mkdir(parents=True)
            (self.target / "README.md").write_text("Previously approved README.\n")
            (self.target / "reports/publication_manifest.json").write_text('{"previous_public_receipt":true}\n')
            (self.target / "keep.txt").write_text("Unrelated approved artifact.\n")

    def write(self, relative, content):
        path = self.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode())

    def allow(self, extras):
        self.write("reports/data_publication_review.json", json.dumps({"safe_file_allowlist": extras}))
        self.write("research_notes/code_coverage_and_runtime/publication_allowlist.json", json.dumps({"files": []}))

    def export(self):
        spec = importlib.util.spec_from_file_location("export_safety_under_test", EXPORTER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.ROOT = self.source
        with contextlib.redirect_stdout(io.StringIO()):
            module.main()


class ExportSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="archive-export-safety-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def rejected_unchanged(self, fixture, expected_message=None):
        before = fingerprint(self.root)
        with self.assertRaises(Exception) as caught:
            fixture.export()
        if expected_message:
            self.assertIn(expected_message, str(caught.exception))
        self.assertTrue(before == fingerprint(self.root), "Rejected export changed source/public files or directories")

    def test_late_credential_preserves_existing_files_and_manifests(self):
        fixture = Fixture(self.root)
        fixture.allow(["aa_good.md", "zz_rejected.md"])
        fixture.write("aa_good.md", "A reviewed new artifact.\n")
        fixture.write("zz_rejected.md", "ghp_" + "A" * 40)
        self.rejected_unchanged(fixture, "Publication scan rejected")

    def test_late_credential_does_not_create_new_target(self):
        fixture = Fixture(self.root, existing=False)
        fixture.allow(["aa_good.md", "zz_rejected.md"])
        fixture.write("aa_good.md", "A reviewed new artifact.\n")
        fixture.write("zz_rejected.md", "ghp_" + "A" * 40)
        self.rejected_unchanged(fixture, "Publication scan rejected")
        self.assertFalse(fixture.target.exists())

    def test_credential_after_underscore_separator_is_rejected(self):
        fixture = Fixture(self.root)
        fixture.allow(["zz_rejected.md"])
        fixture.write("zz_rejected.md", "prefix_" + "ghp_" + "A" * 40)
        self.rejected_unchanged(fixture, "Publication scan rejected")

    def test_credential_shaped_filename_is_rejected_without_echo(self):
        fixture = Fixture(self.root)
        runtime_marker = "ghp_" + "A" * 40
        relative = "zz/prefix_" + runtime_marker + ".md"
        fixture.allow([relative])
        fixture.write(relative, "Reviewed content, unreviewed filename.\n")
        before = fingerprint(self.root)
        with self.assertRaises(Exception) as caught:
            fixture.export()
        self.assertTrue(runtime_marker not in str(caught.exception), "Rejected path echoed a runtime marker")
        self.assertTrue(before == fingerprint(self.root), "Rejected filename changed source/public tree")

    def test_late_missing_source_does_not_publish_earlier_good_file(self):
        fixture = Fixture(self.root)
        fixture.allow(["aa_good.md", "zz_missing.md"])
        fixture.write("aa_good.md", "A reviewed new artifact.\n")
        self.rejected_unchanged(fixture)

    def test_late_traversal_does_not_publish_earlier_good_file(self):
        fixture = Fixture(self.root)
        fixture.allow(["aa_good.md", "zz/../escape.md"])
        fixture.write("aa_good.md", "A reviewed new artifact.\n")
        self.rejected_unchanged(fixture)

    def test_late_oversized_source_preserves_target(self):
        fixture = Fixture(self.root)
        fixture.allow(["zz_large.md"])
        fixture.write("zz_large.md", b"x" * 2_000_001)
        self.rejected_unchanged(fixture)

    def test_late_binary_source_preserves_target(self):
        fixture = Fixture(self.root)
        fixture.allow(["zz_binary.md"])
        fixture.write("zz_binary.md", b"unreviewed\0binary")
        self.rejected_unchanged(fixture)

    def test_late_non_utf8_source_preserves_target(self):
        fixture = Fixture(self.root)
        fixture.allow(["zz_encoding.md"])
        fixture.write("zz_encoding.md", b"not UTF8: \xff")
        self.rejected_unchanged(fixture)

    def test_invalid_allowlist_type_does_not_create_target(self):
        fixture = Fixture(self.root, existing=False)
        fixture.write("reports/data_publication_review.json", '{"safe_file_allowlist":7}')
        self.rejected_unchanged(fixture)

    def test_source_symlink_ancestor_is_rejected_without_writes(self):
        fixture = Fixture(self.root)
        outside = self.root / "outside_source"
        outside.mkdir()
        (outside / "report.md").write_text("Not approved through this link.\n")
        (fixture.source / "zz_link").symlink_to(outside, target_is_directory=True)
        fixture.allow(["zz_link/report.md"])
        self.rejected_unchanged(fixture)

    def test_destination_symlink_ancestor_is_rejected_without_writes(self):
        fixture = Fixture(self.root)
        outside = self.root / "outside_destination"
        outside.mkdir()
        (fixture.target / "scripts").symlink_to(outside, target_is_directory=True)
        self.rejected_unchanged(fixture)

    def test_destination_symlink_leaf_is_not_followed(self):
        fixture = Fixture(self.root)
        outside = self.root / "outside_approved.md"
        outside.write_text("Must stay unchanged.\n")
        (fixture.target / "README.md").unlink()
        (fixture.target / "README.md").symlink_to(outside)
        self.rejected_unchanged(fixture)

    def test_public_run_path_cannot_escape_worktree(self):
        fixture = Fixture(self.root)
        fixture.write("run_info.json", json.dumps({"public_worktree": str(fixture.public), "public_run_path": "../escaped"}))
        self.rejected_unchanged(fixture)

    def test_manifest_path_cannot_be_an_allowlisted_input(self):
        fixture = Fixture(self.root)
        fixture.allow(["reports/publication_manifest.json"])
        self.rejected_unchanged(fixture)

    def test_clean_export_has_matching_hashes_and_preserves_source(self):
        fixture = Fixture(self.root, existing=False)
        fixture.allow(["aa_good.md"])
        fixture.write("aa_good.md", "Original reviewed evidence.\n")
        original = digest((fixture.source / "aa_good.md").read_bytes())
        fixture.export()
        manifest = json.loads((fixture.target / "reports/publication_manifest.json").read_text())
        self.assertEqual(manifest["status"], "Verified")
        self.assertEqual(manifest["files_count"], len(manifest["files"]))
        self.assertFalse(any(item["path"] == "reports/publication_manifest.json" for item in manifest["files"]))
        for item in manifest["files"]:
            self.assertEqual(item["source_sha256"], digest((fixture.source / item["path"]).read_bytes()))
            self.assertEqual(item["published_sha256"], digest((fixture.target / item["path"]).read_bytes()))
        self.assertEqual(original, digest((fixture.source / "aa_good.md").read_bytes()))
        self.assertEqual((fixture.source / "reports/publication_manifest.json").read_bytes(),
                         (fixture.target / "reports/publication_manifest.json").read_bytes())

    def test_sanitization_precedes_scan_without_modifying_source(self):
        fixture = Fixture(self.root, existing=False)
        runtime_marker = "ghp_" + "A" * 40
        relative = "environment/freeinference/pip-freeze.txt"
        fixture.write(relative, "packaging @ file:///private/build/" + runtime_marker + "\n")
        source_hash = digest((fixture.source / relative).read_bytes())
        fixture.export()
        published = (fixture.target / relative).read_text()
        self.assertTrue(runtime_marker not in published, "Removed build URL leaked into export")
        self.assertIn("packaging==26.3", published)
        self.assertEqual(source_hash, digest((fixture.source / relative).read_bytes()))
        manifest = json.loads((fixture.target / "reports/publication_manifest.json").read_text())
        row = next(item for item in manifest["files"] if item["path"] == relative)
        self.assertEqual(row["publication_review"], "sanitized")
        self.assertTrue(bool(row["transformations"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
