# Figure And Table Plan

## Goal

Turn the current runtime outputs into a journal-style figure and table package with one question answered per asset.

## Existing Strong Sources

- `outputs/suites/case141_fedgrid_main_rr/agg/`
- `outputs/suites/case141_fedgrid_main_rr/reports/figures/`
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3/agg/`
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3/reports/figures/`
- `outputs/suites/case141_fedgrid_robust_rr_20260326/agg/`
- `outputs/suites/case141_fedgrid_robust_rr_20260326/reports/figures/`

## Main-Text Figure Plan

### Figure 1

Purpose:

- problem setup and deterministic paired evaluation pipeline schematic

Status:

- missing and should be created manually

### Figure 2

Purpose:

- main paired return comparison on `case141_fedgrid_main_rr`

Current asset:

- `outputs/suites/case141_fedgrid_main_rr/reports/figures/random_reset_delta_return.png`

### Figure 3

Purpose:

- corrected multi-seed ablation result highlighting positive `topo_proto` and negative clustered variants

Current asset:

- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3/reports/figures/random_reset_delta_return.png`

### Figure 4

Purpose:

- robustness or tradeoff panel from `case141_fedgrid_robust_rr_20260326`

Candidate sources:

- return delta
- p-loss delta
- a custom seed-level comparison panel

## Main-Text Table Plan

### Table 1

Purpose:

- benchmark, metrics, and compared methods summary

Status:

- to be authored in LaTeX

### Table 2

Purpose:

- main paired metrics for the primary suite

Primary data source:

- `outputs/suites/case141_fedgrid_main_rr/agg/suite_paired_metrics.csv`

### Table 3

Purpose:

- corrected multi-seed ablation summary

Primary data source:

- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3/agg/suite_paired_metrics.csv`

### Table 4 or appendix

Purpose:

- robustness summary

Primary data source:

- `outputs/suites/case141_fedgrid_robust_rr_20260326/agg/suite_paired_metrics.csv`

## Missing High-Value Assets

- pipeline schematic
- seed-level spread visualization
- a cleaner claim-to-evidence appendix figure or table

## Rule

If a figure or table does not answer one concrete reviewer-facing question, it should not stay in the main text.
