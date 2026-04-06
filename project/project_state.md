# Project State

## Date

2026-04-07

## Current Stage

Active stage:

- evidence reconciliation and Q1-oriented experiment planning

Completed foundations:

- workspace created
- provisional scope selected
- local evidence and risks recorded
- full `pytest -q tests` passed in `tianshou_env`
- the main evidence suite was packaged for paper-facing use
- the robustness suite completed and wrote its reports
- a clean current-workspace `main` rerun completed as `case141_fedgrid_main_rr_20260402_clean`

Current focus:

- reconcile the sign mismatch between the legacy main suite and the clean rerun
- decide whether the paper should stay purely empirical or upgrade to a narrow `fedgrid_topo_proto` story
- turn the experiment stack into a Q1-ready evidence package instead of a mixed historical bundle
- keep the new Q1 autopilot queue running until the fresh main replica, topo-proto power run, and multi-seed robustness upgrade all complete

## One-Sentence Thesis

Deterministic, context-aligned evaluation can reveal that simple prototype-sharing may help multi-area voltage control under topology shift, while clustered distillation remains unstable.

## Primary Direction

Primary paper route:

- strong empirical analysis plus evaluation protocol paper around the current FedGrid-v4 method family on case141

Backup routes:

- narrower method paper around `fedgrid_topo_proto` if independent reruns keep it positive
- robustness or negative-results paper if method gains remain weak but failure modes are informative

## Established Local Evidence

- The repository contains a unified runtime bundle with train, eval, summarize, export, figure, and report stages.
- `scripts/check_runtime_bundle.py --project_root .` passes in the current workspace.
- `D:\Anaconda\envs\tianshou_env\python.exe` imports `torch`.
- `D:\Anaconda\envs\tianshou_env\python.exe -m pytest -q tests` passes in the current workspace.
- `main --dry_run --no_post` completed for `case141_fedgrid_main_rr_20260326` and wrote fresh manifests under the current workspace path.
- Existing suites already contain manifests, checkpoints, aggregate CSVs, LaTeX tables, figures, and markdown reports.
- `case141_fedgrid_robust_rr_20260326` completed with verified aggregate and report artifacts.
- `case141_fedgrid_ablation_custom_rr_20260327` completed, but it only contains one seed because the old PowerShell launch wrapper truncated the seed list.
- `case141_fedgrid_ablation_custom_rr_20260327_ms3` completed end to end after manual postprocess recovery and now has manifests, aggregate CSVs, LaTeX tables, figures, and markdown report.
- `case141_fedgrid_main_rr_20260402_clean` first completed an end-to-end `seed0` reproduction with manifests, aggregate CSVs, LaTeX tables, figures, and markdown report.
- In `case141_fedgrid_ablation_custom_rr_20260327_ms3`, `fedgrid_topo_proto` is the only positive ablation result, with mean paired return gain about `+0.091` on `random_reset` and `+0.092` on `static` across 3 seeds.
- In `case141_fedgrid_ablation_custom_rr_20260327_ms3`, `fedgrid_v4_cluster_distill`, `fedgrid_v4_cluster_nodistill`, and `fedgrid_v4_cluster_gentle` all underperform the baseline on paired return.
- In the older `case141_fedgrid_main_rr` suite, `fedgrid_topo_proto` is negative on paired return on both `random_reset` and `static`.
- In the clean rerun `case141_fedgrid_main_rr_20260402_clean`, `fedgrid_topo_proto` becomes weakly positive on paired return on both `random_reset` and `static`, while `fedgrid_v4_cluster_distill` remains negative.
- The clean rerun aggregate outputs are clearly 3-seed, but the suite manifest only records the last resumed seed because the suite was finished through explicit single-seed continuation launches.

## Current Packaging Decision

