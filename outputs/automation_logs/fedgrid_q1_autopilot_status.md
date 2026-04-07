# FedGrid Task Status

- Updated: `2026-04-07 12:42:24`
- Autopilot action: `status_only`
- Current suite: `case141_fedgrid_topoproto_power_rr_20260407`

## Queue
### case141_fedgrid_main_rr_20260407_replica
- Phase: `complete`
- Running: `False`
- Checkpoints: `10`
- Expected runs: `9`
- Goal: Run a fresh independent main replica to resolve the topo_proto sign discrepancy.
- Latest run dir: `GNN-FMASAC_case141_fedgrid_v4_cluster_distill_seed2_20260407-102830`
- Training log updated: `2026-04-07 11:35:40`
- Recent log tail:
```text
[RUN] 'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\train_gnn_fedgrid.py' --save_dir 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\checkpoints' --log_dir 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\logs' --exp_name case141_fedgrid_topo_proto_seed2 --case 141 --gpu 0 --epochs 100 --val_episodes 5 --topology_mode random_reset --outage_k 6 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --topology_seed 2 --bus_gnn_scope global --mixer_gat_ramp_epochs 50 --mixer_gate_init_bias -5.0 --mixer_gnn_lr_scale 0.1 --mixer_gate_lr_scale 0.1 --edge_drop 0.1 --bus_gnn_lr_scale 0.1 --bus_gnn_use_base_topology --mixer_use_base_topology --fed_mode topo_proto --fed_proto_source hybrid
[RUN] 'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\train_gnn_fedgrid.py' --save_dir 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\checkpoints' --log_dir 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\logs' --exp_name case141_fedgrid_v4_cluster_distill_seed2 --case 141 --gpu 0 --epochs 100 --val_episodes 5 --topology_mode random_reset --outage_k 6 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --topology_seed 2 --bus_gnn_scope global --mixer_gat_ramp_epochs 50 --mixer_gate_init_bias -5.0 --mixer_gnn_lr_scale 0.1 --mixer_gate_lr_scale 0.1 --edge_drop 0.1 --bus_gnn_lr_scale 0.1 --bus_gnn_use_base_topology --mixer_use_base_topology --fed_mode topo_proto --fed_proto_source hybrid --fed_clustered --fed_cluster_knn 2 --fed_cluster_threshold 0.58 --fed_max_clusters 4 --fed_inter_cluster_scale 0.08 --fed_cluster_self_boost 0.1 --fed_distill_coef 0.1 --fed_distill_steps 1 --fed_distill_batch_size 128 --fed_distill_same_cluster_only
[RUN] 'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\evaluate_topology_shift_deterministic.py' --case 141 --baseline_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\checkpoints\best_case141_fedgrid_none_seed2.pth' --gnn_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\checkpoints\best_case141_fedgrid_topo_proto_seed2.pth' --baseline_name fedgrid_none --gnn_name fedgrid_topo_proto --episodes 20 --topology_seed 2 --eval_seed_base 1000 --outage_k 6 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --gpu 0 --out_dir 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\eval\fedgrid_topo_proto_seed2'
[RUN] 'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\evaluate_topology_shift_deterministic.py' --case 141 --baseline_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\checkpoints\best_case141_fedgrid_none_seed2.pth' --gnn_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\checkpoints\best_case141_fedgrid_v4_cluster_distill_seed2.pth' --baseline_name fedgrid_none --gnn_name fedgrid_v4_cluster_distill --episodes 20 --topology_seed 2 --eval_seed_base 1000 --outage_k 6 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --gpu 0 --out_dir 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\eval\fedgrid_v4_cluster_distill_seed2'
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\manifests\fedgrid_v6_run_matrix.csv
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\manifests\fedgrid_v6_commands.csv
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\manifests\fedgrid_v6_suite_manifest.json
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr_20260407_replica\manifests\fedgrid_v6_postprocess.sh
```

### case141_fedgrid_topoproto_power_rr_20260407
- Phase: `running`
- Running: `True`
- Checkpoints: `2`
- Expected runs: `10`
- Goal: Increase statistical power for the topo_proto versus baseline comparison.
- Latest run dir: `GNN-FMASAC_case141_fedgrid_none_seed0_20260407-120107`
- Latest epoch: `90` [TRAIN] RewardSum `-11.74` Reward/Step `-0.12` Loss `0.3058 MW` Alpha `0.083`
- Latest validation: Sum `-3.24` PerStep `-0.03` Best `-3.13`
- Training log updated: `2026-04-07 12:42:03`
- Recent log tail:
```text
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 88 [TRAIN]: RewardSum -10.57 | Reward/Step -0.11, Loss 0.2752 MW, Alpha 0.083
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 89 [TRAIN]: RewardSum -10.39 | Reward/Step -0.11, Loss 0.2705 MW, Alpha 0.083
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
Epoch 90 [TRAIN]: RewardSum -11.74 | Reward/Step -0.12, Loss 0.3058 MW, Alpha 0.083
  --> Validation: Sum -3.24 | PerStep -0.03 (Best: -3.13)
[GNN Utils] Agent Adjacency Matrix Constructed. mode=inv_z, normalize=True, shape=(4, 4)
```

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
