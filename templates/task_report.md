# {{task_name}}

Replace placeholders with evidence-backed values. Leave unsupported facts as `Unknown`; this template contains no execution-success example.

## Identity and scope

| Field | Value |
| --- | --- |
| Task ID | {{task_id}} |
| Task Name | {{task_name}} |
| Task Slug | {{task_slug}} |
| Run ID | {{run_id}} |
| Start Time (UTC) | Unknown |
| End Time (UTC) | Unknown |
| Archive/Export Time (UTC) | Unknown |
| Objective | {{objective}} |
| Related Runs | Unknown |
| Final Status | Unknown |

## Source repositories and versions

| Official source URL | Branch/tag | Full commit SHA | License/access | Evidence |
| --- | --- | --- | --- | --- |

## Runtime environment

Record observed OS, CPU quota, memory limit, disk, GPU, permissions, network/dependency limitations, language/toolchain versions, and environment declarations. Distinguish observed values from paper specifications and inferred requirements.

## Commands executed

Link `execution_log.md` and inspected logs. Include actual argv/cwd, UTC start/end, exit code, input origin/hash, resource bounds, and whether an action was inherited or newly executed. An unrun command is not an execution record.

## Completed work

| Work item | Status | Evidence and scope |
| --- | --- | --- |

## Failed experiments and repairs

| Attempt | Original error/exit status | Repair category and difference | Retest evidence | Remaining limits |
| --- | --- | --- | --- | --- |

## Important findings

Distinguish confirmed source facts, runtime observations, hypotheses, and unverified questions. Each important conclusion should identify its exact source/commit/section/log and use Verified, Partially Verified, Failed, or Unknown.

## Unverified claims

List missing data, code, versions, hardware, permissions, evaluation protocols, and other unresolved prerequisites. Do not infer success from a similar score or a successful installation.

## Artifacts and publication review

List approved artifact paths and hashes. Record sanitization and omitted materials in a publication/exclusion manifest; link to official sources for third-party material. Unknown safety or redistribution permission requires withholding for manual review.

## Final status and next steps

State the result within its verified scope, limitations, reproducibility level if applicable, and concrete next steps. Record the task branch, remote-verification evidence, final commit and PR URL when known. Local commits alone are not upload success; do not automatically merge the PR.
