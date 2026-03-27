# Project State

## Date

2026-03-27

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

- let the recovered custom ablation suite finish cleanly
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
- `case141_fedgrid_ablation_custom_rr_20260327_ms3` is now genuinely running as the corrected multi-seed ablation suite, with active logs and suite directory updates.

## Current Packaging Decision

- `outputs/suites/case141_fedgrid_main_rr` is the main evidence package for the current paper cycle.
- `outputs/suites/case141_fedgrid_main_rr_20260326` is a partial validation rerun, not the primary evidence suite.
- `outputs/suites/case141_fedgrid_robust_rr_20260326` is a completed supporting suite with verified manifests, aggregate CSVs, figures, and report.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327` is a completed exploratory single-seed ablation and should not be used as the final ablation evidence package.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3` is the active live experiment suite now running in the background.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260326` is only a failed launch artifact and should not be cited.

Reason:

- the fresh rerun validated the current environment and pathing, but a full duplicate CPU-only rerun would consume many hours without improving the strongest available paper package today
- the custom multi-seed ablation adds more paper value per unit of compute than an immediate `full` sweep, so `full` is intentionally left opt-in for this cycle

## Live Execution

Current active background run:

- suite: `case141_fedgrid_ablation_custom_rr_20260327_ms3`
- preset: custom ablation on top of the `main` runner path
- environment: `D:\Anaconda\envs\tianshou_env\python.exe`
- status at latest recovery check: training log, suite directory, and checkpoints are updating; the human-readable status board shows the suite as running

Current orchestration layer:

- `scripts/fedgrid_autopilot.py` performs queue inspection, safe wait behavior, postprocess recovery, and next-suite launch decisions
- `scripts/launch_fedgrid_autopilot.ps1` can keep the autopilot loop alive in the background for this project cycle
- current queue status: robustness is complete and the corrected `case141_fedgrid_ablation_custom_rr_20260327_ms3` is active
- `full` is not in the default queue
- after the 2026-03-27 recovery patch, suite launch uses a durable `Start-Process` path, a clean suite name, recent-log activity as a fallback running signal, and a non-special PowerShell variable name for the runner argument list

## Current Negative Evidence

- In the existing main suite, paired return deltas are negative for `fedgrid_topo_proto` and `fedgrid_v4_cluster_distill` on both `random_reset` and `static`.
- Current local evidence does not yet justify a strong "new method beats baseline" headline.
- The completed robustness suite is interesting but still only single-seed, so it does not overturn the main-suite caution by itself.

## Unresolved Questions

- Existing artifacts still contain some historical path drift.
- The literature package exists, but it is still a starter set and needs broader coverage of the exact nearest-neighbor task papers.
- The exploratory `case141_fedgrid_ablation_custom_rr_20260327` suite should not be mistaken for the final multi-seed ablation evidence.
- The live corrected custom ablation suite still needs final artifact verification after completion.
- The final paper framing should remain empirical-first unless the multi-seed ablation materially changes the evidence picture.

## Publication Readiness Snapshot

Readiness today:

- codebase: medium
- experiment packaging: medium to high
- manuscript evidence quality: medium
- reproducibility completeness: medium
- submission readiness: low to medium
