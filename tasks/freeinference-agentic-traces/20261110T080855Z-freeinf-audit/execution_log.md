# 已执行命令索引

下列argv/cwd/UTC/exit读取自执行当时的run_logged元数据；未把计划命令记作已执行。进程exit0仅是过程结果，科学范围以reproduction_report为准。原始stdout/stderr合并日志经公开检查后保留；数据/代码/PDF原件不上传。

## conda_create

- UTC：2026-11-10T08:10:56.581892+00:00 → 2026-11-10T08:11:05.045550+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/conda_create.json) / [输出](logs/conda_create.log)

```json
["/workspace/traffic-repro-audit/.tools/miniforge3/bin/conda", "create", "-y", "--override-channels", "-c", "conda-forge", "-p", "/workspace/freeinference-audit/.conda/freeinference", "python=3.12", "pip"]
```

## official_dependencies_install

- UTC：2026-11-10T08:12:06.154599+00:00 → 2026-11-10T08:12:28.681009+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_dependencies_install.json) / [输出](logs/official_dependencies_install.log)

```json
[".conda/freeinference/bin/python", "-m", "pip", "install", "--no-cache-dir", "-r", "environment/freeinference/requirements-from-upstream.txt"]
```

## selected_requests_download

- UTC：2026-11-10T08:12:57.785482+00:00 → 2026-11-10T08:15:28.487922+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/selected_requests_download.json) / [输出](logs/selected_requests_download.log)

```json
["python", "scripts/download_selected_week.py"]
```

## readme_make_dry_run

- UTC：2026-11-10T08:13:47.918210+00:00 → 2026-11-10T08:13:47.931937+00:00
- cwd：`/workspace/freeinference-audit/upstream/freeinference_agentic_trace`；exit：0
- [原始命令元数据](logs/official_checks/readme_make_dry_run.json) / [输出](logs/official_checks/readme_make_dry_run.log)

```json
["make", "-n", "setup", "figures", "test", "week-2026-08-30"]
```

## release_help

- UTC：2026-11-10T08:13:55.447728+00:00 → 2026-11-10T08:13:56.037446+00:00
- cwd：`/workspace/freeinference-audit/upstream/freeinference_agentic_trace`；exit：0
- [原始命令元数据](logs/official_checks/release_help.json) / [输出](logs/official_checks/release_help.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "-m", "release", "download", "--help"]
```

## readme_make_figures_original

- UTC：2026-11-10T08:13:55.477194+00:00 → 2026-11-10T08:13:55.481611+00:00
- cwd：`/workspace/freeinference-audit/upstream/freeinference_agentic_trace`；exit：2
- [原始命令元数据](logs/official_checks/readme_make_figures_original.json) / [输出](logs/official_checks/readme_make_figures_original.log)

```json
["make", "figures", "PROCESSES=1"]
```

## public_tests

- UTC：2026-11-10T08:13:55.480507+00:00 → 2026-11-10T08:13:55.999182+00:00
- cwd：`/workspace/freeinference-audit/upstream/freeinference_agentic_trace`；exit：5
- [原始命令元数据](logs/official_checks/public_tests.json) / [输出](logs/official_checks/public_tests.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "-m", "pytest", "-p", "no:cacheprovider"]
```

## cache_synthetic_smoke

- UTC：2026-11-10T08:15:00.574769+00:00 → 2026-11-10T08:15:01.140361+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/cache_synthetic_smoke.json) / [输出](logs/official_checks/cache_synthetic_smoke.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=/workspace/freeinference-audit/upstream/freeinference_agentic_trace", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/smoke_official_cache.py"]
```

## paper_one_week

- UTC：2026-11-10T08:17:59.825384+00:00 → 2026-11-10T08:18:24.113195+00:00
- cwd：`/workspace/freeinference-audit/upstream/freeinference_agentic_trace`；exit：0
- [原始命令元数据](logs/official_checks/paper_one_week.json) / [输出](logs/official_checks/paper_one_week.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "TMPDIR=/workspace/freeinference-audit/private/runtime/tmp", "MPLCONFIGDIR=/workspace/freeinference-audit/private/runtime/mpl", "MPLBACKEND=Agg", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/resource_guard.py", "--address-space-gib", "8", "--", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "-m", "paper", "--release", "/workspace/freeinference-audit/private/runtime/release_one_week", "--simulation", "/workspace/freeinference-audit/upstream/freeinference_agentic_trace/data/v1/simulation", "--output", "/workspace/freeinference-audit/private/runtime/figures_one_week"]
```

