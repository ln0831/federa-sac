"""Local bus-level GNN encoder for each partition/agent (pure PyTorch).

Observation per agent must be concatenated as [p_norm, q_norm, v_norm] over
that agent's area buses (as implemented in env_33/env_69/env_141/env_oberrhein).

The encoder builds a *local* weighted adjacency from pandapower net
(respecting in_service for outages) and runs a small weighted GCN.
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


def build_area_adjacency(
    net,
    area_buses: np.ndarray,
    weight_mode: str = 'inv_z',
    eps: float = 1e-6,
    self_loops: bool = True,
) -> torch.Tensor:
    """Build a weighted adjacency for an area's bus subgraph.

    Args:
        net: pandapower net
        area_buses: 1D array of bus indices
        weight_mode: 'inv_z' or 'binary' or 'count'
        eps: stability
        self_loops: add self-loops

    Returns:
        A_norm: torch.FloatTensor [n, n] normalized with D^{-1/2} A D^{-1/2}
    """
    mode = (weight_mode or 'inv_z').lower()
    if mode not in {'inv_z', 'binary', 'count'}:
        raise ValueError(f"Unknown weight_mode: {weight_mode}")

    area_buses = np.asarray(area_buses, dtype=int)
    n = int(area_buses.shape[0])
    bus_to_local = {int(b): i for i, b in enumerate(area_buses.tolist())}

    A = np.zeros((n, n), dtype=np.float32)

    def add_edge(u_bus: int, v_bus: int, w: float):
        if u_bus not in bus_to_local or v_bus not in bus_to_local:
            return
        u = bus_to_local[int(u_bus)]
        v = bus_to_local[int(v_bus)]
        if u == v:
            return
        A[u, v] += float(w)
        A[v, u] += float(w)

    # lines
    if hasattr(net, 'line') and net.line is not None and len(net.line) > 0:
        for row in net.line.itertuples(index=False):
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

    # trafos (for cases that include them)
    if hasattr(net, 'trafo') and net.trafo is not None and len(net.trafo) > 0:
        for row in net.trafo.itertuples(index=False):
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

    # normalize D^{-1/2} A D^{-1/2}
    deg = A.sum(axis=1)
    deg = np.clip(deg, 1e-12, None)
    d_inv_sqrt = 1.0 / np.sqrt(deg)
    A_norm = (A * d_inv_sqrt[None, :]) * d_inv_sqrt[:, None]

    return torch.tensor(A_norm, dtype=torch.float32)


class AreaBusGCNEncoder(nn.Module):
    """GCN encoder for a single area.

    Forward input: obs tensor [B, 3*nbus]
    Output: embedding tensor [B, embed_dim]
    """

    def __init__(
        self,
        net,
        area_buses: np.ndarray,
        embed_dim: int = 32,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.0,
        weight_mode: str = 'inv_z',
        eps: float = 1e-6,
    ):
        super().__init__()
        self.area_buses = np.asarray(area_buses, dtype=int)
        self.n_bus = int(self.area_buses.shape[0])
        self.embed_dim = int(embed_dim)
        self.hidden_dim = int(hidden_dim)
        self.num_layers = int(num_layers)
        self.dropout = float(dropout)
        self.weight_mode = str(weight_mode)
        self.eps = float(eps)

        self.register_buffer('adj_norm', torch.eye(self.n_bus, dtype=torch.float32))
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

        # conservative init
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight.data)
                if m.bias is not None:
                    m.bias.data.fill_(0.0)

    def refresh(self, net) -> None:
        """Refresh adjacency (call this after topology/outage changes)."""
        A = build_area_adjacency(net, self.area_buses, weight_mode=self.weight_mode, eps=self.eps)
        with torch.no_grad():
            A = A.to(self.adj_norm.device)
            if A.shape != self.adj_norm.shape:
                raise ValueError(f"Area adjacency shape changed: got {tuple(A.shape)} expected {tuple(self.adj_norm.shape)}")
            self.adj_norm.copy_(A)

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        # obs: [B, 3*nbus]
        if obs.dim() != 2:
            raise ValueError(f"obs must be [B,D], got {tuple(obs.shape)}")
        B, D = obs.shape
        expected = 3 * self.n_bus
        if D < expected:
            raise ValueError(
                f"obs dim too small for this area: got D={D}, expected >= {expected} (nbus={self.n_bus})."
            )

        p = obs[:, 0:self.n_bus]
        q = obs[:, self.n_bus:2 * self.n_bus]
        v = obs[:, 2 * self.n_bus:3 * self.n_bus]
        x = torch.stack([p, q, v], dim=-1)  # [B, n, 3]

        h = x
        for lin, ln in zip(self.lins, self.lns):
            h0 = h
            # message passing
            h = torch.einsum('ij,bjf->bif', self.adj_norm, h)
            h = lin(h)
            h = F.relu(h)
            h = ln(h)
            if self.dropout > 0:
                h = F.dropout(h, p=self.dropout, training=self.training)
            # residual when shapes align
            if h0.shape == h.shape:
                h = h + h0

        pooled = h.mean(dim=1)  # [B, hidden]
        emb = self.proj(pooled)
        return emb


def build_bus_encoders(
    net,
    areas,
    device: torch.device,
    embed_dim: int = 32,
    hidden_dim: int = 64,
    num_layers: int = 2,
    dropout: float = 0.0,
    weight_mode: str = 'inv_z',
) -> list[AreaBusGCNEncoder]:
    """Convenience to build encoders for all areas."""
    encoders: list[AreaBusGCNEncoder] = []
    for area_buses in areas:
        enc = AreaBusGCNEncoder(
            net=net,
            area_buses=np.asarray(area_buses, dtype=int),
            embed_dim=embed_dim,
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            dropout=dropout,
            weight_mode=weight_mode,
        ).to(device)
        encoders.append(enc)
    return encoders
