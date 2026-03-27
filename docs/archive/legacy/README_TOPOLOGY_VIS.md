# Topology change (paper-style outages) + visualization

This project now supports **topology variation** via **random multi-line outages per episode**.

## 1) Enable topology change

All grid environments (`env_33.py`, `env_69.py`, `env_141.py`, `env_oberrhein.py`) support:

- `topology_mode`:
  - `static`: always use the base topology
  - `random_reset`: on every `reset()`, sample `outage_k` in-service lines and set them `in_service=False`
- `outage_k`: number of line outages per episode
- `topology_seed`: deterministic seed; the actual sample seed is `topology_seed + episode_idx`

Paper-style defaults (used if you do not specify `--outage_k`):
- case33 / case69: `outage_k=3`
- case141 / oberrhein: `outage_k=4`

## 2) Train baseline / GNN under topology change

Baseline (FMASAC + MLP mixer):
```bash
python train_fmasac.py --case 141 --topology_mode random_reset
```

GNN (FMASAC + GraphMixer):
```bash
python train_gnn.py --case 141 --topology_mode random_reset
```

Notes:
- Both trainers support an optional **context embedding** branch in the mixer (enabled by default).
  Disable with `--no_context`.
- In `train_gnn.py`, when `topology_mode=random_reset`, the **agent adjacency** is recomputed on every reset
  and pushed into the mixer via `set_adjacency()`.

## 3) Export rollouts + visualize

Export per-step logs:
```bash
python export_rollout.py --case 141 --algo baseline --ckpt ./checkpoints/best_model_141.pth --episodes 10 --out_dir ./rollouts
python export_rollout.py --case 141 --algo gnn --ckpt ./checkpoints/best_model_gnn_141.pth --episodes 10 --out_dir ./rollouts
```

Plot comparisons:
```bash
python plot_results.py --baseline ./rollouts/rollout_baseline_141_random_reset_k4_seed0.csv \
  --gnn ./rollouts/rollout_gnn_141_random_reset_k4_seed0.csv
```

## 4) Directly quantify topology shift impact

```bash
python evaluate_topology_shift.py --case 141 \
  --baseline_ckpt ./checkpoints/best_model_141.pth \
  --gnn_ckpt ./checkpoints/best_model_gnn_141.pth \
  --episodes 20 --out_dir ./eval
```

This produces:
- per-episode CSVs (return, avg voltage violation, avg losses, avg connectivity)
- a summary CSV comparing `static` vs `random_reset` for baseline vs GNN
