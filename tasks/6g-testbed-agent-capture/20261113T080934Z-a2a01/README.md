# 5G-MAG Agent/A2A capture audit

**Partially Verified.** Official local single-task A2A function **PASS**; application-log to private-PCAP connection alignment **PASS**; RTT intervention contrast **BLOCKED**. Ten separated baseline rounds passed. No shaped group B was executed.

Read [REPORT.md](REPORT.md) for the conclusions, [task_report.md](task_report.md) for the common archive record, [runs.csv](runs.csv) and [reports/summary.json](reports/summary.json) for results, and [execution_log.md](execution_log.md) for retained commands and failures.

The executed unmodified official commit is `d055fa68ef4de30b93a8a30838ae51fe3e4b561c` of [5G-MAG/6G-Testbed](https://github.com/5G-MAG/6G-Testbed). Capture used original external AF_PACKET code in an owned isolated loopback namespace. The upstream sudo/tcpdump CaptureController was not exercised. Historical S4aP260148 is separate provenance and was not numerically reproduced.

For reproduction, copy these approved files to a fresh private working directory and run `bash reproduce.sh --smoke-only`; use `bash reproduce.sh` for the audited ten-round baseline with the explicit netem downgrade gate. It requires Linux, user/network namespaces, AF_PACKET within that child, ip/tc, Git, and independent Python 3.12 dependencies. It creates private raw evidence and refuses to overwrite an existing accepted smoke. Never execute inside this public archive. The smoke-only entry was integration-tested once with exit 0; this does not add to the ten-round baseline or verify an RTT contrast.

Only reviewed original reports/scripts, environment declarations, aggregate summaries and selected small logs are exported. [allowedfiles.json](allowedfiles.json) pins exact file paths and hashes; [reports/publication_review.json](reports/publication_review.json) and [reports/withheld.md](reports/withheld.md) explain scans, transformations and excluded evidence. Raw packets, application databases/logs, literal task, original IDs and namespace inode tokens remain private.

Task start: `2026-11-13T07:55:41Z`. Hard deadline: `2026-11-13T10:55:41Z`. This is an in-progress archive checkpoint; experiment budget has not been reset. Branch `codex/6g-testbed-agent-capture/20261113T080934Z-a2a01`; PR and remote commit remain pending root verification.
