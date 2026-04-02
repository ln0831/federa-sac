# FedGrid v6 suite report

- Suite root: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3`
- Paired metrics source: `suite_paired_metrics.csv`
- Absolute metrics source: `suite_absolute_metrics.csv`
- Ranking source: `suite_rankings.csv`

## Headline findings by context

### Context: case=141, k=6, policy=, radius=

- Main benchmark best paired return on `random_reset`: **fedgrid_topo_proto** with paired Δreturn=0.091 and 95% CI [0.084, 0.097].
- In-distribution best paired return on `static`: **fedgrid_topo_proto** with paired Δreturn=0.092.
- Best method on `random_reset` by voltage-violation reduction: **fedgrid_topo_proto** with Δvviol=0.0000.
- Top-3 methods on `random_reset` by paired return gain in this context: 1) fedgrid_topo_proto, 2) fedgrid_v4_cluster_gentle, 3) fedgrid_v4_cluster_nodistill.

## Manuscript-ready claims

1. Use `random_reset` as the main table because it targets topology-shift generalization rather than in-distribution control.
2. Use paired seed deltas and CIs as the headline statistical evidence; keep absolute means in the appendix or supplementary material.
3. If a method improves return but worsens voltage violations or active-power loss, write it as a control trade-off instead of a strict win.
4. Put `static` in the appendix as an in-distribution sanity check.

## Random-reset paired table

| case | k | policy | radius | method | Δreturn | 95% CI | Δvviol | Δploss | better seeds | paper score |
|---|---:|---|---:|---|---:|---|---:|---:|---:|---:|
| 141 | 6 |  |  | fedgrid_topo_proto | 0.091 | [0.084, 0.097] | 0.0000 | -0.00237 | 3/3 | 1.887 |
| 141 | 6 |  |  | fedgrid_v4_cluster_gentle | -0.085 | [-0.182, -0.016] | 0.0000 | 0.00221 | 0/3 | -1.753 |
| 141 | 6 |  |  | fedgrid_v4_cluster_nodistill | -0.133 | [-0.161, -0.105] | 0.0000 | 0.00346 | 0/3 | -2.751 |
| 141 | 6 |  |  | fedgrid_v4_cluster_distill | -0.136 | [-0.297, 0.049] | 0.0000 | 0.00353 | 1/3 | -2.841 |

## Static paired table

| case | k | policy | radius | method | Δreturn | 95% CI | Δvviol | Δploss | better seeds | paper score |
|---|---:|---|---:|---|---:|---|---:|---:|---:|---:|
| 141 | 6 |  |  | fedgrid_topo_proto | 0.092 | [0.089, 0.094] | 0.0000 | -0.00239 | 3/3 | 1.915 |
| 141 | 6 |  |  | fedgrid_v4_cluster_gentle | -0.083 | [-0.180, -0.015] | 0.0000 | 0.00217 | 0/3 | -1.732 |
| 141 | 6 |  |  | fedgrid_v4_cluster_nodistill | -0.132 | [-0.159, -0.104] | 0.0000 | 0.00344 | 0/3 | -2.754 |
| 141 | 6 |  |  | fedgrid_v4_cluster_distill | -0.135 | [-0.296, 0.047] | 0.0000 | 0.00351 | 1/3 | -2.844 |

## Suggested results narrative

Our main comparison should emphasize the random-reset topology-shift benchmark, where the clustered-distillation family is designed to help under client heterogeneity and changing grid structure. The static benchmark should only be used to verify that the stronger federated mechanism does not sacrifice in-distribution performance.
