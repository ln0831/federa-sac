# Background Context

This file is the long-lived context anchor for the project.

Use it to preserve operational details, paper-positioning constraints, and local facts that are easy to lose when the live conversation context is compressed.

## Project Identity

Repository:

- `C:\Users\ASUS\Desktop\runtime_bundle`

Research coordination workspace:

- `C:\Users\ASUS\Desktop\runtime_bundle\project`

Operational code source of truth:

- repository root scripts, not `project/`

## Active Code Path

Current active execution chain:

- `run_case141_fedgrid_v6.py`
- `train_gnn_fedgrid.py`
- `evaluate_topology_shift_deterministic.py`
- `summarize_fedgrid_suite_v6.py`
- `export_fedgrid_tables_v6.py`
- `make_fedgrid_figures_v6.py`
- `make_fedgrid_report_v6.py`
- `scripts/fedgrid_autopilot.py`
- `scripts/launch_fedgrid_autopilot.ps1`
- `scripts/launch_fedgrid_q1_autopilot.ps1`
- `scripts/show_fedgrid_q1_status.ps1`

Current active rules and docs:

- `docs/VERSION_MAP_AND_SOURCE_OF_TRUTH.md`
- `docs/EXPERIMENT_RUNBOOK.md`
- `docs/RESULTS_CHECKLIST.md`
- `docs/PAPER_TABLE_MAPPING.md`
- `docs/RUNTIME_EXECUTION_PLAN_20260326.md`
- `skills/fedgrid-runtime-runner/SKILL.md`
- `C:\Users\ASUS\Downloads\SKILL.md` for `paper-project-autopilot`
- `outputs/automation_logs/fedgrid_status.md` for the current human-readable task board
- `scripts/show_fedgrid_status.ps1` for one-shot status refresh on demand
- `outputs/automation_logs/fedgrid_q1_autopilot_status.md` for the Q1 queue status board
- `project/analysis/main_suite_reconciliation_20260407.md` for the current source-of-truth reconciliation note

## Environment Facts

Current default system Python observed in this workspace:

- `Python 3.13.2`

Usable environment already confirmed:

- `D:\Anaconda\envs\tianshou_env\python.exe`

Known facts:

- `tianshou_env` imports `torch 2.9.1+cpu`
- `D:\Anaconda\envs\tianshou_env\python.exe -m pytest -q tests` passed on 2026-03-26

Operational rule:

- use `tianshou_env` first before creating a new environment

## Existing Experiment Assets

Important existing suites:

