# FedGrid-v4 论文骨架

## 1. Introduction
- 背景：联邦电网控制、隐私、拓扑迁移、异构 client。
- 问题：简单 FedAvg / topology mixing 容易过度平均，难以保留区域个性。
- 核心 idea：cluster-aware aggregation + post-aggregation distillation。

## 2. Problem formulation
- 多区域配电网电压控制。
- 每个区域一个 agent，本地观测，不共享原始电网数据。
- 拓扑扰动和负荷波动导致 client-level MDP heterogeneity。

## 3. Local control backbone
- GNN-enhanced FMASAC
- global/local bus-GNN encoder
- GraphMixer for inter-area coupling

## 4. Federated representation memory
- obs prototype
- bus-GNN prototype
- reward EMA / trust statistics

## 5. Community-aware federated aggregation
- 构造 topology + prototype + trust + staleness weight matrix
- 从 affinity 动态推导 communities
- 簇内强聚合，簇间弱耦合
- self-boost 抑制过度平均

## 6. Post-aggregation peer distillation
- replay-anchor observations
- peer teacher mixture
- actor mean / log-std alignment
- same-cluster-only distillation

## 7. Robustness and deployment considerations
- partial participation
- Byzantine perturbation
- communication payload accounting
- 可扩展到 secure aggregation / DP hook（未来工作或下一版实现）

## 8. Experiments
- case141 main result
- topology shift
- dropout / Byzantine
- clustering + distillation ablation
- payload overhead

## 9. Conclusion
- 方法优势
- 工程可部署性
- 后续真实电网 / stronger privacy extension
