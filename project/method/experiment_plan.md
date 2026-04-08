# Experiment Plan

## Goal

Produce a Q1-ready evidence package for case141 without overstating what the current FedGrid family actually achieves.

## Current Evidence Snapshot

- `case141_fedgrid_main_rr` is the historical main suite and shows `fedgrid_topo_proto` negative on paired return.
- `case141_fedgrid_main_rr_20260402_clean` is the clean current-workspace rerun and shows `fedgrid_topo_proto` weakly positive on paired return, with `fedgrid_v4_cluster_distill` still negative.
- `case141_fedgrid_main_rr_20260407_replica` is the freshest independent main replica and pulls `fedgrid_topo_proto` back to slightly negative paired return, while `fedgrid_v4_cluster_distill` is clearly negative.
- `case141_fedgrid_ablation_custom_rr_20260327_ms3` strengthens the view that `fedgrid_topo_proto` is the only positive ablation result, while `distill`, `nodistill`, and `gentle` are all negative.
- `case141_fedgrid_robust_rr_20260326` is useful but only single-seed, so it cannot carry a Q1 headline on its own.

## Thesis Gates

Route A:

- empirical evaluation paper if the sign of `fedgrid_topo_proto` remains unstable across fresh replicas

Route B:

- narrow method paper only if the higher-power follow-up overturns the current mixed-sign picture and shows a clearly positive `fedgrid_topo_proto` result on the `random_reset` benchmark

What is currently ruled out:

- a broad positive story for the clustered-distillation family

## Priority Order

### Priority 1: Audit the main-sign discrepancy

Objective:

- explain why `case141_fedgrid_main_rr` and `case141_fedgrid_main_rr_20260402_clean` disagree on the sign of `fedgrid_topo_proto`

Required outputs:

- side-by-side note comparing manifests, paired metrics, seed-level paired deltas, and path provenance
- explicit note that the clean rerun manifest underreports seeds because of resumed single-seed launches

Stop condition:

- the paper can cite the discrepancy honestly and the next replica is scoped precisely

### Priority 2: Fresh independent main replica

Recommended suite:

- `case141_fedgrid_main_rr_20260407_replica`

Methods:

- `fedgrid_none`
- `fedgrid_topo_proto`
- `fedgrid_v4_cluster_distill`

Seeds:

- `0 1 2`

Rules:

- use a brand-new suite directory
- prefer direct single-seed launches if the Windows multi-seed wrapper still truncates seeds
- run full deterministic postprocess and freeze the resulting report immediately

Decision impact:

- if `fedgrid_topo_proto` turns positive again, the project can move toward a narrower method story
- if it flips back negative or near-zero, the Q1 route should stay empirical-first

Observed outcome:

- completed
- `fedgrid_topo_proto` came back slightly negative on `random_reset` (`-0.019`) and `static` (`-0.021`) despite winning `2/3` seeds
- `fedgrid_v4_cluster_distill` remained clearly negative on both contexts
- the default paper route should therefore remain empirical-first unless the higher-power follow-up is much cleaner

### Priority 3: Higher-power topo-proto confirmation

Recommended suite:

- `case141_fedgrid_topoproto_power_rr_20260407`

Methods:

- `fedgrid_none`
- `fedgrid_topo_proto`

Seeds:

- at least `0 1 2 3 4`

Goal:

- tighten the confidence interval on `random_reset` paired return and determine whether the effect is truly positive or simply near zero and unstable

Success threshold:

- `fedgrid_topo_proto` stays positive on mean paired return
- win count is comfortably above half the seeds
- trade-offs in `p_loss_mean` do not reverse the story

Current status:

- running in the Q1 queue
- this suite is now a closure experiment for the mixed-sign main-benchmark story, not just a confirmation of a positive rerun

### Priority 4: Multi-seed robustness upgrade

Run after the higher-power topo-proto suite so the discussion section is supported by more than the older single-seed robustness package.

Recommended suite:

- `case141_fedgrid_robust_rr_20260407_ms3`

Goal:

- convert the interesting single-seed robustness observation into multi-seed supporting evidence

Minimum bar:

- at least 3 seeds for the robustness variants actually discussed in the manuscript

### Priority 5: Optional broader sweep

Run only if the thesis is still ambiguous after Priorities 1 to 4.

Candidate:

- `full`

Reason to defer:

- it is expensive and currently lower value than resolving the `topo_proto` sign flip directly

## Core Metrics

- paired return delta as the headline metric
- `v_viol_lin_mean` as the safety/control constraint metric
- `p_loss_mean` as the trade-off metric
- seed win count and 95 percent confidence interval as the paper-facing stability summary

## Paper-Facing Output Set

- `agg/suite_paired_metrics.csv`
- `agg/suite_seed_level_paired.csv`
- `reports/fedgrid_v6_report.md`
- `reports/latex/table_main_random_reset.tex`
- `reports/latex/table_appendix_static.tex`
- `reports/figures/random_reset_delta_return.png`
- `reports/figures/random_reset_delta_vviol.png`
- `reports/figures/random_reset_delta_ploss.png`

## Q1 Readiness Checklist

- one fresh independent main replica completed
- one clear paper route selected
- no headline claim depends on single-seed evidence
- robustness evidence is either upgraded to multi-seed or kept explicitly secondary
- manuscript and paper package both point to the same current source-of-truth suites
- any remaining method-positive claim for `fedgrid_topo_proto` is backed by the higher-power suite rather than by the clean rerun alone