## processed_release_download

- UTC：2026-11-10T08:18:52.828811+00:00 → 2026-11-10T08:25:26.502890+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/processed_release_download.json) / [输出](logs/processed_release_download.log)

```json
["python", "scripts/download_processed_release.py"]
```

## paper_one_week_quality

- UTC：2026-11-10T08:19:09.945522+00:00 → 2026-11-10T08:19:10.009827+00:00
- cwd：`/workspace/freeinference-audit`；exit：1
- [原始命令元数据](logs/official_checks/paper_one_week_quality.json) / [输出](logs/official_checks/paper_one_week_quality.log)

```json
[".conda/freeinference/bin/python", "scripts/validate_paper_numbers.py", "private/runtime/figures_one_week/numbers.json", "--output", "reports/paper_one_week_numeric_quality.json"]
```

## simulation_one_week_guarded

- UTC：2026-11-10T08:19:23.600821+00:00 → 2026-11-10T08:21:23.635493+00:00
- cwd：`/workspace/freeinference-audit/upstream/freeinference_agentic_trace`；exit：124
- [原始命令元数据](logs/official_checks/simulation_one_week_guarded.json) / [输出](logs/official_checks/simulation_one_week_guarded.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "TMPDIR=/workspace/freeinference-audit/private/runtime/tmp", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/resource_guard.py", "--address-space-gib", "8", "--", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "-m", "simulation", "--week", "2026-08-30", "--release", "/workspace/freeinference-audit/private/runtime/release_one_week", "--output", "/workspace/freeinference-audit/private/runtime/recomputed_simulation", "--processes", "1"]
```

## profile_one_week

- UTC：2026-11-10T08:20:52.851899+00:00 → 2026-11-10T08:21:02.309338+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/profile_one_week.json) / [输出](logs/profile_one_week.log)

```json
[".conda/freeinference/bin/python", "scripts/profile_parquet.py", "--week", "2026-08-30", "--verify-checksums", "--output", "reports/aggregate_stats_one_week.json"]
```

## empty_scope_patch_check

- UTC：2026-11-10T08:21:33.652114+00:00 → 2026-11-10T08:21:37.078688+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/empty_scope_patch_check.json) / [输出](logs/official_checks/empty_scope_patch_check.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=/workspace/freeinference-audit/private/runtime/empty_scope_patch_source:/workspace/freeinference-audit/upstream/freeinference_agentic_trace", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "TMPDIR=/workspace/freeinference-audit/private/runtime/tmp", "MPLCONFIGDIR=/workspace/freeinference-audit/private/runtime/mpl", "MPLBACKEND=Agg", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/resource_guard.py", "--address-space-gib", "8", "--", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/check_empty_scope_patch.py"]
```

## prepare_small_realdata

- UTC：2026-11-10T08:22:54.026193+00:00 → 2026-11-10T08:22:58.400289+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/prepare_small_realdata.json) / [输出](logs/official_checks/prepare_small_realdata.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=/workspace/freeinference-audit/upstream/freeinference_agentic_trace", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "TMPDIR=/workspace/freeinference-audit/private/runtime/tmp", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/resource_guard.py", "--address-space-gib", "8", "--", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/prepare_small_realdata_release.py"]
```

## simulation_small_realdata

- UTC：2026-11-10T08:23:28.727120+00:00 → 2026-11-10T08:23:31.158514+00:00
- cwd：`/workspace/freeinference-audit/upstream/freeinference_agentic_trace`；exit：0
- [原始命令元数据](logs/official_checks/simulation_small_realdata.json) / [输出](logs/official_checks/simulation_small_realdata.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "TMPDIR=/workspace/freeinference-audit/private/runtime/tmp", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/resource_guard.py", "--address-space-gib", "8", "--", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "-m", "simulation", "--week", "2026-08-30", "--release", "/workspace/freeinference-audit/private/runtime/small_realdata_release", "--output", "/workspace/freeinference-audit/private/runtime/small_realdata_simulation", "--processes", "1"]
```

## build_data_dictionary

- UTC：2026-11-10T08:24:01.660558+00:00 → 2026-11-10T08:24:01.877678+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/build_data_dictionary.json) / [输出](logs/build_data_dictionary.log)

