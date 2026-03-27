# Novelty Candidates

## Candidate 1

Title:

- Deterministic paired reevaluation for federated voltage-control benchmarking

Core idea:

- Turn the paper contribution into a rigorous evaluation framework that forces context alignment, paired metrics, and fail-fast artifact validation.

Why it might matter:

- Current workflows already show how misleading non-paired or mixed-context comparisons can be.

Implementation burden:

- low to medium

Main risk:

- novelty may be viewed as protocol-level, not algorithm-level

Fallback:

- frame it as the empirical backbone for a broader robustness study

## Candidate 2

Title:

- Community-aware federated aggregation with post-aggregation peer distillation

Core idea:

- Cluster clients using topology and representation signals, then apply structured aggregation and same-cluster distillation.

Why it might matter:

- could preserve local heterogeneity better than uniform averaging

Implementation burden:

- medium, because the code exists but needs strong validation

Main risk:

- current local evidence is not yet strong enough

Fallback:

- keep the method as the studied system while the paper emphasizes diagnostic findings

## Candidate 3

Title:

- Failure analysis of clustered federated control under topology shift

Core idea:

- turn weak or negative results into a careful explanation of when clustered aggregation and distillation fail

Why it might matter:

- honest negative findings can still be valuable if the evaluation is strong and the failure modes are clear

Implementation burden:

- low to medium

Main risk:

- requires especially strong narrative discipline
