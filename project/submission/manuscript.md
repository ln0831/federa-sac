# Manuscript Assembly

This file is the current integrated submission draft for the empirical-analysis route.

## Working title

Paired Evaluation for Topology-Shifted Federated Grid Control

## Abstract

This paper studies how to evaluate topology-aware federated control methods for active voltage control under topology shift on the case141 benchmark. Instead of relying on mixed-context summaries, we use a deterministic, context-aligned runtime bundle that pairs each federated method with matched baseline rollouts and reports paired seed deltas for return, voltage violation, and active-power loss. In the completed three-seed main benchmark, neither `fedgrid_topo_proto` nor `fedgrid_v4_cluster_distill` shows a reliable advantage over the baseline on the `random_reset` benchmark: mean paired DeltaReturn is `-0.106` and `-0.173`, respectively, and each method wins only `1/3` seeds. A completed one-seed robustness suite shows that stress variants can behave differently, with `fedgrid_v4_cluster_byzantine` reaching `+0.642` paired DeltaReturn on `random_reset`, but that result is not strong enough to support a broad superiority claim because it is single-seed. The current evidence therefore supports an empirical paper about evaluation discipline, context sensitivity, and failure modes rather than a blanket new-method claim. We release the runnable training, deterministic evaluation, aggregation, table, figure, and reporting pipeline together with the current suite artifacts so the conclusions remain traceable and reproducible.

## Introduction

Active voltage control on large distribution networks is a natural setting for decentralized or multi-agent learning, but it is also a setting where evaluation noise can easily turn into paper-level overclaiming. Topology changes, local outages, and heterogeneous operating regions mean that two methods can look different not because one is better, but because the compared rollouts are not properly aligned. This is especially risky for federated variants that introduce extra clustering, prototype-sharing, or distillation logic on top of an already nontrivial multi-agent control stack.

The current repository already contains a substantial FedGrid method family and an end-to-end runtime bundle for training, deterministic evaluation, aggregation, plotting, and report generation. The question for the present paper cycle is therefore not "can we invent another variant" but "what can we defend honestly once the evaluation is tightened?" In the completed main suite for case141, the two most natural headline methods, `fedgrid_topo_proto` and `fedgrid_v4_cluster_distill`, do not show reliable positive paired return deltas on the `random_reset` topology-shift benchmark. Both methods have negative mean DeltaReturn, both increase active-power loss relative to the matched baseline, and each wins only one out of three seeds.

This observation motivates the paper's central position: deterministic, context-aligned paired evaluation is itself a meaningful research contribution for this project. The paper studies the implemented FedGrid family, but the strongest current message is empirical. We ask whether stricter evaluation changes which conclusions remain defensible, which method variants appear robust only under certain stressors, and which apparently attractive design choices fail to translate into stable paired gains.

## Related Work

Wang et al. (2021) are the closest verified task-level reference in the current literature set because they formulate active voltage control on power distribution networks as a multi-agent reinforcement-learning problem. Hassouna et al. (2025) extend the broader grid-control picture with graph-based learning under dynamic operating conditions, although not in the same active-voltage-control setting. On the federated-learning side, Ghosh et al. (2020) and Li et al. (2026) justify clustered learning as a response to heterogeneity and drift, while FedDiSC and FeDiSa show that federated learning already has credible power-system applications on adjacent monitoring and security tasks.

The present paper is best positioned as an empirical and evaluation-focused study of an implemented federated control family rather than as a broad new-method claim. Within the current verified literature set, we do not yet have a directly matched prior paper that combines multi-agent active voltage control, clustered federated aggregation, and deterministic paired topology-shift evaluation. That makes the evaluation protocol and the resulting failure analysis central contributions.

## Method

