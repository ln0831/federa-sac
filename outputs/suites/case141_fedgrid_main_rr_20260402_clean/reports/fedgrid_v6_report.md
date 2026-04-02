# FedGrid v6 suite report

- Suite root: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260402_clean`
- Paired metrics source: `suite_paired_metrics.csv`
- Absolute metrics source: `suite_absolute_metrics.csv`
- Ranking source: `suite_rankings.csv`

## Headline findings by context

### Context: case=141, k=6, policy=, radius=

- Main benchmark best paired return on `random_reset`: **fedgrid_topo_proto** with paired Δreturn=0.078 and 95% CI [-0.016, 0.172].
- In-distribution best paired return on `static`: **fedgrid_topo_proto** with paired Δreturn=0.080.
- Best method on `random_reset` by voltage-violation reduction: **fedgrid_topo_proto** with Δvviol=0.0000.
- Top-3 methods on `random_reset` by paired return gain in this context: 1) fedgrid_topo_proto, 2) fedgrid_v4_cluster_distill.

## Manuscript-ready claims

1. Use `random_reset` as the main table because it targets topology-shift generalization rather than in-distribution control.
2. Use paired seed deltas and CIs as the headline statistical evidence; keep absolute means in the appendix or supplementary material.
3. If a method improves return but worsens voltage violations or active-power loss, write it as a control trade-off instead of a strict win.
4. Put `static` in the appendix as an in-distribution sanity check.

## Random-reset paired table

| case | k | policy | radius | method | Δreturn | 95% CI | Δvviol | Δploss | better seeds | paper score |
|---|---:|---|---:|---|---:|---|---:|---:|---:|---:|
| 141 | 6 |  |  | fedgrid_topo_proto | 0.078 | [-0.016, 0.172] | 0.0000 | -0.00204 | 1/2 | 1.614 |
| 141 | 6 |  |  | fedgrid_v4_cluster_distill | -0.030 | [-0.136, 0.075] | 0.0000 | 0.00079 | 1/2 | -0.644 |

## Static paired table

| case | k | policy | radius | method | Δreturn | 95% CI | Δvviol | Δploss | better seeds | paper score |
|---|---:|---|---:|---|---:|---|---:|---:|---:|---:|
| 141 | 6 |  |  | fedgrid_topo_proto | 0.080 | [-0.013, 0.172] | 0.0000 | -0.00207 | 1/2 | 1.654 |
| 141 | 6 |  |  | fedgrid_v4_cluster_distill | -0.027 | [-0.135, 0.081] | 0.0000 | 0.00070 | 1/2 | -0.585 |

## Suggested results narrative

Our main comparison should emphasize the random-reset topology-shift benchmark, where the clustered-distillation family is designed to help under client heterogeneity and changing grid structure. The static benchmark should only be used to verify that the stronger federated mechanism does not sacrifice in-distribution performance.
