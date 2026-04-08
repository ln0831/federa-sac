# Claims

## Safe Claims

- The repository contains a runnable end-to-end pipeline for training, deterministic evaluation, aggregation, table export, figure export, and report generation.
- The current workspace passes full `pytest -q tests` inside `D:\Anaconda\envs\tianshou_env\python.exe`.
- The project now contains a historical main suite, a clean current-workspace rerun, and a fresh independent main replica, each with paired metrics, LaTeX tables, figures, and markdown reports suitable for audit and paper drafting.
- Context-aligned paired evaluation is the correct evidence layer for this project.
- The current local evidence does not support a strong claim that the clustered method family clearly outperforms the baseline on the main benchmark.
- `fedgrid_v4_cluster_distill` is not supported as a positive headline method by the strongest current evidence packages.
- `fedgrid_topo_proto` is still the only currently promising variant, but it remains mixed-sign or near-zero on the main benchmark, so any superiority claim would currently be overstated.

## Unsafe Claims

- The clustered method is definitively better than baseline.
- `fedgrid_topo_proto` is already proven superior on the main benchmark.
- Single-seed tuning outputs prove the ablation story.
- Single-seed robustness outputs prove a robust positive method story.
- Historical non-deterministic follow-up runs are valid as final paper evidence.