The paper studies the existing FedGrid runtime bundle rather than introducing a brand-new algorithm from scratch. The active execution chain is `run_case141_fedgrid_v6.py`, `train_gnn_fedgrid.py`, `evaluate_topology_shift_deterministic.py`, `summarize_fedgrid_suite_v6.py`, `export_fedgrid_tables_v6.py`, `make_fedgrid_figures_v6.py`, and `make_fedgrid_report_v6.py`. The method family includes `fedgrid_none`, `fedgrid_topo_proto`, `fedgrid_v4_cluster_distill`, `fedgrid_v4_cluster_nodistill`, `fedgrid_v4_cluster_gentle`, `fedgrid_v4_cluster_dropout`, and `fedgrid_v4_cluster_byzantine`.

The main methodological contribution of the current cycle is the evaluation protocol around this family. Comparisons must be context-aligned, metrics must come from deterministic evaluation outputs, headline claims must use paired seed deltas rather than only absolute means, and incomplete suites are not treated as evidence. Return is the primary ranking metric, but voltage violations and power loss are kept in the evidence layer because a return gain is not a clean win if it worsens control trade-offs.

## Experiments

All validated runs in this cycle use `D:\Anaconda\envs\tianshou_env\python.exe`, where full `pytest -q tests` passed. The main benchmark is case141 with outage count `k=6`. The paper treats `random_reset` as the primary topology-shift benchmark and `static` as an in-distribution sanity check.

The current manuscript uses `outputs/suites/case141_fedgrid_main_rr` as the primary multi-seed evidence package and `outputs/suites/case141_fedgrid_robust_rr_20260326` as supporting robustness evidence. The live suite `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327` is intentionally excluded from headline claims until it completes cleanly. Paper-facing metrics are drawn from deterministic outputs, especially `suite_paired_metrics.csv` and `suite_seed_level_paired.csv`.

## Results

The primary completed evidence package is `outputs/suites/case141_fedgrid_main_rr`. On the main `random_reset` benchmark, `fedgrid_topo_proto` records DeltaReturn `-0.106` with 95 percent CI `[-0.267, 0.012]`, DeltaVViol `0.0000`, DeltaPLoss `0.00277`, and better seeds `1/3`. `fedgrid_v4_cluster_distill` records DeltaReturn `-0.173` with 95 percent CI `[-0.357, 0.045]`, DeltaVViol `0.0000`, DeltaPLoss `0.00451`, and better seeds `1/3`. The `static` context shows the same qualitative picture. Under the current protocol, the safest interpretation is that the completed main benchmark does not justify a claim that the clustered or prototype-aware variants clearly outperform the baseline.

The completed robustness suite is more encouraging but should be interpreted cautiously because it is single-seed. On `random_reset`, `fedgrid_v4_cluster_byzantine` reaches DeltaReturn `+0.642` with improved power-loss behavior, `fedgrid_v4_cluster_distill` reaches `+0.113`, and `fedgrid_v4_cluster_dropout` remains negative at `-0.090`. These results show that the method family is context-sensitive rather than uniformly weak, but they are not sufficient to overturn the main multi-seed benchmark posture.

## Discussion

The key finding is that stricter paired evaluation changes the paper story. A method family that can look promising in isolated stress settings does not automatically survive a completed multi-seed main benchmark. This does not mean the FedGrid family is valueless. It means the evidence currently supports a narrower and more defensible message about evaluation discipline, context sensitivity, and failure-aware analysis.

The completed robustness suite suggests that some variants may still deserve mechanism-specific attention. In particular, the positive `byzantine` stress result hints that robustness-oriented changes may expose different strengths than the original distillation narrative. However, the paper should continue to treat such observations as supporting rather than headline evidence until the live multi-seed ablation finishes.

## Conclusion

The current FedGrid evidence package supports a clear but modest conclusion: deterministic, context-aligned paired evaluation is necessary to judge topology-aware federated control methods honestly on this benchmark. In the completed three-seed main suite, the present headline variants do not show a reliable advantage over the baseline on the target topology-shift benchmark. Supporting robustness results show that some variants can look promising under stress, but those observations remain secondary until they are confirmed in stronger multi-seed settings.
