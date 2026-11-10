#!/usr/bin/env python3
"""Generate the audit's complete observed Parquet field dictionary.

JSONL-only aliases/containers and absent network/intent observables are separate
rows, explicitly not presented as observed Parquet fields. No trace rows read.
"""
import csv
import json
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parents[1]
SHA='2b795dbf5eac490a7c081906fdce6cc7a184b7ef'
BASE=f'https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/{SHA}/'
SCHEMA=BASE+'release/schema.py'
REQ=BASE+'export/release/requests_table.py'
TRACE=BASE+'release/trace_lines.py'
FIELD=BASE+'export/log_records/fields.py'
TOOL=BASE+'export/privacy/tool_columns.py'
rows=[]
def add(path,type,grain,meaning,provenance,observed='Observed Parquet schema; exported/derived value',label='No',pcap='No; requires application instrumentation',use='Application-trace analysis or auxiliary supervision only',risk='App-only oracle feature; exclude from network-only feature set',evidence=SCHEMA):
    rows.append(dict(field_path=path,type=type,grain=grain,meaning=meaning,provenance=provenance,observed_or_inferred=observed,public_label=label,pcap_observable=pcap,classification_use=use,leakage_risk=risk,evidence=evidence+'; reports/observed_schemas.json'))

M={
'sessions.session_id':('32-hex pseudonymous reconstructed session key; not a TCP flow or original API request ID','Reconstruction then keyed BLAKE2b with private stable release salt','No','Join/split grouping only; never classifier feature','Strong identity/reconstruction leakage',BASE+'export/privacy/pseudonyms.py#L54'),
'sessions.user_id':('16-hex pseudonymous account key; not verified unique individual','Private raw account ID keyed BLAKE2b; stable within salt series','No','Account-grouped split; never feature','Strong user identity leakage and cross-session dependence',BASE+'export/privacy/pseudonyms.py#L60'),
'sessions.harness':('Harness identity inherited from selected session; rule inferred from intro phrases then user-agent fallback','export/log_records/harness.py; export/configs/harnesses.toml; session selection','Yes: rule-inferred harness','Candidate supervision for newly paired PCAP, with source accuracy Unknown','Target leakage if used as feature; model/provider/user/task/time confounding',BASE+'export/log_records/harness.py#L64'),
'sessions.parent_session_id':('Parent reconstructed session key; null for top-level trace','Released spawn relationship, hashed by same salt','Yes: parent linkage','Subagent supervision/group descendant splits','Cross-split family leakage',BASE+'export/release/build.py#L26'),
'sessions.spawned_by_step':('Parent request step that spawned child; null for top-level','Spawn reconstruction plus released step index','Yes: spawn location','Derived subagent event supervision','App-only relationship reveals target',BASE+'export/release/build.py#L26'),
'sessions.spawned_by_call_index':('Position of spawning call within parent response, from zero; null for top-level','Spawn extraction/reconstruction','Yes: spawn location','Derived subagent event supervision','App-only relationship reveals target',BASE+'export/release/build.py#L26'),
'requests.session_id':('Foreign key to sessions.session_id','Release keyed hash','No','Join/group split only','Identity leakage',REQ+'#L137'),
'requests.step':('Zero-based request order inside reconstructed mainchain session','Session reconstruction assignment','No','Ordering; causal prefix selection only','Sequence-position and post-hoc reconstruction shortcut',REQ+'#L137'),
'requests.link_reason':('tool_call_id or assistant_message explains previous-mainchain linkage; null at step zero','Private link reason normalized for release','Yes: algorithm-inferred linkage','Linkage audit; possible auxiliary target','Derived using message history; unavailable from ciphertext',REQ+'#L137'),
'requests.start_ms':('Derived start = end_ms minus logged latency_ms (missing latency treated zero); physical source event Unknown','Log conversion/export arithmetic, not independently measured client send','No','Only time anchor after paired clock/event validation','Wrong event/clock assumption; absolute calendar shortcut',FIELD+'#L174'),
'requests.end_ms':('Raw record timestamp converted to epoch milliseconds; exact online event/clock location Unknown','Private source record.timestamp -> log conversion','No','Only validated clock/event anchor','Server/client offset and late-log semantics Unknown',FIELD+'#L174'),
'requests.ttft_ms':('Logged time to first token; unit ms; physical instrumentation boundary Unknown','Private record.ttft_ms retained','No','Performance target; not direct PCAP feature','Target/time-boundary leakage; stream/model/provider confounding',FIELD+'#L174'),
'requests.model':('Normalized logged model identity','Private record.model_id retained','Yes: source metadata model','Potential model target or stratification; not harness feature','Model/harness/provider confounding',REQ+'#L137'),
'requests.provider':('Anonymous provider letter; real provider mapping private','Private provider_letters map; pseudonyms.letter_of','Yes: anonymized routing metadata','Stratification or target for newly paired traces','Endpoint/provider shortcut; true provider unavailable',BASE+'export/privacy/pseudonyms.py#L78'),
'requests.stream':('Logged streaming flag','Private record.stream retained','Yes: source metadata mode','Stratification/target; require causal observation','Transport/chunking confound',FIELD+'#L174'),
'requests.step_trigger':('user or tool; input provenance of reconstructed step, not direct measurement of human action','Session reconstruction/tool ID versus assistant text link','Yes: inferred user/tool trigger','Potential paired event target; no intent semantics','Link-derived label errors; target leakage',REQ+'#L137'),
'requests.waited_for':('Null first step; later user/tool/ask_user_tool/subagent, precedence subagent then ask-user','Derived from trigger and previous request tool categories','Yes: derived wait kind','Auxiliary event target after alignment','App labels and future structure leak behavior',TRACE+'#L130'),
'requests.prompt_tokens':('Provider/log-reported prompt input usage; NOT necessarily o200k role sum','First record field, then response.usage fallback','No','Workload measurement; approximate encrypted-size covariate only after new capture','Tokenizer/provider/harness confounding',FIELD+'#L154'),
'requests.completion_tokens':('Provider/log-reported completion usage','First record field, then response.usage fallback','No','Workload/performance analysis; auxiliary target','Provider tokenizer and end-of-request future leakage',FIELD+'#L154'),
'requests.cache_read_tokens':('Provider/log-reported cached input usage; null when unavailable, not necessarily zero','First record field, then response.usage fallback','No','Serving workload/cache statistic','Provider reporting confound; unavailable to passive PCAP',FIELD+'#L154'),
'requests.role_tokens':('Struct of o200k_base input content counts per role plus tool definitions; does not imply provider usage equality','Private digest message tokenization','No','Context composition analysis only','Prompt-structure oracle; tokenizer mismatch',REQ+'#L65'),
'requests.n_messages':('Count of input messages; tool definitions excluded','Private input-message digest','No','Workload/context feature at app layer','Harness formatting shortcut; ciphertext does not expose count',REQ+'#L65'),
'requests.tool_definition_names':('List of declared tool names, lowercased public word or other','Private digest plus public-name allowlist','Yes: normalized declared names','Auxiliary task/tool inventory target','Very strong harness/behavior signature; unavailable from encrypted payload',REQ+'#L65'),
'requests.finish_reason':('Normalized response stop/length/tool_calls/content_filter/other','OpenAI/Anthropic style reasons normalized to release enum','Yes: normalized output reason','Auxiliary response target','Post-response future leakage',REQ+'#L31'),
'requests.transition':('append/mutation/switch versus previous step; null first step','Private input digest transition comparison','Yes: algorithm-inferred transition','Context transition target, no natural-language intent','App history oracle; switch also tied to model',REQ+'#L137'),
'requests.cause':('Mutation cause enum; null unless transition=mutation','Private mutation classifier: compaction/tool_definitions/system_prompt/dropped_turns/injection/tool_result/other','Yes: rule-inferred mutation cause','Mutation target only, not task intent','Heuristic errors Unknown; app content required',REQ+'#L137'),
'requests.block_ids':('Week-local positive IDs for chained input block hashes; 16 o200k tokens/block; equality means same chained hash, not plaintext','Private digests mapped to week-local integer order','No','Prefix-cache simulation; never network-only feature','Extremely strong content-equality/identity oracle; IDs incomparable across weeks',REQ+'#L197'),
'tool_calls.session_id':('Foreign-key session of request that emitted call','Released request association','No','Join/group split only','Identity leakage',SCHEMA+'#L118'),
'tool_calls.step':('Request step whose response emitted call','Tool-call extraction plus session step join','No','Temporal ordering only','App-only sequence structure',SCHEMA+'#L118'),
'tool_calls.call_index':('Zero-based call position in request response; batching does not imply real concurrent execution','Response tool-call list position','No','Call key and batching descriptive analysis','Post-response app structure',SCHEMA+'#L118'),
'tool_calls.name':('Lowercased public tool name or other; not raw arbitrary name','Tool extraction plus public_words allowlist','Yes: rule-normalized tool name','Auxiliary behavior label; not semantic intent','Direct category/harness shortcut',TOOL+'#L113'),
'tool_calls.category':('One of 16 native/shell-purpose categories; starred categories summarize shell programs','Rules in export/configs and tool_calls/categories; not manually verified task semantics','Yes: rule-inferred tool category','Candidate app behavior supervision for newly aligned data','Category is target; shell/tool inference uncertainty',BASE+'export/tool_calls/categories.py'),
'tool_calls.programs':('Shell-only list of public program labels or anonymized stand-ins; not executable commands','Shell parse and privacy public_words/stand_ins mapping','Yes: normalized shell labels','Auxiliary behavior target; never execute','Behavior oracle; parser coverage bias',TOOL+'#L113'),
'tool_calls.parse_status':('Shell-only success/partial/failed parser status; null for other tools','Bash parser result','Yes: parsing status','Quality filter/stratification','Missingness can reveal tool class; not failure of executed task',SCHEMA+'#L118'),
'tool_calls.arguments_skeleton':('Sanitized argument skeleton text; public keys/placeholders/operators/allowed command words and allowed subagent_type retained; <unparsed> possible','Privacy filter; original values/content absent, not simply all values removed','No: structural metadata','Schema/label provenance audit; never execute or train raw strings blindly','Potential formatting/harness shortcut; privacy residuals not independently certified',TOOL+'#L63'),
'tool_calls.outcome':('ok/error/denied/timeout; null if no matching result with call ID','Result extraction/heuristic outcome normalization','Yes: rule-normalized result outcome','Auxiliary result target','Post-result future leakage; not direct network success',SCHEMA+'#L118'),
'tool_calls.result_tokens':('o200k_base tool result token count; null without matched result','Tool result content tokenizer','No','Workload measurement/auxiliary target','Result payload oracle and future leakage',SCHEMA+'#L118'),
'tool_calls.latency_ms':('Shared gap next_request.start_ms minus current_request.end_ms if next waited for tools; not independently observed per-tool runtime','Inferred request adjacency; all calls in batch get same gap; can be negative','No','Wait/performance statistic with explicit inference caveat','Batch confounding; negative gaps and no per-tool ground truth',REQ+'#L178'),
}

