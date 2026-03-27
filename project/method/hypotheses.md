# Hypotheses And Claims

## Primary Claim

Deterministic, context-aligned paired evaluation is necessary to make defensible claims about federated voltage-control methods in this project.

## Secondary Claim 1

Cluster-aware aggregation plus distillation may improve performance relative to weaker baselines in some topology-shifted contexts.

## Secondary Claim 2

Robustness variants may reveal clearer value than the headline benchmark alone.

## Hypotheses

- H1: `fedgrid_v4_cluster_distill` will outperform `fedgrid_none` on at least one meaningful paired pattern under `random_reset`.
- H2: Context-aligned reevaluation will reduce misleading conclusions caused by mixed or non-paired comparisons.
- H3: Even if the main method does not win consistently, the project can still support a publishable empirical or failure-analysis paper.

## Assumptions

- the active runner and postprocess chain are functionally correct
- `tianshou_env` is close enough to the intended runtime environment for immediate validation
- case141 is sufficient as the primary benchmark for this cycle

## Threats To Validity

- incomplete external literature verification
- environment drift between prior runs and the current workspace
- limited benchmark diversity if only case141 is finalized
