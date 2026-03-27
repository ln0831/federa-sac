# FedGrid Task Status

- Updated: `2026-03-27 02:18:07`
- Autopilot action: `status_only`
- Current suite: `case141_fedgrid_ablation_custom_rr_20260327`

## Queue
### case141_fedgrid_robust_rr_20260326
- Phase: `complete`
- Running: `False`
- Checkpoints: `5`
- Expected runs from manifest: `4`
- Goal: Fill the robustness evidence gap for dropout and Byzantine variants.
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

### case141_fedgrid_ablation_custom_rr_20260327
- Phase: `running`
- Running: `True`
- Checkpoints: `2`
- Expected runs from manifest: `0`
- Goal: Run the multi-seed ablation follow-up with nodistill and gentle cluster variants.
- Latest epoch: `5` [WARMUP] RewardSum `-14.99` Reward/Step `-0.16` Loss `0.3902 MW` Alpha `0.200`
- Latest validation: Sum `-15.40` PerStep `-0.16` Best `-inf`
- Training log updated: `2026-03-27 02:18:06`
- Recent log tail:
```text
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 2 [WARMUP]: RewardSum -16.10 | Reward/Step -0.17, Loss 0.4193 MW, Alpha 0.200
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 3 [WARMUP]: RewardSum -16.45 | Reward/Step -0.17, Loss 0.4283 MW, Alpha 0.200
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 4 [WARMUP]: RewardSum -15.48 | Reward/Step -0.16, Loss 0.4030 MW, Alpha 0.200
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 5 [WARMUP]: RewardSum -14.99 | Reward/Step -0.16, Loss 0.3902 MW, Alpha 0.200
```

## Files
- State JSON: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_autopilot_state.json`
- Status Markdown: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_status.md`
- History Log: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_autopilot.log`
