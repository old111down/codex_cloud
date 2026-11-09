# Codex Cloud task archive conventions

## Scope and destination

- Archive Codex Cloud research, code analysis, experimental validation, and paper-reproduction results in `https://github.com/old111down/codex_cloud` (`old111down/codex_cloud`).
- This convention applies to the current task and future tasks that explicitly inherit it or read this repository's `AGENTS.md`. It does not claim to change unrelated chats or repositories.
- Follow the current user's task scope and authorization. Archiving an existing task does not restart its execution budget or authorize rerunning completed experiments.

## Append-only task layout

- Use `tasks/<task-slug>/<run_id>/` for each run. A run ID combines its actual UTC creation timestamp and a unique task identifier: `YYYYMMDDTHHMMSSZ-<unique-id>`.
- Every follow-up run gets a new `run_id`; record its relation to earlier runs in metadata and the task report. Never overwrite another run's historical results.
- Work on `codex/<task-slug>/<run_id>`. Preserve existing repository files and task directories.
- Every run must contain `metadata.json`, `README.md`, `task_report.md`, and `execution_log.md`. Add task-specific reports, CSV/JSON tables, environment declarations, scripts, selected logs, and patches as needed.
- Update `indexes/task_index.csv` by appending a row using its existing column order. Do not rewrite previous rows to imply that old results changed.

## Startup and persistence workflow

1. Check that the target repository exists, verify the authenticated GitHub identity and write permission, and inspect remote branches, local status, and existing instructions/files.
2. Clone or safely fetch/update the repository without discarding local changes. If it is genuinely empty, create only the minimal archive bootstrap on `main` before task work.
3. Create the independent task branch from the current `main`. If a name or run directory already exists, inspect it and choose a new unique run ID rather than overwrite it.
4. Save each important stage's report and execution evidence. About every 30 minutes of active work, commit a checkpoint and push the task branch; do not wait idle just to reach a checkpoint time.
5. Before any public push, perform the publication review below. Push only approved artifacts.
6. At completion, generate the common reports and task-specific results, append the index row, commit, push, and open a pull request targeting `main`.
7. Verify that the remote branch resolves to the intended commit before reporting upload success. A local commit or successful-looking command output alone is insufficient.
8. Return the PR URL, branch name, final commit SHA, and any upload/publication limitations. **Do not merge the PR without explicit user confirmation.**

On a recoverable push failure, retain the original error/exit status, inspect authentication, permissions, connectivity, and branch state, then retry a limited number of times. Never force-push over other work. If upload remains blocked, preserve local commits and an approved downloadable package and state that remote upload is incomplete. Never expose credential values while diagnosing authentication.

## Required task record

Record Task ID, Task Name, Start/End Time in UTC, Objective, Source Repositories, Source Commit SHAs, Runtime Environment, Commands Executed, Completed Work, Failed Experiments, Important Findings, Unverified Claims, Artifacts, and Final Status.

- Use `templates/metadata.schema.json` for the machine-readable record and `templates/task_report.md` for the narrative report. Additional fields are allowed.
- Preserve original research/execution times. Distinguish research start, archive/export start, inherited work, and new execution; do not invent a new experiment start to extend a budget.
- `execution_log.md` records actual commands, cwd, UTC times, exit status, input provenance, and links to the selected logs. Preserve failures and separate original-code execution from compatibility repairs or algorithm changes.
- Distinguish **Verified**, **Partially Verified**, **Failed**, and **Unknown**, with evidence and a precise scope. Installation, a smoke test, synthetic inputs, static code, or similar metrics cannot establish full paper-result reproduction.
- Unknown facts remain `Unknown`. Do not label experiments that were not run as successful. Mark hypotheses and unverified claims separately from observations.
- For third-party software, record the official URL, branch/tag, full commit SHA, license/access status, and necessary patches. Keep original source and audit modifications separate.

## Public-repository publication review

This is a public repository. Use an explicit allowlist, inspect every proposed file, and scan both contents and metadata before committing or pushing. If public safety or redistribution permission cannot be established, **withhold the content and record it for manual review**; do not infer permission from a public download URL.

Allowed after review:

- Original Markdown analysis/reports and CSV/JSON research metadata.
- Environment/dependency declarations, source/version/checksum manifests, reproducible original audit scripts, a small selection of inspected logs, and necessary reviewable patches.
- Official links, version SHAs, hashes, and a publication/exclusion manifest explaining omitted evidence.

Do not upload by default:

- API keys, tokens, passwords, SSH/private keys, authentication headers, credential files, or sensitive infrastructure identifiers.
- Sensitive raw PCAP, personally identifying traces, private data, full Conda environments, large datasets/binaries, or model weights without clear public redistribution authorization.
- Complete third-party repositories, proprietary source/SDKs, full paper PDFs/text, copied source/page dumps, or full local audit bundles containing such material. Link to official sources and retain version/hash metadata instead.
- Unreviewed raw logs, package reports, shell history, or Git diffs that can contain credentials, personal paths, third-party source copies, or sensitive data.

Check path traversal, oversized files, accidental nested `.git` directories, binary payloads, local/private URLs, personal identifiers, and secret patterns. Secret-pattern scans are limited evidence, not a safety guarantee. Sanitize only the public export; preserve the original local evidence and record every transformation. Do not silently alter scientific results.

No upstream PRs, public project-setting changes, paid resources, access-control bypasses, or unrelated external messages are authorized merely by this archiving policy.
