# Failure Mode Audit (2026-04-08)

## Scope

This note audits the current FedGrid paper line from three angles:

- experiment evidence from completed suites
- implementation evidence from the training and federation code
- literature evidence already tracked in the project bibliography

The goal is to explain why `fedgrid_topo_proto` is mixed-sign and why the clustered variants are consistently weak.

## Current Live Experiment

As of this note, the Q1 queue is still running `case141_fedgrid_robust_rr_20260407_ms3`.

Latest visible progress from the live stdout log:

- current run: `case141_fedgrid_none_seed0`
- epoch: `70`
- latest validation: `Sum -3.38`, `PerStep -0.04`

This live suite does not change the conclusions below yet because no new aggregate paired metrics have been produced.

## Hard Evidence From Completed Suites

Evidence files:

- `outputs/suites/case141_fedgrid_main_rr/agg/suite_paired_metrics.csv`
- `outputs/suites/case141_fedgrid_main_rr_20260402_clean/agg/suite_paired_metrics.csv`
- `outputs/suites/case141_fedgrid_main_rr_20260407_replica/agg/suite_paired_metrics.csv`
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3/agg/suite_paired_metrics.csv`
- `outputs/suites/case141_fedgrid_topoproto_power_rr_20260407/agg/suite_paired_metrics.csv`
- `outputs/suites/case141_fedgrid_topoproto_power_rr_20260407/agg/suite_seed_level_paired.csv`

### Stable experimental findings

1. `random_reset` versus `static` is almost a no-op in the final paired outputs.
   The largest suite-level gap in `return_diff_mean_across_seeds` is only about `0.0035`, much smaller than the suite-to-suite variation.

2. All observed method movement is effectively in `p_loss_mean`.
   Across the completed paired summaries, `v_viol_lin_mean` and `n_components_mean` stay flat, and the return deltas track `p_loss_mean` almost exactly.

3. `fedgrid_v4_cluster_distill` is consistently negative.
   It is negative in the historical main suite, the clean rerun, the fresh replica, and the corrected ablation.

4. `fedgrid_v4_cluster_nodistill` and `fedgrid_v4_cluster_gentle` are also negative.
   In the corrected ablation, both remain below baseline, which means the cluster recipe itself is the first suspect, not only distillation.

5. `fedgrid_topo_proto` is the only method family that can beat baseline, but it is not stable across suites.

### Key suite snapshots

#### Historical main

- `fedgrid_topo_proto` on `random_reset`: `-0.106`
- `fedgrid_v4_cluster_distill` on `random_reset`: `-0.173`

#### Clean rerun (2026-04-02)

- `fedgrid_topo_proto` on `random_reset`: `+0.122`
- `fedgrid_v4_cluster_distill` on `random_reset`: `-0.055`

#### Fresh replica (2026-04-07)

- `fedgrid_topo_proto` on `random_reset`: `-0.019`, `2/3` winning seeds
- `fedgrid_v4_cluster_distill` on `random_reset`: `-0.187`, `0/3` winning seeds

#### Corrected multi-seed ablation

- `fedgrid_topo_proto` on `random_reset`: `+0.091`, CI `[+0.084, +0.097]`, `3/3` winning seeds
- `fedgrid_v4_cluster_distill` on `random_reset`: `-0.136`, CI `[-0.297, +0.049]`, `1/3` winning seeds
- `fedgrid_v4_cluster_nodistill` on `random_reset`: `-0.133`, CI `[-0.161, -0.105]`, `0/3` winning seeds
- `fedgrid_v4_cluster_gentle` on `random_reset`: `-0.085`, CI `[-0.182, -0.016]`, `0/3` winning seeds

#### Higher-power topo_proto follow-up

- `fedgrid_topo_proto` on `random_reset`: `-0.277`, CI `[-0.946, +0.138]`, `3/5` winning seeds
- `fedgrid_topo_proto` on `static`: `-0.276`, CI `[-0.943, +0.137]`, `3/5` winning seeds
- `p_loss_mean_diff_mean_across_seeds` is positive in both contexts, about `+0.0072`
- `v_viol_lin_mean_diff_mean_across_seeds` remains `0.0`

### Failure signature from the power run

The power run shows heavy-tailed instability rather than broad uniform underperformance.

- seed `0` is catastrophic: `return_diff_mean ≈ -1.608`, `p_loss_mean_diff_mean ≈ +0.0419`
- seeds `2`, `3`, and `4` are positive
- removing seed `0` would flip the suite mean from negative to mildly positive

This means `fedgrid_topo_proto` currently looks like a fragile method with rare severe failures, not a uniformly weak one.

## Hard Evidence From Code

### 1. The effective benchmark signal is power loss once voltage violations vanish

From `env_141.py`:

- line `408`: `linear_viol = float(np.sum(v_lower + v_upper))`
- line `409`: `squared_viol = float(np.sum(v_lower ** 2 + v_upper ** 2))`
- line `411`: `raw_reward = - (p_loss_val * 10.0) - (200.0 * linear_viol) - (1000.0 * squared_viol)`
- line `412`: `rewards.append(float(raw_reward) * 0.01)`

Implication:

- once `v_viol` is near zero, the paired return metric becomes mostly a proxy for `p_loss`
- this is exactly what the completed paired summaries show

### 2. Topology-aware modules default to the base topology under random-reset training

From `train_gnn_fedgrid.py`:

- lines `93-103` explicitly document the replay/topology mismatch concern
- line `242`: `--mixer_use_base_topology` default `True`
- line `275`: `--bus_gnn_use_base_topology` default `True`
- line `284`: `--fed_use_base_topology` default `True`
- lines `1128-1131`: federated weight construction uses `net_orig` when `fed_use_base_topology=True`

Implication:

- under `topology_mode=random_reset`, the model is evaluated on varying outage topologies but several topology-aware components are anchored to the pre-outage graph by default
- this is an intentional stability choice, but it may suppress the upside of topology-aware modeling

### 3. Clustered variants stack several conservative filters in a 4-agent problem

From `run_case141_fedgrid_v6.py`, clustered presets use:

- `fed_clustered=True`
- `fed_cluster_knn=2`
- `fed_cluster_threshold=0.58` or `0.70`
- `fed_max_clusters=4`
- `fed_inter_cluster_scale=0.03` to `0.08`
- `fed_cluster_self_boost=0.10` to `0.15`
- `fed_distill_same_cluster_only=True`

From `train_gnn_fedgrid.py` and `fedgrid_federated.py`:

- cluster inference: `derive_client_clusters(...)`
- cluster masking: `mask_weights_by_clusters(...)`
- post-round distillation: `distill_actors_from_peers(...)`
- same-cluster-only teacher sharing is enabled in clustered presets

Implication:

- with only four agents, this stack can easily collapse peer sharing into over-personalized updates
- the negative results for `cluster_distill`, `cluster_nodistill`, and `cluster_gentle` fit that pattern

### 4. Federated synchronization is aggressive for an off-policy SAC pipeline

From `train_gnn_fedgrid.py`:

- line `282`: `fed_round_every` default `1`
- line `283`: `fed_alpha` default `1.0`
- line `1086`: federated aggregation can run every epoch
- lines `1220-1237`: actors, critics, and encoders are mixed with full-strength alpha
- lines `1278-1290`: targets are hard-updated and optimizer states are reset after the federated round

Implication:

- even if this is not a bug, it is a very strong intervention
- this can wipe out local adaptation and amplify bad rounds, especially in the clustered variants

### 5. Federated synchronization starts before local RL has meaningfully begun

From `train_gnn_fedgrid.py`:

- line `404`: `steps_per_epoch = 96` for case141
- line `503`: `start_steps = 2000`
- line `504`: `update_after = 2000`
- line `1086`: federated rounds can already run every epoch
- line `1246`: clustered distillation starts once the replay buffer is merely large enough
- line `1287`: optimizer state is reset after each federated round

Implication:

- federated mixing begins long before the first serious SAC updates have accumulated
- clustered variants can start distilling mostly untrained actors
- wiping Adam state every round further destabilizes optimization

This is the strongest direct code-level explanation for why fed variants can go negative.

### 6. Trust is applied twice in the same federated round

From `train_gnn_fedgrid.py` and `fedgrid_federated.py`:

- trust is already folded into the federated weight matrix
- then the same trust vector is passed again as `source_gate` during parameter mixing
- the same trust vector is passed again during actor distillation

Implication:

- lower-trust clients are down-weighted multiple times
- in a small-client regime, this can easily sharpen sharing into almost self-heavy updates

### 7. Validation and checkpoint selection are not truly deterministic

From `train_gnn_fedgrid.py`, `env_141.py`, and `evaluate_topology_shift_deterministic.py`:

- `validate()` is labeled deterministic but does not reseed Python, NumPy, or Torch before each validation pass
- validation reuses the same environment object across calls
- `env_141.reset()` advances `episode_idx` and perturbs loads with global NumPy randomness
- the separate deterministic evaluator does seed correctly, but it runs only after training has already chosen a checkpoint

Implication:

- the selected "best" checkpoint can depend on whichever outage and load draws happened to appear during validation
- this is a strong explanation for close methods flipping sign across repeated suites

### 8. The suite "seed" is only a topology seed, not a full experiment seed

From `run_case141_fedgrid_v6.py` and `train_gnn_fedgrid.py`:

- suite launch passes `--topology_seed`
- training uses that seed for outage/dropout/attack helper RNGs
- I did not find global seeding for model initialization, replay sampling, or policy sampling in the main training path

Implication:

- the reported seed variation is not a clean full-run replication axis
- uncontrolled training randomness can leak into method comparisons and inflate mixed-sign behavior

### 9. The suite runner hardens case141 beyond the trainer and evaluator defaults

From `run_case141_fedgrid_v6.py`, `train_gnn_fedgrid.py`, and `evaluate_topology_shift_deterministic.py`:

- suite runner default: `outage_k = 6`
- train/eval default for case141: `outage_k = 4`

Implication:

- the bundle is running a harsher outage regime than the underlying scripts encode as the paper-style default
- if earlier expectations were calibrated to `k=4`, modest gains can plausibly flip negative at `k=6`

### 10. The launch path can silently reuse stale evidence

From `run_case141_fedgrid_v6.py`, `evaluate_topology_shift_deterministic.py`, and `train_gnn_fedgrid.py`:

- `skip_existing` only checks for expected files, not whether the file was produced under matching eval settings
- eval summary filenames do not encode all evaluation settings such as `episodes` or `eval_seed_base`
- training still writes the generic legacy checkpoint `best_model_gnn_141.pth`

Implication:

- stale or mismatched outputs can survive in a suite directory without obvious detection
- this is a reproducibility risk, even if it is not the main cause of the negative results

## Literature Alignment

The bibliography already contains several primary sources that match the observed failure modes:

1. `Multi-Agent Reinforcement Learning for Active Voltage Control on Power Distribution Networks` (NeurIPS 2021)
   URL: `https://openreview.net/forum?id=hwoK62_GkiT`
   Relevance: establishes AVC as a hard MARL problem and highlights instability/interpretability challenges.

