# Codex Cloud task archive

This repository is the persistent result archive for Codex Cloud research, code analysis, experimental validation, and paper reproduction: [old111down/codex_cloud](https://github.com/old111down/codex_cloud).

The convention applies to the current task and future tasks that explicitly inherit it or read [AGENTS.md](AGENTS.md). It is not a claim of a global setting for unrelated chats or repositories.

## Layout

```text
AGENTS.md
README.md
tasks/
  <task-slug>/
    <UTC-run-id>/
      metadata.json
      README.md
      task_report.md
      execution_log.md
      environment/
      scripts/
      logs/
      reports/
      patches/
indexes/
  task_index.csv
templates/
  task_report.md
  metadata.schema.json
```

Task-specific tables and other approved files belong in the run directory. [The task index](indexes/task_index.csv) is append-only. Each later investigation gets a new run ID and explicitly links its predecessor; existing task history is preserved.

## Automatic archiving convention

At startup, verify repository availability, GitHub identity/write access, branches, workspace state, and existing instructions. Use a new `codex/<task-slug>/<run_id>` branch. A run ID uses its actual UTC creation time plus a unique task identifier. Archive/export time does not replace an existing research task's start time or restart its budget.

Save important stages, and about every 30 minutes of active work commit and push a reviewed checkpoint. At completion, generate `task_report.md`, `execution_log.md`, and `metadata.json`, append the index row, push, and open a PR to `main`. Confirm the remote commit before saying upload succeeded. PRs are **not automatically merged**. An empty repository may receive the minimal bootstrap first; task results are proposed through their own branches.

On upload failure, record the actual error, make a limited retry after diagnosis, and retain local commits/an approved downloadable package if remote upload remains blocked. Never force-push over another task.

## Evidence and status

Every task records its identity, objective, actual UTC start/end, source repositories/full SHAs, runtime, executed commands, completed work, failed experiments, important findings, unverified claims, artifacts, and final status. Use **Verified / Partially Verified / Failed / Unknown** with evidence and a stated scope. A code demo, dependency installation, static inspection, or synthetic test does not establish paper-result reproduction.

Use the [report template](templates/task_report.md) and [metadata JSON Schema](templates/metadata.schema.json). The schema permits task-specific extensions and allows an unknown end time while a run is in progress; it does not validate scientific conclusions.

## Public export policy

Upload only reviewed original reports, CSV/JSON metadata, environment declarations, reproducible audit scripts, a small inspected log selection, and necessary patches. Preserve third-party provenance using official URLs, commit SHAs, licenses/access notes, and checksums.

Do not default-upload credentials, sensitive PCAP/traces, personal data, full environments, large datasets/binaries, unapproved weights, proprietary software, complete third-party source repositories, full paper/page/source dumps, or local bundles containing those materials. Unknown publication safety means **withhold and record for manual review**, not assume permission. Public accessibility alone is not redistribution authorization.

Inspect file contents and metadata, scan for secrets/identifiers, and retain a publication manifest that distinguishes copied, sanitized, and withheld files. Keep original local evidence intact. See [AGENTS.md](AGENTS.md) for the full workflow and restrictions.
