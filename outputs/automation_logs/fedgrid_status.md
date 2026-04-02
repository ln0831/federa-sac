# FedGrid Task Status

- Updated: `2026-04-02 01:52:28`
- Autopilot action: `status_only`
- Current suite: `none`

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
- Phase: `complete`
- Running: `False`
- Checkpoints: `16`
- Expected runs: `15`
- Goal: Run the multi-seed ablation follow-up with nodistill and gentle cluster variants.
- Latest run dir: `GNN-FMASAC_case141_fedgrid_v4_cluster_gentle_seed2_20260327-233519`
- Training log updated: `2026-03-28 01:05:06`
- Recent log tail:
```text
[RUN] 'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\evaluate_topology_shift_deterministic.py' --case 141 --baseline_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\checkpoints\best_case141_fedgrid_none_seed2.pth' --gnn_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\checkpoints\best_case141_fedgrid_topo_proto_seed2.pth' --baseline_name fedgrid_none --gnn_name fedgrid_topo_proto --episodes 20 --topology_seed 2 --eval_seed_base 1000 --outage_k 6 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --gpu 0 --out_dir 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\eval\fedgrid_topo_proto_seed2'
[RUN] 'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\evaluate_topology_shift_deterministic.py' --case 141 --baseline_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\checkpoints\best_case141_fedgrid_none_seed2.pth' --gnn_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\checkpoints\best_case141_fedgrid_v4_cluster_distill_seed2.pth' --baseline_name fedgrid_none --gnn_name fedgrid_v4_cluster_distill --episodes 20 --topology_seed 2 --eval_seed_base 1000 --outage_k 6 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --gpu 0 --out_dir 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\eval\fedgrid_v4_cluster_distill_seed2'
[RUN] 'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\evaluate_topology_shift_deterministic.py' --case 141 --baseline_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\checkpoints\best_case141_fedgrid_none_seed2.pth' --gnn_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\checkpoints\best_case141_fedgrid_v4_cluster_nodistill_seed2.pth' --baseline_name fedgrid_none --gnn_name fedgrid_v4_cluster_nodistill --episodes 20 --topology_seed 2 --eval_seed_base 1000 --outage_k 6 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --gpu 0 --out_dir 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\eval\fedgrid_v4_cluster_nodistill_seed2'
[RUN] 'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\evaluate_topology_shift_deterministic.py' --case 141 --baseline_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\checkpoints\best_case141_fedgrid_none_seed2.pth' --gnn_ckpt 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\checkpoints\best_case141_fedgrid_v4_cluster_gentle_seed2.pth' --baseline_name fedgrid_none --gnn_name fedgrid_v4_cluster_gentle --episodes 20 --topology_seed 2 --eval_seed_base 1000 --outage_k 6 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 --gpu 0 --out_dir 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\eval\fedgrid_v4_cluster_gentle_seed2'
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\manifests\fedgrid_v6_run_matrix.csv
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\manifests\fedgrid_v6_commands.csv
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\manifests\fedgrid_v6_suite_manifest.json
[SAVED] C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_ablation_custom_rr_20260327_ms3\manifests\fedgrid_v6_postprocess.sh
```

## Files
- State JSON: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_autopilot_state.json`
- Status Markdown: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_status.md`
- History Log: `C:\Users\ASUS\Desktop\runtime_bundle\outputs\automation_logs\fedgrid_autopilot.log`
