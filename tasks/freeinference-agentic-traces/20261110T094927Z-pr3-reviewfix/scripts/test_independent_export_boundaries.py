"""Independent metadata-rejection and publication-order checks, synthetic only."""
import importlib.util

import pytest

from test_export_safety import EXPORTER, Fixture, fingerprint


def test_sensitive_filename_is_rejected_without_disclosure_or_tree_mutation(tmp_path):
    fixture = Fixture(tmp_path)
    marker = 'ghp_' + 'B' * 40
    filename = marker + '.md'
    fixture.allow([filename])
    fixture.write(filename, 'Reviewed text with an unsafe public filename.\n')
    before = fingerprint(tmp_path)
    with pytest.raises(ValueError) as caught:
        fixture.export()
    unchanged = before == fingerprint(tmp_path)
    leaked = marker in str(caught.value)
    assert unchanged, 'Rejected metadata changed the disposable source/public trees'
    assert not leaked, 'Error text disclosed the synthetic sensitive filename'


def test_public_manifest_is_last_replacement_before_source_receipt(tmp_path, monkeypatch):
    fixture = Fixture(tmp_path)
    spec = importlib.util.spec_from_file_location('independent_export_order', EXPORTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = fixture.source
    order = []
    replace = module.replace_staged
    receipt = module.update_source_receipt

    def observed_replace(stage_fd, target_fd, relative):
        order.append(('public', relative.as_posix()))
        return replace(stage_fd, target_fd, relative)

    def observed_receipt(root, data):
        order.append(('source', 'reports/publication_manifest.json'))
        return receipt(root, data)

    monkeypatch.setattr(module, 'replace_staged', observed_replace)
    monkeypatch.setattr(module, 'update_source_receipt', observed_receipt)
    module.main()
    assert order[-2:] == [('public', 'reports/publication_manifest.json'),
                          ('source', 'reports/publication_manifest.json')]
    assert all(path != 'reports/publication_manifest.json' for _, path in order[:-2])
    assert (fixture.target / 'reports/publication_manifest.json').read_bytes() == (
        fixture.source / 'reports/publication_manifest.json').read_bytes()
