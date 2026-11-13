# Withheld evidence and publication limits

The complete official 6G-Testbed checkout, full paper HTML/PDF/text/pages, downloaded response headers, original package installation logs, platform state, raw application logs/SQLite/report records, raw PCAP, reassembled requests/responses, literal generated task and private configuration, original run/session/task/connection IDs, raw endpoint tuples and namespace inode tokens stay private. Public URLs, source/version hashes and aggregate checks do not grant redistribution permission.

Excluded paths: upstream/**; private/**; .conda/**; scripts/__pycache__/**; raw package install *.log; logs/conda_create.* (includes another-task tool provenance); failed entrypoint traceback *.log containing copied source excerpts. These are excluded from the exact exporter list, including when their hashes are referenced in an approved report. No recursive copying is used.

smoke001's original argument recorded the wrong parent namespace and was never accepted. Its public metadata replaces that namespace token. The smoke-only reproduction log replaces its actual namespace token. Both original and published SHA256 values are in publication_review.json. Original local evidence is unchanged. The scenario inventory public copy updates its planning-only pending cell to the separately evidenced local PASS; measurements are unchanged.

The original pip-freeze with local Conda build reference is private. Public requirements/environment declarations pin the observed packaging 26.3 version. Unreviewed additions, binary/oversized files, secret-pattern matches, raw UUID/IP/inode matches or unknown redistribution permission must be withheld for manual review. Scans are limited evidence; content inspection remains required.

Public review does not make the public archive sufficient for independent re-reading of raw packets or application evidence. Reviewers can inspect original audit scripts and aggregates and reproduce into a new private workspace. Historical campaign captures/workbook cells and RTT intervention remain unavailable or unverified as stated in REPORT.md.
