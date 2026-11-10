# Session collection and labels

Owner: freeinf_sessions. Task T0 2026-11-10T08:06:28Z; deadline 11:06:28Z. Source pinned to `HarvardMadSys/freeinference_agentic_trace@2b795dbf5eac490a7c081906fdce6cc7a184b7ef`. Scope: collection position, session/turn/subagent algorithms, harness/tool/intent labeling. Outputs: `architecture.md`, `session_reconstruction.md`, `label_mechanisms.csv`.

## Where is collection, and which values are measured?

### Takeaway

Verified source facts place collection on inference-service/Gateway side. Historical deployment/timestamp instrumentation match is Unknown. A current public Gateway snapshot was subsequently found and its DB insert timing is auditable; it does not prove historical deployment semantics. Derived timestamps, tool timing, sessions, triggers and labels must not be called independent client-side measurements.

### Cited findings

- Paper p3: local and forwarded inference, input/output plus metadata, forwarded latency and buffering/queue caveat. https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=3
- Paper p13: service-side view lacks precise client tool timing. https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=13
- Private export origin is called gateway weekly export; the trace artifact itself does not implement the running service. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/build_steps.py#L44-L66
- `start_ms=end_ms-(latency_ms or0)`. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/log_records/fields.py#L174-L192
- Tool latency is the gap to the next inferred request start, shared by a batch. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/release/requests_table.py#L178-L184

### Inferences

Tool duration can include approval, scheduling, transport and synchronization. Provider route labels and input token patterns can confound a downstream network classifier. Those are risks, not measured error rates.

### Gaps

The current online Gateway source is public (see supplemental audit below). Whether historical trace used that version and timestamp semantics, its clock source, client wire-send/first-byte semantics, packet/connection identifiers and independent tool spans are Unknown. No historical public PCAP pairing.

## What does session reconstruction actually do?

### Takeaway

Public code implements a bounded-output-replay linker; no inactivity time cutoff does not mean unlimited history or cross-week continuity. Published requests are a selected main chain.

### Cited findings

- Per-account completion order, previous128 kept requests, tool-ID priority over text, parent 8-word-shingle coverage >=90%. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/sessions/link.py#L20-L99
- Last-assistant-only replay, first8000chars, short-answer fallback. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/sessions/signals.py#L27-L113
- Tool-ID punctuation/shim/conditional numeric-suffix normalization. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/log_records/call_ids.py#L12-L49
- Main chain deepest path; normal agent sessions need >=1tool trigger and >=2user triggers; benchmark has special case. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/sessions/chains.py#L55-L115
- Cross-week sessions split by current pipeline; reference export comparison explicitly reports that outcome. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/reports/reference_comparison.py#L1-L17
- Subagent matching uses same account, [-30s,+10min], delegation-text opening in child first user message, nearest unclaimed root. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/sessions/spawns.py#L26-L167
- Paper 95% is stated only on harnesses providing explicit IDs. https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=3

### Inferences

Repeated generic answers or normalized/reused IDs could false merge; rewritten outputs/window eviction could false split; repeated delegation templates could misattach children. These follow from rules but their real occurrence rate is Unknown. Normal >=2user filter creates selection on interaction count.

### Gaps

Explicit-ID verification dataset, denominator, harness subset, code and confusion statistics not located. `reference_comparison.py` is export-to-export comparison and does not verify95%. No runtime reconstruction on private production text was attempted by this agent.

## How are labels generated, and can intent be relabeled?

### Takeaway

Harness, triggers, tool categories, outcomes and context causes have different rule-based mechanisms. Eight semantic intents are LLM-assisted paper-only labels at this SHA, with insufficient materials to regenerate them from the anonymous release.

### Cited findings

- Current harness implementation phrase-first then UA; first6 input entries, system/user text, first20Kchars. Paper says UA-first: version discrepancy remains explicit. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/log_records/harness.py#L55-L98
- Tool categories use alias/keyword/family/shell-purpose tables, not semantic intent annotation. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/tool_calls/categories.py#L91-L179
- Result outcome defaults ok when no error evidence, unmatched result null. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/tool_calls/outcomes.py#L106-L127
- Fig16: random1.8Ksessions, rough10Kturns, LLM with few-shot examples; eight intents. No model name/manual-IAA details stated there. https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=12
- Public schema lacks intent; registry ends atFig15; README excludes message/prompt/result text. https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/release/schema.py#L67-L120 ; https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/__init__.py#L118-L139 ; https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/README.md#L21-L48

