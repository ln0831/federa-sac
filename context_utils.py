"""Context feature utilities.

In the outage-management GRL paper, the policy/critic uses a combination of
(1) graph embedding and (2) context embedding (global scalar features).

For this project, each agent observation is a concatenation:
  [p_norm (n_bus), q_norm (n_bus), v_norm (n_bus)]
where v_norm = (v_pu - 1.0) * 20.

We expose a batched torch implementation to compute global voltage context
from a list of per-agent observation tensors.

Returned context (dim=4):
  [mean_linear_violation, mean_squared_violation, global_v_min, global_v_max]

`mean_*` are averaged over all buses across all agents to make the feature
scale insensitive to network size.
"""

from __future__ import annotations

from typing import List, Tuple

import torch


def context_from_obs_list(
    obs_list: List[torch.Tensor],
    v_min: float = 0.90,
    v_max: float = 1.10,
    eps: float = 1e-8,
) -> torch.Tensor:
    """Compute global voltage context from a list of per-agent observation tensors.

    Args:
        obs_list: list of tensors, each [B, obs_dim_i] or [obs_dim_i]
        v_min, v_max: voltage bounds in pu

    Returns:
        ctx: torch.Tensor [B, 4]
    """
    # Ensure batch dimension
    v_all = []
    device = obs_list[0].device
    for obs in obs_list:
        if obs.dim() == 1:
            obs = obs.unsqueeze(0)
        B, D = obs.shape
        n = D // 3
        if n <= 0:
            continue
        v_norm = obs[:, 2 * n : 3 * n]
        v = v_norm / 20.0 + 1.0
        v_all.append(v)

    if not v_all:
        # fallback
        B = obs_list[0].shape[0] if obs_list[0].dim() == 2 else 1
        return torch.zeros((B, 4), dtype=torch.float32, device=device)

    v_cat = torch.cat(v_all, dim=1)  # [B, total_buses]
    total = v_cat.shape[1]

    v_lower = torch.relu(torch.tensor(v_min, device=device) - v_cat)
    v_upper = torch.relu(v_cat - torch.tensor(v_max, device=device))
    lin = v_lower + v_upper
    sq = v_lower * v_lower + v_upper * v_upper

    lin_mean = lin.sum(dim=1, keepdim=True) / (float(total) + eps)
    sq_mean = sq.sum(dim=1, keepdim=True) / (float(total) + eps)

    vmin = v_cat.min(dim=1, keepdim=True).values
    vmax = v_cat.max(dim=1, keepdim=True).values

    ctx = torch.cat([lin_mean, sq_mean, vmin, vmax], dim=1)
    return ctx
