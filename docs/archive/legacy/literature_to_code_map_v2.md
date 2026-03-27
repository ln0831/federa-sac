# Literature -> Code Map (v2)

## 1) Prototype Federated Reinforcement Learning for Voltage Regulation in Distribution Systems with Physics-Aware Spatial-Temporal Graph Perception
代码映射：
- `HybridPrototypeBank`
- `--fed_proto_source hybrid`
- `--fed_gnn_proto_weight`

## 2) Federated reinforcement learning with constrained MDPs and graph neural networks for fair and grid-constrained EV charging
代码映射：
- `run_case141_fedgrid_v2.py`
- partial participation / robustness experiment matrix

## 3) Domain knowledge-enhanced graph reinforcement learning method for Volt/Var control in distribution networks
代码映射：
- 保留并强化 bus-GNN + graph mixer 主干
- 面向 topology-shift 的图结构表征

## 4) Blockchain-empowered cluster distillation federated learning for heterogeneous smart grids
代码映射：
- trust-gated aggregation
- heterogeneity-aware federation
- 后续可继续扩展 cluster/distillation 分支

## 5) Smart-grid federated learning surveys / deployment studies
代码映射：
- `--fed_client_dropout`
- `--fed_freeze_inactive`
- `--fed_byzantine_frac`
- `--fed_byzantine_mode`
