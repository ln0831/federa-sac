# Results Draft

Status:
- drafted from completed suites only
- the live multi-seed ablation is intentionally excluded until it finishes cleanly

## Main three-seed benchmark

The primary completed evidence package is `outputs/suites/case141_fedgrid_main_rr`. On the main `random_reset` benchmark, the paired-seed table does not support a strong positive result for the current headline methods.

- `fedgrid_topo_proto`: DeltaReturn `-0.106`, 95 percent CI `[-0.267, 0.012]`, DeltaVViol `0.0000`, DeltaPLoss `0.00277`, better seeds `1/3`
- `fedgrid_v4_cluster_distill`: DeltaReturn `-0.173`, 95 percent CI `[-0.357, 0.045]`, DeltaVViol `0.0000`, DeltaPLoss `0.00451`, better seeds `1/3`

The `static` context shows the same qualitative picture, with DeltaReturn remaining negative for both methods. This matters because it means the evidence gap is not just a random-reset artifact. Under the current evaluation protocol, the safest interpretation is that the completed main benchmark does not justify a claim that the clustered or prototype-aware variants clearly outperform the baseline.

## Seed-level consistency

The seed-level paired table reinforces that conclusion. For `fedgrid_topo_proto`, only seed 1 is positive on `random_reset`, while seeds 0 and 2 are negative. The same pattern appears for `fedgrid_v4_cluster_distill`: one positive seed and two negative seeds. This weak win-count pattern is why the paper treats the current main result as negative or at best ambiguous.

## Supporting robustness evidence

The completed robustness suite, `outputs/suites/case141_fedgrid_robust_rr_20260326`, is more encouraging but should be interpreted cautiously because it is single-seed. On `random_reset`:

- `fedgrid_v4_cluster_byzantine`: DeltaReturn `+0.642`, DeltaVViol `0.0000`, DeltaPLoss `-0.01671`
- `fedgrid_v4_cluster_distill`: DeltaReturn `+0.113`, DeltaVViol `0.0000`, DeltaPLoss `-0.00296`
- `fedgrid_v4_cluster_dropout`: DeltaReturn `-0.090`, DeltaVViol `0.0000`, DeltaPLoss `0.00233`

These results show that the method family is not uniformly weak. Under some stress settings, certain variants look promising. However, the single-seed robustness suite is not a sufficient basis for a broad paper headline, especially when the completed three-seed main benchmark is negative.

## What can be claimed today

The strongest current claim is empirical: stricter paired evaluation changes the paper story. A superficial reading of isolated positive stress-test results could suggest that the method family is broadly successful. The completed multi-seed main suite shows that such a conclusion would be premature. The paper should therefore emphasize evaluation discipline, context sensitivity, and the need to separate exploratory evidence from headline evidence.
