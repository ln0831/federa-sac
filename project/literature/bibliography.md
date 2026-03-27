# Bibliography

## Status

Verified external entries have been added below. This is still not a complete literature package, but it now covers both direct task neighbors and the main clustered-FL positioning papers used in the current manuscript.

## Verified External Entries

### Wang et al. (NeurIPS 2021)

- Title: `Multi-Agent Reinforcement Learning for Active Voltage Control on Power Distribution Networks`
- Authors: Jianhong Wang, Wangkun Xu, Yunjie Gu, Wenbin Song, Tim C. Green
- Source: OpenReview / NeurIPS 2021
- URL: https://openreview.net/forum?id=hwoK62_GkiT
- Why it matters here: direct task-level baseline for multi-agent voltage control on distribution networks

### Xu et al. (KDD 2024)

- Title: `Temporal Prototype-Aware Learning for Active Voltage Control on Power Distribution Networks`
- Authors: Feiyang Xu, Shunyu Liu, Yunpeng Qing, Yihe Zhou, Yuwen Wang, Mingli Song
- Source: OpenReview / KDD 2024
- URL: https://openreview.net/forum?id=cKMzfkBABk
- Why it matters here: direct active-voltage-control paper that explicitly studies longer-timescale distribution shifts; useful near-neighbor for any prototype-aware narrative

### Qu et al. (2024)

- Title: `Safety Constrained Multi-Agent Reinforcement Learning for Active Voltage Control`
- Authors: Yang Qu, Jinming Ma, Feng Wu
- Source: OpenReview / AIforCI 2024
- URL: https://openreview.net/forum?id=I2KKVDUvHP
- Why it matters here: direct task-level AVC paper that emphasizes constrained and safety-aware MARL rather than federated learning

### Yan et al. (IEEE TSG 2024)

- Title: `Multi-Agent Safe Graph Reinforcement Learning for PV Inverters-Based Real-Time Decentralized Volt/Var Control in Zoned Distribution Networks`
- Authors: Rudai Yan, Qiang Xing, Yan Xu
- Source: OpenReview / IEEE Transactions on Smart Grid 2024
- URL: https://openreview.net/forum?id=uB9TMSvFTU
- Why it matters here: graph-based decentralized voltage-control paper with a closely related control objective and 141-bus-style evaluation relevance

### Hassouna et al. (ECML 2025)

- Title: `Learning Topology Actions for Power Grid Control: A Graph-Based Soft-Label Imitation Learning Approach`
- Authors: Mohamed Hassouna, Clara Holzhuter, Malte Lehna, Matthijs de Jong, Jan Viebahn, Bernhard Sick, Christoph Scholz
- Source: arXiv / ECML Applied Data Science Track
- URL: https://arxiv.org/abs/2503.15190
- Why it matters here: recent topology-aware grid-control paper with graph-based modeling, useful for positioning against other learning-based grid-control approaches

### Marchesini et al. (ICLR 2026)

- Title: `MARL2Grid-TR: A Multi-Agent RL Benchmark in Power Grid Operations`
- Authors: Enrico Marchesini, Eva Boguslawski, Alessandro Leite, Christopher Amato, Matthieu Dussartre, Marc Schoenauer, Benjamin Donnot, Priya L. Donti
- Source: OpenReview / ICLR 2026
- URL: https://openreview.net/forum?id=mpAMH1OyMO
- Why it matters here: broader benchmark reference showing that multi-agent evaluation discipline is becoming important in realistic grid-control settings

### Ghosh et al. (NeurIPS 2020)

- Title: `An Efficient Framework for Clustered Federated Learning`
- Authors: Avishek Ghosh, Jichan Chung, Dong Yin, Kannan Ramchandran
- Source: OpenReview / NeurIPS 2020
- URL: https://openreview.net/forum?id=wxYFZU4dpGN
- Why it matters here: foundational clustered federated learning reference for the method-side framing

### Jothimurugesan et al. (NeurIPS Workshop 2022)

- Title: `Federated Learning under Distributed Concept Drift`
- Authors: Ellango Jothimurugesan, Kevin Hsieh, Jianyu Wang, Gauri Joshi, Phillip Gibbons
- Source: OpenReview / NeurIPS 2022 Workshop
- URL: https://openreview.net/forum?id=dOvcWRIcLA
- Why it matters here: useful drift-handling FL reference for the broader shift narrative even though it is not power-systems-specific

### Li et al. (AISTATS 2026)

- Title: `FIELDING: Clustered Federated Learning with Data Drift`
- Authors: Minghao Li, Dmitrii Avdiukhin, Rana Shahout, Nikita Ivkin, Vladimir Braverman, Minlan Yu
- Source: OpenReview / AISTATS 2026
- URL: https://openreview.net/forum?id=i4q2xjAuld
- Why it matters here: recent clustered FL under drift, relevant to the heterogeneity and shift narrative

### Husnoo et al. (2023)

- Title: `FedDiSC: A Computation-efficient Federated Learning Framework for Power Systems Disturbance and Cyber Attack Discrimination`
- Authors: Muhammad Akbar Husnoo, Adnan Anwar, Haftu Tasew Reda, Nasser Hosseinzadeh, Shama Naz Islam, Abdun Naser Mahmood, Robin Doss
- Source: arXiv 2023
- URL: https://arxiv.org/abs/2304.03640
- Why it matters here: not the same task, but directly relevant as a power-systems FL reference

### Husnoo et al. (INFOCOM AidTSP 2023)

- Title: `FeDiSa: A Semi-asynchronous Federated Learning Framework for Power System Fault and Cyberattack Discrimination`
- Authors: Muhammad Akbar Husnoo, Adnan Anwar, Haftu Tasew Reda, Nasser Hosseinzadeh, Shama Naz Islam, Abdun Naser Mahmood, Robin Doss
- Source: arXiv / IEEE INFOCOM AidTSP 2023
- URL: https://arxiv.org/abs/2303.16956
- Why it matters here: useful reference for asynchronous or systems-oriented FL in power settings

## Internal Project References

These are internal evidence sources for the current cycle:

- `docs/VERSION_MAP_AND_SOURCE_OF_TRUTH.md`
- `docs/EXPERIMENT_RUNBOOK.md`
- `docs/RESULTS_CHECKLIST.md`
- `docs/PAPER_TABLE_MAPPING.md`
- `docs/analysis/CURRENT_RESULTS_ANALYSIS.md`
- `docs/paper/FEDGRID_PAPER_OUTLINE_v4.md`
- `skills/fedgrid-runtime-runner/SKILL.md`

## Planned Literature Buckets

- federated learning for smart grid control
- multi-agent reinforcement learning for voltage control
- topology shift and generalization under grid perturbations
- robust federated aggregation and clustered federated learning
- distillation or representation-sharing in federated settings
