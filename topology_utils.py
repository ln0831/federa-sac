"""Topology utilities for pandapower-based distribution network environments.

Key features:
- Snapshot/restore topology using `in_service` flags for lines and trafos.
- Random line outage sampling and application.
- Connectivity statistics (number of connected components) from current topology.

Design notes:
- We do NOT import pandapower here; callers pass in a `net` object.
- We consider only `in_service` edges when building connectivity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


@dataclass
class TopologySnapshot:
    line_in_service: Optional[np.ndarray] = None
    trafo_in_service: Optional[np.ndarray] = None


def snapshot_topology(net) -> TopologySnapshot:
    """Capture current `in_service` flags of lines and transformers."""
    snap = TopologySnapshot()
    if hasattr(net, "line") and net.line is not None and len(net.line) > 0 and "in_service" in net.line.columns:
        snap.line_in_service = net.line["in_service"].values.astype(bool).copy()
    if hasattr(net, "trafo") and net.trafo is not None and len(net.trafo) > 0 and "in_service" in net.trafo.columns:
        snap.trafo_in_service = net.trafo["in_service"].values.astype(bool).copy()
    return snap


def restore_topology(net, snap: TopologySnapshot) -> None:
    """Restore `in_service` flags from a snapshot."""
    if snap.line_in_service is not None and hasattr(net, "line") and net.line is not None and len(net.line) > 0:
        if "in_service" not in net.line.columns:
            net.line["in_service"] = True
        net.line.loc[:, "in_service"] = snap.line_in_service
    if snap.trafo_in_service is not None and hasattr(net, "trafo") and net.trafo is not None and len(net.trafo) > 0:
        if "in_service" not in net.trafo.columns:
            net.trafo["in_service"] = True
        net.trafo.loc[:, "in_service"] = snap.trafo_in_service


def _eligible_line_indices(net) -> List[int]:
    if not (hasattr(net, "line") and net.line is not None and len(net.line) > 0):
        return []
    if "in_service" not in net.line.columns:
        # assume all in service
        return list(map(int, net.line.index.tolist()))
    return [int(i) for i, row in net.line["in_service"].items() if bool(row)]


def _slack_bus_from_net(net) -> Optional[int]:
    """Best-effort slack/ext_grid bus inference."""
    try:
        if hasattr(net, "ext_grid") and net.ext_grid is not None and len(net.ext_grid) > 0:
            return int(net.ext_grid.bus.values[0])
    except Exception:
        pass
    try:
        if hasattr(net, "bus") and net.bus is not None and len(net.bus) > 0:
            return int(net.bus.index.tolist()[0])
    except Exception:
        pass
    return None


def _is_connected_from_slack(net, slack_bus: int, buses_subset: Optional[Iterable[int]] = None) -> bool:
    """Check if all buses in subset are reachable from slack using in-service edges."""
    adj = _build_bus_adjacency_from_net(net)
    if slack_bus not in adj:
        return False

    if buses_subset is None:
        targets = set(adj.keys())
    else:
        targets = set(int(x) for x in buses_subset)
        targets.add(int(slack_bus))

    # BFS
    seen = {int(slack_bus)}
    stack = [int(slack_bus)]
    while stack:
        u = stack.pop()
        for v in adj.get(u, []):
            if v not in seen:
                seen.add(v)
                stack.append(v)

    # all targets must be reachable
    return targets.issubset(seen)


def sample_line_outages(
    net,
    k: int,
    seed: int = 0,
    *,
    ensure_connected: bool = False,
    slack_bus: Optional[int] = None,
    buses_subset: Optional[Iterable[int]] = None,
    outage_policy: str = "global",
    outage_radius: int = 2,
    center_bus: Optional[int] = None,
    avoid_slack_hops: int = 1,
    max_tries: int = 200,
) -> List[int]:
    """Sample k distinct in-service line indices for outages.

    Compared to the earlier naive implementation, this version is *paper-style robust*:
    - For outage_policy=local, if the r-hop neighborhood has insufficient candidates,
      we automatically expand the neighborhood radius (r -> r+1 -> ...), and finally
      fall back to global sampling if still insufficient.
    - Under ensure_connected=True, we clamp the requested k to the feasible candidate
      set size at every stage to avoid ValueError from numpy.choice.

    Args:
        ensure_connected: if True, try to ensure that all buses in `buses_subset` remain
            reachable from `slack_bus` after outages. If `buses_subset` is None, we require
            the whole network to remain connected to the slack.
        slack_bus: slack/ext_grid bus index; if None and ensure_connected=True, infer from net.
        buses_subset: buses to keep connected to slack.
        outage_policy: 'global' or 'local'. 'local' samples faults inside an r-hop neighborhood.
        outage_radius: initial neighborhood radius for 'local'.
        avoid_slack_hops: avoid faulting lines within <= this hop distance from the slack bus.
        max_tries: random-rejection attempts before falling back to greedy selection.

    Returns:
        List[int]: chosen line indices (may be < k in extreme cases when constraints are tight).
    """
    eligible_all = _eligible_line_indices(net)
    if k <= 0 or len(eligible_all) == 0:
        return []

    k_req = int(k)
    rng = np.random.default_rng(int(seed))

    outage_policy = str(outage_policy).lower()
    if outage_policy not in {"global", "local"}:
        outage_policy = "global"

    eligible = list(eligible_all)

    # -------- Local (paper-style) sampling with automatic radius expansion --------
    if outage_policy == "local":
        slack = int(slack_bus) if slack_bus is not None else _slack_bus_from_net(net)
        subset = list(int(x) for x in buses_subset) if buses_subset is not None else None
        center_pool = subset if subset is not None and len(subset) > 0 else None

        adj = _build_bus_adjacency_from_net(net)

        if center_pool is None and slack is not None:
            center_pool = [int(n) for n in adj.keys() if int(n) != int(slack)]
        if center_pool is None:
            center_pool = [int(n) for n in adj.keys()]

        def bfs_neighborhood(center: int, r: int) -> set:
            seen = {int(center)}
            frontier = [int(center)]
            for _ in range(int(r)):
                nxt = []
                for u in frontier:
                    for v in adj.get(int(u), []):
                        if int(v) not in seen:
                            seen.add(int(v))
                            nxt.append(int(v))
                frontier = nxt
                if not frontier:
                    break
            return seen

        def candidate_lines(nodes: set) -> List[int]:
            cand: List[int] = []
            if hasattr(net, "line") and net.line is not None and len(net.line) > 0:
                has_is = "in_service" in net.line.columns
                for idx, row in net.line.iterrows():
                    if has_is and (not bool(row["in_service"])):
                        continue
                    u = int(row["from_bus"])
                    v = int(row["to_bus"])
                    if u in nodes and v in nodes:
                        cand.append(int(idx))
            return cand

        # Choose outage center (deterministic if center_bus is provided)
        if center_bus is not None and int(center_bus) in adj:
            center = int(center_bus)
        else:
            center = int(rng.choice(center_pool))

        r0 = max(1, int(outage_radius))
        r_max = max(r0, 6)  # hard cap; matches paper-style small radii

        cand = []
        for r in range(r0, r_max + 1):
            nodes = bfs_neighborhood(center, r)
            cand = candidate_lines(nodes)
            # Aim for k_req candidates; if not possible, get as many as we can.
            if len(cand) >= min(k_req, len(eligible_all)):
                break

        if len(cand) >= 1:
            eligible = cand

        # If still too few candidates, fall back to global eligible set
        if len(eligible) < min(k_req, len(eligible_all)):
            eligible = list(eligible_all)

    # -------- No connectivity constraint: choose directly (safe clamp) --------
    if not ensure_connected:
        k_eff = min(int(k_req), len(eligible))
        if k_eff <= 0:
            return []
        chosen = rng.choice(eligible, size=k_eff, replace=False)
        return [int(x) for x in np.asarray(chosen).tolist()]

    # -------- Connectivity constrained sampling --------
    slack = int(slack_bus) if slack_bus is not None else _slack_bus_from_net(net)
    if slack is None:
        k_eff = min(int(k_req), len(eligible))
        if k_eff <= 0:
            return []
        chosen = rng.choice(eligible, size=k_eff, replace=False)
        return [int(x) for x in np.asarray(chosen).tolist()]

    # Optional: avoid cutting lines too close to slack
    if avoid_slack_hops is not None and int(avoid_slack_hops) >= 0:
        try:
            hops = int(avoid_slack_hops)
            if hops >= 0:
                adj0 = _build_bus_adjacency_from_net(net)
                dist = {int(slack): 0}
                q = [int(slack)]
                while q:
                    u = q.pop(0)
                    du = dist[u]
                    if du >= hops:
                        continue
                    for v in adj0.get(u, []):
                        if int(v) not in dist:
                            dist[int(v)] = du + 1
                            q.append(int(v))

                safe_eligible: List[int] = []
                if hasattr(net, "line") and net.line is not None and len(net.line) > 0:
                    for idx in eligible:
                        row = net.line.loc[int(idx)]
                        u = int(row["from_bus"])
                        v = int(row["to_bus"])
                        if (u in dist) or (v in dist):
                            continue
                        safe_eligible.append(int(idx))

                # Only apply the filter if it doesn't make k infeasible
                if len(safe_eligible) >= max(1, min(int(k_req), len(eligible))):
                    eligible = safe_eligible
        except Exception:
            pass

    # clamp k to feasible candidate size
    k_eff = min(int(k_req), len(eligible))
    if k_eff <= 0:
        return []

    snap = snapshot_topology(net)
    for _ in range(int(max_tries)):
        chosen = rng.choice(eligible, size=k_eff, replace=False)
        apply_line_outages(net, chosen)
        ok = _is_connected_from_slack(net, int(slack), buses_subset=buses_subset)
        restore_topology(net, snap)
        if ok:
            return [int(x) for x in np.asarray(chosen).tolist()]

    # Fallback: greedy build a connected outage set (may return fewer than k_eff)
    chosen_list: List[int] = []
    perm = eligible.copy()
    rng.shuffle(perm)
    for idx in perm:
        trial = chosen_list + [int(idx)]
        apply_line_outages(net, trial)
        ok = _is_connected_from_slack(net, int(slack), buses_subset=buses_subset)
        restore_topology(net, snap)
        if ok:
            chosen_list.append(int(idx))
        if len(chosen_list) >= k_eff:
            break

    return chosen_list



def apply_line_outages(net, line_indices: Sequence[int]) -> None:
    """Apply outages by setting net.line.in_service=False for selected indices."""
    if not (hasattr(net, "line") and net.line is not None and len(net.line) > 0):
        return
    if "in_service" not in net.line.columns:
        net.line["in_service"] = True
    if len(line_indices) == 0:
        return
    net.line.loc[list(line_indices), "in_service"] = False


def _build_bus_adjacency_from_net(net) -> Dict[int, List[int]]:
    """Build undirected bus adjacency list using only in-service lines/trafos."""
    buses = []
    if hasattr(net, "bus") and net.bus is not None:
        buses = [int(b) for b in net.bus.index.tolist()]
    adj: Dict[int, List[int]] = {b: [] for b in buses}

    # lines
    if hasattr(net, "line") and net.line is not None and len(net.line) > 0:
        cols = net.line.columns
        has_in_service = "in_service" in cols
        for idx, row in net.line.iterrows():
            if has_in_service and (not bool(row["in_service"])):
                continue
            u = int(row["from_bus"])
            v = int(row["to_bus"])
            if u not in adj:
                adj[u] = []
            if v not in adj:
                adj[v] = []
            adj[u].append(v)
            adj[v].append(u)

    # trafos
    if hasattr(net, "trafo") and net.trafo is not None and len(net.trafo) > 0:
        cols = net.trafo.columns
        has_in_service = "in_service" in cols
        for idx, row in net.trafo.iterrows():
            if has_in_service and (not bool(row["in_service"])):
                continue
            u = int(row["hv_bus"])
            v = int(row["lv_bus"])
            if u not in adj:
                adj[u] = []
            if v not in adj:
                adj[v] = []
            adj[u].append(v)
            adj[v].append(u)

    return adj


def connectivity_stats(net, buses_subset: Optional[Iterable[int]] = None) -> Tuple[int, List[int]]:
    """Compute number of connected components and their sizes.

    Args:
        net: pandapower net
        buses_subset: optional iterable of bus indices; if provided, compute connectivity only among these buses.

    Returns:
        (n_components, sizes_sorted_desc)
    """
    adj = _build_bus_adjacency_from_net(net)

    if buses_subset is None:
        nodes = set(adj.keys())
    else:
        nodes = set(int(x) for x in buses_subset)
        # ensure nodes appear in adj
        for n in list(nodes):
            adj.setdefault(n, [])

    visited = set()
    sizes: List[int] = []

    for n in nodes:
        if n in visited:
            continue
        # BFS
        q = [n]
        visited.add(n)
        size = 0
        while q:
            u = q.pop()
            size += 1
            for v in adj.get(u, []):
                if v not in nodes:
                    continue
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        sizes.append(size)

    sizes.sort(reverse=True)
    return (len(sizes), sizes)
