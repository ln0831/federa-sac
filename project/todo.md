# TODO

## Immediate

- [x] Create the `project/` workspace required by the autopilot skill.
- [x] Record current project state, decisions, scope, and experiment plan.
- [x] Verify full `pytest -q tests` inside `D:\Anaconda\envs\tianshou_env\python.exe`.
- [x] Run `main --dry_run --no_post` in the current workspace and record outputs.
- [x] Add a local autopilot orchestration layer that can watch the live queue and launch the next suite safely.
- [ ] Revalidate the existing `case141_fedgrid_main_rr` suite for path consistency and artifact completeness.
- [x] Write an audit note comparing `case141_fedgrid_main_rr` and `case141_fedgrid_main_rr_20260402_clean`, including the `fedgrid_topo_proto` sign flip and the clean-rerun manifest caveat.
- [x] Decide whether to continue or stop the live `case141_fedgrid_main_rr_20260326` duplicate rerun.
- [x] Package the existing completed main suite into `docs/paper_package/`.
- [x] Refresh `docs/paper_package/` and `submission/manuscript.md` so they reflect the finished clean rerun, the finished multi-seed ablation, and the new negative fresh replica rather than the older partially negative-only story.

## Research

- [x] Build an initial verified external literature bibliography.
- [x] Fill `literature/related_work_matrix.csv` with a starter set of real papers and baselines.
- [x] Lock the current paper route as an empirical-analysis paper unless the live multi-seed ablation materially flips the evidence.

## Experiments

- [x] Reproduce `main` with deterministic postprocess outputs via `case141_fedgrid_main_rr_20260402_clean`; the final suite now contains the completed 3-seed package.
- [x] Run custom multi-seed ablation with `fedgrid_v4_cluster_nodistill` and `fedgrid_v4_cluster_gentle` in `case141_fedgrid_ablation_custom_rr_20260327_ms3`.
- [x] Run `robustness`.
- [x] Decide that `full` is not auto-queued in this cycle and should remain opt-in unless robustness plus ablation leave a decisive evidence gap.
- [x] Run an independent fresh main replica under a new dated suite name to resolve the `case141_fedgrid_main_rr` versus `case141_fedgrid_main_rr_20260402_clean` discrepancy.
- [x] Stop the old live queue after the 2026-04-08 failure-mode audit instead of spending more compute on the pre-fix code path.
- [x] Refactor the active training and runner path to add explicit experiment seeds, fixed validation episode sets, delayed federated warmup, safer federation defaults, and paper-aligned `outage_k=4`.
- [x] Re-audit the repaired code path before resuming experiments.
- [ ] Finish the repaired fresh main replica `case141_fedgrid_main_rr_20260408_auditfix5`.
- [ ] Decide the next repaired queue after `auditfix5`, with the leading options being a repaired topo-proto power rerun and a repaired multi-seed robustness rerun.
- [ ] Finish the already-running higher-power `fedgrid_none` versus `fedgrid_topo_proto` follow-up and use it to quantify whether the mixed-sign main-benchmark result is merely unstable or actually positive in the narrower comparison.
- [ ] Finish the multi-seed robustness upgrade so the supporting evidence is no longer single-seed.

## Live Queue

- [x] Launch `case141_fedgrid_robust_rr_20260326` in the background.
- [x] Verify `case141_fedgrid_robust_rr_20260326` completed with manifests, agg outputs, tables, figures, and report.
- [x] Decide that the next automated expensive run is the custom ablation suite.
- [x] Keep `scripts/fedgrid_autopilot.py` running until the live custom ablation suite finishes cleanly.
- [x] Repair the broken custom-ablation queue launch path.
- [x] Recover the custom ablation under the clean suite name `case141_fedgrid_ablation_custom_rr_20260327`.
- [x] Detect that `case141_fedgrid_ablation_custom_rr_20260327` was still only single-seed and should remain exploratory.
- [x] Relaunch the corrected multi-seed ablation as `case141_fedgrid_ablation_custom_rr_20260327_ms3`.
- [x] Verify `case141_fedgrid_ablation_custom_rr_20260327_ms3` completes with manifests, agg outputs, tables, figures, and report.
- [x] Keep the fresh `case141_fedgrid_main_rr_20260402_clean` rerun alive until the resumed `seed1/seed2` train, eval, and postprocess chain all finish.
- [x] Verify the scheduled `seed2` follow-up actually fires after `seed1` because the PowerShell multi-seed wrapper is still truncating to a single live seed per launch in this environment.
- [x] Remove the stale `Serena Dashboard` popups by terminating old `serena.cmd` trees and disabling the `serena` MCP entry in local Codex configs for future sessions.

## Writing

- [x] Replace placeholders in `paper/abstract.md` with evidence-backed text.
- [x] Write `paper/related_work.md` from verified citations.
- [x] Tighten contributions to only what experiments support.
- [x] Assemble `submission/manuscript.md`.
- [x] Rewrite the manuscript narrative around the empirical-first route after the negative fresh replica, while treating the running topo-proto power suite as uncertainty reduction rather than headline proof.

## Cleanup

- [x] Add `outputs/suites/INDEX.md` for suite-level tracking.
- [ ] Normalize remaining references to old workspace paths.
- [x] Add `case141_fedgrid_main_rr_20260402_clean` to the active suite index with its reproducibility caveat.

## Q1 Queue

- [x] Create a dedicated Q1 queue file at `project/experiments/runs/q1_queue_20260407.json`.
- [x] Add Q1 launcher and status scripts.
- [x] Start the Q1 background autopilot.
- [x] Finish `case141_fedgrid_main_rr_20260407_replica`.
- [x] Recover the Q1 queue after the stalled `resume_needed` state and get `case141_fedgrid_topoproto_power_rr_20260407` running again.
- [x] Stop the Q1 queue before more compute after the 2026-04-08 failure-mode audit.
- [ ] Finish `case141_fedgrid_topoproto_power_rr_20260407`.
- [ ] Finish `case141_fedgrid_robust_rr_20260407_ms3`.
- [ ] Refresh manuscript and paper package against the completed Q1 queue outputs.
