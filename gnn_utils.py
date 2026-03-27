import torch
import numpy as np


def _safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def get_agent_adjacency(net, areas, device='cpu', mode: str = 'inv_z', eps: float = 1e-6, normalize: bool = True):
    """Compute agent adjacency (optionally weighted) from a pandapower grid and area partition.

    By default, returns an **edge-weighted** adjacency using an impedance-inspired weight:
        w_ij += 1 / (|Z| + eps)
    accumulated over all inter-area lines. For trafos, uses a simple proxy.

    Args:
        net: pandapower net
        areas: list of arrays/lists, each containing bus indices managed by that agent
        device: torch device
        mode: 'inv_z' (default), 'count', or 'binary'
        eps: numerical stability
        normalize: if True, scales off-diagonal weights to [0, 1] by dividing by max off-diagonal weight

    Returns:
        adj_tensor: torch.FloatTensor [num_agents, num_agents] with self-loops = 1.
    """

    mode = (mode or 'inv_z').lower()
    if mode not in {'inv_z', 'count', 'binary'}:
        raise ValueError(f"Unknown adj mode: {mode}. Choose from ['inv_z','count','binary']")

    num_agents = len(areas)
    adj = np.zeros((num_agents, num_agents), dtype=np.float32)
    np.fill_diagonal(adj, 1.0)

    # bus -> agent mapping
    bus_to_agent = {}
    for agent_id, buses in enumerate(areas):
        for b in list(buses):
            bus_to_agent[int(b)] = agent_id

    def add_weight(i: int, j: int, w: float):
        if i == j:
            return
        if mode == 'binary':
            w = 1.0
        elif mode == 'count':
            w = 1.0
        else:
            w = float(w)
        adj[i, j] += w
        adj[j, i] += w

    # Lines
    if hasattr(net, 'line') and len(net.line) > 0:
        # Iterate rows; robust to missing columns.
        for row in net.line.itertuples(index=False):
            # Respect outages / topology changes
            in_serv = getattr(row, 'in_service', True)
            if in_serv is not True and (not bool(in_serv)):
                continue
            f_bus = int(getattr(row, 'from_bus'))
            t_bus = int(getattr(row, 'to_bus'))
            if f_bus not in bus_to_agent or t_bus not in bus_to_agent:
                continue
            ai = bus_to_agent[f_bus]
            aj = bus_to_agent[t_bus]
            if ai == aj:
                continue

            if mode == 'inv_z':
                r = _safe_float(getattr(row, 'r_ohm_per_km', 0.0))
                x = _safe_float(getattr(row, 'x_ohm_per_km', 0.0))
                length = _safe_float(getattr(row, 'length_km', 1.0), 1.0)
                z = (r * length) ** 2 + (x * length) ** 2
                z = float(np.sqrt(max(z, 0.0)))
                w = 1.0 / (z + eps)
            else:
                w = 1.0

            add_weight(ai, aj, w)

    # Transformers (Oberrhein often has trafos)
    if hasattr(net, 'trafo') and (net.trafo is not None) and (len(net.trafo) > 0):
        for row in net.trafo.itertuples(index=False):
            # Respect outages / topology changes
            in_serv = getattr(row, 'in_service', True)
            if in_serv is not True and (not bool(in_serv)):
                continue
            hv = int(getattr(row, 'hv_bus'))
            lv = int(getattr(row, 'lv_bus'))
            if hv not in bus_to_agent or lv not in bus_to_agent:
                continue
            ai = bus_to_agent[hv]
            aj = bus_to_agent[lv]
            if ai == aj:
                continue

            if mode == 'inv_z':
                # Use vk_percent as a weak proxy for impedance (larger vk => weaker coupling)
                vk = _safe_float(getattr(row, 'vk_percent', 10.0), 10.0)
                w = 1.0 / (abs(vk) + eps)
            else:
                w = 1.0

            add_weight(ai, aj, w)

    if normalize and num_agents > 1:
        mask = ~np.eye(num_agents, dtype=bool)
        max_off = float(np.max(adj[mask])) if np.any(mask) else 0.0
        if max_off > 0:
            adj[mask] = adj[mask] / max_off

    adj_tensor = torch.tensor(adj, dtype=torch.float32, device=device)
    print(f"[GNN Utils] Agent Adjacency Matrix Constructed. mode={mode}, normalize={normalize}, shape={tuple(adj_tensor.shape)}")
    return adj_tensor
