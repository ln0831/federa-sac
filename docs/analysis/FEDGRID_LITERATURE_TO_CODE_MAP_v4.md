# Literature -> Code Map (v4)

## 1. STT-PFRL / ProtoFedSAC
论文动机：prototype transmission、physics-aware representation、heterogeneity handling。
代码对应：
- `fedgrid_federated.py` -> `HybridPrototypeBank`
- `train_gnn_fedgrid.py` -> `fed_proto_source`, hybrid prototype update

## 2. Cluster distillation for heterogeneous smart grids
论文动机：heterogeneity-aware clustering + quality-aware distillation。
代码对应：
- `fedgrid_federated.py` -> `derive_client_clusters`, `mask_weights_by_clusters`
- `train_gnn_fedgrid.py` -> `--fed_clustered`, cluster-aware federated round
- `fedgrid_federated.py` -> `distill_actors_from_peers`

## 3. Dynamic weighted asynchronous FL
论文动机：quality + staleness jointly determine aggregation.
代码对应：
- `build_federated_weight_matrix`
- `fed_staleness`
- `sample_active_clients`
- partial participation path in `train_gnn_fedgrid.py`

## 4. Safe voltage control / human intervention
论文动机：在危险状态下降低不可靠策略扩散风险。
当前吸收方式：
- trust-gated source weighting
- clustered self-boost
- same-cluster-only peer distillation

## 5. Secure aggregation + multiple local steps
论文动机：现实部署下不能假设每一步都通信。
当前吸收方式：
- 本版先保留多 local steps + payload accounting
- 下一轮再接 secure aggregation / DP hook
