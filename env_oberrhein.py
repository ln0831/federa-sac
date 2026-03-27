import gymnasium as gym
import numpy as np
import pandapower as pp
import pandapower.networks as pn
from gymnasium import spaces
import copy
import warnings

# 忽略警告
warnings.filterwarnings("ignore")

from collections import deque

# Topology outage utilities
from topology_utils import snapshot_topology, restore_topology, sample_line_outages, apply_line_outages, connectivity_stats

def _build_bus_graph(net):
    """Build undirected bus adjacency list from pandapower net (lines + trafos)."""
    adj = {int(b): set() for b in net.bus.index.tolist()}
    if hasattr(net, 'line') and len(net.line) > 0:
        for row in net.line[['from_bus','to_bus']].itertuples(index=False):
            u, v = int(row[0]), int(row[1])
            adj.setdefault(u, set()).add(v)
            adj.setdefault(v, set()).add(u)
    if hasattr(net, 'trafo') and (net.trafo is not None) and len(net.trafo) > 0:
        for row in net.trafo[['hv_bus','lv_bus']].itertuples(index=False):
            u, v = int(row[0]), int(row[1])
            adj.setdefault(u, set()).add(v)
            adj.setdefault(v, set()).add(u)
    return adj

def _multi_source_dist(adj, sources, nodes_set):
    """Shortest hop distance from any source to all nodes (BFS). Unreachable => inf."""
    INF = 10**9
    dist = {n: INF for n in nodes_set}
    q = deque()
    for s in sources:
        if s in nodes_set:
            dist[s] = 0
            q.append(s)
    while q:
        u = q.popleft()
        du = dist[u]
        for v in adj.get(u, ()):
            if v not in nodes_set:
                continue
            if dist[v] > du + 1:
                dist[v] = du + 1
                q.append(v)
    return dist

def _select_seeds(adj, nodes, k, seed=0):
    """Farthest-point seeding using hop distance (deterministic)."""
    nodes_sorted = sorted(int(x) for x in nodes)
    if k <= 1:
        return [nodes_sorted[0]]
    rng = np.random.default_rng(int(seed))
    first = int(rng.choice(nodes_sorted))
    seeds = [first]
    nodes_set = set(nodes_sorted)
    for _ in range(1, k):
        dist = _multi_source_dist(adj, seeds, nodes_set)
        # pick farthest; tie-break by smallest bus id
        cand = sorted(((d, n) for n, d in dist.items() if n not in seeds), key=lambda x: (-x[0], x[1]))
        if not cand:
            break
        far_d, far_n = cand[0]
        if far_d >= 10**9:
            far_n = min(n for n in nodes_sorted if n not in seeds)
        seeds.append(int(far_n))
    while len(seeds) < k:
        seeds.append(min(n for n in nodes_sorted if n not in seeds))
    return seeds

def partition_buses_contiguous(net, valid_buses, num_agents, partition_seed=0):
    """Topology-contiguous partition via farthest-point seeds + multi-source BFS assignment."""
    valid = [int(b) for b in valid_buses]
    if num_agents <= 1:
        return [np.array(valid, dtype=int)]
    adj = _build_bus_graph(net)
    nodes_set = set(valid)
    seeds = _select_seeds(adj, valid, num_agents, seed=partition_seed)
    owner = {n: None for n in nodes_set}
    q = deque()
    for i, s in enumerate(seeds):
        if s in nodes_set:
            owner[s] = i
            q.append(s)
    while q:
        u = q.popleft()
        ou = owner[u]
        for v in adj.get(u, ()):
            if v not in nodes_set:
                continue
            if owner[v] is None:
                owner[v] = ou
                q.append(v)
    for n in nodes_set:
        if owner[n] is None:
            owner[n] = 0
    areas = [[] for _ in range(num_agents)]
    for n in sorted(nodes_set):
        areas[owner[n]].append(n)
    for i in range(num_agents):
        if len(areas[i]) == 0:
            largest = max(range(num_agents), key=lambda j: len(areas[j]))
            areas[i].append(areas[largest].pop())
    return [np.array(a, dtype=int) for a in areas]


