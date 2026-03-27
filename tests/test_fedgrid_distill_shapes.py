from __future__ import annotations

import math

import torch

from fedgrid_federated import distill_actors_from_peers


class TinyActor(torch.nn.Module):
    def __init__(self, obs_dim: int, action_dim: int) -> None:
        super().__init__()
        self.backbone = torch.nn.Linear(obs_dim, 16)
        self.mean_layer = torch.nn.Linear(16, action_dim)
        self.log_std_layer = torch.nn.Linear(16, action_dim)

    def forward(self, obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        hidden = torch.tanh(self.backbone(obs))
        return self.mean_layer(hidden), self.log_std_layer(hidden)


def test_distill_skips_incompatible_teacher_shapes_without_crashing() -> None:
    actors = [
        TinyActor(5, 2),
        TinyActor(6, 3),
        TinyActor(5, 2),
    ]
    actor_optims = [torch.optim.Adam(actor.parameters(), lr=1e-3) for actor in actors]
    anchor_obs = [
        torch.randn(8, 5),
        torch.randn(8, 6),
        torch.randn(8, 5),
    ]
    weight_matrix = torch.tensor(
        [
            [0.0, 0.5, 0.5],
            [0.5, 0.0, 0.5],
            [0.5, 0.5, 0.0],
        ],
        dtype=torch.float32,
    )

    loss = distill_actors_from_peers(
        actors,
        actor_optims,
        anchor_obs,
        weight_matrix,
        coef=0.5,
        steps=1,
        log_std_weight=0.25,
    )

    assert math.isfinite(loss)
    assert loss >= 0.0
