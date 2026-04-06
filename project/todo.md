# TODO

## Immediate

- [x] Create the `project/` workspace required by the autopilot skill.
- [x] Record current project state, decisions, scope, and experiment plan.
- [x] Verify full `pytest -q tests` inside `D:\Anaconda\envs\tianshou_env\python.exe`.
- [x] Run `main --dry_run --no_post` in the current workspace and record outputs.
- [x] Add a local autopilot orchestration layer that can watch the live queue and launch the next suite safely.
- [ ] Revalidate the existing `case141_fedgrid_main_rr` suite for path consistency and artifact completeness.
- [x] Decide whether to continue or stop the live `case141_fedgrid_main_rr_20260326` duplicate rerun.
- [x] Package the existing completed main suite into `docs/paper_package/`.

## Research

- [x] Build an initial verified external literature bibliography.
- [x] Fill `literature/related_work_matrix.csv` with a starter set of real papers and baselines.
- [x] Lock the current paper route as an empirical-analysis paper unless the live multi-seed ablation materially flips the evidence.

## Experiments

- [x] Reproduce `main` with deterministic postprocess outputs via `case141_fedgrid_main_rr_20260402_clean`; the final suite now contains the completed 3-seed package.
- [x] Run custom multi-seed ablation with `fedgrid_v4_cluster_nodistill` and `fedgrid_v4_cluster_gentle` in `case141_fedgrid_ablation_custom_rr_20260327_ms3`.
- [x] Run `robustness`.
- [x] Decide that `full` is not auto-queued in this cycle and should remain opt-in unless robustness plus ablation leave a decisive evidence gap.

## Live Queue

- [x] Launch `case141_fedgrid_robust_rr_20260326` in the background.
- [x] Verify `case141_fedgrid_robust_rr_20260326` completed with manifests, agg outputs, tables, figures, and report.
- [x] Decide that the next automated expensive run is the custom ablation suite.
- [ ] Keep `scripts/fedgrid_autopilot.py` running until the live custom ablation suite finishes cleanly.
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

## Cleanup

- [x] Add `outputs/suites/INDEX.md` for suite-level tracking.
- [ ] Normalize remaining references to old workspace paths.
