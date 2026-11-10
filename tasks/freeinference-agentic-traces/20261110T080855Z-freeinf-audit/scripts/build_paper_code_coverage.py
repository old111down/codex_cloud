#!/usr/bin/env python3
"""Map the pinned public figure registry and independently inventoried paper items.

Uses AST rather than importing the third-party package. It does not execute
trace content or claim paper-level numerical reproduction.
"""
import ast
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream/freeinference_agentic_trace"
SHA = "2b795dbf5eac490a7c081906fdce6cc7a184b7ef"
BASE = f"https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/{SHA}/"
FIELDS = "claim_id,paper_page_section,figure_table,research_question,data_source,features,method,code_path_function,entrypoint,measured_or_inferred_or_simulated,execution_status,coverage_status,missing,evidence".split(",")


def source_ref(function):
    parts = ["paper"] + function.split(".")[:-1]
    path = UPSTREAM.joinpath(*parts).with_suffix(".py")
    if not path.exists():
        path = UPSTREAM.joinpath(*parts, "__init__.py")
    line = 1
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function.split(".")[-1]:
            line = node.lineno
            break
    rel = path.relative_to(UPSTREAM).as_posix()
    return f"{rel}:{line}::{function.split('.')[-1]}", BASE + rel + f"#L{line}"


def registry():
    tree = ast.parse((UPSTREAM / "paper/__init__.py").read_text())
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "FIGURES" for t in n.targets))
    return [dict(zip(["paper", "section", "key", "function", "outputs", "shows"], [ast.literal_eval(a) for a in call.args])) for call in assignment.value.elts]


