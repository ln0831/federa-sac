# Experiments Draft

Status:
- drafted from the historical main suite, clean main rerun, corrected ablation suite, and robustness suite

## Environment and benchmark

All current validated runs use `D:\Anaconda\envs\tianshou_env\python.exe`. Full `pytest -q tests` passed in that environment during the current cycle, and `scripts/check_runtime_bundle.py --project_root .` also passed. The main benchmark in this cycle is case141 with outage count `k=6`. The two evaluation contexts are:

- `random_reset`, which is treated as the primary topology-shift benchmark
- `static`, which is treated as an in-distribution sanity check

## Suites used in the manuscript

The current manuscript uses four completed suites:

- `outputs/suites/case141_fedgrid_main_rr` as the historical main benchmark package
- `outputs/suites/case141_fedgrid_main_rr_20260402_clean` as the clean current-workspace rerun
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3` as the corrected final multi-seed ablation package
- `outputs/suites/case141_fedgrid_robust_rr_20260326` as supporting robustness evidence

The partial rerun `case141_fedgrid_main_rr_20260326` is kept only as environment-validation evidence.

## Compared methods

The completed main suite currently supports comparisons among:

- baseline `fedgrid_none`
- `fedgrid_topo_proto`
- `fedgrid_v4_cluster_distill`

The completed robustness suite adds:

- `fedgrid_v4_cluster_dropout`
- `fedgrid_v4_cluster_byzantine`

The corrected multi-seed ablation suite adds:

- `fedgrid_v4_cluster_nodistill`
- `fedgrid_v4_cluster_gentle`

## Metrics and aggregation

The paper-facing metrics are produced from deterministic evaluation outputs. The primary evidence layer is `suite_paired_metrics.csv`, with `suite_seed_level_paired.csv` used to inspect seed-level consistency. Paper-facing tables and figures are exported automatically to:

- `reports/latex/*.tex`
- `reports/figures/*.png`
- `reports/fedgrid_v6_report.md`

The main manuscript prioritizes paired DeltaReturn and retains DeltaVViol and DeltaPLoss to identify trade-offs rather than declaring wins from a single metric.

## Fairness and evidence rules

The current cycle follows four fairness rules:

1. multi-seed paired summaries outrank single-seed summaries
2. `random_reset` outranks `static` for headline claims because it is the topology-shift target
3. incomplete suites are not cited as evidence
4. exploratory single-seed runs such as `case141_fedgrid_tune_seed2_rr_v1` can inform discussion, but not headline claims

## Current Q1 follow-up

The next live queue is now a dedicated Q1 sequence:

- `case141_fedgrid_main_rr_20260407_replica`
- `case141_fedgrid_topoproto_power_rr_20260407`
- `case141_fedgrid_robust_rr_20260407_ms3`

These runs are not yet used in the manuscript, but they are the active path for resolving whether the final paper remains empirical-first or upgrades to a narrow `fedgrid_topo_proto` method paper.
