# Troubleshooting

## Workspace preflight fails

Run:

```bash
python scripts/check_runtime_bundle.py --project_root .
```

If files are missing, do not continue. The unified bundle root is incomplete.

## Runner dry run fails

Check:

- Python environment is activated
- `train_gnn_fedgrid.py` imports resolve
- `evaluate_topology_shift_deterministic.py` exists
- `project_root` is `.`

## summarize fails

Common causes:

- some compare runs have `summary_*.csv` but no `per_episode_*.csv`
- duplicate episode ids
- baseline/compare episode alignment mismatch

Do not bypass these checks.

## figures fail with multi-context error

This means the input paper table mixes multiple `(case, outage_k, outage_policy, outage_radius)` contexts. Split the suite or filter rows before plotting.

## report looks incomplete

Check whether:

- `suite_paired_metrics.csv` exists
- `suite_rankings.csv` exists
- all expected compare methods made it into the paired table

Do not summarize from absolute metrics only.
