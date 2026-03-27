# Checkpoint naming update

## What changed

`train_fmasac.py` and `train_gnn.py` now support these optional arguments:

- `--exp_name`
- `--log_dir`
- `--save_dir`

If `--exp_name` is provided:

- A unique checkpoint is saved as `best_<exp_name>.pth` (sanitized for filesystem safety).
- The legacy compatibility alias is still updated:
  - baseline: `best_model_<case>.pth`
  - gnn: `best_model_gnn_<case>.pth`

If `--exp_name` is not provided, behavior remains unchanged.

## Example

```powershell
python .\train_fmasac.py --case 141 --exp_name fmasac_B_k4_seed0
python .\train_gnn.py --case 141 --exp_name gnn_global_B_k4_seed0
```

This will additionally create:

- `checkpoints/best_fmasac_B_k4_seed0.pth`
- `checkpoints/best_gnn_global_B_k4_seed0.pth`

while still keeping the legacy latest aliases updated.
