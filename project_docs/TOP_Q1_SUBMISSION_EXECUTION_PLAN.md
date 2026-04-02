# Top-Q1 Submission Execution Plan

## Objective

Turn this repository into a submission-ready paper package for a realistic Q1 target by running one integrated workflow:

- lock the honest research contribution
- audit literature, code, and experiments from a reviewer perspective
- patch the highest-value weaknesses
- regenerate publication-grade figures and tables
- assemble LaTeX sources and compile a PDF

## Current Best Paper Route

Based on the existing code, reports, and manuscript draft, the strongest current route is:

- an empirical evaluation paper on deterministic, context-aligned assessment of topology-shifted federated grid control

Not the default route:

- a broad superiority claim for clustered distillation

This route can change only if new validated experiments materially change the evidence.

## Deliverables

### Main deliverables

- final LaTeX manuscript
- bibliography file
- final figure pack
- final table pack
- compiled PDF

### Support deliverables

- literature positioning memo
- reviewer-style code and reproducibility memo
- experiment and result provenance memo
- submission-readiness checklist

## Workstreams

### 1. Direction And Claim Lock

Goal:

- decide the exact paper type this repository can honestly support

Outputs:

- locked contribution statement
- locked non-goal statement
- fallback story if strongest route fails

### 2. Literature And Venue Search

Goal:

- identify nearest work, missing comparisons, and realistic Q1 venue directions

Outputs:

- closest-paper reading list
- theme-gap map
- candidate venue shortlist with fit and risk

### 3. Reviewer Audit Of Code And Pipeline

Goal:

- inspect the actual implemented method family and identify what reviewers will challenge

Outputs:

- method-family summary grounded in code
- honest contribution boundary
- reproducibility and evaluation risk list
- highest-value code or experiment fixes

### 4. Experiment Validation And Gap Filling

Goal:

- make sure every headline claim comes from validated, defendable evidence

Outputs:

- frozen list of paper-driving suites
- rerun list only for gaps that actually matter
- provenance mapping from suite CSVs to manuscript claims

### 5. Figure And Table Upgrade

Goal:

- move from internal report visuals to publication-grade visuals

Outputs:

- final figure inventory
- final table inventory
- new plotting scripts or regenerated assets if needed

### 6. Manuscript Production

Goal:

- convert the current markdown and report assets into a coherent LaTeX paper

Outputs:

- main `.tex` file
- section files if needed
- `.bib` file
- compiled PDF

### 7. Submission Readiness

Goal:

- perform final reviewer-style and formatting-style checks

Outputs:

- readiness verdict
- blocking issue list
- final patch set before submission

## Execution Sequence

### Phase A

- finish literature scan
- finish reviewer audit
- finish result asset audit

### Phase B

- merge findings into one locked paper route
- decide which code or experiment changes are actually worth doing

### Phase C

- perform targeted fixes and reruns
- regenerate figures and tables

### Phase D

- write LaTeX manuscript
- compile PDF
- run final submission check

## Current Known Risks

### Claim risk

- current main evidence does not justify a strong new-method superiority story

### Venue-fit risk

- if the contribution is mostly evaluation discipline, some method-heavy venues may judge novelty too narrowly

### Reproducibility risk

- historical path drift and archived debug artifacts can weaken confidence if the final paper does not explain the clean source-of-truth path

### Presentation risk

- current report figures are useful, but not yet sufficient as final Q1 figures without redesign or refinement

## Reviewer-Facing Quality Bar

Before calling the paper submission-ready, the project should satisfy:

- every main claim maps to validated suite outputs
- the nearest baselines and literature are cited fairly
- the method description matches the implemented method family
- limitations are acknowledged explicitly
- the code path for reproducing tables and figures is documented and runnable

## Delegated Sub-Agent Tasks

### Sub-agent A

Task:

- literature search plus Q1 venue scouting

Expected return:

- closest papers
- theme gaps
- venue shortlist
- literature-derived reviewer risks

### Sub-agent B

Task:

- reviewer-style audit of code, tests, docs, and pipeline

Expected return:

- actual implemented method family
- honest contribution boundary
- code and reproducibility weaknesses
- highest-value fixes

### Sub-agent C

Task:

- result asset and figure-gap audit

Expected return:

- which suites should drive the paper
- what figure/table assets already exist
- what new figures are needed for a Q1-level paper

## Immediate Next Actions

1. Collect the three delegated reports.
2. Merge them into a locked contribution and venue direction.
3. Decide the first concrete code or experiment fix.
4. Start manuscript-grade figure production.
5. Start LaTeX paper assembly.
