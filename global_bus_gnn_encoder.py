
"""Global bus-level GNN encoder (shared across agents).

Scheme-B implementation: run *one* GNN on the full grid graph (all buses that
appear in the agent partitions), then produce a per-agent embedding by
pooling the node embeddings of that agent's area buses.

Why this helps:
- Avoids cutting the physical graph by administrative partitions.
- Preserves cross-area coupling information in the message passing.
- Keeps per-agent policy heads local: each agent reads out only its own buses.

Input format assumption (same as env_33/env_69/env_141/env_oberrhein):
Each agent observation is concatenated as:
    [p_norm (n_bus), q_norm (n_bus), v_norm (n_bus)]
where n_bus is the number of buses assigned to that agent (area_buses).

This encoder reconstructs a global bus feature matrix by placing each agent's
local features into the corresponding global bus indices (areas are assumed to
be a partition of the valid buses used for training).
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def _safe_float(x, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _line_weight_inv_z(row, eps: float = 1e-6) -> float:
    r = _safe_float(getattr(row, 'r_ohm_per_km', 0.0), 0.0)
    x = _safe_float(getattr(row, 'x_ohm_per_km', 0.0), 0.0)
    length = _safe_float(getattr(row, 'length_km', 1.0), 1.0)
    z = (r * length) ** 2 + (x * length) ** 2
    z = float(np.sqrt(max(z, 0.0)))
    return 1.0 / (z + eps)


def _trafo_weight_inv_z(row, eps: float = 1e-6) -> float:
    vk = _safe_float(getattr(row, 'vk_percent', 10.0), 10.0)
    return 1.0 / (abs(vk) + eps)


def build_global_adjacency(
    net,
    buses_global: np.ndarray,
    weight_mode: str = 'inv_z',
    eps: float = 1e-6,
    self_loops: bool = True,
    respect_in_service: bool = True,
) -> torch.Tensor:
    """Build a weighted adjacency for the *global* bus graph (restricted to buses_global).

    Args:
        net: pandapower net (base or current)
        buses_global: 1D array of bus indices included in the encoder
        weight_mode: 'inv_z' | 'binary' | 'count'
        respect_in_service: if True, drop edges with in_service=False (outages)

    Returns:
        A_norm: torch.FloatTensor [n, n] normalized with D^{-1/2} A D^{-1/2}
    """
    mode = (weight_mode or 'inv_z').lower()
    if mode not in {'inv_z', 'binary', 'count'}:
        raise ValueError(f"Unknown weight_mode: {weight_mode}")

    buses_global = np.asarray(buses_global, dtype=int)
    n = int(buses_global.shape[0])
    bus_to_idx = {int(b): i for i, b in enumerate(buses_global.tolist())}

    A = np.zeros((n, n), dtype=np.float32)

    def add_edge(u_bus: int, v_bus: int, w: float):
        if u_bus not in bus_to_idx or v_bus not in bus_to_idx:
            return
        u = bus_to_idx[int(u_bus)]
        v = bus_to_idx[int(v_bus)]
        if u == v:
            return
        A[u, v] += float(w)
        A[v, u] += float(w)

    # Lines
    if hasattr(net, 'line') and net.line is not None and len(net.line) > 0:
        for row in net.line.itertuples(index=False):
            if respect_in_service:
                in_serv = getattr(row, 'in_service', True)
                if in_serv is not True and (not bool(in_serv)):
                    continue
            f = int(getattr(row, 'from_bus'))
            t = int(getattr(row, 'to_bus'))
            if mode == 'inv_z':
                w = _line_weight_inv_z(row, eps=eps)
            else:
                w = 1.0
            add_edge(f, t, w)

    # Transformers (if any)
    if hasattr(net, 'trafo') and net.trafo is not None and len(net.trafo) > 0:
        for row in net.trafo.itertuples(index=False):
            if respect_in_service:
                in_serv = getattr(row, 'in_service', True)
                if in_serv is not True and (not bool(in_serv)):
                    continue
            hv = int(getattr(row, 'hv_bus'))
            lv = int(getattr(row, 'lv_bus'))
            if mode == 'inv_z':
                w = _trafo_weight_inv_z(row, eps=eps)
            else:
                w = 1.0
            add_edge(hv, lv, w)

    if self_loops:
        A += np.eye(n, dtype=np.float32)

    deg = A.sum(axis=1)
    deg = np.clip(deg, 1e-12, None)
    d_inv_sqrt = 1.0 / np.sqrt(deg)
    A_norm = (A * d_inv_sqrt[None, :]) * d_inv_sqrt[:, None]

    return torch.tensor(A_norm, dtype=torch.float32)


class GlobalBusGCNEncoder(nn.Module):
    """A shared GCN encoder on the full bus graph, with per-agent readout.

    Forward input:
        obs_list: list of agent observations, each tensor shape [B, 3*n_bus_i]

    Output:
        z_list: list of per-agent embeddings, each tensor shape [B, embed_dim]
    """

    def __init__(
        self,
        net,
        areas,
        device: torch.device,
        embed_dim: int = 32,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.0,
        weight_mode: str = 'inv_z',
        eps: float = 1e-6,
        use_base_topology: bool = True,
    ):
        super().__init__()
        self.device = device
        self.embed_dim = int(embed_dim)
        self.hidden_dim = int(hidden_dim)
        self.num_layers = int(num_layers)
        self.dropout = float(dropout)
        self.weight_mode = str(weight_mode)
        self.eps = float(eps)
        self.use_base_topology = bool(use_base_topology)

        # Flatten bus list in a stable order: concatenate areas in agent order.
        self.areas = [np.asarray(a, dtype=int) for a in areas]
        self.buses_global = np.concatenate(self.areas, axis=0).astype(int)
        self.n_bus_total = int(self.buses_global.shape[0])
        self.bus_to_idx = {int(b): i for i, b in enumerate(self.buses_global.tolist())}

        # Pre-compute slice indices for each agent (for fast pooling)
        self.agent_slices = []
        offset = 0
        for a in self.areas:
            n = int(a.shape[0])
            self.agent_slices.append((offset, offset + n))
            offset += n

        self.register_buffer('adj_norm', torch.eye(self.n_bus_total, dtype=torch.float32))
        # Build adjacency from provided net (usually base net) once.
        self.refresh(net)

        # bus feature dim: (p_norm, q_norm, v_norm)
        self.in_dim = 3

        self.lins = nn.ModuleList()
        self.lns = nn.ModuleList()
        for li in range(self.num_layers):
            in_f = self.in_dim if li == 0 else self.hidden_dim
            self.lins.append(nn.Linear(in_f, self.hidden_dim))
            self.lns.append(nn.LayerNorm(self.hidden_dim))
        self.proj = nn.Linear(self.hidden_dim, self.embed_dim)

        # Conservative init (stable for SAC)
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight.data)
                if m.bias is not None:
                    m.bias.data.fill_(0.0)

        self.to(device)

    def refresh(self, net) -> None:
        """Refresh adjacency. If use_base_topology=True, call this with the base net."""
        A = build_global_adjacency(
            net,
            self.buses_global,
            weight_mode=self.weight_mode,
            eps=self.eps,
            respect_in_service=(not self.use_base_topology),
        )
        with torch.no_grad():
            A = A.to(self.adj_norm.device)
            if A.shape != self.adj_norm.shape:
                raise ValueError(f"Global adjacency shape changed: got {tuple(A.shape)} expected {tuple(self.adj_norm.shape)}")
            self.adj_norm.copy_(A)

    def _reconstruct_global_x(self, obs_list: list[torch.Tensor]) -> torch.Tensor:
        """Reconstruct global node features x from per-agent observations.

        Returns:
            x: Tensor [B, n_bus_total, 3]
        """
        if len(obs_list) != len(self.areas):
            raise ValueError(f"obs_list length {len(obs_list)} != num_agents {len(self.areas)}")
        B = obs_list[0].shape[0]
        x = torch.zeros((B, self.n_bus_total, 3), dtype=obs_list[0].dtype, device=obs_list[0].device)
        cursor = 0
        for i, (o, area) in enumerate(zip(obs_list, self.areas)):
            if o.dim() != 2:
                raise ValueError(f"obs[{i}] must be [B,D], got {tuple(o.shape)}")
            n = int(area.shape[0])
            D_expected = 3 * n
            if o.shape[1] < D_expected:
                raise ValueError(f"obs[{i}] dim too small: got {o.shape[1]}, expected >= {D_expected}")
            p = o[:, :n]
            q = o[:, n:2*n]
            v = o[:, 2*n:3*n]
            x[:, cursor:cursor+n, 0] = p
            x[:, cursor:cursor+n, 1] = q
            x[:, cursor:cursor+n, 2] = v
            cursor += n
        return x

    def forward(self, obs_list: list[torch.Tensor]) -> list[torch.Tensor]:
        # Build global node features
        x = self._reconstruct_global_x(obs_list)  # [B, n, 3]

        # GCN message passing
        h = x
        for lin, ln in zip(self.lins, self.lns):
            h0 = h
            h = torch.einsum('ij,bjf->bif', self.adj_norm, h)
            h = lin(h)
            h = F.relu(h)
            h = ln(h)
            if self.dropout > 0:
                h = F.dropout(h, p=self.dropout, training=self.training)
            if h0.shape == h.shape:
                h = h + h0

        # Per-agent readout: mean pool over that agent's bus nodes
        z_list = []
        for (s, e) in self.agent_slices:
            pooled = h[:, s:e, :].mean(dim=1)  # [B, hidden]
            z_list.append(self.proj(pooled))  # [B, embed]
        return z_list


def build_global_bus_encoder(
    env,
    device: torch.device,
    embed_dim: int = 32,
    hidden_dim: int = 64,
    num_layers: int = 2,
    dropout: float = 0.0,
    weight_mode: str = 'inv_z',
    use_base_topology: bool = True,
) -> GlobalBusGCNEncoder:
    """Convenience builder from environment object."""
    be = getattr(env, 'env', env)
    net = getattr(be, 'net_orig', None) if use_base_topology else getattr(be, 'net', None)
    if net is None:
        net = getattr(be, 'net', None)
    areas = getattr(be, 'areas', None)
    if areas is None:
        raise ValueError("env must have attribute 'areas'")
    enc = GlobalBusGCNEncoder(
        net=net,
        areas=areas,
        device=device,
        embed_dim=embed_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        dropout=dropout,
        weight_mode=weight_mode,
        use_base_topology=use_base_topology,
    )
    return enc
