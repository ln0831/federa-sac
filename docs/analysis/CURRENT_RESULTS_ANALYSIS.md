# 当前上传结果的快速分析（基于你这次 followup_runs）

## 1. rr_k6 当前聚合结果（旧评估，仅供趋势参考）

### gnn_global vs baseline
- random_reset: return +6.2733%, p_loss -6.2733%
- static: return +5.4682%, p_loss -5.4682%

### gnn_nobus vs baseline
- random_reset: return +0.7442%, p_loss -0.7442%
- static: return +0.3655%, p_loss -0.3655%

## 2. static_k6_shift 当前聚合结果（旧评估，仅供趋势参考）

### gnn_global vs baseline
- random_reset: return +0.8511%, p_loss -0.8511%
- static: return +0.8372%, p_loss -0.8372%

### gnn_nobus vs baseline
- random_reset: return +0.6580%, p_loss -0.6580%
- static: return +0.2506%, p_loss -0.2506%

## 3. 为什么这些数还不能直接当最终论文表格

因为同一个 baseline checkpoint 在不同 compare label 下被评出了不同分数。例如：

- rr_k6 / seed0 / static
  - 在 `gnn_global` 对比里：baseline return = -2.2239161
  - 在 `gnn_nobus` 对比里：baseline return = -2.2128478

- rr_k6 / seed0 / static
  - 在 `gnn_global` 对比里：baseline p_loss = 0.05791448
  - 在 `gnn_nobus` 对比里：baseline p_loss = 0.05762624

这说明当前结果是旧版非确定性评估跑出来的，baseline 和 compare model 没有看到完全相同的随机负载轨迹。

## 4. 当前最合理的判断

- 训练本身已经跑通，而且 `rr_k6` 和 `static_k6_shift` 的 3-seed checkpoint 已经齐了；
- 当前趋势对 `gnn_global` 是偏正面的，尤其是在 `rr_k6` 上；
- 但在没有 paired deterministic reevaluation 之前，不建议把这批数直接写成正式结论；
- 最优策略不是重训，而是先用现有 checkpoint 重评估。
