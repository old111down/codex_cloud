# 5G-MAG Agent/A2A capture and alignment audit

## Identity and scope

| Field | Value |
| --- | --- |
| Task ID | 6g-a2a-audit-20261113 |
| Task Name | 5G-MAG Agent/A2A capture and alignment audit |
| Task Slug | 6g-testbed-agent-capture |
| Run ID | 20261113T080934Z-a2a01 |
| Start Time (UTC) | 2026-11-13T07:55:41Z |
| End Time (UTC) | 2026-11-13T08:30:42Z |
| Archive Start (UTC) | 2026-11-13T08:09:34Z |
| Checkpoint generated (UTC) | 2026-11-13T08:26:38.281783+00:00 |
| Local archive sealed (UTC) | 2026-11-13T08:30:42Z |
| Hard deadline (UTC) | 2026-11-13T10:55:41Z |
| Objective | Official local Agent/A2A function, application-to-PCAP alignment, isolated RTT contrast |
| Related Runs | No prior experiment run asserted; S4aP260148 is historical provenance |
| Final Status | Partially Verified |

## Source repositories and versions

| Official source URL | Branch/tag | Full commit SHA | License/access | Evidence |
| --- | --- | --- | --- | --- |
| https://github.com/5G-MAG/6G-Testbed | detached paper review revision | d055fa68ef4de30b93a8a30838ae51fe3e4b561c | 5G-MAG v1.0 files; conflicting netemu package declaration; full source withheld | manifest.json; reports/source_provenance.json |

Fetched main was `7231ae8e5670b67564cf28d397c2820d9403ecdc`; it was not the executed revision. The paper is https://arxiv.org/html/2611.07250v1. Historical S4aP260148 ZIP returned HTTP 403, so workbook cells were not independently verified. Original source remained pristine; no upstream patch was applied.

## Runtime environment

Debian 13.6, CPU quota 4 cores, memory limit 16 GiB, independent Conda Python 3.12.16. No GPU/model invocation. Scoped dependencies and source PYTHONPATH satisfy the real orchestrator import chain without running other scenarios. See environment/README.md and environment/agent/versions.json. Parent AF_PACKET was unavailable; owned user/network namespace loopback capture passed. The isolated netem operation failed with unknown qdisc kind; no shared interface/qdisc mutation or host module workaround occurred. reports/permission_summary.json preserves the exact inner exit and distinction from outer probe exit 0.

## Commands executed

[execution_log.md](execution_log.md) retains selected actual argv, cwd, UTC start/end (Unknown for help logs without absolute timestamps), exit status and provenance. Synthetic input uses the published generator and task hash, while literal request/response remain private. Bounded launch timeouts were 110 seconds per round; official application subprocess timeout is 75 seconds. A001–A010 were actual separate executions, not repetitions inferred from packets.

## Completed work

| Work item | Status | Evidence and scope |
| --- | --- | --- |
| Official A2A local single-task | Verified / PASS | Ten separated original-code rounds; runs.csv, reports/summary.json |
| Log-to-PCAP alignment | Verified / PASS | Ten unique HTTP/1.1 task connections; ten observed negative controls rejected; reports/independent_outcome_review.json |
| Collector integrity | Verified | 400 records read; all hashes/counts/directions and drop/drain checks; reports/collector_baseline_review.json |
| Smoke-only reproduce entry | Verified | logs/reproduce_smoke_integration.json exit 0; fresh private output, reused environment/source; excluded from baseline n |
| Checkpoint publication / PR | Verified | reports/archive_checkpoint.json; local/remote checkpoint SHA agree; PR 4 targets main, unmerged |
| RTT intervention contrast | Unknown / BLOCKED | reports/permission_summary.json; B attempts 0 |

## Failed experiments and repairs

