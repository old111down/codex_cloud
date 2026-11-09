# Network classification reproducibility audit — public archive

Run `20261109T124228Z-netclass-47956bf`; task branch `codex/network-classification-reproducibility/20261109T124228Z-netclass-47956bf`.

This is a **filtered snapshot of completed research**, not a new execution. Original autonomous T0 is 2026-11-09T11:06:24Z and the three-hour deadline remains14:06:24Z; public archiving began12:37:16Z. Source audit commit: `47956bf6c3eaa0cceee3ac5e525432ca6919b478`. No completed experiment was rerun.

The audit screened37 records /35 in-scope families, verified official associations for30 families, and produced10 detailed packages /574 coverage rows. R1/R2 are scoped component evidence. **No full paper-result R3/R4 reproduction, P4 compilation/simulation or real hardware performance is established.** YaTC full-paper inventory isUnknown; Lens main model isR0/not run.

Start with [final report](reports/final_audit_report.md), [critical findings](reports/critical_findings.md), [timeline](reports/execution_timeline.md), and [next steps](reports/reproduce_next.md). Required tables: [papers](papers.csv), [coverage](coverage_matrix.csv), [actual commands/results](reproduction_results.csv). Per-paper reports are in`papers/`; versions/dependency declarations in`environment/`; original audit harnesses and necessary patches in`scripts/` and`patches/`.

## Publication scope and evidence references

Only original analysis/metadata/scripts, version declarations, necessary small patches and a reviewed subset of logs/derived evidence are public. Full paper PDFs/text, copied third-party source/README/page/API bodies, datasets, row-level predictions, model weights, full environments, cloud identity/status files and original Git/bundle history remain local. **Withheld does not mean missing from the paper or author repository.**

Source-relative paths inside preserved reports/CSV are original artifact IDs, not a claim that every file is public. Resolve them using [source reference index](reports/source_reference_index.md), its[CSV](reports/source_reference_index.csv), and the[export manifest](reports/archive_manifest.csv). Official sources and fixed SHAs are in[official_sources.csv](reports/official_sources.csv). The source table retains Unknown and rejected associations as explicitly labelled catalog records; only verified associations count toward30 families. Original/public hashes distinguish copies from redactions. No scientific metric was changed during export.

Local build paths, emails and infrastructure identifiers are removed only in this public copy. Sanitized pip-freeze records are not blindly portable installation inputs; Conda explicit versions and environment declarations remain. Raw local evidence is retained unchanged.

## Inspection and replay boundaries

Run `python scripts/validate_public_archive.py` to validate this public snapshot. Original internal validators reference retained local evidence and are preserved for provenance, not advertised as passing on the filtered subset. Replaying scientific commands needs the separately acquired official source/data/weights and recorded versions; no code or dataset is downloaded/executed by the public validator.

See[task report](task_report.md),[execution log](execution_log.md) and[metadata](metadata.json). Remote upload/PR status must be set by the archiving owner after checking the remote commit; export generation itself does not establish upload success.

## Persistence and scope

Reviewed checkpoint upload is verified; [PR1](https://github.com/old111down/codex_cloud/pull/1) is open and unmerged. See [publication receipt](reports/archive_publication.md) and [level definitions](reports/reproduction_levels.md). Historical local branch/publication statements describe the source phase; current status is in metadata/PR. Final branch SHA is checked after the last push.
