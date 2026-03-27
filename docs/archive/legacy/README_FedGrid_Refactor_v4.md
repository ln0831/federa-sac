# FedGrid Refactor v4

这一版在 v3 的 `topology + prototype + trust + staleness` 基础上，继续往“更像一区主方法”的方向推进，重点不是再加一个聚合权重，而是把 **动态分簇（community-aware federation）** 和 **联邦轮后知识蒸馏（peer distillation）** 真正接进训练主干。

## v4 的主方法定位

**FedGrid-v4: Clustered-and-Distilled Federated Multi-Agent Graph RL for Topology-Shift Robust Voltage Control**

它解决的是以下三个现实问题：
1. 客户端并不总是同质，单一全局混合会把区域差异抹平；
2. 仅靠参数平均很难把异构 client 的“好策略”稳定迁移到别的 client；
3. 论文需要的不只是主结果，还要有异构性、通信代价和鲁棒性叙事。

## 这版真正新增了什么

### 1) Dynamic client clustering
新增动态社区感知聚合：
- 从 federated affinity / weight matrix 推导 client 社区；
- 聚合时优先在簇内传播，簇间仅保留少量 residual mixing；
- 支持 `self_boost`，避免异构场景下被过度平均。

关键参数：
- `--fed_clustered`
- `--fed_cluster_knn`
- `--fed_cluster_threshold`
- `--fed_max_clusters`
- `--fed_inter_cluster_scale`
- `--fed_cluster_self_boost`

### 2) Post-aggregation peer distillation
每轮参数聚合后，从 replay buffer 抽取 anchor observations：
- 用聚合矩阵生成 teacher mixture；
- 让每个 actor 对齐来自 peers 的 action mean / log-std；
- 默认可限制为同簇蒸馏，减少错误迁移。

关键参数：
- `--fed_distill_coef`
- `--fed_distill_steps`
- `--fed_distill_batch_size`
- `--fed_distill_logstd_weight`
- `--fed_distill_same_cluster_only`

### 3) Communication accounting
新增联邦轮有效载荷统计：
- 统计 actor / critic / local bus-GNN 的混合参数量；
- 输出 round-trip payload 估计（MiB）；
- 支持后续论文表格里的 overhead 对比。

### 4) Checkpoint reproducibility
checkpoint 里新增 `fedgrid_cfg`：
- 聚合模式
- clustering 参数
- distillation 参数

## 训练主入口

主入口（推荐）：
- `train_gnn_fedgrid.py`

版本别名：
- `train_gnn_fedgrid_v4.py`

实验矩阵脚本：
- `run_case141_fedgrid_v4.py`

## 推荐先跑的命令

### 主方法 smoke / dry run
```bash
python run_case141_fedgrid_v4.py --dry_run
```

### 主方法正式训练
```bash
python train_gnn_fedgrid.py \
  --case 141 \
  --topology_mode random_reset \
  --outage_k 6 \
  --fed_mode topo_proto \
  --fed_clustered \
  --fed_distill_coef 0.10 \
  --fed_distill_steps 1 \
  --fed_distill_batch_size 128
```

## 这一版的边界

v4 已经把“cluster + distill”接成可运行主线，但还没有实现真正的密码学 secure aggregation，也没有做正式长训结果表。
因此，这一版适合：
- 交给 Claude 审结构、创新点、方法完整性；
- 继续做 case141 主实验与 paired-seed 统计；
- 下一轮再接 DP / secure aggregation hook / 更完整的鲁棒评测。
