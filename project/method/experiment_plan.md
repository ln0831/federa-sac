# Experiment Plan

## Primary Benchmark

- case141

## Active Presets

- `main`
- `ablation`
- `robustness`
- `full` only if compute and evidence justify it

## Core Metrics

- return
- `v_viol_lin_mean`
- `p_loss_mean`
- `n_components_mean`

## Seed Strategy

- use `0 1 2`
- do not claim success from single-seed results
- prefer paired multi-seed summaries with confidence intervals and win counts

## Table Plan

- `table_main_random_reset.tex`
- `table_appendix_static.tex`
- `table_ablation_random_reset.tex`

## Figure Plan

- `random_reset_delta_return.png`
- `random_reset_delta_vviol.png`
- `random_reset_delta_ploss.png`

## Decision Gates

- If `main` remains weak, shift the paper framing toward empirical analysis or failure analysis.
- If `ablation` and `robustness` are stronger than `main`, emphasize robustness or mechanism insight rather than raw headline superiority.
