# FedGrid v6 suite report

- Suite root: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_robust_rr_20260326`
- Paired metrics source: `suite_paired_metrics.csv`
- Absolute metrics source: `suite_absolute_metrics.csv`
- Ranking source: `suite_rankings.csv`

## Headline findings by context

### Context: case=141, k=6, policy=, radius=

- Main benchmark best paired return on `random_reset`: **fedgrid_v4_cluster_byzantine** with paired Δreturn=0.642 and 95% CI [0.642, 0.642].
- In-distribution best paired return on `static`: **fedgrid_v4_cluster_byzantine** with paired Δreturn=0.643.
- Best method on `random_reset` by voltage-violation reduction: **fedgrid_v4_cluster_byzantine** with Δvviol=0.0000.
- Top-3 methods on `random_reset` by paired return gain in this context: 1) fedgrid_v4_cluster_byzantine, 2) fedgrid_v4_cluster_distill, 3) fedgrid_v4_cluster_dropout.

## Manuscript-ready claims

1. Use `random_reset` as the main table because it targets topology-shift generalization rather than in-distribution control.
2. Use paired seed deltas and CIs as the headline statistical evidence; keep absolute means in the appendix or supplementary material.
3. If a method improves return but worsens voltage violations or active-power loss, write it as a control trade-off instead of a strict win.
4. Put `static` in the appendix as an in-distribution sanity check.

## Random-reset paired table

| case | k | policy | radius | method | Δreturn | 95% CI | Δvviol | Δploss | better seeds | paper score |
|---|---:|---|---:|---|---:|---|---:|---:|---:|---:|
| 141 | 6 |  |  | fedgrid_v4_cluster_byzantine | 0.642 | [0.642, 0.642] | 0.0000 | -0.01671 | 1/1 | 12.895 |
| 141 | 6 |  |  | fedgrid_v4_cluster_distill | 0.113 | [0.113, 0.113] | 0.0000 | -0.00296 | 1/1 | 2.280 |
| 141 | 6 |  |  | fedgrid_v4_cluster_dropout | -0.090 | [-0.090, -0.090] | 0.0000 | 0.00233 | 0/1 | -1.799 |

## Static paired table

| case | k | policy | radius | method | Δreturn | 95% CI | Δvviol | Δploss | better seeds | paper score |
|---|---:|---|---:|---|---:|---|---:|---:|---:|---:|
| 141 | 6 |  |  | fedgrid_v4_cluster_byzantine | 0.643 | [0.643, 0.643] | 0.0000 | -0.01674 | 1/1 | 13.001 |
| 141 | 6 |  |  | fedgrid_v4_cluster_distill | 0.113 | [0.113, 0.113] | 0.0000 | -0.00295 | 1/1 | 2.295 |
| 141 | 6 |  |  | fedgrid_v4_cluster_dropout | -0.089 | [-0.089, -0.089] | 0.0000 | 0.00231 | 0/1 | -1.794 |

## Suggested results narrative

Our main comparison should emphasize the random-reset topology-shift benchmark, where the clustered-distillation family is designed to help under client heterogeneity and changing grid structure. The static benchmark should only be used to verify that the stronger federated mechanism does not sacrifice in-distribution performance.
