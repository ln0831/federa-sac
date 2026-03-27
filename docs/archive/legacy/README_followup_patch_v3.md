# rr_k6 / followup_runs 补丁 v3

这个补丁不修改原训练代码，只新增两个外部工具：

1. `audit_followup_runs.py`
   - 检查 `followup_runs` 下每个 suite 的 checkpoint / eval 是否完整；
   - 检测同一个 baseline checkpoint 是否在不同 compare label 下出现不一致分数；
   - 如果出现不一致，通常说明当前结果是旧版非确定性评估跑出来的，需要重新做 paired deterministic eval。

2. `reevaluate_existing_followups.py`
   - 不重训练；
   - 直接使用已存在的 checkpoint；
   - 调用 `evaluate_topology_shift_deterministic.py` 重新跑 paired deterministic eval；
   - 自动聚合成 `agg_*.csv` 和 `pairwise_*.csv`。

---

## 你当前这批结果的建议结论

- `rr_k6` 和 `static_k6_shift` 的训练已经完成，checkpoint 也齐了；
- 但当前上传结果里的 baseline 在 `global` 对比和 `nobus` 对比里分数不一致，说明旧评估有随机负载噪声；
- 所以这批数 **可以看趋势，但不建议直接写论文最终表格**；
- 最省事的下一步是：**不重训，先对现有 checkpoint 做 deterministic reevaluation**。

---

## VSCode / PowerShell 可直接运行

### 1) 先体检当前 followup_runs

```powershell
python -u .\audit_followup_runs.py `
  --followup_root .\followup_runs
```

### 2) 用现有 checkpoint 重跑 rr_k6 的确定性评估（不重训）

```powershell
python -u .\reevaluate_existing_followups.py `
  --project_root . `
  --followup_root .\followup_runs `
  --suite rr_k6 `
  --gpu 0 `
  --episodes 40 `
  --output_tag det40
```

结果会输出到：

```text
.\followup_runs\rr_k6_det40\agg\
```

重点看：

```text
agg_gnn_global.csv
pairwise_gnn_global.csv
agg_gnn_nobus.csv
pairwise_gnn_nobus.csv
```

### 3) 用现有 checkpoint 重跑 static_k6_shift 的确定性评估（不重训）

```powershell
python -u .\reevaluate_existing_followups.py `
  --project_root . `
  --followup_root .\followup_runs `
  --suite static_k6_shift `
  --gpu 0 `
  --episodes 40 `
  --output_tag det40
```

### 4) fed_rr_k4 当前是未完成状态，先补齐训练，再重评估

你当前已有结果显示：
- `fed_rr_k4` 的 seed0 比较完整；
- seed1 只完成了 baseline + gnn_global_none；
- seed2 还没开始；
- 所以 `fed_rr_k4\agg\` 还是空的。

先补齐缺失训练（使用你已有的 `run_case141_followups_v2.py`）：

```powershell
python -u .\run_case141_followups_v2.py `
  --suite fed_rr_k4 `
  --project_root . `
  --output_root .\followup_runs `
  --gpu 0 `
  --seeds 0 1 2 `
  --skip_existing
```

跑完以后，再单独对 fed suite 做确定性 reevaluation：

```powershell
python -u .\reevaluate_existing_followups.py `
  --project_root . `
  --followup_root .\followup_runs `
  --suite fed_rr_k4 `
  --gpu 0 `
  --episodes 40 `
  --output_tag det40
```

---

## 推荐实验顺序

1. `audit_followup_runs.py`
2. `reevaluate_existing_followups.py --suite rr_k6`
3. `reevaluate_existing_followups.py --suite static_k6_shift`
4. 补齐 `fed_rr_k4`
5. 对 `fed_rr_k4` 做 deterministic reevaluation
6. 最后再做 Scenario C

这样最省时间，也不会浪费你已经训练好的 checkpoint。
