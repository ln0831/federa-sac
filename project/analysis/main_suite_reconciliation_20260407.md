# Main Suite Reconciliation Note

## Purpose

This note reconciles the three most important evidence packages for the current paper cycle:

- `outputs/suites/case141_fedgrid_main_rr`
- `outputs/suites/case141_fedgrid_main_rr_20260402_clean`
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3`

The goal is to explain what is already stable, what is still unstable, and what the next experiment must resolve before the paper thesis is frozen.

## Shared Context

Across the compared suites:

- the benchmark is case141
- the main comparison context is `random_reset`
- the main methods of interest are `fedgrid_none`, `fedgrid_topo_proto`, and `fedgrid_v4_cluster_distill`
- the paper-facing evidence layer is `agg/suite_paired_metrics.csv` plus `agg/suite_seed_level_paired.csv`

## Historical Main Suite

Source:

- `outputs/suites/case141_fedgrid_main_rr/agg/suite_paired_metrics.csv`

Key paired results:

- `fedgrid_topo_proto`: `Δreturn = -0.106` on `random_reset`, `1/3` winning seeds
- `fedgrid_v4_cluster_distill`: `Δreturn = -0.173` on `random_reset`, `1/3` winning seeds

Interpretation:

- this suite supports the original empirical-first framing
- neither headline method is clearly better than baseline

## Clean Current-Workspace Rerun

Source:

- `outputs/suites/case141_fedgrid_main_rr_20260402_clean/agg/suite_paired_metrics.csv`

Key paired results:

- `fedgrid_topo_proto`: `Δreturn = +0.122` on `random_reset`, `2/3` winning seeds, 95 percent CI `[-0.016, 0.208]`
- `fedgrid_v4_cluster_distill`: `Δreturn = -0.055` on `random_reset`, `1/3` winning seeds

Interpretation:

- `fedgrid_topo_proto` becomes weakly positive in the fresh rerun
- `fedgrid_v4_cluster_distill` remains negative
- the sign of the main positive candidate changed relative to the historical main suite

## Corrected Multi-Seed Ablation

Source:

- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3/agg/suite_paired_metrics.csv`

Key paired results on `random_reset`:

- `fedgrid_topo_proto`: `Δreturn = +0.091`, `3/3` winning seeds
- `fedgrid_v4_cluster_distill`: `Δreturn = -0.136`, `1/3` winning seeds
- `fedgrid_v4_cluster_nodistill`: `Δreturn = -0.133`, `0/3` winning seeds
- `fedgrid_v4_cluster_gentle`: `Δreturn = -0.085`, `0/3` winning seeds

Interpretation:

- this suite strongly supports a negative statement about the clustered-distillation family in its current form
- it also supports `fedgrid_topo_proto` as the only consistently positive ablation result

## Configuration Check

What matches:

- the historical main suite and the clean rerun use the same main method set
- both compare against `fedgrid_none`
- both evaluate the same case and benchmark contexts

What needs caution:

- the clean rerun was finished through explicit single-seed continuation launches
- its aggregate outputs clearly include seeds `0`, `1`, and `2`
- its manifest currently only records the last resumed seed, so the manifest alone understates seed coverage

## Stable Conclusions

These statements are already safe:

- `fedgrid_v4_cluster_distill` is not supported as a positive headline method by the strongest current evidence
- the broader clustered-distillation family is not winning in the corrected multi-seed ablation
- the paper should not claim a broad clustered-method superiority result

## Unstable Conclusion

This statement is not yet stable enough:

- `fedgrid_topo_proto` clearly beats baseline on the main benchmark

Reason:

- the historical main suite is negative
- the clean rerun is weakly positive
- the ablation is positive, but it is still not the same evidence role as an independent fresh main replica

## Required Next Experiment

Run:

- a brand-new independent main replica under a new suite name

Why:

- this is the cheapest experiment that directly resolves the sign disagreement
- until this is done, the paper should remain empirical-first

## Paper Impact

If the next replica is positive again:

- move toward a narrow method story centered on `fedgrid_topo_proto`
- keep clustered distillation as a negative or unstable comparison

If the next replica is negative or near zero:

- freeze the paper as a Q1-oriented empirical evaluation and failure-analysis paper
