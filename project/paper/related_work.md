# Related Work Draft

Status:
- drafted from the current verified bibliography starter set
- broaden the citation set later if the final submission target demands deeper coverage

## Multi-agent voltage control and grid-control learning

Wang et al. (2021) are the closest verified task-level reference in the current literature set because they formulate active voltage control on power distribution networks as a multi-agent reinforcement-learning problem. Xu et al. (2024) and Qu et al. (2024) push that direct AVC line further, respectively emphasizing temporal prototype-aware learning and safety-constrained multi-agent optimization. Yan et al. (2024) add a graph-based decentralized volt-var-control perspective that is particularly relevant for topology-aware modeling. For this project, these papers matter less as direct federated baselines and more as proof that the underlying control task, environment style, and graph-structured decision problem are already meaningful research territory. Hassouna et al. (2025) and MARL2Grid-TR (Marchesini et al., 2026) broaden that picture by showing how evaluation and graph-aware control are becoming central in realistic grid-operation settings, even when the benchmark or action space differs.

## Clustered federated learning under heterogeneity and drift

The method-side justification for the FedGrid family comes from clustered federated learning. Ghosh et al. (2020) provide a foundational clustered FL reference that explicitly treats client heterogeneity as the reason to move beyond uniform aggregation. Li et al. (2026) extend that line of thought to data drift, which is especially relevant for the present project because topology shift and local outages create a distribution-shift narrative even when the exact benchmark differs from standard FL benchmarks. These papers help explain why cluster-aware aggregation and post-aggregation information sharing are plausible ideas. They do not, however, establish that such mechanisms will reliably help on topology-shifted active voltage control.

## Federated learning in power-system domains

The verified power-systems FL papers in the current bibliography, FedDiSC (Husnoo et al., 2023) and FeDiSa (Husnoo et al., 2023), focus on disturbance, fault, and cyberattack discrimination rather than voltage control. Their value here is not direct task equivalence but domain relevance. They show that privacy-aware or communication-aware federation is already a credible design axis for power-system learning problems. At the same time, the task mismatch is important: evidence from detection or fault classification cannot be treated as proof for control under topology shift.

## Positioning of the current paper

The present paper is best positioned as an empirical and evaluation-focused study of an implemented federated control family rather than as a broad new-method claim. Within the current verified literature set, we do not yet have a directly matched prior paper that combines multi-agent active voltage control, clustered federated aggregation, and deterministic paired topology-shift evaluation. That makes the evaluation protocol and the resulting failure analysis central contributions. The paper studies the FedGrid variants as serious candidate methods, but its strongest current message is that stricter context alignment changes which claims remain defensible.
