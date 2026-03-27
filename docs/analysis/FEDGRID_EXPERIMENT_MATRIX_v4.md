# FedGrid v4 Experiment Matrix

## Main comparisons
1. `fedgrid_none`：无联邦混合。
2. `fedgrid_topo_proto`：v3 主线，topology + prototype + trust。
3. `fedgrid_v4_cluster_distill`：v4 主方法，clustered federation + peer distillation。

## Robustness / realism
4. `fedgrid_v4_cluster_dropout`：25% client dropout。
5. `fedgrid_v4_cluster_byzantine`：25% Byzantine perturbation。

## Core ablations
- `clustered off` vs `clustered on`
- `same_cluster_only distillation` vs `global distillation`
- `cluster_threshold`: 0.50 / 0.58 / 0.66
- `inter_cluster_scale`: 0.00 / 0.08 / 0.15
- `distill_coef`: 0.00 / 0.05 / 0.10 / 0.20
- `prototype source`: `obs` / `gnn` / `hybrid`

## Suggested tables
- Table 1: Main topology-shift performance on case141.
- Table 2: Robustness under dropout and Byzantine clients.
- Table 3: Ablation on clustering and distillation.
- Table 4: Communication payload and runtime overhead.

## Suggested figures
- Figure 1: Framework overview (clustered federation + distillation).
- Figure 2: Aggregation heatmap before/after cluster masking.
- Figure 3: Distillation loss and trust statistics over rounds.
- Figure 4: Per-agent voltage violation / reward distribution.
