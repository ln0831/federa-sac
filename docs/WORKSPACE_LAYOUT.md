# Workspace Layout

This note explains what each top-level area is for so the workspace can stay usable as both a runtime bundle and a paper project.

## Keep At The Root

The repository root is the operational source of truth for runnable code. The active files are:

- `run_case141_fedgrid_v6.py`
- `train_gnn_fedgrid.py`
- `evaluate_topology_shift_deterministic.py`
- `fedgrid_federated.py`
- `summarize_fedgrid_suite_v6.py`
- `export_fedgrid_tables_v6.py`
- `make_fedgrid_figures_v6.py`
- `make_fedgrid_report_v6.py`

The remaining root-level Python modules are support modules used by the active runtime or preserved compatibility scripts.

## Documentation

- `project_docs/`: human-facing document hub and reading entrypoint
- `docs/`: curated runtime and experiment documentation
- `docs/archive/legacy/`: superseded notes kept only for traceability
- `project/`: paper-writing and research coordination workspace

If you are resuming research work, start with:

1. `project_docs/README.md`
2. `project/README.md`
3. `project/project_state.md`
4. `project/todo.md`
5. `outputs/suites/INDEX.md`

## Experiment Outputs

- `outputs/suites/`: preserved suite-level experiment assets
- `outputs/automation_logs/`: autopilot and monitoring logs
- `outputs/suites/archive_debug/`: failed or debug-only suites moved out of the main suite list
- `outputs/automation_logs/archive/`: archived failure and wrapper-debug logs
- `outputs/tmp_ablation_smoke/`: disposable smoke-test output and should not be treated as evidence

Recommended evidence directories at the moment:

- `outputs/suites/case141_fedgrid_main_rr`
- `outputs/suites/case141_fedgrid_robust_rr_20260326`
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3`

Supporting but non-headline directories:

- `outputs/suites/case141_fedgrid_tune_seed2_rr_v1`
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327`
- `outputs/suites/case141_fedgrid_main_rr_20260326`

## Packaging

- `skills/`: source for the packaged assistant skill
- `dist/skill.zip`: packaged export artifact

## Cleanup Rule

It is safe to remove the following when they reappear:

- Python cache directories
- `.pytest_cache/`
- smoke-test outputs under `outputs/tmp_ablation_smoke/`
- dry-run or wrapper-check suites created only to validate orchestration
- transient monitoring logs in `outputs/automation_logs/`