2. `Temporal Prototype-Aware Learning for Active Voltage Control on Power Distribution Networks` (KDD 2024)
   URL: `https://openreview.net/forum?id=cKMzfkBABk`
   Relevance: supports the idea that prototype-based temporal structure can help AVC, which is broadly consistent with `fedgrid_topo_proto` being the only sometimes-positive method family.

3. `Safety Constrained Multi-Agent Reinforcement Learning for Active Voltage Control` (AIforCI 2024)
   URL: `https://openreview.net/forum?id=I2KKVDUvHP`
   Relevance: emphasizes that AVC performance must be analyzed beyond a single scalar objective.

4. `Multi-Agent Safe Graph Reinforcement Learning for PV Inverters-Based Real-Time Decentralized Volt/Var Control in Zoned Distribution Networks` (IEEE TSG 2024)
   URL: `https://openreview.net/forum?id=uB9TMSvFTU`
   Relevance: supports graph-structured control for voltage regulation, but also raises the bar for making topology modeling actually help.

5. `An Efficient Framework for Clustered Federated Learning` (NeurIPS 2020)
   URL: `https://openreview.net/forum?id=wxYFZU4dpGN`
   Relevance: clustered FL assumes meaningful client grouping. In a tiny 4-client regime, over-clustering can easily become brittle.