- `outputs/suites/case141_fedgrid_main_rr`
- `outputs/suites/case141_fedgrid_main_rr_20260402_clean` as the clean current-workspace rerun
- `outputs/suites/case141_fedgrid_main_rr_20260407_replica` as the fresh independent main replica
- `outputs/suites/case141_fedgrid_topoproto_power_rr_20260407` as the running higher-power topo_proto suite
- `outputs/suites/case141_fedgrid_robust_rr_20260407_ms3` as the queued multi-seed robustness upgrade
- `outputs/suites/case141_fedgrid_tune_seed2_rr_v1`
- `outputs/suites/case141_fedgrid_main_rr_20260326` for the validation rerun
- `outputs/suites/case141_fedgrid_robust_rr_20260326` as the completed robustness suite
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327` as the completed single-seed exploratory ablation affected by the launch bug
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3` as the corrected completed multi-seed custom ablation run
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260326` only as a failed launch artifact that should not be treated as evidence

Important main-suite artifacts:

- `outputs/suites/case141_fedgrid_main_rr/manifests/fedgrid_v6_suite_manifest.json`
- `outputs/suites/case141_fedgrid_main_rr/manifests/fedgrid_v6_run_matrix.csv`
- `outputs/suites/case141_fedgrid_main_rr/agg/suite_paired_metrics.csv`
- `outputs/suites/case141_fedgrid_main_rr/reports/fedgrid_v6_report.md`
- `outputs/suites/case141_fedgrid_main_rr/reports/latex/table_main_random_reset.tex`
- `outputs/suites/case141_fedgrid_main_rr/reports/latex/table_appendix_static.tex`
- `outputs/suites/case141_fedgrid_main_rr/reports/figures/random_reset_delta_return.png`
- `outputs/suites/case141_fedgrid_main_rr/reports/figures/random_reset_delta_vviol.png`
- `outputs/suites/case141_fedgrid_main_rr/reports/figures/random_reset_delta_ploss.png`
- `outputs/suites/case141_fedgrid_main_rr_20260402_clean/agg/suite_paired_metrics.csv`
- `outputs/suites/case141_fedgrid_main_rr_20260402_clean/reports/fedgrid_v6_report.md`
- `outputs/suites/case141_fedgrid_main_rr_20260407_replica/agg/suite_paired_metrics.csv`
- `outputs/suites/case141_fedgrid_main_rr_20260407_replica/agg/suite_seed_level_paired.csv`
- `outputs/suites/case141_fedgrid_main_rr_20260407_replica/reports/fedgrid_v6_report.md`

## Important Evidence Constraints

Do not forget:

- the repository is runnable and has already produced complete-looking suite artifacts
- existing `main` artifacts are sufficient for auditing, but not yet sufficient for a strong positive method claim
- current paired return deltas in the existing `main` suite are negative for `fedgrid_topo_proto` and `fedgrid_v4_cluster_distill`
- the clean rerun `case141_fedgrid_main_rr_20260402_clean` changes the picture: `fedgrid_topo_proto` is weakly positive on paired return while `fedgrid_v4_cluster_distill` remains negative
- the fresh independent main replica `case141_fedgrid_main_rr_20260407_replica` did not confirm that weakly positive sign: `fedgrid_topo_proto` returned to slightly negative paired return on both `random_reset` and `static`, while `fedgrid_v4_cluster_distill` became clearly negative
- old non-deterministic follow-up results must not be used as final paper evidence
- single-seed tuning results must not be used as headline paper evidence
- the completed robustness suite is supporting evidence only because it is single-seed
- the completed `case141_fedgrid_ablation_custom_rr_20260327` suite is also single-seed and must not be treated as the final ablation answer
- the completed `case141_fedgrid_ablation_custom_rr_20260327_ms3` suite is the final custom ablation evidence package for this cycle
- in `case141_fedgrid_ablation_custom_rr_20260327_ms3`, `fedgrid_topo_proto` is positive across 3 seeds, while `fedgrid_v4_cluster_distill`, `fedgrid_v4_cluster_nodistill`, and `fedgrid_v4_cluster_gentle` are negative on paired return
- the clean rerun suite artifacts contain all 3 seeds at the aggregate level, but its manifest currently only records the last resumed seed because the suite was completed through explicit single-seed continuation launches

## Current Paper Positioning

Primary route:

- empirical or evaluation-protocol paper first

Conditional upgrade route:

- only if the running higher-power topo-proto suite overturns the current mixed-sign picture, upgrade to a narrower method paper around `fedgrid_topo_proto` rather than the full clustered-distillation family

Backup route:

- method paper if reruns produce stable positive paired gains

Second backup route:

- robustness or negative-results paper if headline gains remain weak but the failure analysis is informative

Current safe thesis:

- deterministic, context-aligned reevaluation is necessary to judge which parts of the federated method family actually help under topology shift, and current evidence suggests `fedgrid_topo_proto` is more promising than clustered distillation but still mixed-sign on the main benchmark

Current unsafe thesis:

- the new clustered method clearly beats the baseline

## Known Risks

- some historical artifacts still reference the old path `C:\Users\ASUS\Desktop\fuxian\...`
- the literature package now has a verified starter set, but it still needs broader coverage of nearest-neighbor task papers
- code structure is still legacy-heavy even though documents are cleaner now
- the corrected multi-seed ablation is complete, but the paper-story integration is still in progress
- the historical `case141_fedgrid_main_rr` suite, the clean rerun `case141_fedgrid_main_rr_20260402_clean`, and the fresh replica `case141_fedgrid_main_rr_20260407_replica` still disagree on the sign of `fedgrid_topo_proto`, which is now the main experimental blocker
- the clean rerun manifest needs caution because resumed single-seed launches overwrote the manifest-level `seeds` field even though the aggregate outputs are 3-seed
- the Q1 queue is now the main operational path: the higher-power topo_proto suite must finish before the queued multi-seed robustness upgrade can fire

## Operational Do And Don't

Do:

- treat the repository root as the only `project_root`
- use paired metrics as the main evidence layer
- require both `summary_*.csv` and `per_episode_*.csv`
- keep all claims traceable to actual artifacts
- update `project_state.md`, `todo.md`, and `decision_log.md` after major milestones
- use `outputs/automation_logs/fedgrid_status.md` as the first-stop operational status board
- treat a completed full artifact set as the ground truth even if a stale monitor heartbeat keeps the suite marked as running
- use the corrected multi-seed ablation result before deciding whether any more expensive rerun is justified
- compare `case141_fedgrid_main_rr`, `case141_fedgrid_main_rr_20260402_clean`, and `case141_fedgrid_main_rr_20260407_replica` before freezing the manuscript thesis
- treat manifest metadata in resumed suites as auditable but potentially lossy when seeds were launched separately
- use `outputs/automation_logs/fedgrid_q1_autopilot_status.md` as the first-stop board for the current Q1 queue rather than the older general board

Do not:

- fabricate literature entries
- force a method-positive narrative before reruns support it
- use mixed-context comparisons as main evidence
- refactor the active runner before the baseline execution path is revalidated
- treat the failed `case141_fedgrid_ablation_custom_rr_20260326` launch as a real experiment suite

## Suggested Reading Order After Context Compression

If context is lost, reload these files first:

1. `project/background_context.md`
2. `project/project_state.md`
3. `project/todo.md`
4. `project/decision_log.md`
5. `project/ideas/problem_framing.md`
6. `project/method/experiment_plan.md`
7. `docs/RUNTIME_EXECUTION_PLAN_20260326.md`

## Next Best Actions

Near-term:

- treat `case141_fedgrid_main_rr` as the historical main evidence package
- treat `case141_fedgrid_main_rr_20260402_clean` as the current-workspace reproduction package
- treat `case141_fedgrid_main_rr_20260407_replica` as the freshest independent main evidence package
- use `case141_fedgrid_main_rr_20260326` only as validation evidence for the current environment and dry run
- treat `case141_fedgrid_robust_rr_20260326` as completed supporting robustness evidence
- treat `case141_fedgrid_ablation_custom_rr_20260327` as exploratory single-seed evidence only
- treat `case141_fedgrid_ablation_custom_rr_20260327_ms3` as the key completed multi-seed ablation suite for the current cycle
- keep drafting the paper around the empirical-analysis framing while reconciling the historical main suite, the clean rerun, and the fresh replica
- keep the running `case141_fedgrid_topoproto_power_rr_20260407` suite alive and let the queued `case141_fedgrid_robust_rr_20260407_ms3` suite fire afterward

After that:

- use the higher-power topo_proto suite to decide whether the narrow method route is still viable
- only consider the optional `full` run after the main-sign discrepancy is resolved
