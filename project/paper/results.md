# Results Draft

Status:
- drafted from completed suites only
- includes the corrected multi-seed ablation and the clean current-workspace main rerun

## Historical main versus clean rerun

The historical main suite and the clean rerun disagree in a way that is scientifically important.

From `outputs/suites/case141_fedgrid_main_rr` on `random_reset`:

- `fedgrid_topo_proto`: DeltaReturn `-0.106`, 95 percent CI `[-0.267, 0.012]`, DeltaPLoss `0.00277`, better seeds `1/3`
- `fedgrid_v4_cluster_distill`: DeltaReturn `-0.173`, 95 percent CI `[-0.357, 0.045]`, DeltaPLoss `0.00451`, better seeds `1/3`

From `outputs/suites/case141_fedgrid_main_rr_20260402_clean` on `random_reset`:

- `fedgrid_topo_proto`: DeltaReturn `+0.122`, 95 percent CI `[-0.016, 0.208]`, DeltaPLoss `-0.00317`, better seeds `2/3`
- `fedgrid_v4_cluster_distill`: DeltaReturn `-0.055`, 95 percent CI `[-0.136, 0.075]`, DeltaPLoss `0.00142`, better seeds `1/3`

The clean rerun therefore weakly upgrades `fedgrid_topo_proto` while leaving `fedgrid_v4_cluster_distill` negative. The historical suite still matters because it prevents an overconfident superiority claim.

## Corrected multi-seed ablation

The corrected three-seed ablation, `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3`, sharpens the mechanism story.

- `fedgrid_topo_proto`: DeltaReturn `+0.091`, better seeds `3/3`
- `fedgrid_v4_cluster_distill`: DeltaReturn `-0.136`, better seeds `1/3`
- `fedgrid_v4_cluster_nodistill`: DeltaReturn `-0.133`, better seeds `0/3`
- `fedgrid_v4_cluster_gentle`: DeltaReturn `-0.085`, better seeds `0/3`

This is the strongest current evidence that prototype-sharing is the only promising direction in the current family, while the broader clustered-distillation variants remain unsupported.

## Supporting robustness evidence

The completed robustness suite, `outputs/suites/case141_fedgrid_robust_rr_20260326`, is more encouraging but should be interpreted cautiously because it is single-seed. On `random_reset`:

- `fedgrid_v4_cluster_byzantine`: DeltaReturn `+0.642`, DeltaVViol `0.0000`, DeltaPLoss `-0.01671`
- `fedgrid_v4_cluster_distill`: DeltaReturn `+0.113`, DeltaVViol `0.0000`, DeltaPLoss `-0.00296`
- `fedgrid_v4_cluster_dropout`: DeltaReturn `-0.090`, DeltaVViol `0.0000`, DeltaPLoss `0.00233`

These results show that the method family is not uniformly weak. Under some stress settings, certain variants look promising. However, the single-seed robustness suite is not a sufficient basis for a broad paper headline, especially when the completed three-seed main benchmark is negative.

## What can be claimed today

The strongest current claim is empirical: stricter paired evaluation and fresh reruns change the paper story. A superficial reading of isolated positive stress-test results could suggest that the method family is broadly successful. The corrected multi-seed ablation shows that this is false for the clustered-distillation family, while the clean rerun shows that `fedgrid_topo_proto` is promising but not yet fully settled. The paper should therefore emphasize evaluation discipline, context sensitivity, and the need to separate promising subcomponents from unsupported family-wide claims.