6. `Federated Learning under Distributed Concept Drift` (NeurIPS 2022 Workshop)
   URL: `https://openreview.net/forum?id=dOvcWRIcLA`
   Relevance: supports the idea that stale or drifting client relationships can make static aggregation structures underperform.

7. `FIELDING: Clustered Federated Learning with Data Drift` (AISTATS 2026)
   URL: `https://openreview.net/forum?id=i4q2xjAuld`
   Relevance: newer clustered-FL work still treats drift handling as a first-class problem, which lines up with the topology-shift mismatch seen here.

8. `Federated Optimization in Heterogeneous Networks` (FedProx)
   URL: `https://arxiv.org/abs/1812.06127`
   Relevance: classic support for the claim that aggressive synchronization under heterogeneity can hurt optimization.

### Literature-backed diagnosis

Hard evidence:

- the current project already shows that clustered methods are consistently negative
- the benchmark signal is effectively `p_loss`
- topology-aware components mostly use base-topology priors during random-reset training

Inference from code plus literature:

- `fedgrid_topo_proto` may help when prototype sharing regularizes useful structure, but it is vulnerable to rare bad seeds because topology shift, off-policy replay, and aggressive mixing create mismatch
- the clustered variants likely overfit a brittle client partition in a too-small client regime, then further reduce useful sharing through cluster masking and same-cluster-only distillation
- the non-clustered `topo_proto` line may be suffering from checkpoint-selection noise and rare unstable seeds, not only from weak average effect