```json
[".conda/freeinference/bin/python", "scripts/build_data_dictionary.py"]
```

## alignment_synthetic_checks

- UTC：2026-11-10T08:24:25.402535+00:00 → 2026-11-10T08:24:25.467192+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/alignment_synthetic_checks.json) / [输出](logs/alignment_synthetic_checks.log)

```json
["python", "scripts/alignment/synthetic_checks.py"]
```

## small_realdata_simulation_validation

- UTC：2026-11-10T08:24:42.795494+00:00 → 2026-11-10T08:24:43.361789+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/small_realdata_simulation_validation.json) / [输出](logs/official_checks/small_realdata_simulation_validation.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=/workspace/freeinference-audit/upstream/freeinference_agentic_trace", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", ".conda/freeinference/bin/python", "scripts/verify_small_realdata_simulation.py"]
```

## paper_all_weeks

- UTC：2026-11-10T08:25:55.173910+00:00 → 2026-11-10T08:26:59.410799+00:00
- cwd：`/workspace/freeinference-audit/private/runtime/readme_workspace`；exit：0
- [原始命令元数据](logs/official_checks/paper_all_weeks.json) / [输出](logs/official_checks/paper_all_weeks.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "TMPDIR=/workspace/freeinference-audit/private/runtime/tmp", "MPLCONFIGDIR=/workspace/freeinference-audit/private/runtime/mpl", "MPLBACKEND=Agg", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/resource_guard.py", "--address-space-gib", "8", "--", "make", "figures", "PYTHON=/workspace/freeinference-audit/.conda/freeinference/bin/python", "PROCESSES=1"]
```

## profile_full_release

- UTC：2026-11-10T08:25:56.165992+00:00 → 2026-11-10T08:26:24.738260+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/profile_full_release.json) / [输出](logs/profile_full_release.log)

```json
[".conda/freeinference/bin/python", "scripts/profile_parquet.py", "--verify-checksums", "--output", "reports/aggregate_stats.json"]
```

## build_data_manifest

- UTC：2026-11-10T08:26:45.569041+00:00 → 2026-11-10T08:26:45.633764+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/build_data_manifest.json) / [输出](logs/build_data_manifest.log)

```json
[".conda/freeinference/bin/python", "scripts/build_data_manifest.py"]
```

## profile_full_release_final

- UTC：2026-11-10T08:27:22.292180+00:00 → 2026-11-10T08:27:51.184047+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/profile_full_release_final.json) / [输出](logs/profile_full_release_final.log)

```json
[".conda/freeinference/bin/python", "scripts/profile_parquet.py", "--verify-checksums", "--output", "reports/aggregate_stats.json"]
```

## paper_all_weeks_quality

- UTC：2026-11-10T08:27:30.119980+00:00 → 2026-11-10T08:27:30.184614+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/paper_all_weeks_quality.json) / [输出](logs/official_checks/paper_all_weeks_quality.log)

```json
[".conda/freeinference/bin/python", "scripts/validate_paper_numbers.py", "private/runtime/figures/numbers.json", "--output", "reports/paper_all_weeks_numeric_quality.json"]
```

## extra_paper_metrics_all_weeks

- UTC：2026-11-10T08:27:30.126214+00:00 → 2026-11-10T08:27:49.888005+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/extra_paper_metrics_all_weeks.json) / [输出](logs/official_checks/extra_paper_metrics_all_weeks.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=/workspace/freeinference-audit/upstream/freeinference_agentic_trace", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", ".conda/freeinference/bin/python", "scripts/resource_guard.py", "--address-space-gib", "8", "--", ".conda/freeinference/bin/python", "scripts/extract_extra_paper_metrics.py", "--release", "private/data/release", "--output", "reports/extra_paper_metrics_all_weeks.json"]
```

## anomaly_and_confounding_audit

- UTC：2026-11-10T08:28:39.715797+00:00 → 2026-11-10T08:28:40.184046+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/anomaly_and_confounding_audit.json) / [输出](logs/anomaly_and_confounding_audit.log)

```json
[".conda/freeinference/bin/python", "scripts/audit_aggregate_anomalies.py"]
```

## extra_paper_metrics_all_weeks_v2

- UTC：2026-11-10T08:29:37.096790+00:00 → 2026-11-10T08:29:55.616638+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/extra_paper_metrics_all_weeks_v2.json) / [输出](logs/official_checks/extra_paper_metrics_all_weeks_v2.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=/workspace/freeinference-audit/upstream/freeinference_agentic_trace", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "MPLCONFIGDIR=/workspace/freeinference-audit/private/runtime/mpl", "MPLBACKEND=Agg", ".conda/freeinference/bin/python", "scripts/resource_guard.py", "--address-space-gib", "8", "--", ".conda/freeinference/bin/python", "scripts/extract_extra_paper_metrics.py", "--release", "private/data/release", "--output", "reports/extra_paper_metrics_all_weeks_v2.json"]
```

