# Project State

## Date

2026-03-28

## Current Stage

Active stage:

- experiment execution and manuscript drafting in parallel

Completed foundations:

- workspace created
- provisional scope selected
- local evidence and risks recorded
- full `pytest -q tests` passed in `tianshou_env`
- the main evidence suite was packaged for paper-facing use
- the robustness suite completed and wrote its reports

Current focus:

- consolidate the corrected multi-seed ablation results into the paper-facing evidence stack
- keep the paper framing aligned with verified evidence
- convert the workspace from notes into a submission-ready draft

## One-Sentence Thesis

Deterministic, context-aligned evaluation can reveal when cluster-aware federated aggregation and post-aggregation distillation help multi-area voltage control under topology shift, and when they do not.

## Primary Direction

Primary paper route:

- strong empirical analysis plus evaluation protocol paper around the current FedGrid-v4 method family on case141

Backup routes:

- method paper if reruns show stable paired gains
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

## Current Packaging Decision

- `outputs/suites/case141_fedgrid_main_rr` is the main evidence package for the current paper cycle.
- `outputs/suites/case141_fedgrid_main_rr_20260326` is a partial validation rerun, not the primary evidence suite.
- `outputs/suites/case141_fedgrid_robust_rr_20260326` is a completed supporting suite with verified manifests, aggregate CSVs, figures, and report.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327` is a completed exploratory single-seed ablation and should not be used as the final ablation evidence package.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3` is the corrected completed multi-seed ablation suite and is now the final ablation evidence package for this cycle.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260326` is only a failed launch artifact and should not be cited.

Reason:

- the fresh rerun validated the current environment and pathing, but a full duplicate CPU-only rerun would consume many hours without improving the strongest available paper package today
- the custom multi-seed ablation adds more paper value per unit of compute than an immediate `full` sweep, so `full` is intentionally left opt-in for this cycle

## Execution Status

Current execution state:

- there is no required live training suite left for the default queue
- the corrected `case141_fedgrid_ablation_custom_rr_20260327_ms3` suite has already completed train, eval, summarize, table export, figure generation, and markdown report generation
- a fresh clean rerun of the `main` preset has now been launched as `outputs/suites/case141_fedgrid_main_rr_20260402_clean` to produce a current-workspace reproduction before the paper draft is frozen
- the first pass of `case141_fedgrid_main_rr_20260402_clean` only covered `seed0`; `seed1` and `seed2` are now being resumed into the same suite with `-SkipExisting` so the final main evidence package becomes multi-seed rather than single-seed
- because the historical PowerShell multi-seed launch path still binds only one seed at a time in this environment, `seed2` has been scheduled as an explicit follow-up launch after the live `seed1` resume finishes
- on 2026-04-03, the stale `Serena Dashboard` popup issue was traced to accumulated hourly `serena.cmd` trees under the Codex app; the stale trees were terminated and the `serena` MCP entry was disabled in both `E:\Codex\config.toml` and `C:\Users\ASUS\.codex\config.toml` for future sessions
- on 2026-04-03, `seed1` finished end to end and `seed2` was launched directly as a single-seed continuation into `case141_fedgrid_main_rr_20260402_clean` using `-Seeds 2 -SkipExisting`
- environment: `D:\Anaconda\envs\tianshou_env\python.exe`
- the remaining status-board mismatch came from a stale monitor heartbeat, not from ongoing training

Current orchestration layer:

- `scripts/fedgrid_autopilot.py` performs queue inspection, safe wait behavior, postprocess recovery, and next-suite launch decisions
- `scripts/launch_fedgrid_autopilot.ps1` can keep the autopilot loop alive in the background for this project cycle
- current queue status: robustness is complete and the corrected `case141_fedgrid_ablation_custom_rr_20260327_ms3` is complete
- `full` is not in the default queue
- after the 2026-03-27 recovery patch, suite launch uses a durable `Start-Process` path, a clean suite name, recent-log activity as a fallback running signal, and a non-special PowerShell variable name for the runner argument list
- after the 2026-03-28 status patch, a suite with a complete artifact set is treated as complete even if the monitor file still says `running`

## Current Negative Evidence

- In the existing main suite, paired return deltas are negative for `fedgrid_topo_proto` and `fedgrid_v4_cluster_distill` on both `random_reset` and `static`.
- Current local evidence does not yet justify a strong "new method beats baseline" headline.
- The completed robustness suite is interesting but still only single-seed, so it does not overturn the main-suite caution by itself.
- In the corrected multi-seed ablation, the cluster variants that matter for the mechanism story are not helping on paired return: `distill`, `nodistill`, and `gentle` are all negative relative to baseline.

## Unresolved Questions

- Existing artifacts still contain some historical path drift.
- The literature package exists, but it is still a starter set and needs broader coverage of the exact nearest-neighbor task papers.
- The exploratory `case141_fedgrid_ablation_custom_rr_20260327` suite should not be mistaken for the final multi-seed ablation evidence.
- The final paper framing should remain empirical-first because the corrected multi-seed ablation strengthens `topo_proto` but does not validate the clustered distillation family as a headline win.
- The optional `full` sweep should only be justified if the manuscript needs broader negative controls than `main + robustness + corrected ablation`.

## Publication Readiness Snapshot

Readiness today:

- codebase: medium
- experiment packaging: high
- manuscript evidence quality: medium to high
- reproducibility completeness: medium
- submission readiness: medium
