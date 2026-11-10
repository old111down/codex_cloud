# Trace–PCAP alignment and Hermes MVP research notes

Owner: `/root/freeinf_alignment`. Task T0: 2026-11-10T08:06:28Z. Primary working directory: `/workspace/freeinference-audit`. Evidence was collected without inference calls, credentials, admin access or packet capture. Official source snapshots and raw web responses remain private; original reports/scripts/aggregate logs are intended for publication review.

## Key question 1: Can historical public traces directly label our independent PCAP?

### Takeaway

No direct join is supported by the available identities and measurement conditions. This is a limitation of this particular released dataset and independent capture, not a proof that paired Agent/network collection is impossible.

### Cited findings

- The released request key is `(session_id, step)`, and tool key adds `call_index`. The public schema lacks the external HTTP request ID, IP/ports, socket identity and HTTP stream identity: [fixed schema source](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/release/schema.py#L67-L120).
- The author repository describes a sanitized historical release, not a live export of our own experiment: [official repository README](https://github.com/HarvardMadSys/freeinference_agentic_trace/tree/2b795dbf5eac490a7c081906fdce6cc7a184b7ef).
- The paper discusses inference-service collection, reconstructed sessions and client-side observation limits: [paper §3/p3 and §9/p13](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf).

### Inferences

Clock proximity or similar size patterns cannot establish identity when the application run is different and no legal mapping is provided. Public traces remain useful for workload hypotheses and distribution-level comparisons, with inference labels kept distinct from direct observations.

### Gaps

No authorized mapping from our runs/captures to public release identities exists. No historical synchronized PCAP was obtained. Exact per-packet supervised labels from historical release are therefore Unknown/unavailable under current conditions.

## Key question 2: Can an ordinary user retrieve their own Gateway metadata and join identities?

### Takeaway

A current-user metadata endpoint exists in the reviewed source and requires login JWT. It is not a verified ordinary-user full session-trace export. Internal ID bridges exist, but the reviewed ordinary-user list does not expose the response-ID bridge.

### Cited findings

- The public website at [FreeInference](https://freeinference.org/) linked at 2026-11-10T08:13:19Z to the [commit `7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255`](https://github.com/HarvardMadSys/hybridInference/commit/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255). This is a site-advertised source version, not historical deployment attestation. Homepage private response SHA256: `a7672032abf5f95365b0506bec1ba952400c045fdaff51e1b881e7ee7ce4e5ae`.
- [`GET /user/recent-requests`](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/user_routes.py#L1279-L1388) filters by current account, supports limit/offset and returns request ID, model/provider, timestamp, latency, TTFT, stream, tokens, status and related metadata. Limit is clamped to 1–200.
- [`get_current_user`](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/deps.py#L349-L393) validates a login JWT Bearer token. This is not proof an inference API key can authenticate dashboard routes.
- [`RequestIdMiddleware`](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/middleware/request_id.py#L32-L68) propagates `X-Request-ID`. Our anonymous public catalog GET observed a matching synthetic echo. But [`completions.py`](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/completions.py#L883-L884) creates another internal request ID.
- [`postgres_log.py`](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/storage/postgres_log.py#L238-L250) stores actual response `id` into `metadata.response_id`; the ordinary list does not expose it. A protected [internal grant usage path](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/agent_grants.py#L313-L377) can expose both IDs and start/logged timestamps; the entire [router requires a dispatch token](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/agent_grants.py#L46-L60).
- [Admin request export](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/admin/export.py#L42-L80) requires admin authentication; it is not a normal-user alternative.

### Inferences

The safest MVP anchor is a client-owned local UUID/attempt/socket ledger. Gateway metadata can supplement it only after authorized end-to-end ID and timing checks. A successful public header echo is insufficient. The internal bridge means it would also be wrong to assert that every authorized exact join is impossible.

### Gaps

No login JWT or authorized self-log export was available. Anonymous GET of user recent requests returned 401, and its body was not read. Full session export, retention, completeness and exact ordinary-user response ID exposure remain Unknown outside the inspected paths. No internal/admin route was accessed.

## Key question 3: What do start/end/latency actually mean?

### Takeaway

Historical start is reconstructed, and historical physical end event is unverified. Current published Gateway source gives a concrete reason not to equate DB timestamp with the last provider/client byte, but does not establish historical deployment equivalence.

### Cited findings

- [`kept_fields`](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/log_records/fields.py#L174-L192) computes start as end minus logged latency (missing latency becomes zero).
- Current Gateway [`ledger_attribution`](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/grant_auth.py#L302-L323) explicitly says `api_logs.timestamp` is insert time of a write scheduled after response completion; actual handler start is retained only for grant-authenticated requests. Sessions agent independently traced the async logger, DB default and handler code.
- Current [`completions.py`](https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/completions.py#L883-L928) starts its own timer after HTTP body decoding, not at socket first byte.
- Historical tool latency is a [next-request-start minus current-end gap](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/release/requests_table.py#L178-L184), shared by calls in a batch. It is not a tool network timer.

### Inferences

Subtracting latency from an asynchronously inserted DB timestamp may carry scheduling lag and DB–Gateway clock differences. Even exact clock offset correction cannot repair a mismatched physical event definition. Treat end/start as source-defined fields, not network packet boundaries.

### Gaps

Historical collector version and tap-event semantics were not established. Current code review was not a live observation of latency components or queue delay. No numerical correction is justified.

## Key question 4: Are Hermes hooks usable, and is the exact MiMo route available now?

### Takeaway

Hermes has inspectable official hook/correlation interfaces. They need a metadata allowlist, retry-aware local identities and transport supplementation. Current anonymous catalog does not list the requested MiMo ID; account availability and real inference are Unknown.

### Cited findings

- [Official Hermes repository](https://github.com/NousResearch/hermes-agent), reviewed SHA `b7db40d82568ea68ce321ac1ead3bfea354c7f56`; [observer contract](https://github.com/NousResearch/hermes-agent/blob/b7db40d82568ea68ce321ac1ead3bfea354c7f56/website/docs/developer-guide/observer-hooks.md#L72-L170) lists API/tool/session IDs and separate auxiliary-call hooks.
- [`pre_api_request` call site](https://github.com/NousResearch/hermes-agent/blob/b7db40d82568ea68ce321ac1ead3bfea354c7f56/agent/turn_api_request.py#L60-L107) still supplies content-bearing compatibility fields as well as sanitized payload. Metadata-only recording must whitelist fields, not dump kwargs.
- [`conversation_loop` ID/timer allocation](https://github.com/NousResearch/hermes-agent/blob/b7db40d82568ea68ce321ac1ead3bfea354c7f56/agent/conversation_loop.py#L1767-L1771) sits outside its [retry loop](https://github.com/NousResearch/hermes-agent/blob/b7db40d82568ea68ce321ac1ead3bfea354c7f56/agent/conversation_loop.py#L1577-L1606). Its API ID should not be assumed to uniquely enumerate every HTTP attempt. Retry count is passed to pre hook.
- [`post_api_request`](https://github.com/NousResearch/hermes-agent/blob/b7db40d82568ea68ce321ac1ead3bfea354c7f56/agent/turn_response_intake.py#L66-L107) contains first_chunk_at and source span times; [stream observers](https://github.com/NousResearch/hermes-agent/blob/b7db40d82568ea68ce321ac1ead3bfea354c7f56/agent/plugin_stream_hooks.py#L1-L60) are asynchronous and can drop old queued events.
- [FreeInference model docs](https://doc.freeinference.org/models.html) identify the OpenAI-compatible base URL and access-filtered authenticated catalog as the source for exact model IDs. The [public `/v1/models`](https://freeinference.org/v1/models) returned three IDs at 08:21:02Z: `bge-m3`, `deepseek-v4-flash`, `qwen3.6-35b`. `mimo-v2.6-flash` was absent.

### Inferences

Use a local per-pre-event attempt sequence plus transport attempts, preserve auxiliary calls, and explicitly track missing/error callbacks. Future proxy fallback is feasible in principle but changes fingerprints and buffering. It cannot be represented as untouched native Hermes traffic.

### Gaps

Hermes installation/plugin loading was not run. The exact MiMo authenticated catalog, account eligibility, tool/stream API compatibility, price/quota and inference success were not tested. Historical mentions or demos do not establish current support. No substitute model was run.

## Key question 5: How should cross-host clocks and uncertainty be handled?

### Takeaway

Client wall/monotonic pairs and capture settings are first-class metadata. Cooperative four-timestamp calibration yields an offset interval, not magic removal of asymmetric delay. FreeInference calibration endpoints are unverified.

### Cited findings

- [RFC 5905 §8](https://www.rfc-editor.org/rfc/rfc5905.html#section-8) defines four-timestamp clock offset and round-trip delay calculations. Official text was retrieved privately and inspected.
- The source-defined production fields above do not provide independent receive/send server timestamps or establish a publicly callable calibration interface: [release schema](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/release/schema.py#L78-L104).

### Inferences

Given c1/g2/g3/c4 and nonnegative one-way delays, `g3-c4 <= offset <= g2-c1`; an RTT/2 correction assumes symmetric paths. Record calibration error, drift, callback/capture semantics and server/DB residual separately. A local-client paired experiment can avoid unknown cross-host absolute offset for its principal labels.

### Gaps

No NTP status, real offset, drift, capture timestamp type, kernel scheduling residual or server calibration was measured. All proposed numerical tolerances remain parameters to measure, not reported results.

## Key question 6: Why can TLS/HTTP2/HTTP3 break time-only matching?

### Takeaway

Sessions, requests, flows, bursts, streams and tool events have different grain. A conservative matcher must retain ambiguity instead of choosing a nearest request.

### Cited findings

- [RFC 9113 §5](https://www.rfc-editor.org/rfc/rfc9113.html#section-5) permits multiple concurrent streams with interleaved frames on one HTTP/2 connection.
- [RFC 9114 §4.1](https://www.rfc-editor.org/rfc/rfc9114.html#section-4.1) maps HTTP/3 requests to QUIC bidirectional streams; [RFC 9000 §5.1/§9](https://www.rfc-editor.org/rfc/rfc9000.html#section-9) describes connection IDs and migration across paths.
- The published application trace schema does not expose these wire/transport identities: [schema](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/release/schema.py#L78-L120).

### Inferences

An encrypted packet may coalesce several streams; a persistent flow may contain many calls; one call may span several bursts; one local tool may have no packets. Independently instrumented endpoint transport evidence is needed for exact mapping, while serial time windows are conditional candidates. NAT/QUIC migration and port reuse require connection epochs and source-specific maps.

### Gaps

No real FreeInference/Hermes negotiated ALPN, H2/H3 usage or TLS stream mapping was measured. Enabling a metadata proxy or TLS key logging was only considered as future controlled instrumentation, not executed.

## Key question 7: What was actually run, and what would constitute a useful MVP result?

### Takeaway

Public GET checks and small synthetic matcher invariants ran successfully. Real Agent/network alignment remains unverified. Future evaluation must separate known-boundary classification from network-only segmentation and classification.

### Cited findings

- Local executed source: `scripts/alignment/check_public_gateway_metadata.py`; aggregate output: `logs/alignment_public_http_checks.json`. At 08:21:02Z the public [catalog](https://freeinference.org/v1/models) returned HTTP 200 and matched synthetic header echo; unauthenticated user metadata returned 401 with body not read. No credentials/inference.
- Local command: `python scripts/run_logged.py --log logs/alignment_synthetic_checks --timeout 30 -- python scripts/alignment/synthetic_checks.py`. `logs/alignment_synthetic_checks.json` records 2026-11-10T08:24:25Z, exit 0; `.log` records Python 3.12.14 and 11 passing synthetic invariants. Source: `scripts/alignment/match_intervals.py` and `synthetic_checks.py`.
- Matching checks covered reused connections, overlapping intervals, explicit transport IDs, multi-stream observations, clock uncertainty, unrelated/missing connections, late packets, boundaries and invalid intervals. These are our own constructed examples, not measurements from the paper or real captures.

### Inferences

The next useful experiment is one pinned Hermes, the exact verified route, one NIC, a few owned tasks, paired metadata/capture, serial first and concurrency stress second. Measure event completeness, alignment residuals, ambiguity and label age before any classifier. Group splits by task/session/user/time, isolate provider/endpoint/harness confounds, and report oracle segmentation separately.

### Gaps

Real captures = 0; real Agent runs = 0; model inference calls = 0. Classification accuracy, real alignment precision, authorized Gateway joins and generalization are Unknown. The check does not validate upstream export correctness.

## Retrieval and handoff record

- The Tavily research researcher reference and Tavily search skill were read. One advanced search succeeded; two subsequent searches returned HTTP 429. As directed by root, no repeated throttled retries or account rotation were attempted. Known official URLs and public pinned GitHub source were read directly using Python urllib.
- `private/evidence/alignment/official_fetch_log*.json` retain source URLs/status/size/hash/time for official web/source retrieval. Full source copies, raw HTML, dataset rows, IDs, credentials and paper fulltext are not publication artifacts.
- Sessions agent independently verified current Gateway time/ID paths and passed fixed source evidence. Related-work agent noted that classification with application-defined boundaries is not network-only end-to-end recognition; this distinction is included in both deliverables.
- Main deliverables: `trace_pcap_alignment.md`, `mvp_experiment_plan.md`; original scripts under `scripts/alignment/`; safe execution logs under `logs/alignment_*`; source metadata index under `reports/alignment_evidence.csv`.
