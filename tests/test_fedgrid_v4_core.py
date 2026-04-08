import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

from fedgrid_federated import (
    derive_client_clusters,
    mask_weights_by_clusters,
    distill_actors_from_peers,
    estimate_module_payload_bits,
)
from networks import LocalActor
from train_gnn_fedgrid import (
    derive_experiment_seed,
    should_run_federated_round,
    trust_source_gate,
)


def test_cluster_masking_and_payload():
    affinity = torch.tensor([
        [1.0, 0.9, 0.1, 0.0],
        [0.9, 1.0, 0.2, 0.1],
        [0.1, 0.2, 1.0, 0.8],
        [0.0, 0.1, 0.8, 1.0],
    ])
    clusters = derive_client_clusters(affinity, knn=1, threshold=0.5, max_clusters=4)
    assert len(set(clusters)) == 2
    W = torch.full((4, 4), 0.25)
    Wm = mask_weights_by_clusters(W, clusters, inter_cluster_scale=0.0, self_boost=0.0)
    assert torch.allclose(Wm.sum(dim=1), torch.ones(4), atol=1e-5)
    assert Wm[0, 2].item() == 0.0

    actors = [LocalActor(6, 2, hidden_dim=16) for _ in range(4)]
    bits = estimate_module_payload_bits(actors, exclude_prefixes=('l1.', 'mean_layer.', 'log_std_layer.'))
    assert bits > 0


def test_peer_distillation_runs():
    torch.manual_seed(0)
    actors = [LocalActor(6, 2, hidden_dim=16) for _ in range(3)]
    optims = [torch.optim.Adam(a.parameters(), lr=1e-3) for a in actors]
    obs = [torch.randn(8, 6) for _ in range(3)]
    W = torch.tensor([
        [0.6, 0.4, 0.0],
        [0.4, 0.6, 0.0],
        [0.2, 0.2, 0.6],
    ], dtype=torch.float32)
    loss = distill_actors_from_peers(
        actors,
        optims,
        obs,
        W,
        coef=0.1,
        steps=1,
        same_cluster_only=False,
    )
    assert loss >= 0.0


def test_should_run_federated_round_waits_until_local_learning_starts() -> None:
    assert not should_run_federated_round(
        fed_mode="topo_proto",
        fed_round_every=1,
        epoch=0,
        total_steps=96,
        fed_start_after=2000,
        local_updates_started=False,
    )
    assert not should_run_federated_round(
        fed_mode="topo_proto",
        fed_round_every=1,
        epoch=20,
        total_steps=2016,
        fed_start_after=2000,
        local_updates_started=False,
    )
    assert should_run_federated_round(
        fed_mode="topo_proto",
        fed_round_every=1,
        epoch=20,
        total_steps=2050,
        fed_start_after=2000,
        local_updates_started=True,
    )


def test_trust_source_gate_is_opt_in() -> None:
    trust = torch.tensor([0.2, 0.8], dtype=torch.float32)
    assert trust_source_gate(trust, apply_gate=False) is None
    gated = trust_source_gate(trust, apply_gate=True)
    assert torch.allclose(gated, trust)


def test_derive_experiment_seed_uses_base_seed_if_present() -> None:
    assert derive_experiment_seed(None, topology_seed=2) == 2
    assert derive_experiment_seed(7002, topology_seed=2) == 7002