### Inferences

Cannot reconstruct text intent equivalently from anonymized counts/block equality. A new labeling experiment would require new authorized text/log collection and validated label protocol, and would not reproduce original Fig16 absent its model/template/sample. Tool-category accuracy does not imply intent accuracy.

### Gaps

LLM name/version, actual input fields/history, prompt template/fewshot examples, exact sample/seed, public per-turn labels, human checking and agreement/accuracy assessment Unknown or missing. Lack of documentation does not prove authors never manually checked.

## Audit actions and validation

Read AGENTS.md and full user attachment. Read primary PDF pages2,3,6–9,12–13 and relevant text search; another agent owns complete-PDF read. Read source with `nl -ba` and targeted `sed`: session extract/signals/link/chains/spawns/relabel/release_sessions; log fields/harness/call_ids/messages; tool calls/categories/results/outcomes/arguments/tool_turns; privacy pseudonyms/public_words/tool_columns/stand_ins/privacy_check; release build/requests/tool_calls/schema/trace_lines; README/build_steps/reference comparison/figure registry. Used tracked-tree inventory and source `rg` searches for intent, fewshot, annotation, validation, labels and class names. No web search was needed beyond already downloaded primary sources for this scoped topic. No third-party source copy/raw IDs/text emitted in reports.

This agent did not install dependencies, execute trace commands, reconstruct private sessions or call paid models. Reports are static evidence audits, not runtime success. CSV structure/link integrity checked with standard-library local validation; aggregate dataset/runtime validation is owned by the data and code agents.

## Supplemental current Gateway audit, 2026-11-10T08:20–08:25Z

### Takeaway

Alignment agent found official-site-linked `HarvardMadSys/hybridInference@7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255`. I independently traced timing/storage/ID code and corrected the earlier overbroad assumption that no Gateway source was public. Current-source facts are separate from May–September trace deployment Unknowns.

### Cited findings

- Handler generates an internal request ID separately from X-Request-ID middleware, and sets time.time start. https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/completions.py#L883-L928
- Stream TTFT first meaningful delta; fallback can reset reference before token while total latency includes whole wall time. https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/completions_stream.py#L247-L279 ; https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/completions_stream.py#L605-L613
- Explicit doc: api_logs.timestamp is DB insert time of a write scheduled after response completed; request_started_at metadata only for grant-authenticated requests, not ordinary traffic. https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/grant_auth.py#L302-L323
- Baseline timestamp default NOW; insert column list does not specify timestamp. https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/migrations/baseline/api_logs.py#L350-L356 ; https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/storage/postgres_log.py#L96-L122
- Logger uses bounded async queue; current potential loss behavior is not evidence of historical dataset loss. https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/completions_logging.py#L126-L213
- SSE completion ID is stored in response.id; storage metadata retains response_id bridge, but ordinary user recent-requests does not expose response_id. https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/completions_stream.py#L931-L946 ; https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/storage/postgres_log.py#L239-L250 ; https://github.com/HarvardMadSys/hybridInference/blob/7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255/apps/backend/serving/servers/routers/user_routes.py#L1320-L1388

### Inferences

If historical logging used equivalent DB timestamp semantics, end-latency can shift inferred start by DB queue delay and clock differences. The magnitude and whether it explains any negative gaps are Unknown. Response ID mapping exists internally in current source but does not establish a publicly available ordinary-user precise join.

### Gaps

Current live deployment/schema/API auth capability not runtime-validated by this agent. No inference request made. The full Gateway repo was not copied into the public task. Current ordinary API vs grant-scoped API distinctions remain in alignment agent's scope.

Known-URL source downloads were saved privately: baseline/api_logs.py HTTP200 21,253B sha256 `6c0202fd798ad1d0cca1df0b7c1a4a937c7827dee4e0a8d4ba3f2eb94b97419a` at08:21:23Z; erasure_fence.py HTTP200 25,079B `5d0c899f50aad30685786330d7cbfe7481d50c495bae72bedd369c6d050c1066` at08:22:12Z; grant_auth.py HTTP200 13,673B `3004bc1b1fce16d7ee5f155720a53b62474a20b3d89efe17fce9a1e216a75c89` at08:22:35Z. One guessed path `serving/utils/ledger_attribution.py` returned404; corrected via import to `serving/grant_auth.py`. Tavily extract failed because the connector required a nonempty link_id argument; direct known-URL primary-source downloads were the fallback. All files remain private evidence only.
