# Method Draft

Status:
- drafted around the implemented runtime bundle and the current empirical-analysis framing

## System under study

The repository contains a FedGrid runtime bundle whose active execution chain is:

- `run_case141_fedgrid_v6.py`
- `train_gnn_fedgrid.py`
- `evaluate_topology_shift_deterministic.py`
- `summarize_fedgrid_suite_v6.py`
- `export_fedgrid_tables_v6.py`
- `make_fedgrid_figures_v6.py`
- `make_fedgrid_report_v6.py`

The paper studies the behavior of the implemented method family rather than proposing a brand-new algorithm from scratch. The currently available method labels are:

- `fedgrid_none`
- `fedgrid_topo_proto`
- `fedgrid_v4_cluster_distill`
- `fedgrid_v4_cluster_nodistill`
- `fedgrid_v4_cluster_gentle`
- `fedgrid_v4_cluster_dropout`
- `fedgrid_v4_cluster_byzantine`

The baseline is `fedgrid_none`. The other variants add topology-aware prototypes, clustered aggregation, distillation, or robustness stress mechanisms on top of the same overall control stack.

## Evaluation protocol as part of the contribution

The main methodological contribution of the current paper cycle is the evaluation protocol around this method family. Every paper-facing result is required to satisfy four rules:

1. comparisons must be context-aligned
2. metrics must be computed on deterministic evaluation outputs
3. headline claims must use paired seed deltas rather than only absolute means
4. artifact completeness must be checked before a suite is treated as evidence

In practice, this means that each suite is expected to produce manifests, deterministic per-episode outputs, summary CSVs, aggregate paired metrics, LaTeX tables, figures, and a markdown report. The human-readable status board and the autopilot scripts are part of this method layer because they reduce the chance that incomplete or mixed-path runs are mistaken for final evidence.

## Metrics and comparison logic

The paper uses three core control metrics:

- return
- `v_viol_lin_mean`
- `p_loss_mean`

Return is the primary ranking metric, but voltage violations and power loss are retained because an apparent return gain is not a clean win if it comes with worse control-quality trade-offs. For this reason, the paper treats the paired delta vector, not a single scalar, as the main unit of interpretation. Positive DeltaReturn is better, while negative DeltaVViol and DeltaPLoss are better.

## Failure-aware claim discipline

The methodological stance of the paper is intentionally failure-aware. If a method shows negative paired return on the main multi-seed benchmark, that result is not hidden behind a more favorable single-seed or mixed-context table. Likewise, if a robustness variant looks strong in a limited stress test, the paper reports it as supporting evidence rather than promoting it to a headline claim. This discipline is central to the paper's positioning and is one reason the current manuscript is written as an empirical study rather than a forced superiority narrative.