| Attempt | Original error/exit status | Repair category and difference | Retest evidence | Remaining limits |
| --- | --- | --- | --- | --- |
| smoke001 | outer exit 0, invalid parent-namespace argument; not accepted | audit wrapper repair; launcher reads actual parent namespace | smoke002.json and reports/per_run/smoke002.json | raw failed attempt retained privately; public argv value sanitized |
| first baseline gate | exit 1 before any A round; incorrect summary key | audit schema gate repaired to match_status | logs/baseline_gate_schema_error.* and baseline_batch.* | failure retained; no round fabricated |
| initial CLI help | missing colorlog/SDK server dependencies; exit 1 | scoped dependency install and http-server extra | entrypoint JSONs and reports/entrypoint_audit.md | not full historical lock reproduction |
| netem delay probe | inner tc exit 2: Specified qdisc kind is unknown | authorized downgrade; no host change | reports/permission_summary.json | no B group or network-delay effect |

## Important findings

Each claim below has evidence; static facts and runtime observations remain distinct.

- **Verified runtime:** Official deterministic single-task A2A succeeds in ten baseline rounds, with one controlled synthetic prompt, zero retries and a fresh server/session each round. Evidence: runs.csv, environment/scenario_snapshot.json, reports/summary.json.
- **Verified runtime:** Every task has one unique connection match and one excluded TCP connect/close negative control. Each selected keepalive connection contains Agent Card GET and task POST; connection byte totals are not exact task bytes. Evidence: reports/per_run/*.json, reports/independent_outcome_review.json.
- **Verified runtime:** APP median 7.548451 ms; same-observer SYN-to-SYNACK median 0.111419 ms; neither establishes an RTT intervention effect. Evidence: reports/summary.json and reports/independent_outcome_review.md.
- **Verified source/provenance:** d055 is the executed and paper implementation-review revision; S4aP260148 is a separate historical report. Evidence: manifest.json, reports/source_provenance.json, reports/paper_evidence.md.
- **Verified runtime boundary:** External AF_PACKET collector passed declared checks; upstream CaptureController was not run. Nanosecond timestamp representation, observed clock-anchor widths and the 50 ms matching tolerance are distinct quantities. Evidence: manifest.json, reports/collector_baseline_review.json, reports/alignment_method.md.

## Unverified claims

RTT intervention, nominal 2d calibration, socket RTT, historical workbook numerical reproduction, TLS/H2/H3/concurrent task assignment, WAN/multihop, desktop Agent behavior and per-packet SDK/tool semantics remain unverified. These are listed as limits, not inferred successes. No classifier, AR/XR, video, P4, paid inference or GPU experiment was run.

## Artifacts and publication review

[allowedfiles.json](allowedfiles.json) is the exact reviewed export set with pinned hashes and sizes. See reports/publication_review.json for scans and original/published transformation hashes; reports/withheld.md excludes raw PCAP, application database/records/logs, real IDs/inodes, full official repositories and full paper/page dumps. Original evidence is preserved privately. requirements-runtime.txt normalizes only the local packaging build reference to the observed 26.3 release pin. The convenience environment/agent/pip-freeze.txt is byte-identical to that sanitized declaration; the original freeze remains private. Public-artifact publication review is Verified within this exact allowlist; the scientific verdict remains Partially Verified.

## Final status and next steps

**Partially Verified:** three separate verdicts are **PASS / PASS / BLOCKED**, scoped as above. The local archive was sealed at `2026-11-13T08:30:42Z` within the original budget. Archive start did not reset T0. Root verified local/remote checkpoint SHA `815c30ea4464abc8aac5447ad8ede4469effa8be` and created [PR 4](https://github.com/old111down/codex_cloud/pull/4) targeting main; it remains unmerged. This recorded SHA binds that checkpoint only. Root will verify the subsequent closure commit externally in the PR description and final reply, avoiding self-reference. The branch is `codex/6g-testbed-agent-capture/20261113T080934Z-a2a01`. Fresh-private-output smoke-only integration passed using the existing independent environment and pinned source; the default full entry was not rerun end to end after assembly. An RTT follow-up requires an authorized isolated path with usable netem, independent endpoint RTT calibration and unchanged task/phase controls.
