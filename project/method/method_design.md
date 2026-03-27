# Method Design

## Working Framing

This project currently has two layers:

- an implemented FedGrid-v4 method family in the repository root
- a paper-layer question about how to evaluate and position that family honestly

## Task Formulation

Task:

- multi-area voltage control on the case141 benchmark under topology perturbations and local outage settings

Comparison target:

- compare cluster-aware and prototype-aware federated variants against a simpler baseline under matched contexts

## System Under Study

Methods currently available in the active runner:

- `fedgrid_none`
- `fedgrid_topo_proto`
- `fedgrid_v4_cluster_distill`
- `fedgrid_v4_cluster_nodistill`
- `fedgrid_v4_cluster_gentle`
- `fedgrid_v4_cluster_dropout`
- `fedgrid_v4_cluster_byzantine`

## Active Pipeline

- training through `train_gnn_fedgrid.py`
- deterministic evaluation through `evaluate_topology_shift_deterministic.py`
- aggregation through `summarize_fedgrid_suite_v6.py`
- table and figure export through `export_fedgrid_tables_v6.py` and `make_fedgrid_figures_v6.py`
- markdown reporting through `make_fedgrid_report_v6.py`

## Failure Modes

- negative paired return despite attractive method intuition
- trade-off improvements only in one metric but not in return
- inconsistent results across contexts
- path inconsistency or incomplete artifacts breaking reproducibility
