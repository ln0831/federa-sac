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

- The historical suite `case141_fedgrid_main_rr` is retained because it carries the original negative main-benchmark result.
- The clean rerun `case141_fedgrid_main_rr_20260402_clean` is the current working-draft main package.
- The corrected multi-seed ablation `case141_fedgrid_ablation_custom_rr_20260327_ms3` is the current working-draft ablation package.

## Current Q1 Queue

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\ASUS\Desktop\runtime_bundle\scripts\launch_fedgrid_q1_autopilot.ps1" -RootDir "C:\Users\ASUS\Desktop\runtime_bundle" -PythonExe "D:\Anaconda\envs\tianshou_env\python.exe"
```

## Q1 Status Command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\ASUS\Desktop\runtime_bundle\scripts\show_fedgrid_q1_status.ps1" -RootDir "C:\Users\ASUS\Desktop\runtime_bundle" -PythonExe "D:\Anaconda\envs\tianshou_env\python.exe"
```

## Future Full Rerun Command

```powershell
D:\Anaconda\envs\tianshou_env\python.exe run_case141_fedgrid_v6.py --project_root . --suite_name case141_fedgrid_main_rr_20260326 --preset main --methods preset --seeds 0 1 2 --train_topology_mode random_reset --outage_k 6 --outage_policy local --outage_radius 2 --gpu 0 --epochs 100 --no_post
```
