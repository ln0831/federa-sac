# Discussion Draft

Status:
- drafted from the current completed evidence package

The most important finding of the current cycle is not that the FedGrid family "fails" in every setting. It is that the evidence is highly context-sensitive, and that the method story changes substantially once the evaluation is forced into deterministic, paired, context-aligned form. The completed main suite shows that the current headline variants do not reliably improve return on the target `random_reset` benchmark. At the same time, the completed robustness suite shows that some stress variants can look materially better in narrower settings. Both observations can be true at once.

This pattern suggests two practical interpretations. First, the clustered and prototype-aware mechanisms may be interacting with topology shift in a more brittle way than the original method intuition implied. A method that looks attractive conceptually can still underperform if the added structure is not consistently aligned with the actual source of heterogeneity in the benchmark. Second, robustness-oriented variants may be probing a different part of the design space than the original distillation story. The positive single-seed `byzantine` result does not prove robustness superiority, but it does justify further mechanism-specific study.

The paper therefore benefits from a modest contribution statement. Rather than forcing a broad method-superiority claim, the manuscript can make a stronger and more credible contribution by showing how a reproducible paired protocol changes which conclusions survive scrutiny. This is a publishable position if the writing remains disciplined and if the final ablation is used to sharpen, not inflate, the narrative.

Several limitations remain. The robustness suite is single-seed. Historical path drift is still visible in some legacy reports. The verified literature package is real but still incomplete. Most importantly, the live multi-seed ablation is not finished yet, so the current discussion cannot fully resolve whether distillation, gentler clustering, or no-distillation variants best explain the observed behavior. These limits should remain explicit in the final paper.
