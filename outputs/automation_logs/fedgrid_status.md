# FedGrid Task Status

- Updated: `2026-03-27 13:39:11`
- Autopilot action: `status_only`
- Current suite: `case141_fedgrid_ablation_custom_rr_20260327_ms3`

## Queue
### case141_fedgrid_robust_rr_20260326
- Phase: `complete`
- Running: `False`
- Checkpoints: `5`
- Expected runs: `4`
- Goal: Fill the robustness evidence gap for dropout and Byzantine variants.
- Latest run dir: `GNN-FMASAC_case141_fedgrid_v4_cluster_byzantine_seed0_20260326-193908`
- Training log updated: `2026-03-26 21:02:35`
- Recent log tail:
```text
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_robust_rr_20260326\agg\suite_paper_table_main_random_reset.csv
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_robust_rr_20260326\agg\suite_paper_table_appendix_static.csv
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_robust_rr_20260326\reports\latex
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_robust_rr_20260326\reports\figures\random_reset_delta_return.png
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_robust_rr_20260326\reports\figures\random_reset_delta_vviol.png
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_robust_rr_20260326\reports\figures\random_reset_delta_ploss.png
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_robust_rr_20260326\reports\figures\static_delta_return.png
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_robust_rr_20260326\reports\fedgrid_v6_report.md
```

### case141_fedgrid_ablation_custom_rr_20260327_ms3
- Phase: `running`
- Running: `True`
- Checkpoints: `5`
- Expected runs: `15`
- Goal: Run the multi-seed ablation follow-up with nodistill and gentle cluster variants.
- Latest run dir: `GNN-FMASAC_case141_fedgrid_v4_cluster_nodistill_seed0_20260327-133534`
- Latest epoch: `8` [WARMUP] RewardSum `-15.36` Reward/Step `-0.16` Loss `0.4001 MW` Alpha `0.200`
- Latest validation: Sum `-7.92` PerStep `-0.08` Best `-6.71`
- Training log updated: `2026-03-27 13:39:11`
- Recent log tail:
```text
Epoch 6 [WARMUP]: RewardSum -13.19 | Reward/Step -0.14, Loss 0.3434 MW, Alpha 0.200
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 7 [WARMUP]: RewardSum -15.96 | Reward/Step -0.17, Loss 0.4156 MW, Alpha 0.200
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 8 [WARMUP]: RewardSum -15.36 | Reward/Step -0.16, Loss 0.4001 MW, Alpha 0.200
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
```

## Files
- State JSON: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_autopilot_state.json`
- Status Markdown: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_status.md`
- History Log: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_autopilot.log`
