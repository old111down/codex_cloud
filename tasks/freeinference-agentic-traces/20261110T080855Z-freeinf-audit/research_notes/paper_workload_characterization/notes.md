# FreeInference paper: workload characterization

## Key question

What did the eighteen-page official paper actually measure, what did it reconstruct or simulate, and which findings can support Agent network-traffic research without implying that the release contains PCAP or client instrumentation?

### Takeaway

The paper characterizes production coding-agent **LLM-serving workloads from the inference-service side**. Its distinctive unit is a reconstructed long-lived session rather than a standalone request. It reports measured request/token/cache counters, inferred session/tool/mutation structure, and separate cache/cost counterfactuals. It does not establish application-event-to-packet correspondence or a network-side classifier. This note is a paper reading, not an execution-success claim.

### Cited findings

- The retrieved official PDF has eighteen pages: main text through p13, references beginning p13 and continuing through p18, sixteen numbered figures and seven numbered tables; no appendix is present in this version. The local evidence hash is `0ab3b7968bb57f3edd27d7102cb48d99a23c72c0fcb42e6178f81bd8ba077c46`. — [Official paper](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf).
- The unit hierarchy is session → user turn → user/tool-triggered LLM steps, with one response able to launch multiple tools or child agents. A tool is executed by the harness; its semantic category is not a claim about a network request. — [§2.1/Fig1, p2](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=2).
- Table1 describes 12,002 sessions, 1,186,582 LLM requests, 1,213,347 tool calls, 209.2B input tokens, 552.5M output tokens and 197.1B cached tokens. Its fourteen rows comprise thirteen human-driven harnesses and one SWE-Bench replay; §3 says analyses exclude SWE-Bench unless stated. — [Table1, p1](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=1), [§3, p3](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=3).
- Session reconstruction matches earlier assistant output replayed in a later request, using tool-call IDs for tool-calling responses and assistant-message content otherwise. The reported 95% one-to-one agreement is only on harnesses with explicit session identifiers; no fixed inactivity cutoff is imposed. — [§3, p3](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=3).
- Table3 lists internal prompt/response text among production-trace fields. It must not be read as the public release schema. The pinned release README says message text, prompts, tool results and raw IDs are omitted. — [Table3, p3](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=3), [official README at audited SHA](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/README.md#L24-L48).
- Human-driven sessions have median four user steps, thirty-six tool steps and forty-two LLM steps; median session duration is about thirty minutes, versus about one minute per user turn. The longest ten percent exceed 7.7h. — [§4.1/Fig2, pp3–4](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=3).
- Median request input is 129.1K tokens, uncached input about 500, and output about 200. Early context growth is roughly 2.5K tokens/step and later about 330 tokens/step. The cost shares are computed with stated assumed token prices, not observed invoices. — [§4.2/Fig2–3, p4](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=4).
- Externally routed-model TTFT is decomposed using an estimated prefill rate; the residual labelled queueing includes other serving overheads. Effective tool latency comes from the LLM-response-to-result gap minus estimated RTT. Neither is a direct server queue probe or client process timer. — [§4.3/Fig4 and §5, pp4–5](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=5).
- Average session time shares are user idle 50.3%, tools 21.7%, decode 18.1% and prefill 9.9%. The 1.38× benefit of doubling tool throughput is a what-if excluding user idle and capping tool gaps at fifteen minutes. — [Fig4/§4.3, p5](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=5).
- Native tools account for 47% of calls and shell tools 53%. Rules normalize names and shell commands by intended function; tool categories exhibit heavy latency/output tails. Batched tools appear in 66.9% of sessions, and subagents in 10.4%. — [Table4–6/Fig5–7/§5, pp5–7](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=6).
- Cache hit degrades with inter-request gap; mean hit after ordinary tool gaps is 97.5% versus 84% after user idle. Provider identities in this comparison are anonymous A–D. — [Fig8/§6.1, pp7–8](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=8).
- Four percent of step transitions are mutations, while 56.4% of sessions contain at least one. The 62.5% mutation share of fresh prefill is attributed under an infinite-retention model, not a measured share of production prefill bills. — [Fig9/Table7/§6.2, pp8–9](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=8).
- Fig10–13 replay a prefix cache with sixteen-token hash blocks and use retention/pricing/storage assumptions. Cheaper-cache behavioral changes and lifecycle-hint reclamation are counterfactuals, not deployed evaluations. — [§6.3–6.4, pp9–11](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=9).
- SWE-Bench versus human medians are 188s versus 61s per turn, about 3.2min versus 30min per session, 25.4K versus 129.1K input tokens, and 1.4K versus 42 user-prompt tokens. Human sessions show longer idle retention requirements. — [Fig14–15/§7, pp11–12](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=11).
- Fig16 labels roughly 10K turns from a random 1.8K-session sample using an LLM and few-shot examples, in eight classes. Create is 35% of first turns; Steer/Refine/Extend jointly account for 46% after the first turn. The model, exact prompt/examples, human verification and agreement/accuracy are not specified in the paper. — [Fig16/§7, p12](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=12).
- The authors identify provider-side timing, reconstructed session boundaries and heterogeneous uncontrolled usage as limitations. — [§9, p13](https://data.freeinference.org/pdf/paper/from-requests-to-sessions.pdf#page=13).

### Inferences

- Treating request tokens as encrypted wire bytes would conflate tokenizer counts, request serialization, provider cache state and transport behavior. The paper supports this distinction through its application/server-side fields, but does not test packet-level transfer models.
- The 95% reconstruction agreement should not be exported to unknown harnesses, subagent-parent edges, turn boundaries or PCAP labels without a new ground-truth evaluation. The paper does not give a subset size or an error matrix.
- The harness distribution, opt-in service population and unequal models/providers/tasks are plausible sources of label imbalance and confounding in a new classifier. Their actual predictive effect requires a separate experiment.
- Public historical traces can guide task design and expected workload scales. Pairing a new independent PCAP with them requires shared experiment events/identifiers that the paper does not establish.

### Gaps

- Venue/DOI and an authoritative publication date are not established from the PDF; its metadata date alone is insufficient.
- Exact session-reconstruction implementation, export transformations, intent labeling artifacts and figure completeness require the sibling code audit; paper description is not proof that a method was published.
- Actual public-field missingness, consistency and one-week/global aggregate agreement require the sibling dataset run. This note contains no runtime-success claim.
- No exact client-side tool timing, packet data, HTTP stream identifiers, clock-error distribution or event-to-flow validation is provided in the paper.
- The reported subagent slowdown wording varies between introduction, Fig7 caption and §5.2. Ratios must be tied to their aggregation; do not combine them as one statistic.
