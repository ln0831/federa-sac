# FedGrid Task Status

- Updated: `2026-04-07 03:40:59`
- Autopilot action: `status_only`
- Current suite: `case141_fedgrid_main_rr_20260407_replica`

## Queue
### case141_fedgrid_main_rr_20260407_replica
- Phase: `running`
- Running: `True`
- Checkpoints: `2`
- Expected runs: `9`
- Goal: Run a fresh independent main replica to resolve the topo_proto sign discrepancy.
- Latest run dir: `GNN-FMASAC_case141_fedgrid_none_seed0_20260407-033923`
- Latest epoch: `2` [WARMUP] RewardSum `-14.82` Reward/Step `-0.15` Loss `0.3860 MW` Alpha `0.200`
- Latest validation: Sum `-9.69` PerStep `-0.10` Best `-inf`
- Training log updated: `2026-04-07 03:40:52`
- Recent log tail:
```text
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 0 [WARMUP]: RewardSum -15.71 | Reward/Step -0.16, Loss 0.4090 MW, Alpha 0.200
  --> Validation: Sum -9.69 | PerStep -0.10 (Best: -inf)
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 1 [WARMUP]: RewardSum -15.02 | Reward/Step -0.16, Loss 0.3911 MW, Alpha 0.200
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 2 [WARMUP]: RewardSum -14.82 | Reward/Step -0.15, Loss 0.3860 MW, Alpha 0.200
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
```

### case141_fedgrid_topoproto_power_rr_20260407
- Phase: `missing`
- Running: `False`
- Checkpoints: `0`
- Expected runs: `10`
- Goal: Increase statistical power for the topo_proto versus baseline comparison.

### case141_fedgrid_robust_rr_20260407_ms3
- Phase: `missing`
- Running: `False`
- Checkpoints: `0`
- Expected runs: `12`
- Goal: Upgrade robustness evidence from single-seed to multi-seed support.

## Files
- State JSON: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_q1_autopilot_state.json`
- Status Markdown: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_q1_autopilot_status.md`
- History Log: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_q1_autopilot.log`