class DistNetEnv(gym.Env):
    def __init__(
        self,
        num_agents=4,
        contiguous_partition=True,
        partition_seed=0,
        topology_mode: str = 'static',
        outage_k: int = 0,
        topology_seed: int = 0,
        outage_policy: str = 'local',
        outage_radius: int = 2,
        avoid_slack_hops: int = 1,
        outage_center_bus: int = None,
        **kwargs,
    ):
        super(DistNetEnv, self).__init__()
        
        # Oberrhein 网络较大，建议切分给 4 个或更多智能体
        self.num_agents = num_agents
        self.v_min = 0.90
        self.v_max = 1.10

        self.topology_mode = str(topology_mode).lower()
        if self.topology_mode not in {'static', 'random_reset'}:
            raise ValueError("topology_mode must be 'static' or 'random_reset'")
        self.outage_k = int(outage_k)
        self.topology_seed = int(topology_seed)
        self.outage_policy = str(outage_policy).lower()
        self.outage_radius = int(outage_radius)
        self.avoid_slack_hops = int(avoid_slack_hops)
        self.outage_center_bus = outage_center_bus
        self.episode_idx = 0

        # 1. 加载德国 MV Oberrhein 真实配电网 (179 节点)
        print("[Env] 正在加载德国 MV Oberrhein 配电网 (179节点)...")
        
        # [关键修复] scenario 必须是 'load' 或 'generation'
        # 我们选择 'load' (重负荷场景) 作为基准
        self.net_orig = pn.mv_oberrhein(scenario='load')
        
        # 2. 添加设备
        self._init_modifications()
        
        # 3. 创建工作对象
        self.net = copy.deepcopy(self.net_orig)

        # Snapshot of the base topology (used for restoring at every reset)
        self._topo_snapshot = snapshot_topology(self.net)
        
        # [加速缓存] 
        self.initial_load_p = self.net.load.p_mw.values.copy()
        self.initial_load_q = self.net.load.q_mvar.values.copy()
        
        print("[Env] Oberrhein 网络构建及缓存完成。")
        
        # 4. 区域划分
        all_buses = self.net.bus.index.tolist()
        
        # 排除高压连接点 (Ext Grid)
        if len(self.net.ext_grid) > 0:
            ext_grid_bus = self.net.ext_grid.bus.values
            self.slack_bus = int(ext_grid_bus[0])
            valid_buses = [b for b in all_buses if b not in ext_grid_bus]
        else:
            self.slack_bus = None
            valid_buses = all_buses

        self.valid_buses = [int(b) for b in valid_buses]
        
        # 自动切分区域
        if contiguous_partition:
            self.areas = partition_buses_contiguous(self.net, valid_buses, self.num_agents, partition_seed=partition_seed)
        else:
            self.areas = np.array_split(valid_buses, self.num_agents)
        
        # 5. 定义空间
        self.action_space = []
        self.observation_space = []
        
        for i, area_buses in enumerate(self.areas):
            n_pv = len(self.net.sgen[self.net.sgen.bus.isin(area_buses)])
            n_svc = len(self.net.shunt[self.net.shunt.bus.isin(area_buses)])
            act_dim = max(1, n_pv * 2 + n_svc)
            
            self.action_space.append(spaces.Box(low=-1, high=1, shape=(act_dim,), dtype=np.float32))
            
            # 观测维度
            obs_dim = len(area_buses) * 3
            self.observation_space.append(spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32))
            
        self.success = True

    def _init_modifications(self):
        """为 Oberrhein 系统添加 PV 和 SVC"""
        buses = self.net_orig.bus.index.tolist()
        ext_bus = -1
        if len(self.net_orig.ext_grid) > 0:
            ext_bus = self.net_orig.ext_grid.bus.values[0]
        
        valid_buses = [b for b in buses if b != ext_bus]
        
        # [策略] 179 个节点，网络较大
        # 添加 PV: 每隔 8 个节点放一个 (约 22 个 PV)
        # 容量设为 2.5 MVA (Oberrhein是中压网，容量较大)
        cnt_pv = 0
        for bus in valid_buses[::8]: 
            pp.create_sgen(self.net_orig, bus, p_mw=0.0, q_mvar=0, sn_mva=2.5, name=f"PV_{bus}", type="PV")
            cnt_pv += 1
        
        # 添加 SVC: 每隔 15 个节点放一个 (约 12 个 SVC)
        # 容量 1.5 MVar
        cnt_svc = 0
        for bus in valid_buses[::15]:
            pp.create_shunt(self.net_orig, bus, q_mvar=0, p_mw=0, name=f"SVC_{bus}")
            cnt_svc += 1
                
        print(f"[Env] Oberrhein: 已添加 {cnt_pv} 个 PV (2.5MW) 和 {cnt_svc} 个 SVC。")

    def reset(self):
        # Restore base topology
        restore_topology(self.net, self._topo_snapshot)

        # Apply random line outages per episode (paper-style multi-line outage)
        self.outage_lines = []
        if self.topology_mode == 'random_reset' and self.outage_k > 0:
            seed = self.topology_seed + self.episode_idx
            self.outage_lines = sample_line_outages(
                self.net,
                self.outage_k,
                seed=seed,
                ensure_connected=True,
                slack_bus=self.slack_bus,
                buses_subset=self.valid_buses,
                outage_policy=self.outage_policy,
                outage_radius=self.outage_radius,
                center_bus=self.outage_center_bus,
                avoid_slack_hops=self.avoid_slack_hops,
            )
            apply_line_outages(self.net, self.outage_lines)

        self.episode_idx += 1
        # [优化] 极速数值重置
        self.net.load.p_mw[:] = self.initial_load_p
        self.net.load.q_mvar[:] = self.initial_load_q
        
        # 随机波动 ±10%
        if len(self.net.load) > 0:
            scale = np.random.uniform(0.90, 1.10, size=len(self.net.load))
            self.net.load.p_mw *= scale
            self.net.load.q_mvar *= scale
        
        # 清零设备
        self.net.sgen.p_mw[:] = 0.0
        self.net.sgen.q_mvar[:] = 0.0
        self.net.shunt.q_mvar[:] = 0.0
        
        try:
            pp.runpp(self.net, numba=False)
            self.success = bool(getattr(self.net, 'converged', False))
            if self.success:
                vm = self.net.res_bus.loc[self.valid_buses, 'vm_pu'].values if len(self.valid_buses) > 0 else None
                if vm is None or (not np.isfinite(vm).all()):
                    self.success = False
        except Exception:
            self.success = False
            
        return self._get_obs()

    def step(self, actions):
        for i, area_buses in enumerate(self.areas):
            act = actions[i]
            ptr = 0
            
            # PV Control
            area_pv = self.net.sgen[self.net.sgen.bus.isin(area_buses)].index
            for idx in area_pv:
                if ptr + 1 >= len(act): break
                s_max = self.net.sgen.at[idx, 'sn_mva']
                p_val = (act[ptr] + 1) / 2 * s_max 
                q_lim = np.sqrt(max(0, s_max**2 - p_val**2))
                q_val = act[ptr+1] * q_lim
                
                self.net.sgen.at[idx, 'p_mw'] = p_val
                self.net.sgen.at[idx, 'q_mvar'] = q_val
                ptr += 2
                
            # SVC Control
            area_svc = self.net.shunt[self.net.shunt.bus.isin(area_buses)].index
            for idx in area_svc:
                if ptr >= len(act): break
                # 调节范围 2.0
                self.net.shunt.at[idx, 'q_mvar'] = act[ptr] * 2.0
                ptr += 1

        try:
            pp.runpp(self.net, numba=False)
            self.success = bool(getattr(self.net, 'converged', False))
            if self.success:
                vm = self.net.res_bus.loc[self.valid_buses, 'vm_pu'].values if len(self.valid_buses) > 0 else None
                if vm is None or (not np.isfinite(vm).all()):
                    self.success = False
        except Exception:
            self.success = False
            
        rewards = []
        done = False
        p_loss_val = 0.0
        
        if self.success:
            p_loss_val = self.net.res_line.pl_mw.sum()
            for i, area_buses in enumerate(self.areas):
                v_vals = self.net.res_bus.loc[area_buses, 'vm_pu'].values
                
                # [核心逻辑] 平滑奖励
                v_lower = np.maximum(0, self.v_min - v_vals)
                v_upper = np.maximum(0, v_vals - self.v_max)
                
                linear_viol = np.sum(v_lower + v_upper)
                squared_viol = np.sum(v_lower**2 + v_upper**2)
                
                raw_reward = - (p_loss_val * 10.0) - (200.0 * linear_viol) - (1000.0 * squared_viol)
                rewards.append(raw_reward * 0.01)
        else:
            rewards = [-5.0] * self.num_agents
            done = True 

        # ---- Global stats for logging / visualization ----
        if self.success and hasattr(self.net, 'res_bus') and len(self.net.res_bus) > 0:
            v_all = self.net.res_bus.loc[self.valid_buses, 'vm_pu'].values
            v_all = np.nan_to_num(v_all, nan=1.0)
            v_lower = np.maximum(0, self.v_min - v_all)
            v_upper = np.maximum(0, v_all - self.v_max)
            v_viol_lin_total = float(np.sum(v_lower + v_upper))
            v_viol_sq_total = float(np.sum(v_lower**2 + v_upper**2))
            v_min_global = float(np.min(v_all)) if len(v_all) > 0 else 1.0
            v_max_global = float(np.max(v_all)) if len(v_all) > 0 else 1.0
        else:
            v_viol_lin_total = 0.0
            v_viol_sq_total = 0.0
            v_min_global = 0.0
            v_max_global = 0.0

        n_comp, comp_sizes = connectivity_stats(self.net, buses_subset=self.valid_buses)

        info = {
            "p_loss": float(p_loss_val),
            "v_viol_lin_total": v_viol_lin_total,
            "v_viol_sq_total": v_viol_sq_total,
            "v_min": v_min_global,
            "v_max": v_max_global,
            "num_outages": int(len(getattr(self, 'outage_lines', []))),
            "outage_lines": list(getattr(self, 'outage_lines', [])),
            "n_components": int(n_comp),
            "component_sizes": list(comp_sizes),
            "topology_mode": self.topology_mode,
        }

        return self._get_obs(), rewards, done, info

    def _get_obs(self):
        # [优化] 静态归一化
        obs_list = []
        for area_buses in self.areas:
            if self.success:
                p = self.net.res_bus.loc[area_buses, 'p_mw'].values
                q = self.net.res_bus.loc[area_buses, 'q_mvar'].values
                v = self.net.res_bus.loc[area_buses, 'vm_pu'].values
            else:
                p = np.zeros(len(area_buses))
                q = np.zeros(len(area_buses))
                v = np.ones(len(area_buses))
            
            p_norm = p / 5.0
            q_norm = q / 5.0
            v_norm = (v - 1.0) * 20.0
            
            state = np.concatenate([p_norm, q_norm, v_norm])
            state = np.nan_to_num(state, nan=0.0, posinf=5.0, neginf=-5.0)
            obs_list.append(state.astype(np.float32))
        return obs_list