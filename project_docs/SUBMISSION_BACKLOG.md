# Submission Backlog

## Locked Current Position

Primary paper route for now:

- empirical and evaluation-focused paper on topology-shifted federated grid control with deterministic paired evaluation and failure-aware analysis

Why this is locked for now:

- current multi-seed evidence does not support a strong blanket superiority claim for the clustered distillation family
- the strongest positive signal currently comes from `fedgrid_topo_proto` in the corrected multi-seed ablation suite
- the codebase and pipeline look materially usable, so the bigger risk is framing and claim discipline rather than missing infrastructure

## Immediate Priority Tasks

### P0

- rewrite claim-to-evidence mapping so every headline claim is explicitly backed by one verified suite
- audit and refresh the markdown manuscript to remove stale statements about unfinished suites
- start a real LaTeX manuscript workspace

### P1

- expand the related-work base with the closest AVC, graph-MARL, topology-shift, robustness, and federated-control papers
- decide the final figure set for the main text and appendix
- promote the best existing figures and tables into a paper-ready asset folder
- decide whether any targeted reruns are necessary for venue fit

### P2

- style-upgrade figures for journal readability
- complete appendix and reproducibility section
- run final submission-readiness audit

## Known Strong Assets

- `outputs/suites/case141_fedgrid_main_rr`
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3`
- `outputs/suites/case141_fedgrid_robust_rr_20260326`
- `outputs/suites/case141_fedgrid_tune_seed2_rr_v1`
- `project/submission/manuscript.md`
- `docs/paper_package/`

## Known Risks

- manuscript framing still leans on an older weaker story in places
- external validity is limited by current benchmark scope
- clustered distillation is currently not defensible as the strongest headline
- there is not yet a formal LaTeX submission project
- reviewer confidence will drop if stale text and stale path references remain in the manuscript

## Candidate Venue Direction

Current shortlist to validate:

- `IEEE Transactions on Smart Grid`
- `Applied Energy`
- `IEEE Transactions on Sustainable Energy`
- backup: `Engineering Applications of Artificial Intelligence`

## Current Execution Rule

Do not start expensive reruns until one of these is true:

- a target venue clearly requires an experiment that is currently missing
- a reviewer-facing gap cannot be closed by tighter writing, better positioning, or existing suite assets

## Next Concrete Edits

1. Set up `paper_latex/` with a compilable skeleton.
2. Begin migrating the markdown manuscript into LaTeX with corrected claims.
3. Refresh the manuscript against `outputs/suites/INDEX.md` and the corrected ablation suite.
4. Build a clean claim-to-evidence mapping appendix or working note.
5. Decide whether any venue-driven targeted rerun is necessary.
