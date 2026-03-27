# Repro Commands

## Verified Validation

```powershell
D:\Anaconda\envs\tianshou_env\python.exe -m pytest -q tests
```

## Verified Dry Run

```powershell
D:\Anaconda\envs\tianshou_env\python.exe run_case141_fedgrid_v6.py --project_root . --suite_name case141_fedgrid_main_rr_20260326 --preset main --methods preset --seeds 0 1 2 --train_topology_mode random_reset --outage_k 6 --outage_policy local --outage_radius 2 --gpu 0 --epochs 100 --no_post --dry_run
```

## Current Packaging Decision

- The existing completed suite `case141_fedgrid_main_rr` is used as the main evidence package.
- The fresh rerun `case141_fedgrid_main_rr_20260326` was used to validate the current environment and manifests, then stopped to avoid wasting many hours on a CPU-only duplicate of an already completed main suite.

## Future Full Rerun Command

```powershell
D:\Anaconda\envs\tianshou_env\python.exe run_case141_fedgrid_v6.py --project_root . --suite_name case141_fedgrid_main_rr_20260326 --preset main --methods preset --seeds 0 1 2 --train_topology_mode random_reset --outage_k 6 --outage_policy local --outage_radius 2 --gpu 0 --epochs 100 --no_post
```
