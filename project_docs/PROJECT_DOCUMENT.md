# Project Document

## 1. Project Overview

Project name:

- FedGrid unified runtime bundle plus paper workspace

Project goal:

- keep one workspace that can both run the FedGrid training and evaluation pipeline and support paper writing, experiment tracking, and reproducibility packaging

Current paper direction:

- empirical analysis and evaluation-protocol paper around the FedGrid-v4 family on the `case141` benchmark

Current headline constraint:

- local evidence supports a careful empirical story, not a strong unconditional "new method beats baseline" claim

## 2. Current Source Of Truth

The repository root is still the operational source of truth for runnable code.

Active runtime files:

- `run_case141_fedgrid_v6.py`
- `train_gnn_fedgrid.py`
- `evaluate_topology_shift_deterministic.py`
- `fedgrid_federated.py`
- `summarize_fedgrid_suite_v6.py`
- `export_fedgrid_tables_v6.py`
- `make_fedgrid_figures_v6.py`
- `make_fedgrid_report_v6.py`

Supporting validation entry:

- `scripts/check_runtime_bundle.py`

## 3. Workspace Structure

### Root

Purpose:

- runnable training, evaluation, summarization, export, and report code

### `project_docs/`

Purpose:

- human-facing documentation hub for the whole workspace

Key files:

- `PROJECT_DOCUMENT.md`
- `README.md`
- `runtime/README.md`
- `research/README.md`
- `results/README.md`
- `archive/README.md`

### `docs/`

Purpose:

- runtime instructions, version map, curated references, paper-package mapping, and historical notes

### `project/`

Purpose:

- research management, writing, manuscript drafting, literature notes, and reproducibility notes

### `outputs/suites/`

Purpose:

- preserved experiment suites

### `outputs/suites/archive_debug/`

Purpose:

- failed or historical debug suites moved out of the main evidence view

### `outputs/automation_logs/`

Purpose:

- current autopilot and run-monitor logs

### `outputs/automation_logs/archive/`

Purpose:

- archived failure logs and wrapper-debug logs

## 4. Recommended Reading Order

If you want to understand the whole project quickly, read in this order:

1. `project_docs/PROJECT_DOCUMENT.md`
2. `README_UNIFIED_RUNTIME_BUNDLE.md`
3. `docs/WORKSPACE_LAYOUT.md`
4. `project/README.md`
5. `project/project_state.md`
6. `outputs/suites/INDEX.md`

If you want to run experiments:

1. `project_docs/runtime/README.md`
2. `docs/VERSION_MAP_AND_SOURCE_OF_TRUTH.md`
3. `docs/ENVIRONMENT_SETUP_CONDA_AND_UV.md`
4. `docs/EXPERIMENT_RUNBOOK.md`

If you want to write or revise the paper:

1. `project_docs/research/README.md`
2. `project/background_context.md`
3. `project/project_state.md`
4. `project/todo.md`
5. `project/submission/manuscript.md`

## 5. Current Experiment Evidence

Main evidence suite:

- `outputs/suites/case141_fedgrid_main_rr`

Supporting evidence suites:

- `outputs/suites/case141_fedgrid_robust_rr_20260326`
- `outputs/suites/case141_fedgrid_tune_seed2_rr_v1`

Exploratory but not final:

- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327`
- `outputs/suites/case141_fedgrid_main_rr_20260326`

Final ablation evidence for the current cycle:

- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3`

Archived debug-only suites:

- `outputs/suites/archive_debug/case141_fedgrid_ablation_custom_rr_20260326`
- `outputs/suites/archive_debug/case141_fedgrid_main_rr_failed_prefix_20260323_153748`
- `outputs/suites/archive_debug/case141_fedgrid_tune_seed2_rr`

## 6. Current Evidence Summary

Verified local status:

- runtime bundle check passes in the current workspace
- the main suite is available as the primary paper evidence package
- the robustness suite completed and is usable as supporting evidence
- the corrected multi-seed ablation suite completed and has manifests, aggregate outputs, tables, figures, and report

Most important finding right now:

- `fedgrid_topo_proto` is the only positive result in the corrected three-seed custom ablation

Important negative finding:

- the clustered distillation variants do not support the strongest mechanism headline in the current evidence

## 7. Writing Status

The writing workspace already contains:

- scope and decision records in `project/`
- literature notes and matrix in `project/literature/`
- section drafts in `project/paper/`
- assembled manuscript draft in `project/submission/manuscript.md`

Writing rule:

- keep claims aligned with verified suites, especially `main`, `robustness`, and `ablation_custom_rr_20260327_ms3`

## 8. Cleanup Rules

Safe to remove when they reappear:

- `__pycache__/`
- `.pytest_cache/`
- smoke-test outputs
- temporary dry-run or wrapper-check suites
- transient monitor logs that have already been archived

Should be archived instead of casually deleted:

- failed historical suites
- old wrapper or launch failure logs
- outdated manifests that still help explain path drift or orchestration bugs

## 9. Next Recommended Actions

If the goal is execution:

- rerun `pytest -q tests`
- use the main runner with `--dry_run` before any expensive suite launch

If the goal is paper progress:

- tighten manuscript framing around empirical findings
- avoid overclaiming clustered distillation gains
- use the corrected multi-seed ablation as the final ablation evidence source

If the goal is further cleanup:

- only move old `v2` and `v4` root scripts after checking every remaining legacy reference under `docs/archive/legacy/`

## 10. One-Line Orientation

This workspace is now organized as:

- root for runnable code
- `project_docs/` for human-facing navigation
- `project/` for research and manuscript work
- `outputs/suites/` for active experiment evidence
- archive folders for debug history
