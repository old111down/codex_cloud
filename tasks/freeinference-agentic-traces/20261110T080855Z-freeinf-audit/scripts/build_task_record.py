"""Build an evidence index from saved command metadata; never run an experiment."""
from __future__ import annotations
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(path):
    return json.loads(path.read_text())
def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
def utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--finish", action="store_true")
    parser.add_argument("--pr-url")
    args = parser.parse_args()
    info = load(ROOT / "run_info.json")
    now = stamp()
    commands = []
    for path in sorted((ROOT / "logs").rglob("*.json")):
        rec = load(path)
        if not isinstance(rec, dict) or "argv" not in rec or "exit_code" not in rec:
            continue
        rel = path.relative_to(ROOT).as_posix()
        commands.append({"command": rec["argv"], "cwd": rec.get("cwd", "Unknown"),
                         "start_time_utc": rec.get("start_utc"), "end_time_utc": rec.get("end_utc"),
                         "exit_code": rec["exit_code"],
                         "status": "Verified" if rec["exit_code"] == 0 else "Failed",
                         "scope": "Process outcome only; scientific scope is qualified in reproduction_report.md",
                         "evidence": [rel, rel.removesuffix(".json") + ".log"]})
    commands.sort(key=lambda c: c["start_time_utc"] or "")
    finding = lambda description, status, evidence, kind="source_fact": {
        "description": description, "status": status, "evidence_type": kind, "evidence": evidence}
    source = lambda name, url, sha: {"name": name, "url": url, "commit_shas": [sha],
                                   "license": "Unknown unless qualified in source evidence", "version_status": "Verified"}
    metadata = {
        "schema_version": "1.0", "task_id": info["run_id"],
        "task_name": "FreeInference Agent Traces deep audit and network-research feasibility",
        "task_slug": info["task_slug"], "run_id": info["run_id"],
        "archive_repository": "https://github.com/old111down/codex_cloud",
        "start_time_utc": info["t0_utc"], "end_time_utc": now if args.finish else None,
        "archive_started_time_utc": "2026-11-10T08:08:55Z", "archive_completed_time_utc": None,
        "deadline_utc": info["deadline_utc"], "record_generated_at_utc": now,
        "objective": "Audit full paper, public implementation/data/labels and actual CPU execution; design defensible self-collected trace–PCAP alignment and Hermes MVP without claiming unrun success.",
        "branch": info["branch"], "related_runs": [],
        "inherited_policy": "Root archive conventions only; this run does not reuse prior network/AR/XR experimental data or reset its own T0.",
        "source_repositories": [
            source("FreeInference trace", "https://github.com/HarvardMadSys/freeinference_agentic_trace", "2b795dbf5eac490a7c081906fdce6cc7a184b7ef"),
            source("FreeInference current Gateway", "https://github.com/HarvardMadSys/hybridInference", "7f7585bc60a303f9dc8e2a0f219ab7f0b99f3255"),
            source("Hermes", "https://github.com/NousResearch/hermes-agent", "b7db40d82568ea68ce321ac1ead3bfea354c7f56"),
            source("MAGIC26", "https://github.com/simula/magic26", "bf6797f7da735a6fccb8f140f27106c78a87490f"),
            source("TraceLab", "https://github.com/uw-syfi/TraceLab", "5c6550b0d08beff983e9159fe2575e7a2334c8c1")],
        "data_source": load(ROOT / "reports/data_source_summary.json"),
        "runtime_environment": load(ROOT / "environment/host_summary.json"), "commands_executed": commands,
        "completed_work": [finding("Full18-page paper and public source/schema/label audit;16figures and7tables enumerated", "Verified", ["paper_analysis.md", "paper_code_coverage.csv"]),
            finding("Independent Conda plus48Parquet checksum/aggregate audit;top-level Table1 inventory matches", "Verified", ["data_validation_report.md", "reports/data_manifest.csv"], "runtime_observation"),
            finding("Original full16-week Make statistics/figures;author cache intermediates reused", "Partially Verified", ["paper_execution_report.md", "logs/official_checks/paper_all_weeks.json"], "runtime_observation"),
            finding("Actual original simulation on3real selectedsessions and11synthetic alignment checks", "Verified", ["reports/small_realdata_simulation_validation.json", "logs/alignment_synthetic_checks.log"], "runtime_observation")],
        "failed_experiments": [finding("Original Make missing default.venv;pytest collected0tests;one-week output8NaN;full-week simulation audit120s timeout", "Failed", ["reproduction_report.md", "logs/official_checks/"], "runtime_observation")],
        "important_findings": [finding("Current full public batchmix64.0174/35.9826 differs frompaper71.3/28.7;84.5%width iscall-weighted", "Verified", ["paper_metric_comparison.csv", "reports/batching_denominator_check.json"], "runtime_observation"),
            finding("Historical released trace cannot directlylabel independentlycapturedPCAP;own concurrent client/transport instrumentation isneeded", "Partially Verified", ["trace_pcap_alignment.md", "mvp_experiment_plan.md"]),
            finding("Anonymous modelcatalog lacks exact MiMoID;authorized availabilityUnknown;no inference attempted", "Verified", ["logs/alignment_public_http_checks.json"], "runtime_observation")],
        "unverified_claims": [finding("Historical deployment/timing instrumentation;95%reconstruction validation;intent labels/quality;full independent cache replay;pairedAgentPCAP/classifier", "Unknown", ["reproduction_report.md", "task_report.md"], "unverified_question")],
        "artifacts": [{"path": p, "status": "Verified", "description": "Original audit artifact; status refers to presence, not full-paper success", "publication_review": "approved"}
                      for p in ["README.md", "task_report.md", "paper_analysis.md", "architecture.md", "data_dictionary.csv", "label_mechanisms.csv", "session_reconstruction.md", "paper_code_coverage.csv", "paper_metric_comparison.csv", "reproduction_report.md", "trace_pcap_alignment.md", "mvp_experiment_plan.md", "research_opportunities.md", "execution_timeline.md", "execution_log.md"]],
        "publication_review": {"status": "Partially Verified", "manifest": "reports/publication_manifest.json", "withheld_manifest": "reports/withheld_artifacts.md", "limitations": ["Explicitly reviewed export only;pattern scans alone cannot guarantee absence of all sensitive information"]},
        "final_status": "Partially Verified", "final_status_scope": "Audit evidence complete within scope;paper results and downstream network feasibility only partially verified",
        "pull_request_url": args.pr_url,
        "limitations": ["NoPCAP/noAgent/modelinference", "Nohistoricalrawlogs/intentdata", "Authorcacheintermediatesreused", "NoautomaticPRmerge"]}
    if (ROOT / "reports/remote_verification.json").exists():
        metadata["remote_verification"] = load(ROOT / "reports/remote_verification.json")
    (ROOT / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    elapsed = (utc(now) - utc(info["t0_utc"])).total_seconds()
    lines = ["# 实际执行时间线", "", f"T0：{info['t0_utc']}；硬截止：{info['deadline_utc']}；本记录生成：{now}。", "",
             f"截至记录生成累计 {elapsed/60:.2f} 分钟；没有等待耗尽预算。并行子任务的时段相互重叠，不相加冒充总墙钟时间。", "",
             "| UTC时段 | 已执行阶段 | 状态/范围 |", "|---|---|---|",
             "| 08:06:28起 | 读完整用户请求、环境/归档指令、任务分工 | 新任务T0，不重跑昨日任务 |",
             "| 08:08:55起 | 检查GitHub身份/写权限，fetch main，新建独立worktree/分支 | 原有任务分支和历史保留 |",
             "| 08:10–08:13 | 固定论文/代码/HF版本；全文/源代码并行阅读；Conda构建 | 原始证据私有保存 |",
             "| 08:12–08:27 | 完整周先行，随后16周Parquet下载校验与列裁剪统计 | 48文件8.37GB，无108GBJSONL |",
             "| 08:16–08:27 | 原版失败、smoke、单周与全量统计、真实小子集cache | 缓存全周120秒超时如实保留 |",
             "| 08:21–08:24 | 公共GET/401检查及11项合成对齐检查 | 无模型调用、无Agent/PCAP |",
             "| 08:27起 | 论文/数据/时间与ID独立复核；分母差异、报告集成、公开安全审查 | 未验证根因保持Unknown |", "",
             "后续归档操作与远程提交收据见 `reports/remote_verification.json`、`reports/checkpoints.json`（生成后）。", "",
             "## 阻断及停止原因", "",
             "原始维护者日志/测试、95%验证集、intent正文/标签未公开；精确MiMo授权路由、capture权限未建立；未启动付费推理。完整cache重算未在本轮局部时限完成，保留小子集与作者中间表的不同证据等级。", "",
             "## 命令时间明细", "", "| 开始UTC | 结束UTC | 命令记录 | exit |", "|---|---|---|---|"]
    for c in commands:
        lines.append(f"| {c['start_time_utc']} | {c['end_time_utc']} | [{Path(c['evidence'][0]).stem}]({c['evidence'][0]}) | {c['exit_code']} |")
    (ROOT / "execution_timeline.md").write_text("\n".join(lines) + "\n")
    log = ["# 已执行命令索引", "", "下列argv/cwd/UTC/exit读取自执行当时的run_logged元数据；未把计划命令记作已执行。进程exit0仅是过程结果，科学范围以reproduction_report为准。原始stdout/stderr合并日志经公开检查后保留；数据/代码/PDF原件不上传。", ""]
    for c in commands:
        log += [f"## {Path(c['evidence'][0]).stem}", "", f"- UTC：{c['start_time_utc']} → {c['end_time_utc']}", f"- cwd：`{c['cwd']}`；exit：{c['exit_code']}",
                f"- [原始命令元数据]({c['evidence'][0]}) / [输出]({c['evidence'][1]})", "", "```json", json.dumps(c["command"], ensure_ascii=False), "```", ""]
    log += ["## 归档与只读源获取", "", "GitHub身份/写权限、main与工作区检查和来源HTTP获取另记录于source_provenance、alignment_evidence及related source_manifest。没有保存凭据或完整平台状态。归档命令的检查点和远程SHA见对应收据；Git提交不会被描述为实验验证。", ""]
    (ROOT / "execution_log.md").write_text("\n".join(log))
    fields = ["experiment", "start_utc", "end_utc", "actual_argv", "cwd", "exit_code", "status", "scope", "evidence"]
    with (ROOT / "reports/reproduction_results.csv").open("w") as out:
        writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader()
        for c in commands:
            writer.writerow({"experiment": Path(c["evidence"][0]).stem, "start_utc": c["start_time_utc"], "end_utc": c["end_time_utc"], "actual_argv": json.dumps(c["command"], ensure_ascii=False), "cwd": c["cwd"], "exit_code": c["exit_code"], "status": c["status"], "scope": c["scope"], "evidence": ";".join(c["evidence"])})
    print(json.dumps({"generated_at_utc": now, "elapsed_seconds": elapsed, "saved_command_records": len(commands), "finalized": args.finish}))
if __name__ == "__main__":
    main()
