# FedGrid v3 Package Manifest

## Primary entry points
- `train_gnn_fedgrid.py`: unified main training entry.
- `fedgrid_federated.py`: federated aggregation, prototype bank, trust/staleness logic.
- `run_case141_fedgrid_v2.py`: batch experiment runner for case141.

## Primary documents
- `README_FedGrid_Refactor_v3.md`: project-level description and usage.
- `FEDGRID_EXPERIMENT_MATRIX_v3.md`: experiment matrix and paper table/figure plan.
- `FEDGRID_PAPER_OUTLINE_v3.md`: method and paper outline.
- `FEDGRID_LITERATURE_TO_CODE_MAP.md`: literature-to-module mapping.
- `CURRENT_RESULTS_ANALYSIS.md`: notes about current results and caveats.

## Compatibility notes
- `train_gnn_fedgrid_v2.py` is preserved for backwards compatibility.
- `train_gnn_fedgrid.py` is the preferred filename for external review.
