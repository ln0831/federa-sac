# Reviewer Risk Register

## P0 Risks

### Overclaiming the method

Risk:

- the current evidence does not support a broad claim that the clustered distillation family consistently beats the baseline

Mitigation:

- frame the paper around deterministic paired evaluation, topology shift, and failure-aware analysis
- treat `fedgrid_topo_proto` as the clearest positive ablation in the corrected multi-seed suite

### Stale manuscript statements

Risk:

- the markdown manuscript still contains outdated references to unfinished or non-final suite states

Mitigation:

- refresh every section against `outputs/suites/INDEX.md` and the current verified artifacts before LaTeX migration

### External validity pressure

Risk:

- reviewers may challenge conclusions drawn mainly from one benchmark family

Mitigation:

- add an honest limitations paragraph
- explain clearly why case141 plus multiple topology contexts and seed-paired evaluation still provide value

### Paper identity drift

Risk:

- the manuscript may read ambiguously between method paper, evaluation paper, and tooling paper

Mitigation:

- lock one paper route and make every section support it

## P1 Risks

### Figure package feels report-like

Risk:

- existing plots are useful but may still look like exported runtime artifacts rather than curated journal figures

Mitigation:

- rebuild the final figure set with paper-specific styling and captions

### Related work under-positioned

Risk:

- if AVC, graph-control, federated learning, and robustness-evaluation strands are not separated clearly, the novelty statement will feel vague

Mitigation:

- rewrite related work by theme and contribution gap, not just by chronology

### Reproducibility not surfaced as a contribution

Risk:

- the code and tests are in decent shape, but that strength is not yet visible in the paper package

Mitigation:

- add a concise reproducibility paragraph and artifact note

## Hard Gate Before Submission

- title, abstract, introduction, results, and conclusion must make the same contribution claim
- every main-text figure and table must support one explicit claim
- stale or contradicted experimental statements must be removed
- the target venue must be locked
- the LaTeX PDF must compile cleanly
