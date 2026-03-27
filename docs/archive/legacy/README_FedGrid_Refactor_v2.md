# FedGrid Refactor v2

这一版不是简单把旧工程里的 `topology-weighted FedAvg` 调一调，而是按“联邦电网 + 电压控制 / 拓扑迁移 + 可发论文”的思路做的第二轮重构。

## 这版新增了什么

### 1. Hybrid prototype federation
在旧版只看 topology 的聚合上，加入了两类 prototype：
- **obs prototype**：从每个 agent 的局部电网观测提取统计表征；
- **bus-GNN prototype**：从 bus-level GNN embedding 提取结构化表征；
- **hybrid prototype**：把两者统一进联邦相似度矩阵。

对应文件：
- `fedgrid_federated.py`
- `train_gnn_fedgrid_v2.py`

### 2. Robust federated aggregation
联邦聚合不再只由 topology 决定，而是同时由：
- topology similarity
- prototype similarity
- trust score
- staleness penalty
共同决定。

此外新增：
- `fed_mode=proto`
- `fed_mode=topo_proto`
- `fed_mode=consensus`

### 3. Partial participation / async-like robustness
加入 `--fed_client_dropout` 与 `--fed_freeze_inactive`：
- 模拟通信掉线 / 轮次不完整参与；
- inactive client 可以冻结，不被错误覆盖；
- staleness 会进入下一轮聚合权重。

### 4. Byzantine robustness hooks
加入：
- `--fed_byzantine_frac`
- `--fed_byzantine_mode`
- `--fed_byzantine_strength`

支持对部分活跃 client 做 synthetic perturbation：
- noise
- signflip
- scale

### 5. Case141 实验矩阵脚本
新增 `run_case141_fedgrid_v2.py`，可一次性拉起：
- `fedgrid_none`
- `fedgrid_topo`
- `fedgrid_topo_proto`
- `fedgrid_consensus`
- `fedgrid_dropout`
- `fedgrid_byzantine`

## 推荐主方法命名

推荐论文主方法命名：

**FedGrid-v2: Hybrid-Prototype and Trust-Gated Federated Multi-Agent Graph RL for Topology-Shift Robust Voltage Control**

## 推荐主实验表

### 主表 1：总体性能
- static topology
- random-reset topology
- topology-shift deterministic evaluation

指标：
- return
- p_loss
- v_viol_lin
- v_viol_sq
- n_components

### 主表 2：联邦消融
- none
- fedavg
- topo
- proto
- topo_proto
- consensus

### 主表 3：鲁棒性消融
- no dropout / 25% dropout
- no attack / 25% attack
- noise / signflip / scale

### 主表 4：prototype 来源消融
- obs only
- gnn only
- hybrid

## 推荐下一步

1. 先在 `case141` 跑 `fedgrid_none / topo / topo_proto / consensus`。
2. 再补 dropout 与 byzantine ablation。
3. 最后写 paired-seed 显著性与 topology-shift robustness 章节。
