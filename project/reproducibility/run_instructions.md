# Run Instructions

## Preflight

```powershell
D:\Anaconda\envs\tianshou_env\python.exe scripts\check_runtime_bundle.py --project_root .
```

## Lightweight validation

```powershell
D:\Anaconda\envs\tianshou_env\python.exe -m pytest -q tests\test_v8_runner_flags.py tests\test_v8_summary_pipeline.py
```

## Full validation

```powershell
D:\Anaconda\envs\tianshou_env\python.exe -m pytest -q tests
```

## Main dry run

```powershell
D:\Anaconda\envs\tianshou_env\python.exe run_case141_fedgrid_v6.py --project_root . --suite_name case141_fedgrid_main_rr --preset main --methods preset --seeds 0 1 2 --train_topology_mode random_reset --outage_k 6 --outage_policy local --outage_radius 2 --gpu 0 --epochs 100 --no_post --dry_run
```

## Main run

```powershell
D:\Anaconda\envs\tianshou_env\python.exe run_case141_fedgrid_v6.py --project_root . --suite_name case141_fedgrid_main_rr --preset main --methods preset --seeds 0 1 2 --train_topology_mode random_reset --outage_k 6 --outage_policy local --outage_radius 2 --gpu 0 --epochs 100 --no_post
```

## Postprocess

```powershell
D:\Anaconda\envs\tianshou_env\python.exe summarize_fedgrid_suite_v6.py --suite_root outputs/suites/case141_fedgrid_main_rr
D:\Anaconda\envs\tianshou_env\python.exe export_fedgrid_tables_v6.py --suite_root outputs/suites/case141_fedgrid_main_rr
D:\Anaconda\envs\tianshou_env\python.exe make_fedgrid_figures_v6.py --suite_root outputs/suites/case141_fedgrid_main_rr
D:\Anaconda\envs\tianshou_env\python.exe make_fedgrid_report_v6.py --suite_root outputs/suites/case141_fedgrid_main_rr
```

## Notes

- Treat the current workspace root as the only `project_root`.
- Do not claim success until manifests, aggregate CSVs, figures, LaTeX tables, and the markdown report all exist.
- Reruns should record new suite names if historical path contamination is a concern.