## Recommended Next Experiments

1. Shared-eval audit:
   Re-evaluate checkpoints from `clean`, `replica`, and `topoproto_power` on one common larger eval seed set.

2. True-topology ablation:
   Run `fedgrid_topo_proto` with:
   - `--no_mixer_use_base_topology`
   - `--no_bus_gnn_use_base_topology`
   - `--no_fed_use_base_topology`

3. Delayed and gentler federated mixing:
   Try `--fed_round_every 5` and `--fed_alpha 0.2` or `0.5`, and do not start federated rounds until after local RL warmup has passed.

4. Cluster ablation in the 4-agent regime:
   Compare:
   - cluster masking on/off
   - same-cluster-only distillation on/off
   - lower threshold versus no clustering

5. Deterministic checkpoint-selection audit:
   Seed Python, NumPy, and Torch inside validation, or evaluate checkpoints on a fixed held-out deterministic set before selecting the best model.

6. Full-seed reproducibility audit:
   Add and log a true experiment seed that controls model initialization, replay sampling, policy sampling, and auxiliary batching.

7. Seed-collapse telemetry:
   For catastrophic seeds, log per-episode `p_loss`, action entropy, and any invalid or clipped action statistics.

## Paper Implication Right Now

The safest Q1 paper framing is still empirical-first:

- clustered distillation is not supported as a positive headline method
- `fedgrid_topo_proto` is the only promising variant, but its main-benchmark sign is not stable enough for a strong superiority claim
- the strongest publishable story is currently a careful analysis of topology-aware federated MARL under topology shift, including failure modes and evaluation sensitivity
