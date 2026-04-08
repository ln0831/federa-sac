# Main Suite Reconciliation Note

## Purpose

This note reconciles the four most important evidence packages for the current paper cycle:

- `outputs/suites/case141_fedgrid_main_rr`
- `outputs/suites/case141_fedgrid_main_rr_20260402_clean`
- `outputs/suites/case141_fedgrid_main_rr_20260407_replica`
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3`

The goal is to explain what is already stable, what is still unstable, and what the remaining queued experiments should resolve before the paper thesis is frozen.

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

## Fresh Independent Main Replica

Source:

- `outputs/suites/case141_fedgrid_main_rr_20260407_replica/agg/suite_paired_metrics.csv`

Key paired results:

- `fedgrid_topo_proto`: `Δreturn = -0.019` on `random_reset`, `2/3` winning seeds, 95 percent CI `[-0.159, 0.094]`
- `fedgrid_v4_cluster_distill`: `Δreturn = -0.187` on `random_reset`, `0/3` winning seeds

Interpretation:

- the clean rerun's weakly positive `fedgrid_topo_proto` result did not repeat in an independent dated replica
- `fedgrid_topo_proto` is now better described as mixed-sign or near-zero on the main benchmark than as clearly positive
- `fedgrid_v4_cluster_distill` becomes even more clearly negative

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

- the historical main suite, the clean rerun, and the fresh replica use the same main method set
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
- `fedgrid_topo_proto` is not stable enough yet for a positive main-benchmark headline because the historical main suite is negative, the clean rerun is weakly positive, and the fresh replica is slightly negative
- the paper should not claim a broad clustered-method superiority result

## Remaining Uncertainty

This question is not yet stable enough:

- whether the already-running higher-power `fedgrid_none` versus `fedgrid_topo_proto` suite will tighten around a real positive effect or simply confirm that the main-benchmark result is near zero and unstable

Reason:

- the historical main suite is negative
- the clean rerun is weakly positive
- the fresh replica is slightly negative
- the ablation is positive, but it is still not the same evidence role as a dedicated higher-power confirmation run

## Required Next Evidence

Finish:

- the already-running `case141_fedgrid_topoproto_power_rr_20260407` suite
- the queued `case141_fedgrid_robust_rr_20260407_ms3` suite

Why:

- the fresh replica has already resolved the original sign disagreement enough to keep the default paper route empirical-first
- the higher-power topo-proto suite is now the right place to quantify whether the narrower comparison is genuinely positive
- the multi-seed robustness upgrade is the right supporting package for the discussion and limitations sections

## Paper Impact

Primary route today:

- stay with an empirical evaluation and failure-analysis paper
- present clustered distillation as negative or unstable
- present `fedgrid_topo_proto` as mixed-sign evidence that is promising enough to study further but not yet strong enough for a broad superiority claim

If the higher-power topo-proto suite becomes clearly positive with tighter uncertainty:

- a narrow `fedgrid_topo_proto` method story can be reconsidered, but it should still preserve the negative clustered-distillation result rather than hide it