## batching_denominator_check

- UTC：2026-11-10T08:30:17.016370+00:00 → 2026-11-10T08:30:17.985021+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/batching_denominator_check.json) / [输出](logs/official_checks/batching_denominator_check.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=/workspace/freeinference-audit/upstream/freeinference_agentic_trace", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", ".conda/freeinference/bin/python", "scripts/resource_guard.py", "--address-space-gib", "8", "--", ".conda/freeinference/bin/python", "scripts/check_batching_denominators.py", "--release", "private/data/release", "--output", "reports/batching_denominator_check.json"]
```

## summarize_data_validation

- UTC：2026-11-10T08:30:55.869935+00:00 → 2026-11-10T08:30:55.934442+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/summarize_data_validation.json) / [输出](logs/summarize_data_validation.log)

```json
[".conda/freeinference/bin/python", "scripts/summarize_data_validation.py"]
```

## workspace_preparation

- UTC：2026-11-10T08:32:25.125890+00:00 → 2026-11-10T08:32:25.240412+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/workspace_preparation.json) / [输出](logs/official_checks/workspace_preparation.log)

```json
[".conda/freeinference/bin/python", "scripts/prepare_official_workspaces.py", "--empty-scope-patch"]
```

## archive_checkpoint

- UTC：2026-11-10T08:38:33.321900+00:00 → 2026-11-10T08:38:35.194823+00:00
- cwd：`/workspace/codex_cloud_freeinference`；exit：0
- [原始命令元数据](logs/archive_checkpoint.json) / [输出](logs/archive_checkpoint.log)

```json
["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential", "push", "-u", "origin", "codex/freeinference-agentic-traces/20261110T080855Z-freeinf-audit"]
```

## complete_week_selection

- UTC：2026-11-10T08:44:17.624766+00:00 → 2026-11-10T08:44:18.140205+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/complete_week_selection.json) / [输出](logs/official_checks/complete_week_selection.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", ".conda/freeinference/bin/python", "scripts/select_complete_week_replay.py"]
```

## simulation_complete_smallest_week

