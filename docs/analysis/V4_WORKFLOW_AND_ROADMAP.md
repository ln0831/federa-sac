# 当前整体流程（建议按这个顺序推进）

## Phase 0. Code audit
- 对照原始 `codes-v10.zip`、v2、v3，梳理主训练入口、环境、评测脚本。
- 锁定可复用主线：`train_gnn.py -> train_gnn_fedgrid.py`。

## Phase 1. Literature refresh
- 重新筛选 2024-2026 联邦电网 / smart-grid FL / voltage control / robust FL 文献。
- 不只看“更高分”，而是抽取能进方法章节的机制。

## Phase 2. Base refactor
- 维护 v3 的 prototype-aware / trust-gated 主线。
- 清理入口与参数，统一 checkpoint 配置。

## Phase 3. v4 method upgrade
- 动态社区分簇
- 联邦轮后 peer distillation
- payload accounting

## Phase 4. Experiment build-out
- case141 主实验
- topology shift
- dropout / Byzantine
- clustering / distillation ablation

## Phase 5. Paper packaging
- 主表、消融表、payload 表
- 方法图
- per-agent 可视化
- paired-seed statistics

## 下一轮优先项
1. 正式长训 case141，并导出首版结果表。
2. 加 paired-seed significance 与更标准的结果聚合脚本。
3. 视收敛情况决定是否再推 secure aggregation / DP 或 safety-intervention 模块。