def main():
    week=ROOT/'private/data/release/2026-08-30_2026-09-05'
    schemas={}
    for file in ['sessions.parquet','requests.parquet','tool_calls.parquet']:
        table=file.split('.')[0];sch=pq.read_schema(week/file);schemas[file]=str(sch)
        for f in sch:
            path=f'{table}.{f.name}';meaning,prov,label,use,risk,evi=M[path]
            obs='Observed actual Parquet schema; value semantics source-verified, upstream production instrumentation Unknown'
            add(path,str(f.type),table[:-1] if table!='tool_calls' else 'tool call',meaning,prov,obs,label,use=use,risk=risk,evidence=evi)
            if pa.types.is_struct(f.type):
                for child in f.type:
                    add(path+'.'+child.name,str(child.type),'request',f'o200k_base input tokens of {child.name}; tool_definitions are not messages','Private digest tokenization',label='No',use='App context composition; auxiliary target',risk='Prompt composition oracle; provider-token counts need not match',evidence=REQ+'#L65')
    # Distinguish the user's JSONL field names from actual Parquet storage.
    extras=[
      ('jsonl.week','string','trace','Named completion-week release folder','JSONL-only wrapper; source verified, JSONL not downloaded',TRACE+'#L232'),
      ('jsonl.day','string','trace','UTC date of top-level derived first start; may precede named completion week','JSONL-only wrapper; source verified, JSONL not downloaded',TRACE+'#L232'),
      ('jsonl.session.start_ms','int64','session','min(start_ms) of this session own mainchain requests; no such sessions.parquet field','JSONL-only derived value; source verified',TRACE+'#L153'),
      ('jsonl.session.end_ms','int64','session','max(end_ms) of own mainchain requests; excludes nested child span in this formula','JSONL-only derived value; source verified',TRACE+'#L153'),
      ('jsonl.session.requests','list<object>','session','Own mainchain requests in step order; child sessions nested below tool calls','JSONL-only structural container; source verified',TRACE+'#L214'),
      ('jsonl.requests.turn_index','int','request','Starts zero; increments before every later user-triggered step; absent in Parquet','JSONL-only derived value; source verified',TRACE+'#L214'),
      ('jsonl.requests.provider_tokens','object','request','JSONL container of prompt/completion/cached; flattened in Parquet','JSONL-only structural alias; source verified',TRACE+'#L95'),
      ('jsonl.requests.provider_tokens.prompt','int64','request','Alias of requests.prompt_tokens','JSONL-only alias; source verified',TRACE+'#L95'),
      ('jsonl.requests.provider_tokens.completion','int64','request','Alias of requests.completion_tokens','JSONL-only alias; source verified',TRACE+'#L95'),
      ('jsonl.requests.provider_tokens.cached','int64?','request','Alias of requests.cache_read_tokens','JSONL-only alias; source verified',TRACE+'#L95'),
      ('jsonl.requests.mutation','object?','request','Container transition/cause or null; flattened in Parquet; also includes append/switch','JSONL-only alias; source verified',TRACE+'#L95'),
      ('jsonl.requests.mutation.transition','string?','request','Alias of requests.transition','JSONL-only alias; source verified',TRACE+'#L95'),
      ('jsonl.requests.mutation.cause','string?','request','Alias of requests.cause','JSONL-only alias; source verified',TRACE+'#L95'),
      ('jsonl.requests.tool_calls','list<object>','request','Call list; keyed by session/step/call_index in Parquet','JSONL-only structural container; source verified',TRACE+'#L95'),
      ('jsonl.tool_calls.arguments','list<[key,value]>?','tool call','Pairs from sanitized arguments_skeleton; preserves repeated keys; not original arguments','JSONL-only structural alias; source verified',TRACE+'#L69'),
      ('jsonl.tool_calls.subagent','object?','tool call','Nested session when parent/spawn keys join; absent as Parquet column','JSONL-only structural alias; source verified',TRACE+'#L214'),
    ]
    for path,typ,grain,meaning,obs,evi in extras:
        add(path,typ,grain,meaning,'release/trace_lines.py mapping',obs,label='No separate new label',use='Use corresponding actual Parquet fields; derived hierarchy only',risk='Same leakage risk as source fields',evidence=evi)
    missing=[
      ('absent.intent','Create/Extend/Refine/Debug/Explain/Steer/Setup/Other labels absent from public schema; intent annotation inputs/code unavailable'),
      ('absent.prompt_messages','Original user/system/assistant message text and responses absent; semantic intent cannot be regenerated from counts'),
      ('absent.original_tool_arguments_results','Original tool arguments and tool result bodies absent; sanitized structure/counts only'),
      ('absent.raw_request_id','Original Gateway request ID absent; session_id+step is a public reconstruction key'),
      ('absent.pcap_packets','No packet timestamps, lengths, directions, IATs, retransmissions or packet payloads'),
      ('absent.flow_tuple','No IP/port/protocol 5-tuples, TCP sequence numbers, QUIC connection IDs or connection mapping'),
      ('absent.http_stream_id','No HTTP/2 or HTTP/3 stream ID or TLS session correlation key'),
      ('absent.client_clock_sync','No client monotonic event timestamps, clock offset/drift/RTT or capture-side event clock calibration'),
      ('absent.physical_timestamp_event','Exact online instrumentation event of source timestamp/latency/TTFT remains Unknown'),
    ]
    for path,meaning in missing:
        add(path,'Absent','not represented',meaning,'Actual Parquet schema + release mapping; paper/code audit','Confirmed absent from inspected public schema; broader private-source existence Unknown','No','No paired observables in this dataset','Requires authorized new collection or unreleased labels','Cannot build or validate network-only classifier from these missing inputs',SCHEMA)
    fields=['field_path','type','grain','meaning','provenance','observed_or_inferred','public_label','pcap_observable','classification_use','leakage_risk','evidence']
    with (ROOT/'data_dictionary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    (ROOT/'reports/observed_schemas.json').write_text(json.dumps({'source_commit':SHA,'dataset_revision':'bb26cf72c9c20f2b05f765d88548156a74d3c253','observed_week':week.name,'schemas':schemas,'parquet_top_level_field_count':38,'expanded_struct_child_field_count':5,'dictionary_rows':len(rows),'scope':'Schema only; no records/IDs/content'},indent=2)+'\n')
    print(json.dumps({'dictionary_rows':len(rows),'observed_parquet_top_level_fields':38,'expanded_struct_children':5,'jsonl_only_aliases_containers':len(extras),'explicit_absent_fields':len(missing)}))

if __name__=='__main__':main()
