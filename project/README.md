# Paper Project Workspace

This workspace follows the `paper-project-autopilot` skill and acts as the research coordination layer for the FedGrid runtime bundle.

## Purpose

The repository root still contains the authoritative training, evaluation, and postprocess code. This `project/` directory tracks the paper workflow:

- project state
- decisions
- scoped research direction
- experiment plan
- manuscript drafts
- reproducibility notes

## Current Scope

Primary working scope:

- deterministic, evidence-backed evaluation of cluster-aware federated control under topology shift on the case141 benchmark

Fallback routes:

- method paper if reruns show stable paired gains
- empirical or negative-results paper if gains stay weak

## Source Of Truth

Operational source files remain in the repository root:

- `run_case141_fedgrid_v6.py`
- `train_gnn_fedgrid.py`
- `evaluate_topology_shift_deterministic.py`
- `summarize_fedgrid_suite_v6.py`
- `export_fedgrid_tables_v6.py`
- `make_fedgrid_figures_v6.py`
- `make_fedgrid_report_v6.py`

Suggested reading order:

1. `background_context.md`
2. `project_state.md`
3. `todo.md`
4. `decision_log.md`
5. `ideas/problem_framing.md`
6. `method/experiment_plan.md`
7. `submission/manuscript.md`