- `outputs/suites/case141_fedgrid_main_rr` is the historical main evidence package and still matters because it carries the original negative result.
- `outputs/suites/case141_fedgrid_main_rr_20260402_clean` is the current-workspace reproduction package and currently provides the freshest main-benchmark evidence.
- `outputs/suites/case141_fedgrid_main_rr_20260326` is a partial validation rerun, not the primary evidence suite.
- `outputs/suites/case141_fedgrid_robust_rr_20260326` is a completed supporting suite with verified manifests, aggregate CSVs, figures, and report.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327` is a completed exploratory single-seed ablation and should not be used as the final ablation evidence package.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3` is the corrected completed multi-seed ablation suite and is now the final ablation evidence package for this cycle.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260326` is only a failed launch artifact and should not be cited.

Reason:

- the fresh rerun validated the current environment and pathing, but a full duplicate CPU-only rerun would consume many hours without improving the strongest available paper package today
- the custom multi-seed ablation adds more paper value per unit of compute than an immediate `full` sweep, so `full` is intentionally left opt-in for this cycle
- the clean rerun now matters because it materially changes the sign of the `fedgrid_topo_proto` conclusion relative to the older main suite, so the next experiment cycle must resolve that discrepancy before the paper thesis is frozen

## Execution Status

Current execution state:

- there is no required live training suite left for the default queue
- the corrected `case141_fedgrid_ablation_custom_rr_20260327_ms3` suite has already completed train, eval, summarize, table export, figure generation, and markdown report generation
- a fresh clean rerun of the `main` preset has now been launched as `outputs/suites/case141_fedgrid_main_rr_20260402_clean` to produce a current-workspace reproduction before the paper draft is frozen
- the first pass of `case141_fedgrid_main_rr_20260402_clean` only covered `seed0`; `seed1` and `seed2` are now being resumed into the same suite with `-SkipExisting` so the final main evidence package becomes multi-seed rather than single-seed
- because the historical PowerShell multi-seed launch path still binds only one seed at a time in this environment, `seed2` has been scheduled as an explicit follow-up launch after the live `seed1` resume finishes
- on 2026-04-03, the stale `Serena Dashboard` popup issue was traced to accumulated hourly `serena.cmd` trees under the Codex app; the stale trees were terminated and the `serena` MCP entry was disabled in both `E:\Codex\config.toml` and `C:\Users\ASUS\.codex\config.toml` for future sessions
- on 2026-04-03, `seed1` finished end to end and `seed2` was launched directly as a single-seed continuation into `case141_fedgrid_main_rr_20260402_clean` using `-Seeds 2 -SkipExisting`
- `case141_fedgrid_main_rr_20260402_clean` is now complete as a 3-seed package at the artifact level: 10 checkpoints, 30 eval files, aggregate CSVs, LaTeX tables, figures, and markdown report are all present
- environment: `D:\Anaconda\envs\tianshou_env\python.exe`
- the remaining status-board mismatch came from a stale monitor heartbeat, not from ongoing training
- after the final `seed2` continuation completed, the remaining `running=True` state was confirmed to be only the old monitor process; the monitor was stopped and the suite should now be treated as complete
- the next cycle has now been launched under a dedicated Q1 queue file at `project/experiments/runs/q1_queue_20260407.json`
- the live suite is `case141_fedgrid_main_rr_20260407_replica`
- the Q1 background status board is `outputs/automation_logs/fedgrid_q1_autopilot_status.md`
- after the main replica, the queue will continue automatically into `case141_fedgrid_topoproto_power_rr_20260407` and `case141_fedgrid_robust_rr_20260407_ms3`

Current orchestration layer:

- `scripts/fedgrid_autopilot.py` performs queue inspection, safe wait behavior, postprocess recovery, and next-suite launch decisions
- `scripts/launch_fedgrid_autopilot.ps1` can keep the autopilot loop alive in the background for this project cycle
- current queue status: robustness is complete and the corrected `case141_fedgrid_ablation_custom_rr_20260327_ms3` is complete
- `full` is not in the default queue
- after the 2026-03-27 recovery patch, suite launch uses a durable `Start-Process` path, a clean suite name, recent-log activity as a fallback running signal, and a non-special PowerShell variable name for the runner argument list
- after the 2026-03-28 status patch, a suite with a complete artifact set is treated as complete even if the monitor file still says `running`

## Current Negative Evidence

- In the existing main suite, paired return deltas are negative for `fedgrid_topo_proto` and `fedgrid_v4_cluster_distill` on both `random_reset` and `static`.
- Current local evidence still does not justify a strong "new clustered method beats baseline" headline.
- The completed robustness suite is interesting but still only single-seed, so it does not overturn the main-suite caution by itself.
- In the corrected multi-seed ablation, the cluster variants that matter for the mechanism story are not helping on paired return: `distill`, `nodistill`, and `gentle` are all negative relative to baseline.
- The legacy main suite and the clean rerun disagree on the sign of `fedgrid_topo_proto`, so the most important claim is still not stable enough for a Q1 submission.

## Unresolved Questions

- Existing artifacts still contain some historical path drift.
- The literature package exists, but it is still a starter set and needs broader coverage of the exact nearest-neighbor task papers.
- The exploratory `case141_fedgrid_ablation_custom_rr_20260327` suite should not be mistaken for the final multi-seed ablation evidence.
- The final paper framing should remain empirical-first unless a fresh independent main replica confirms the clean rerun and shrinks the uncertainty around `fedgrid_topo_proto`.
- The clean rerun manifest metadata should be repaired or at least documented, because it currently understates the actual seed count used in the aggregate outputs.
- The optional `full` sweep should only be justified if a fresh replica still leaves the paper thesis ambiguous and broader controls are needed.
- The Q1 queue itself is now running, so the main execution risk is no longer planning drift but only runtime stability and eventual result interpretation.

## Publication Readiness Snapshot

Readiness today:

- codebase: medium
- experiment packaging: high
- manuscript evidence quality: medium
- reproducibility completeness: medium
- submission readiness: medium
