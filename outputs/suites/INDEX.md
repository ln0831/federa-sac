# Suite Index

## Purpose

This file tracks the current role of each suite directory so later paper-writing and auditing work does not mix final evidence with exploratory or partial runs.

## Suites

### `case141_fedgrid_main_rr`

Status:

- primary completed main suite available in the current workspace

Use level:

- main evidence source for current tables, figures, and report

Notes:

- contains complete manifests, eval outputs, aggregate CSVs, LaTeX tables, figures, and markdown report
- current paired results do not support a strong positive method-superiority claim

### `case141_fedgrid_tune_seed2_rr_v1`

Status:

- completed supporting tuning suite

Use level:

- supporting evidence only

Notes:

- single-seed tuning-oriented asset
- useful for ablation exploration but not headline paper evidence
- historical path references need caution

### `case141_fedgrid_main_rr_20260326`

Status:

- partial rerun intentionally stopped

Use level:

- environment-validation artifact only

Notes:

- created to validate current `tianshou_env` execution path
- dry run completed and live rerun was started
- live rerun was stopped after confirming runtime health because a full CPU-only duplicate run was lower value than packaging existing completed assets

### `case141_fedgrid_robust_rr_20260326`

Status:

- running

Use level:

- next-priority experimental evidence

Notes:

- launched after the main packaging pass to fill the robustness gap
- now watched by the local autopilot queue so the next suite can launch without manual intervention
- should become the key source for dropout and Byzantine claims if it completes cleanly

### `case141_fedgrid_ablation_custom_rr_20260326`

Status:

- queued

Use level:

- next-priority experimental evidence after robustness

Notes:

- planned as a custom multi-seed ablation run, not the stock `ablation` preset
- method set: `fedgrid_none`, `fedgrid_topo_proto`, `fedgrid_v4_cluster_distill`, `fedgrid_v4_cluster_nodistill`, `fedgrid_v4_cluster_gentle`
- intended to clarify whether distillation and gentler clustering matter once robustness evidence is in hand
