# FedGrid v6 suite report

- Suite root: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327`
- Paired metrics source: `suite_paired_metrics.csv`
- Absolute metrics source: `suite_absolute_metrics.csv`
- Ranking source: `suite_rankings.csv`

## Headline findings by context

### Context: case=141, k=6, policy=, radius=

- Main benchmark best paired return on `random_reset`: **fedgrid_topo_proto** with paired Δreturn=0.192 and 95% CI [0.192, 0.192].
- In-distribution best paired return on `static`: **fedgrid_topo_proto** with paired Δreturn=0.190.
- Best method on `random_reset` by voltage-violation reduction: **fedgrid_topo_proto** with Δvviol=0.0000.
- Top-3 methods on `random_reset` by paired return gain in this context: 1) fedgrid_topo_proto, 2) fedgrid_v4_cluster_nodistill, 3) fedgrid_v4_cluster_distill.

## Manuscript-ready claims

1. Use `random_reset` as the main table because it targets topology-shift generalization rather than in-distribution control.
2. Use paired seed deltas and CIs as the headline statistical evidence; keep absolute means in the appendix or supplementary material.
3. If a method improves return but worsens voltage violations or active-power loss, write it as a control trade-off instead of a strict win.
4. Put `static` in the appendix as an in-distribution sanity check.

## Random-reset paired table

| case | k | policy | radius | method | Δreturn | 95% CI | Δvviol | Δploss | better seeds | paper score |
|---|---:|---|---:|---|---:|---|---:|---:|---:|---:|
| 141 | 6 |  |  | fedgrid_topo_proto | 0.192 | [0.192, 0.192] | 0.0000 | -0.00500 | 1/1 | 4.048 |
| 141 | 6 |  |  | fedgrid_v4_cluster_nodistill | -0.027 | [-0.027, -0.027] | 0.0000 | 0.00070 | 0/1 | -0.570 |
| 141 | 6 |  |  | fedgrid_v4_cluster_distill | -0.040 | [-0.040, -0.040] | 0.0000 | 0.00103 | 0/1 | -0.837 |
| 141 | 6 |  |  | fedgrid_v4_cluster_gentle | -0.262 | [-0.262, -0.262] | 0.0000 | 0.00681 | 0/1 | -5.515 |

## Static paired table

| case | k | policy | radius | method | Δreturn | 95% CI | Δvviol | Δploss | better seeds | paper score |
|---|---:|---|---:|---|---:|---|---:|---:|---:|---:|
| 141 | 6 |  |  | fedgrid_topo_proto | 0.190 | [0.190, 0.190] | 0.0000 | -0.00495 | 1/1 | 4.034 |
| 141 | 6 |  |  | fedgrid_v4_cluster_nodistill | -0.028 | [-0.028, -0.028] | 0.0000 | 0.00073 | 0/1 | -0.596 |
| 141 | 6 |  |  | fedgrid_v4_cluster_distill | -0.043 | [-0.043, -0.043] | 0.0000 | 0.00112 | 0/1 | -0.911 |
| 141 | 6 |  |  | fedgrid_v4_cluster_gentle | -0.260 | [-0.260, -0.260] | 0.0000 | 0.00677 | 0/1 | -5.522 |

## Suggested results narrative

Our main comparison should emphasize the random-reset topology-shift benchmark, where the clustered-distillation family is designed to help under client heterogeneity and changing grid structure. The static benchmark should only be used to verify that the stronger federated mechanism does not sacrifice in-distribution performance.
