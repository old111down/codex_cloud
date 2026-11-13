# Execution timeline

All timestamps are UTC; these stages share the original budget.

| UTC | Event | Evidence |
| --- | --- | --- |
| 2026-11-13T07:55:41Z | Actual task start; deadline 10:55:41Z | metadata.json |
| 07:57:39–07:59:40 | Permission/isolation probes; child AF_PACKET works; netem inner exit 2 | reports/permission_summary.json |
| 07:57:54 | Official paper saved privately; historical ZIP later HTTP 403 | reports/paper_evidence.md |
| 08:01:00–08:04:42 | Independent environment and scoped dependencies; initial CLI failures retained | reports/entrypoint_audit.md; selected dependency metadata |
| 08:07:21–08:07:26 | smoke001 completed but excluded for incorrect parent namespace argument | logs/smoke_001.json |
| 08:08:30–08:08:34 | smoke002 launcher scope verified and accepted | logs/smoke_002.json; reports/per_run/smoke002.json |
| 08:09:34 | Independent archive run/branch created | metadata.json |
| 08:10:55 | Baseline summary-key gate failed before any A round | logs/baseline_gate_schema_error.json |
| 08:10:56–08:11:31 | A001–A010 actual separated baseline executions | logs/baseline_batch.json; runs.csv |
| 08:18:08 | Independent direct raw-evidence outcome review recorded | reports/independent_outcome_review.json |
| 08:22:27–08:22:33 | Fresh-private-copy smoke-only reproduce integration exit 0 | logs/reproduce_smoke_integration.json |
| 2026-11-13T08:26:38.281783+00:00 | In-progress approved archive checkpoint generated; end null | metadata.json; reports/publication_review.json |
| Exact operation time Unknown; recorded 2026-11-13T08:30:42Z | Root verified pushed checkpoint `815c30ea4464abc8aac5447ad8ede4469effa8be` equals remote ls-remote; PR 4 created against main, unmerged | reports/archive_checkpoint.json |
| 2026-11-13T08:30:42Z | Local archive sealed; original task start and deadline unchanged | metadata.json; reports/publication_review.json |

No B group was executed. Remote verification in these files binds the preceding checkpoint only. The subsequent closure commit SHA will be externally verified and reported by root after commit/push. Smoke-only integration passed with existing environment/source; the default full entry was not rerun end to end after assembly.
