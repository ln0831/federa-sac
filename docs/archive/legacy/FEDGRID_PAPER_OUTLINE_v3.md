# 论文方法骨架（FedGrid-v2）

## 1. Problem formulation

我们考虑一个配电网电压控制问题，其中每个区域 agent 只能访问本区域局部观测，不能共享原始运行数据。各区域在不同拓扑扰动、负荷波动和可再生出力场景下形成异构的局部 MDP，因此需要一种兼顾隐私、异构性和拓扑迁移鲁棒性的联邦多智能体控制框架。

## 2. Local control backbone

本地控制器采用 GNN-enhanced FMASAC：
- actor：局部观测 + bus-GNN embedding
- critic：局部价值建模
- mixer：以 agent adjacency 建模区域间耦合

## 3. Hybrid prototype bank

给每个 client 维护两个 prototype：
- observation prototype：原始局部电气统计摘要；
- graph prototype：bus-GNN 表征；

通过 EMA 更新，形成 client-level representation memory。

## 4. Trust-gated federated aggregation

每轮联邦聚合时，构造加权矩阵：

\[
W = f(W_{topo}, W_{proto}, trust, staleness)
\]

其中：
- `W_topo`：电网区域拓扑相似度
- `W_proto`：prototype 相似度
- `trust`：基于模型签名与 reward EMA 的可信度
- `staleness`：掉线或低质量 client 的轮次陈旧度

## 5. Consensus branch

为避免在强异构场景下过度平均，引入 consensus/self-retention 分支：
- 对称化 client graph；
- 保留一定比例的 self-weight；
- 提高拓扑迁移和部分参与场景下的稳定性。

## 6. Robust federation

### 6.1 Partial participation
通过 client dropout 模拟通信不完整参与：
- inactive client 不上传更新；
- 可选择冻结 inactive target；
- staleness 进入下一轮联邦权重。

### 6.2 Byzantine stress test
通过 synthetic attack 检验聚合鲁棒性：
- noise
- signflip
- scale

## 7. Expected contributions

1. 提出一种面向联邦电网控制的 hybrid-prototype 聚合框架；
2. 将 topology、prototype、trust、staleness 统一进多智能体联邦聚合矩阵；
3. 针对 topology shift、partial participation 和 byzantine perturbation 提供统一评测；
4. 在 case141 等配电网场景上验证其在鲁棒性和可部署性上的优势。
