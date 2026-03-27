# rr_k6 pilot 分析后的外部补丁（不改原工程）

这个压缩包解决两个实际问题：

1. **pilot 用 `--epochs 100` 不能用来判断最终排名**
   - 原训练代码使用 `CosineAnnealingLR(T_max=epochs)`。
   - 所以 100 epoch 不是“先跑 500 里的前 100”，而是把整条学习率曲线压缩到 100。
   - 对 case141 + k6 这种更难任务，100 epoch 只能用于检查流程是否能跑通，不适合下最终结论。

2. **原评估存在重复评估噪声**
   - `env_141.reset()` 里 load scale 来自 `np.random.uniform(...)`，但未固定种子。
   - 因此同一个 checkpoint 重复评估，甚至 baseline 与 GNN 对比时，也可能看到不同 episode 负荷扰动。
   - 新的 `evaluate_topology_shift_deterministic.py` 会在每个 episode reset 前固定 `python / numpy / torch` 的随机种子，让 baseline 和 GNN 看同一组 episode 扰动。

## 你现在应该怎么做

### 先不要据此 pilot 直接开 full suite
先用下面这条做**seed0 全 epoch + 稳定评估**：

```powershell
python -u .\run_case141_followups_v2.py `
  --suite rr_k6 `
  --project_root . `
  --output_root .\followup_runs_v2 `
  --gpu 0 `
  --seeds 0 `
  --episodes 40 `
  --val_episodes 10 `
  --skip_existing
```

说明：
- 不再传 `--epochs 100`，直接用原训练默认 500 epoch；
- `--val_episodes 10` 让 hardest setting 下的 best checkpoint 选择更稳；
- `--episodes 40` 让最终评估更稳；
- `--skip_existing` 会复用已经存在的 checkpoint，若你想重训，请删掉这个参数。

### 如果 seed0 全 epoch 后 GNN-global >= baseline
再开全 3 seeds：

```powershell
python -u .\run_case141_followups_v2.py `
  --suite rr_k6 `
  --project_root . `
  --output_root .\followup_runs_v2 `
  --gpu 0 `
  --seeds 0 1 2 `
  --episodes 40 `
  --val_episodes 10
```

### 如果 seed0 全 epoch 后 GNN-global 仍略输 baseline
只做一个最小改动版本：

```powershell
python -u .\run_case141_followups_v2.py `
  --suite rr_k6 `
  --project_root . `
  --output_root .\followup_runs_v2_tuned `
  --gpu 0 `
  --seeds 0 `
  --episodes 40 `
  --val_episodes 10 `
  --mixer_gat_ramp_epochs 100 `
  --edge_drop 0.05
```

含义：
- `mixer_gat_ramp_epochs 100`：让 harder k6 下 GAT 分支更慢接入；
- `edge_drop 0.05`：减少结构扰动过强带来的信息损失。

如果这个版本回到持平或反超 baseline，再扩到 3 个 seeds。

## 这次 pilot 应该怎么解释

### 可以确认的
- **整个 pipeline 已经跑通**：训练、保存 checkpoint、评估、聚合都没坏。
- **nobus 仍然明显更差**，这一点和你之前主结论一致：GraphMixer alone 不够，bus-level encoding 依然关键。

### 现在还不能下结论的
- 不能根据 100 epoch seed0 pilot 就说 “k=6 下 global 不行”。
- 更准确的表述是：
  - 当前 pilot 下，`gnn_global` 与 baseline **接近持平但略输**；
  - 差距很小，且当前评估有噪声，训练又是压缩学习率的短跑，所以**不足以否定方法**。

## 跑完 rr_k6 后下一步
1. 先补 `static_k6_shift`
2. 再做 `fed_rr_k4`
3. 最后做 Scenario C
   - Scenario C 建议用你原有脚本，但加上：

```powershell
--reset_load_mode base
```

这样会去掉 env.reset 的随机 load jitter，让 stress test 更公平。
