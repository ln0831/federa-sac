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

- completed and verified

Use level:

- supporting robustness evidence

Notes:

- launched after the main packaging pass to fill the robustness gap
- contains manifests, aggregate CSVs, LaTeX tables, figures, and a markdown report
- single-seed only, so it should support the discussion and robustness section rather than headline superiority claims

### `case141_fedgrid_ablation_custom_rr_20260327`

Status:

- completed, but exploratory only

Use level:

- do not use as final ablation evidence

Notes:

- recovered custom ablation run after the queue-launch bug was fixed
- method set: `fedgrid_none`, `fedgrid_topo_proto`, `fedgrid_v4_cluster_distill`, `fedgrid_v4_cluster_nodistill`, `fedgrid_v4_cluster_gentle`
- completed with only seed `0`, so it remains exploratory and should not carry the final ablation story

### `case141_fedgrid_ablation_custom_rr_20260327_ms3`

Status:

- completed and verified

Use level:

- final ablation evidence for the current cycle

Notes:

- corrected multi-seed rerun of the custom ablation after the PowerShell wrapper seed bug was fixed
- method set: `fedgrid_none`, `fedgrid_topo_proto`, `fedgrid_v4_cluster_distill`, `fedgrid_v4_cluster_nodistill`, `fedgrid_v4_cluster_gentle`
- contains complete manifests, aggregate CSVs, LaTeX tables, figures, and markdown report
- `fedgrid_topo_proto` shows positive paired return across 3 seeds
- `fedgrid_v4_cluster_distill`, `fedgrid_v4_cluster_nodistill`, and `fedgrid_v4_cluster_gentle` remain negative on paired return and therefore do not support a clustered-distillation headline

## Archived Debug Suites

### `archive_debug/case141_fedgrid_ablation_custom_rr_20260326`

Status:

- failed launch artifact retained only for traceability

Use level:

- do not cite as evidence

Notes:

- archived out of the main suite list to reduce noise in `outputs/suites/`
- paired with archived wrapper and monitor logs under `outputs/automation_logs/archive/`

### `archive_debug/case141_fedgrid_main_rr_failed_prefix_20260323_153748`

Status:

- failed-prefix historical debug artifact

Use level:

- do not cite as evidence

Notes:

- retained only to preserve the old path-prefix failure trace
- paired console and launcher logs were moved to `outputs/automation_logs/archive/`

### `archive_debug/case141_fedgrid_tune_seed2_rr`

Status:

- partial historical tuning manifest retained only for traceability

Use level:

- do not cite as evidence

Notes:

- contains old manifest files but no real checkpoints in the current workspace
- command paths still point to the old `fuxian` workspace layout, so it was archived out of the active suite list