def main():
    inv = json.loads((ROOT / "research_notes/paper_workload_characterization/inventory.json").read_text())
    figures = {i["number"]: i for i in inv["figures"]}
    tables = {i["number"]: i for i in inv["tables"]}
    runtime_numbers_path = ROOT / "private/runtime/figures/numbers.json"
    runtime_numbers = json.loads(runtime_numbers_path.read_text()) if runtime_numbers_path.exists() else {}
    rows = []
    for index, item in enumerate(registry(), 1):
        paper_name = item["paper"]
        numeric = "".join(c for c in paper_name if c.isdigit())
        number = int(numeric) if numeric else None
        target = (tables if paper_name.startswith("Table") else figures).get(number, {})
        section = item["section"]
        is_sim = section == "prefix_caching" and item["key"] not in {"hit_ratio_by_gap_bin", "retention_by_provider", "gap_by_cause", "mean_hit_ratio_by_cause"}
        is_sim |= section == "benchmark_vs_production" and item["key"] == "prefill_against_storage"
        kind = "trace-driven simulation / counterfactual" if is_sim else "production-derived metadata statistics"
        if item["key"].startswith("ttft_decomposition") or item["key"] in {"session_time_breakdown", "speedup_if_twice_as_fast", "latency_by_batch_width"}:
            kind = "mixed measured gateway values and inferred/modelled quantities"
        path, evidence = source_ref(item["function"])
        values = runtime_numbers.get(section, {}).get(item["key"], {})
        state = "Not executed; static mapping verified"
        if runtime_numbers:
            if str(values.get("drawn", "")).startswith("no:"):
                state = "Not drawn by official all16-week run: " + values["drawn"]
            elif item["key"] in runtime_numbers.get(section, {}):
                state = "Executed on all16 public weeks (original controlled Make target)"
                if is_sim:
                    state += "; redraw from author-precomputed simulation (not a cache replay rerun)"
            else:
                state = "Unknown: key absent from official all16-week output"
        missing = "Original gateway collection/reconstruction ground truth not reverified; numeric agreement assessed separately in paper_metric_comparison.csv"
        if is_sim:
            missing += "; all16-week cache aggregates supplied by authors; smaller complete-week replay evidence is separate"
        if item["key"] == "speedup_if_twice_as_fast":
            missing += "; hypothetical 2x improvement, tool waits capped15min, excludes human time"
        if item["key"].startswith("ttft_decomposition"):
            missing += "; prefill/queueing split inferred from >=200 long misses, not serving telemetry"
        rows.append(dict(zip(FIELDS, [
            f"REG-{index:02d}", f"PDFp{target.get('pdf_page', 'Unknown')}; {section}", paper_name,
            item["shows"], "Public release sessions/requests/tool_calls Parquet" + (" + tracked simulation/*.parquet" if is_sim else ""),
            "; ".join(item["outputs"]) or item["key"], target.get("evidence_kind", "Descriptive aggregate from public schema"),
            path, f"python -m paper --only '{paper_name}' --release RELEASE --simulation SIM --output OUTPUT (draws entire section)",
            kind, state, "Partially Verified" if is_sim or not runtime_numbers else "Verified", missing,
            f"{inv['paper_url']}#page={target.get('pdf_page', 1)}; {evidence}; " + ("logs/official_checks/paper_all_weeks.json" if runtime_numbers else "paper/__init__.py registry static read")
        ])))

    def add(cid, page, item, question, data, features, method, code, entry, kind, execution, status, missing, evidence):
        rows.append(dict(zip(FIELDS, [cid, page, item, question, data, features, method, code, entry, kind, execution, status, missing, evidence])))

    add("EX-01", "PDFp2 §2", "Figure1", "Execution hierarchy session/turn/request/tool call", "Conceptual definition", "session, turn, tool loop", "Conceptual diagram", "release/schema.py; release/convert.py", "Not applicable", "conceptual", "Not applicable", "Not applicable", "Original drawing source not required for numeric reproduction", inv["paper_url"] + "#page=2")
    add("EX-02", "PDFp2 §2", "Table2", "Comparison to prior workload traces", "Cited literature", "trace features and provenance", "Literature comparison", "Unknown", "Not applicable", "literature synthesis", "Not applicable", "Not applicable", "Not a release-data calculation", inv["paper_url"] + "#page=2")
    add("EX-03", "PDFp3 §3.1", "Table3", "Internal gateway trace fields", "Private original gateway logs", "message bodies, timing, account metadata", "Gateway logging", "export/log_records; export/requests", "python -m export build --week WEEK (private inputs required)", "measured private input inventory", "Not executed: private logs unavailable", "Partially Verified", "Table3 includes text; public release intentionally excludes it", inv["paper_url"] + "#page=3; " + BASE + "release/schema.py")
    add("EX-04", "PDFp3 §3.2", "95% session-link validation", "Session reconstruction agreement on explicit-ID harness subset", "Private raw messages plus explicit session-ID ground truth", "tool IDs; 8-word shingles; 128-request lookback", "Tool-ID links then content-prefix overlap", "export/sessions/link.py; export/reports/reference_comparison.py", "python -m export build --week WEEK; export report reference requires external reference", "inferred sessions; validation claim", "Not executed", "Unknown", "Ground-truth subset, sample size, validation driver and full disagreement records unavailable; reference comparison is not proof of95%", inv["paper_url"] + "#page=3; " + BASE + "export/sessions/")
    add("EX-05", "PDFp6–7 §5.2", "Table6b", "Subagent frequency, fanout, synchronous versus asynchronous use", "Public parent-session/tool-call structure partly usable", "parent_session_id, spawned_by_step/call_index, waits", "Nested-session/fanout reconstruction", "release/schema.py; paper/metrics/tools.py::overview_table covers Subagent session share; no fanout/fanin draw entry located", "python -m paper --only 'Table5' covers session-share component only", "inferred subagent structure", "Subagent session share computed in Table5; remaining profile not executed", "Partially Verified", "No Table6b dedicated aggregate/plot/registry implementation for fanout/fanin found", inv["paper_url"] + "#page=6; " + BASE + "paper/__init__.py")
    add("EX-06", "PDFp7 §5.2", "Figure7a–b", "Synchronous fanout straggler imbalance and role/work/mixed group types", "Public nested metadata partly usable; original classification evidence Unknown", "fanout sibling completion/request/token imbalance; agent roles", "Subagent-group statistics", "No dedicated analysis or registry entry located", "Unknown", "inferred straggler groups and role/work labels", "Not executed", "Missing", "No provided grouping/classification function or released exact Fig7 aggregates; schema alone does not supply methodology implementation", inv["paper_url"] + "#page=7; " + BASE + "paper/__init__.py")
    add("EX-07", "PDFp12 §7", "Figure16a–b", "User-intent shifts and intent transition matrix", "Random sample1.8K sessions/about10K turns; private prompts", "8 intent labels from few-shot LLM", "Few-shot intent labeling then transition counts", "No intent annotation code, label column or registry entry located", "Unknown", "LLM-inferred labels", "Not executed", "Missing", "Prompt text, label table, classifier model/prompt/examples, seeds, validation and code absent; cannot reconstruct from public token-count metadata", inv["paper_url"] + "#page=12; " + BASE + "release/schema.py; " + BASE + "paper/__init__.py")
    add("PIPE-01", "README Reproduction; PDFp3 §3", "Source export pipeline", "Build anonymized release from gateway logs", "Private original logs, private/export.toml, salt/provider mappings", "extraction→sessions→analysis→toolcalls→anonymization", "Maintainer pipeline", "export/build_steps.py; export/__main__.py", "make week-WEEK", "inferred and anonymized release construction", "Dry-run only", "Partially Verified", "Maintainer configuration/logs/salts/reference and tests intentionally not published", BASE + "Makefile; " + BASE + "export/paths.py; logs/official_checks/readme_make_dry_run.log")
    add("PIPE-02", "README Reproduction", "Setup and tests", "Install official dependencies and execute test target", "Official pyproject dependency ranges", "Python>=3.12 and declared packages", "Conda-compatible environment; original Make setup dry-run", "Makefile; pyproject.toml", "make setup; python -m pytest -p no:cacheprovider", "runtime environment", "Dependencies installed by data agent; pytest exit5 (0tests)", "Partially Verified", "Original .venv creation not executed; published tests/ absent; no public test suite passed", "logs/official_checks/readme_make_dry_run.log; logs/official_checks/public_tests.json")
    add("PIPE-03", "README Reproduction", "Parquet download and integrity", "Fetch all16 public weeks; validate fixed checksums", "HF public Parquet at pinned revision, all16weeks", "48tables +16manifests +16tables.json", "Bounded download and official reader checks", "release/download.py; release/reader.py::check_week", "python -m release download --tables --week 2026-08-30 --release DIR --hub DIR (official syntax; actual acquisition commands in data report)", "public measured metadata with inference fields", "All16weeks downloaded and official reader checks passed during Make figures; see data_validation_report.md", "Verified", "108GB anonymous JSONL not downloaded; original private gateway data unavailable", BASE + "release/download.py; " + BASE + "release/reader.py; data_validation_report.md; reports/data_manifest.csv")
    add("PIPE-04", "README Reproduction", "JSONL→Parquet conversion", "Recover flattened public tables from nested anonymous traces", "108GB decompressed anonymous JSONL across16weeks", "schema columns; nested session traversal", "Official converter", "release/convert.py", "python -m release convert --release DIR", "schema-preserving transformation", "Not executed", "Unknown", "Raw JSONL not downloaded within storage budget; not confused with private gateway logs", BASE + "release/convert.py; " + BASE + "README.md")
    add("PIPE-05", "PDFp8–10 §6", "Cache replay all policies/TTLs", "Recompute tracked simulation intermediates from prefix blocks", "Aug30 requests.block_ids; fresh cache perweek", "16-token blocks;64 partitions;13TTLs;4policies;2scopes", "Block-level trace-driven cache replay", "simulation/simulate.py::simulate_week; simulation/cache.py::tally", "python -m simulation --week 2026-08-30 --release DIR --output DIR --processes 1", "simulation (not hardware measurements)", "Full Aug30week: timeout124 after120s under8GiB audit guard; no complete artifacts", "Partially Verified", "Full16-week replay not executed; timeout is this audit budget observation, not proof cloud replay impossible", BASE + "simulation/simulate.py; " + BASE + "simulation/cache.py; logs/official_checks/simulation_one_week_guarded.json")
    add("PIPE-06", "Smoke test (audit-defined)", "Cache algorithm hand check", "Three reads: first miss, gaps4s/14s, TTL1s/10s/infinite", "Synthetic3reads, not original traces", "one16-token block; three request timestamps", "Official sort_reads+tally with hand-derived assertions", "simulation/cache.py::sort_reads,tally; scripts/smoke_official_cache.py", "PYTHONPATH=UPSTREAM python scripts/smoke_official_cache.py", "synthetic smoke test", "Passed exit0", "Verified", "Does not validate paper metrics, real provider cache or GPU behavior", "logs/official_checks/cache_synthetic_smoke.json; logs/official_checks/cache_synthetic_smoke.log")
    add("PIPE-07", "Audit-defined public-data subset", "Cache+cheaper-reads full pipeline smoke", "Exercise original simulator on a bounded real-data subset", "Derived3complete childless top-level sessions/42requests/39toolcalls fromAug30", "539494block reads; original block IDs; separate derived manifest", "Original64partition/13TTL/4policy CLI; firstread/conservation/monotonicity checks", "simulation/__main__.py; scripts/prepare_small_realdata_release.py; scripts/verify_small_realdata_simulation.py", "python -m simulation --week 2026-08-30 --release SMALL_RELEASE --output OUTPUT --processes 1", "simulation on a real-data subset", "Passed exit0/2.43s;52tallies+63cheaper-read rows; invariant checks passed", "Verified", "Subset is not original fullweek population; resulting hit/miss counts are not paper metrics", "reports/small_realdata_subset_provenance.json; reports/small_realdata_simulation_validation.json; logs/official_checks/simulation_small_realdata.json")
    add("PIPE-08", "Audit-defined partial-week output check", "Empty benchmark scope", "Does plotting exit0 imply finite meaningful comparison outputs?", "Aug30week has no SWE-Bench sessions", "4benchmark medians+4ratios; zero benchmark trajectory", "Finite-number audit and isolated runtime-error fix", "paper/benchmark_vs_production/__init__.py; patches/0001-report-empty-benchmark-scope.patch", "python -m paper --release ONE_WEEK --simulation SIM --output OUTPUT; scripts/validate_paper_numbers.py", "runtime boundary condition", "Original exit0 but8NaN; quality check exit1; isolated patch check exit0", "Verified", "Patch skips entire comparison section when either population empty; original all16run has both scopes and0NaN; no upstream modification", "reports/paper_one_week_numeric_quality.json; reports/paper_all_weeks_numeric_quality.json; logs/official_checks/empty_scope_patch_check.json")
    for cid, week, log, comparison in [("PIPE-09", "2026-06-07_2026-06-13", "simulation_complete_smallest_week", "complete_smallest_week_simulation_comparison"),
                                       ("PIPE-10", "2026-05-31_2026-06-06", "simulation_complete_mixed_scope_week", "complete_mixed_scope_week_simulation_comparison")]:
        result_path = ROOT / "reports" / (comparison + ".json")
        result = json.loads(result_path.read_text()) if result_path.exists() else {}
        state = "Completed independent full-week replay; all four tables match author keys and values exactly" if result.get("status") == "Verified" else "Unknown: run/comparison not yet complete"
        add(cid, "PDFp8–10 §6; audit-selected complete week", "Independent complete-week cache+cheaper-reads replay", "Verify original simulation from full public week against author's same-week outputs", f"Complete public week {week}; no rows/subsessions sampled away", "16-token blocks;64partitions;13TTLs;4policies; separate available scopes", "Original explicit --week CLI followed by key/integer/float comparisons", "simulation/__main__.py; scripts/compare_complete_week_simulation.py", f"python -m simulation --week {week[:10]} --release RELEASE --output FRESH --processes 1", "simulation independently recomputed for this week only", state, "Verified" if result.get("status") == "Verified" else "Unknown", "Does not upgrade all16week paper simulation values; GPU/provider hardware and missing intent/subagent experiments remain unverified", f"reports/{comparison}.json; reports/{comparison}.csv; logs/official_checks/{log}.json; reports/full_week_replay_selection.json")

    destination = ROOT / "paper_code_coverage.csv"
    with destination.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / "research_notes/code_coverage_and_runtime/coverage_inventory.json").write_text(json.dumps({"source_sha": SHA, "registry_items": len(registry()), "independent_extra_items": len(rows)-len(registry()), "rows": len(rows), "coverage_semantics": "code/data evidence only; no full-paper numerical reproduction claimed"}, indent=2)+"\n")
    print(json.dumps({"output": str(destination), "rows": len(rows), "registry_items": len(registry())}))


if __name__ == "__main__":
    main()
