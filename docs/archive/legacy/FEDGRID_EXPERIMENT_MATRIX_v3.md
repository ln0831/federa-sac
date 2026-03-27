# FedGrid v3 Experiment Matrix

## Main comparison
1. `none`: no federated mixing, shared GNN-MARL backbone only.
2. `topo`: topology-weighted aggregation.
3. `topo_proto`: topology + prototype + trust gated aggregation.
4. `consensus`: symmetric consensus-style aggregation.

## Robustness and realism
5. `dropout`: partial participation / client dropout.
6. `byzantine`: malicious-client perturbation before aggregation.

## Core ablations
- Prototype source: `obs_stats` vs `bus_gnn` vs `hybrid`
- Aggregation weights: topo / proto / trust / stale
- Update trimming and clipping
- Base-topology vs current-topology graph encoding

## Recommended tables
- Table 1: Main case141 topology-shift result table.
- Table 2: Robustness under dropout and byzantine clients.
- Table 3: Ablation on prototype source and aggregation weights.
- Table 4: Computation and communication overhead.

## Recommended figures
- Figure 1: Framework overview.
- Figure 2: Topology-shift evaluation curve.
- Figure 3: Per-agent voltage violation distribution.
- Figure 4: Aggregation weight heatmap / similarity matrix.