- UTC：2026-11-10T08:44:45.286368+00:00 → 2026-11-10T08:46:35.580503+00:00
- cwd：`/workspace/freeinference-audit/upstream/freeinference_agentic_trace`；exit：0
- [原始命令元数据](logs/official_checks/simulation_complete_smallest_week.json) / [输出](logs/official_checks/simulation_complete_smallest_week.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "TMPDIR=/workspace/freeinference-audit/private/runtime/tmp", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/resource_guard.py", "--address-space-gib", "8", "--", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "-m", "simulation", "--week", "2026-06-07", "--release", "/workspace/freeinference-audit/private/data/release", "--output", "/workspace/freeinference-audit/private/runtime/complete_smallest_week_simulation", "--processes", "1"]
```

## compare_complete_smallest_week

- UTC：2026-11-10T08:47:04.749147+00:00 → 2026-11-10T08:47:05.367199+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/compare_complete_smallest_week.json) / [输出](logs/official_checks/compare_complete_smallest_week.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=/workspace/freeinference-audit/upstream/freeinference_agentic_trace", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", ".conda/freeinference/bin/python", "scripts/compare_complete_week_simulation.py", "--week", "2026-06-07_2026-06-13", "--recomputed", "private/runtime/complete_smallest_week_simulation", "--output", "reports/complete_smallest_week_simulation_comparison.json"]
```

## complete_mixed_scope_selection

- UTC：2026-11-10T08:48:30.093379+00:00 → 2026-11-10T08:48:30.658915+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/complete_mixed_scope_selection.json) / [输出](logs/official_checks/complete_mixed_scope_selection.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", ".conda/freeinference/bin/python", "scripts/select_complete_week_replay.py"]
```

## simulation_complete_mixed_scope_week_missing_time

- UTC：2026-11-10T08:48:30.698756+00:00 → 2026-11-10T08:48:30.699593+00:00
- cwd：`/workspace/freeinference-audit/upstream/freeinference_agentic_trace`；exit：127
- [原始命令元数据](logs/official_checks/simulation_complete_mixed_scope_week_missing_time.json) / [输出](logs/official_checks/simulation_complete_mixed_scope_week_missing_time.log)

```json
["/usr/bin/time", "-v", "-o", "/workspace/freeinference-audit/logs/official_checks/simulation_complete_mixed_scope_week.time.log", "env", "PYTHONDONTWRITEBYTECODE=1", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "TMPDIR=/workspace/freeinference-audit/private/runtime/tmp", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/resource_guard.py", "--address-space-gib", "8", "--", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "-m", "simulation", "--week", "2026-05-31", "--release", "/workspace/freeinference-audit/private/data/release", "--output", "/workspace/freeinference-audit/private/runtime/complete_mixed_scope_simulation", "--processes", "1"]
```

## simulation_complete_mixed_scope_week

- UTC：2026-11-10T08:49:16.915491+00:00 → 2026-11-10T08:52:27.782666+00:00
- cwd：`/workspace/freeinference-audit/upstream/freeinference_agentic_trace`；exit：0
- [原始命令元数据](logs/official_checks/simulation_complete_mixed_scope_week.json) / [输出](logs/official_checks/simulation_complete_mixed_scope_week.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", "TMPDIR=/workspace/freeinference-audit/private/runtime/tmp", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/run_with_resource_usage.py", "--output", "/workspace/freeinference-audit/reports/complete_mixed_scope_week_resource_usage.json", "--", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "/workspace/freeinference-audit/scripts/resource_guard.py", "--address-space-gib", "8", "--", "/workspace/freeinference-audit/.conda/freeinference/bin/python", "-m", "simulation", "--week", "2026-05-31", "--release", "/workspace/freeinference-audit/private/data/release", "--output", "/workspace/freeinference-audit/private/runtime/complete_mixed_scope_simulation", "--processes", "1"]
```

## compare_complete_smallest_week_with_footer

- UTC：2026-11-10T08:50:13.239939+00:00 → 2026-11-10T08:50:13.959851+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/compare_complete_smallest_week_with_footer.json) / [输出](logs/official_checks/compare_complete_smallest_week_with_footer.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=/workspace/freeinference-audit/upstream/freeinference_agentic_trace", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", ".conda/freeinference/bin/python", "scripts/compare_complete_week_simulation.py", "--week", "2026-06-07_2026-06-13", "--recomputed", "private/runtime/complete_smallest_week_simulation", "--output", "reports/complete_smallest_week_simulation_comparison.json"]
```

## compare_complete_mixed_scope_week

- UTC：2026-11-10T08:52:48.762567+00:00 → 2026-11-10T08:52:49.378455+00:00
- cwd：`/workspace/freeinference-audit`；exit：0
- [原始命令元数据](logs/official_checks/compare_complete_mixed_scope_week.json) / [输出](logs/official_checks/compare_complete_mixed_scope_week.log)

```json
["env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=/workspace/freeinference-audit/upstream/freeinference_agentic_trace", "OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "MKL_NUM_THREADS=2", ".conda/freeinference/bin/python", "scripts/compare_complete_week_simulation.py", "--week", "2026-05-31_2026-06-06", "--recomputed", "private/runtime/complete_mixed_scope_simulation", "--output", "reports/complete_mixed_scope_week_simulation_comparison.json"]
```

## archive_scientific

- UTC：2026-11-10T08:56:57.340542+00:00 → 2026-11-10T08:56:58.908293+00:00
- cwd：`/workspace/codex_cloud_freeinference`；exit：0
- [原始命令元数据](logs/archive_scientific.json) / [输出](logs/archive_scientific.log)

```json
["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential", "push", "origin", "codex/freeinference-agentic-traces/20261110T080855Z-freeinf-audit"]
```

## 归档与只读源获取

GitHub身份/写权限、main与工作区检查和来源HTTP获取另记录于source_provenance、alignment_evidence及related source_manifest。没有保存凭据或完整平台状态。归档命令的检查点和远程SHA见对应收据；Git提交不会被描述为实验验证。
