import torch
import torch.optim as optim
import torch.nn.functional as F
try:
    from torch.utils.tensorboard import SummaryWriter
except Exception:
    class SummaryWriter:
        def __init__(self, *args, **kwargs):
            pass
        def add_scalar(self, *args, **kwargs):
            pass
        def flush(self):
            pass
        def close(self):
            pass
from torch.optim.lr_scheduler import CosineAnnealingLR
import numpy as np
import os
import time
import importlib
import argparse 
import re
from tqdm import tqdm

# ==========================================
# 导入 GNN 相关模块
# ==========================================
from networks import LocalActor, LocalCritic 
from networks_gnn import GraphMixer 
from gnn_utils import get_agent_adjacency
from fmasac_utils import (
    MultiAgentReplayBuffer,
    soft_update,
    hard_update,
    topology_weighted_mix,
    reset_optimizers_state,
)
from context_utils import context_from_obs_list

# Local bus-level encoder (variable-length obs -> fixed embedding)
from bus_gnn_encoder import build_bus_encoders
from global_bus_gnn_encoder import build_global_bus_encoder, GlobalBusGCNEncoder
from fedgrid_federated import (
    AgentPrototypeBank,
    HybridPrototypeBank,
    build_federated_weight_matrix,
    adaptive_parameter_mix,
    sample_active_clients,
    apply_participation_mask,
    select_byzantine_clients,
    inject_module_perturbation,
)


def agent_node_features_from_obs_list(obs_list_tensors, clip_val: float = 5.0):
    """Derive compact per-agent node features from observations.

    Observations are concatenated as [p_norm (nbus), q_norm (nbus), v_norm (nbus)].
    We compute summary stats that are informative for voltage control and topology shifts.

    Returns:
        node_feat: Tensor[B, N, 5] = [mean_p, mean_q, mean_abs_v, v_min, v_max]
    """
    feats = []
    for o in obs_list_tensors:
        # o: [B, D]
        B, D = o.shape
        nbus = max(1, D // 3)
        p = o[:, :nbus]
        q = o[:, nbus:2 * nbus]
        v = o[:, 2 * nbus:3 * nbus]

        mean_p = p.mean(dim=1)
        mean_q = q.mean(dim=1)
        mean_abs_v = v.abs().mean(dim=1)
        v_min = v.min(dim=1).values
        v_max = v.max(dim=1).values

        f = torch.stack([mean_p, mean_q, mean_abs_v, v_min, v_max], dim=1)
        if clip_val is not None and clip_val > 0:
            f = torch.clamp(f, -clip_val, clip_val)
        feats.append(f)
    return torch.stack(feats, dim=1)  # [B, N, 5]


def refresh_adjacency(env, mixer, target_mixer, opts):
    """Recompute agent adjacency and push into mixers.

    ⚠️  Off-policy + topology randomization note
    ------------------------------------------
    When topology_mode=random_reset, the replay buffer contains transitions from
    many different outage topologies. If we always use the *current episode*
    adjacency to train on a mixed batch, it creates a topology/transition
    mismatch that can hurt learning and make the GNN mixer underperform.

    Therefore, by default we use the **base (pre-outage) topology** to build the
    agent adjacency for the GraphMixer. You can switch to the current topology
    via:
        --no_mixer_use_base_topology
    """
    be = _base_env(env)
    if getattr(opts, 'mixer_use_base_topology', True) and hasattr(be, 'net_orig'):
        net_for_adj = be.net_orig
    else:
        net_for_adj = be.net
    adj_matrix = get_agent_adjacency(net_for_adj, be.areas, device=opts.device, mode=opts.adj_mode)
    mixer.set_adjacency(adj_matrix)
    target_mixer.set_adjacency(adj_matrix)
    return adj_matrix


def _base_env(env):
    """Unwrap ScenarioWrapper if present."""
    return getattr(env, 'env', env)


def refresh_bus_encoders(env, bus_encoders, target_bus_encoders=None):
    """Refresh bus adjacency for encoder(s) after topology/outage changes.

    - For legacy local encoders: refresh each area's adjacency.
    - For global encoder: refresh only if it is configured to use current topology.
    """
    if bus_encoders is None:
        return
    be = _base_env(env)
    try:
        net_cur = be.net
        net_base = getattr(be, 'net_orig', net_cur)
    except Exception:
        return

    def _refresh_one(enc, net_to_use):
        try:
            enc.refresh(net_to_use)
        except Exception:
            pass

    if isinstance(bus_encoders, GlobalBusGCNEncoder):
        net_to_use = net_base if getattr(bus_encoders, 'use_base_topology', True) else net_cur
        _refresh_one(bus_encoders, net_to_use)
    else:
        for enc in bus_encoders:
            _refresh_one(enc, net_cur)

    if target_bus_encoders is not None:
        if isinstance(target_bus_encoders, GlobalBusGCNEncoder):
            net_to_use = net_base if getattr(target_bus_encoders, 'use_base_topology', True) else net_cur
            _refresh_one(target_bus_encoders, net_to_use)
        else:
            for enc in target_bus_encoders:
                _refresh_one(enc, net_cur)
def compute_bus_embeddings(bus_encoders, obs_list_tensors, *, detach: bool = False):
    """Compute per-agent bus-GNN embeddings for a list of observations.

    Supports:
      - list[AreaBusGCNEncoder]   (legacy local-per-area)
      - GlobalBusGCNEncoder       (Scheme-B global shared encoder)

    Args:
        bus_encoders: encoder object(s) or None
        obs_list_tensors: list of tensors, each [B, D_i]
        detach: if True, detach the resulting embeddings (no gradient)

    Returns:
        z_list: list of tensors, each [B, embed_dim]
    """
    if bus_encoders is None:
        return None
    if isinstance(bus_encoders, GlobalBusGCNEncoder):
        z_list = bus_encoders(obs_list_tensors)
    else:
        # legacy: compute one by one
        z_list = [enc(o) for enc, o in zip(bus_encoders, obs_list_tensors)]
    if detach:
        z_list = [z.detach() for z in z_list]
    return z_list

def add_bool_arg(parser: argparse.ArgumentParser, name: str, default: bool, help: str):
    """Add a boolean flag with both positive and negative forms.

    Example:
        add_bool_arg(parser, '--mixer_node_feat', default=True, help='...')
    will add:
        --mixer_node_feat         (set True)
        --no_mixer_node_feat      (set False)

    This keeps Windows/PowerShell usage simple and avoids relying on
    argparse.BooleanOptionalAction (for Python < 3.9 compatibility).
    """
    dest = name.lstrip('-').replace('-', '_')
    grp = parser.add_mutually_exclusive_group(required=False)
    grp.add_argument(name, dest=dest, action='store_true', help=help + ' (enable)')
    grp.add_argument(f'--no_{dest}', dest=dest, action='store_false', help=help + ' (disable)')
    parser.set_defaults(**{dest: bool(default)})

class Opts:
    def __init__(self):
        parser = argparse.ArgumentParser(description="FedGrid-v2 GNN-FMASAC: Hybrid-Prototype Robust Federated Topology Control")

        # [环境选择]
        parser.add_argument('--case', type=str, default='33',
                            choices=['33', '69', '141', 'ober'],
                            help="Select grid case")
        parser.add_argument('--gpu', type=str, default='0', help="GPU ID")
        parser.add_argument('--log_dir', type=str, default='./logs', help='TensorBoard log root directory')
        parser.add_argument('--save_dir', type=str, default='./checkpoints', help='Checkpoint output directory')
        parser.add_argument('--exp_name', type=str, default='', help='Optional experiment name for log/checkpoint naming')

        # [训练超参]
        parser.add_argument('--epochs', type=int, default=None)
        parser.add_argument('--batch_size', type=int, default=None)
        parser.add_argument('--hidden_dim', type=int, default=None)

        # [学习率分离] —— 与 train_fmasac.py 对齐
        parser.add_argument('--actor_lr', type=float, default=None)
        parser.add_argument('--critic_lr', type=float, default=None)

        # [高级特性开关]
        add_bool_arg(parser, '--auto_alpha', default=True, help='Auto temperature tuning (SAC)')
        parser.add_argument('--init_alpha', type=float, default=0.2)
        parser.add_argument('--entropy_ratio', type=float, default=0.9)
        parser.add_argument('--grad_clip', type=float, default=1.0)
        parser.add_argument('--val_episodes', type=int, default=5)


        # [Topology partition & adjacency options]
        parser.add_argument('--no_contiguous_partition', action='store_true', default=False,
                    help="Disable topology-contiguous area partition (fallback to np.array_split).")
        parser.add_argument('--partition_seed', type=int, default=0, help="Seed for contiguous partition.")
        parser.add_argument('--adj_mode', type=str, default='inv_z', choices=['inv_z','count','binary'],
                    help="Inter-area adjacency weighting mode for GNN mixer.")

        # [GNN mixer stabilization / capacity]
        add_bool_arg(parser, '--mixer_node_feat', default=True,
                     help='Use per-agent node features (derived from observations) as GAT inputs.')
        parser.add_argument('--edge_drop', type=float, default=0.10,
                            help='DropEdge probability for the GAT branch (helps topology generalization).')
        add_bool_arg(parser, '--mixer_use_base_topology', default=True,
                     help='Use base (pre-outage) topology to build agent adjacency for GraphMixer (recommended with replay).')
        parser.add_argument('--mixer_gate_init_bias', type=float, default=-5.0,
                            help='Initial gate bias for GraphMixer (more negative => closer to MLP-only at start).')
        parser.add_argument('--mixer_gat_ramp_epochs', type=int, default=50,
                            help='Linear ramp epochs for GAT branch scale from 0->1. Set 0 to disable.')
        parser.add_argument('--mixer_gate_reg', type=float, default=0.0,
                            help='Regularization on mean gate value (encourages staying near baseline).')
        add_bool_arg(parser, '--mixer_disable_gat', default=False,
                     help='Force GAT branch contribution to 0 (MLP-only mixer ablation).')
        parser.add_argument('--mixer_gnn_lr_scale', type=float, default=0.1,
                            help='LR scale for GAT branch parameters relative to critic_lr.')
        parser.add_argument('--mixer_gate_lr_scale', type=float, default=0.1,
                            help='LR scale for gate parameters relative to critic_lr.')
        parser.add_argument('--mixer_weight_decay', type=float, default=1e-4,
                            help='Weight decay applied to GAT branch parameters (not MLP/gate).')

        # [Bus-level GNN encoder] (variable-length obs -> fixed embedding)
        parser.add_argument('--no_bus_gnn', action='store_true', default=False,
                            help='Disable bus-level local GNN encoder (bus_gnn).')
        parser.add_argument('--bus_gnn_embed_dim', type=int, default=32, help='Bus-GNN embedding dimension appended to obs.')
        parser.add_argument('--bus_gnn_hidden_dim', type=int, default=64, help='Bus-GNN hidden dimension.')
        parser.add_argument('--bus_gnn_layers', type=int, default=2, help='Bus-GNN message passing layers.')
        parser.add_argument('--bus_gnn_dropout', type=float, default=0.0, help='Bus-GNN dropout.')
        parser.add_argument('--bus_gnn_weight_mode', type=str, default='inv_z', choices=['inv_z','binary','count'],
                            help='Bus-GNN intra-area edge weights.')
        parser.add_argument('--bus_gnn_lr_scale', type=float, default=0.1,
                            help='LR scale for bus-GNN parameters relative to critic_lr.')
        # [Bus-level GNN scope]
        # 'global' = Scheme-B: shared full-graph encoder + per-agent readout (recommended)
        # 'local'  = old behavior: per-area encoders (each agent only sees its subgraph)
        parser.add_argument('--bus_gnn_scope', type=str, default='global', choices=['global','local'],
                            help="Bus-GNN scope: global(shared full graph) or local(per-area).")
        add_bool_arg(parser, '--bus_gnn_use_base_topology', default=True,
                     help='Use base (pre-outage) topology to build bus-GNN adjacency (more stable with replay + outages).')

        # [Topology-aware federated aggregation]
        parser.add_argument('--fed_mode', type=str, default='none',
                            choices=['topo','fedavg','none','proto','topo_proto','consensus'],
                            help='Federated mixing strategy: baseline topo/FedAvg or FedGrid-style prototype-aware consensus.')
        parser.add_argument('--fed_round_every', type=int, default=1, help='Federated aggregation frequency (epochs).')
        parser.add_argument('--fed_alpha', type=float, default=1.0, help='Aggregation strength (0..1).')
        add_bool_arg(parser, '--fed_use_base_topology', default=True,
                     help='Use base topology (pre-outage) for weight matrix W. Recommended for stability.')
        parser.add_argument('--fed_topo_weight', type=float, default=0.45, help='Weight of topology similarity in federated aggregation.')
        parser.add_argument('--fed_proto_weight', type=float, default=0.35, help='Weight of prototype similarity in federated aggregation.')
        parser.add_argument('--fed_trust_weight', type=float, default=0.20, help='Weight of trust gating in federated aggregation.')
        parser.add_argument('--fed_stale_weight', type=float, default=0.10, help='Penalty weight for stale or low-trust clients.')
        parser.add_argument('--fed_proto_momentum', type=float, default=0.95, help='EMA momentum for client prototype tracking.')
        parser.add_argument('--fed_trust_temp', type=float, default=4.0, help='Temperature for trust score sharpening.')
        parser.add_argument('--fed_update_clip', type=float, default=0.15, help='Clip federated parameter delta norm as a ratio of source norm. 0 disables clipping.')
        parser.add_argument('--fed_trim_ratio', type=float, default=0.0, help='Drop the lowest-trust source fraction before aggregation. 0 disables trimming.')
        parser.add_argument('--fed_consensus_eta', type=float, default=0.50, help='Reserved coefficient for consensus-style aggregation variants.')
        parser.add_argument('--fed_proto_source', type=str, default='hybrid', choices=['obs','gnn','hybrid'],
                            help='Prototype source for federated similarity: raw observation stats, bus-GNN embeddings, or hybrid of both.')
        parser.add_argument('--fed_obs_proto_weight', type=float, default=0.35, help='Weight of raw observation prototypes inside the hybrid prototype bank.')
        parser.add_argument('--fed_gnn_proto_weight', type=float, default=0.65, help='Weight of bus-GNN embedding prototypes inside the hybrid prototype bank.')
        parser.add_argument('--fed_client_dropout', type=float, default=0.0, help='Fraction of clients that skip a federated round, simulating partial participation and communication failures.')
        parser.add_argument('--fed_dropout_seed', type=int, default=0, help='Seed offset for federated client dropout sampling.')
        add_bool_arg(parser, '--fed_freeze_inactive', default=True,
                     help='Freeze inactive clients during a federated round instead of updating them from active peers.')
        parser.add_argument('--fed_byzantine_frac', type=float, default=0.0, help='Fraction of active clients perturbed before aggregation to test robustness.')
        parser.add_argument('--fed_byzantine_mode', type=str, default='none', choices=['none','noise','signflip','scale'],
                            help='How to perturb Byzantine clients before aggregation.')
        parser.add_argument('--fed_byzantine_strength', type=float, default=0.5, help='Perturbation strength for Byzantine client simulation.')
        parser.add_argument('--fed_attack_seed', type=int, default=0, help='Seed offset for Byzantine client sampling / perturbation.')

        # [Topology change / outage settings]
        # NOTE: default to 'static' so running without flags reproduces the original (no-topology-shift) setting.
        parser.add_argument('--topology_mode', type=str, default='static', choices=['static','random_reset'],
                            help="Network topology mode. 'random_reset' applies random line outages on every reset.")
        parser.add_argument('--outage_k', type=int, default=None,
                            help="Number of line outages per episode when topology_mode=random_reset. If omitted, use paper-style defaults per case.")
        parser.add_argument('--outage_policy', type=str, default='local', choices=['global','local'],
            help="Outage sampling policy when topology_mode=random_reset. 'local' samples k line faults within an r-hop neighborhood (paper-style).")
        parser.add_argument('--outage_radius', type=int, default=2,
            help="Neighborhood radius (in hops) for outage_policy=local.")
        parser.add_argument('--avoid_slack_hops', type=int, default=1,
            help="Avoid faulting lines within <= this hop distance from the slack bus (reduces system-wide collapse).")
        parser.add_argument('--topology_seed', type=int, default=0,
                            help="Base seed for deterministic outage sampling (seed + episode_idx).")


        # [Disturbance scenarios (A/B/C): tidal / step / combined]
        parser.add_argument('--disturbance', type=str, default='none',
                            choices=['none','tidal','step','tidal_step'],
                            help="Disturbance mode: A=tidal, C=tidal_step. B is controlled by topology_mode/outages.")
        parser.add_argument('--reset_load_mode', type=str, default='keep', choices=['keep','base'],
                            help="Load reset mode: keep env.reset random jitter, or force base loads (deterministic).")
        # tidal params
        parser.add_argument('--tidal_period', type=int, default=96, help='Period (steps) for tidal profile.')
        parser.add_argument('--tidal_load_base', type=float, default=1.0, help='Baseline load scale for tidal.')
        parser.add_argument('--tidal_load_amp', type=float, default=0.2, help='Amplitude for tidal load scale.')
        parser.add_argument('--tidal_pv_base', type=float, default=1.0, help='Baseline PV availability scale for tidal.')
        parser.add_argument('--tidal_pv_amp', type=float, default=0.5, help='Amplitude for tidal PV availability scale.')
        parser.add_argument('--tidal_phase', type=float, default=0.0, help='Phase (radians) for tidal sinusoid.')
        # step params
        parser.add_argument('--step_t', type=int, default=24, help='Step time (step index) for step disturbance.')
        parser.add_argument('--step_factor', type=float, default=1.2, help='Multiplicative factor for step disturbance.')
        parser.add_argument('--step_target', type=str, default='random_agent',
                            choices=['all','random_agent','agent0','agent1','agent2','agent3'],
                            help='Where to apply the step disturbance (loads).')
        parser.add_argument('--dist_seed', type=int, default=0, help='Seed for selecting step target per episode (deterministic).')

        # [Context embedding]
        parser.add_argument('--no_context', action='store_true', default=False,
                            help="Disable global context embedding branch in the mixer.")

        args = parser.parse_args()

        # Disturbance settings
        self.disturbance = str(args.disturbance).lower()
        self.reset_load_mode = str(args.reset_load_mode).lower()
        self.tidal_period = int(args.tidal_period)
        self.tidal_load_base = float(args.tidal_load_base)
        self.tidal_load_amp = float(args.tidal_load_amp)
        self.tidal_pv_base = float(args.tidal_pv_base)
        self.tidal_pv_amp = float(args.tidal_pv_amp)
        self.tidal_phase = float(args.tidal_phase)
        self.step_t = int(args.step_t)
        self.step_factor = float(args.step_factor)
        self.step_target = str(args.step_target)
        self.dist_seed = int(args.dist_seed)
        self.case_name = args.case
        self.auto_alpha = args.auto_alpha
        self.init_alpha = args.init_alpha
        self.entropy_ratio = args.entropy_ratio
        self.grad_clip = args.grad_clip

        # Mixer stabilization
        self.mixer_node_feat = bool(args.mixer_node_feat)
        self.edge_drop = float(args.edge_drop)
        self.mixer_gnn_lr_scale = float(args.mixer_gnn_lr_scale)
        self.mixer_gate_lr_scale = float(args.mixer_gate_lr_scale)
        self.mixer_weight_decay = float(args.mixer_weight_decay)
        self.mixer_use_base_topology = bool(getattr(args, 'mixer_use_base_topology', True))
        self.mixer_gate_init_bias = float(getattr(args, 'mixer_gate_init_bias', -5.0))
        self.mixer_gat_ramp_epochs = int(getattr(args, 'mixer_gat_ramp_epochs', 0))
        self.mixer_gate_reg = float(getattr(args, 'mixer_gate_reg', 0.0))
        self.mixer_disable_gat = bool(getattr(args, 'mixer_disable_gat', False))

        # --- 自动配置默认参数 (与 train_fmasac.py 对齐) ---
        base_alr = 3e-4
        base_clr = 3e-4

        if self.case_name == '33':
            self.num_agents = 2; self.env_module = 'env_33'
            default_ep = 400; default_bs = 256; default_hd = 256
            default_alr = 3e-4; default_clr = 3e-4
            self.steps_per_epoch = 96
            self.gamma = 0.95

        elif self.case_name == '69':
            self.num_agents = 4; self.env_module = 'env_69'
            default_ep = 800; default_bs = 128; default_hd = 512
            default_alr = base_alr; default_clr = base_clr
            self.steps_per_epoch = 96
            self.gamma = 0.9

        elif self.case_name == '141':
            self.num_agents = 4; self.env_module = 'env_141'
            default_ep = 500; default_bs = 64; default_hd = 256
            default_alr = base_alr; default_clr = base_clr
            self.steps_per_epoch = 96
            self.gamma = 0.9

        elif self.case_name == 'ober':
            self.num_agents = 4; self.env_module = 'env_oberrhein'
            default_ep = 1000; default_bs = 256; default_hd = 512
            default_alr = base_alr; default_clr = base_clr
            self.steps_per_epoch = 96
            self.gamma = 0.9

        self.epochs = args.epochs if args.epochs is not None else default_ep
        self.batch_size = args.batch_size if args.batch_size is not None else default_bs
        self.hidden_dim = args.hidden_dim if args.hidden_dim is not None else default_hd
        self.actor_lr = args.actor_lr if args.actor_lr is not None else default_alr
        self.critic_lr = args.critic_lr if args.critic_lr is not None else default_clr
        self.val_episodes = args.val_episodes
        self.contiguous_partition = (not args.no_contiguous_partition)
        self.partition_seed = args.partition_seed
        self.adj_mode = args.adj_mode

        self.topology_mode = args.topology_mode
        # Paper-style defaults: 33/69 => 3 outages, 141/ober => 4 outages
        default_outage_k = 0
        if self.case_name in {'33','69'}:
            default_outage_k = 3
        elif self.case_name in {'141','ober'}:
            default_outage_k = 4
        self.outage_k = int(args.outage_k) if args.outage_k is not None else default_outage_k
        self.outage_policy = str(args.outage_policy).lower()
        self.outage_radius = int(args.outage_radius)
        self.avoid_slack_hops = int(args.avoid_slack_hops)
        self.topology_seed = int(args.topology_seed)

        self.use_context = (not args.no_context)

        # Bus-level encoder
        self.use_bus_gnn = (not args.no_bus_gnn)
        self.bus_gnn_embed_dim = int(args.bus_gnn_embed_dim)
        self.bus_gnn_hidden_dim = int(args.bus_gnn_hidden_dim)
        self.bus_gnn_layers = int(args.bus_gnn_layers)
        self.bus_gnn_dropout = float(args.bus_gnn_dropout)
        self.bus_gnn_weight_mode = str(args.bus_gnn_weight_mode)
        self.bus_gnn_lr_scale = float(args.bus_gnn_lr_scale)
        self.bus_gnn_scope = str(args.bus_gnn_scope).lower()
        self.bus_gnn_use_base_topology = bool(args.bus_gnn_use_base_topology)

        # Federated mixing
        self.fed_mode = str(args.fed_mode).lower()
        self.fed_round_every = int(args.fed_round_every)
        self.fed_alpha = float(args.fed_alpha)
        self.fed_use_base_topology = bool(args.fed_use_base_topology)
        self.fed_topo_weight = float(args.fed_topo_weight)
        self.fed_proto_weight = float(args.fed_proto_weight)
        self.fed_trust_weight = float(args.fed_trust_weight)
        self.fed_stale_weight = float(args.fed_stale_weight)
        self.fed_proto_momentum = float(args.fed_proto_momentum)
        self.fed_trust_temp = float(args.fed_trust_temp)
        self.fed_update_clip = float(args.fed_update_clip)
        self.fed_trim_ratio = float(args.fed_trim_ratio)
        self.fed_consensus_eta = float(args.fed_consensus_eta)
        self.fed_proto_source = str(args.fed_proto_source).lower()
        self.fed_obs_proto_weight = float(args.fed_obs_proto_weight)
        self.fed_gnn_proto_weight = float(args.fed_gnn_proto_weight)
        self.fed_client_dropout = float(args.fed_client_dropout)
        self.fed_dropout_seed = int(args.fed_dropout_seed)
        self.fed_freeze_inactive = bool(args.fed_freeze_inactive)
        self.fed_byzantine_frac = float(args.fed_byzantine_frac)
        self.fed_byzantine_mode = str(args.fed_byzantine_mode).lower()
        self.fed_byzantine_strength = float(args.fed_byzantine_strength)
        self.fed_attack_seed = int(args.fed_attack_seed)

        self.tau = 0.005

        self.buffer_size = 100000
        self.start_steps = 2000
        self.update_after = 2000
        self.update_every = 50
        self.update_times = 50

        self.log_dir = str(args.log_dir)
        self.save_dir = str(args.save_dir)
        self.exp_name = str(args.exp_name).strip()
        self.exp_tag = re.sub(r"[^A-Za-z0-9._-]+", "_", self.exp_name).strip("._-") if self.exp_name else ''
        self.val_interval = 5

        if torch.cuda.is_available():
            self.device = torch.device(f"cuda:{args.gpu}")
        else:
            self.device = torch.device("cpu")

def validate(env, actors, bus_encoders, opts, step, tb_logger):
    """Deterministic evaluation.
    NOTE: LocalActor.forward() returns (mean, log_std). We must tanh(mean) to get a valid action.
    """
    avg_ret = 0.0
    for _ in range(opts.val_episodes):
        obs_list = env.reset()
        refresh_bus_encoders(env, bus_encoders)
        ep_ret = 0

        for _ in range(opts.steps_per_epoch):
            actions = []
            with torch.no_grad():
                obs_tensors = [torch.FloatTensor(obs_list[i]).unsqueeze(0).to(opts.device) for i in range(opts.num_agents)]
                z_list = compute_bus_embeddings(bus_encoders, obs_tensors, detach=True) if (opts.use_bus_gnn and bus_encoders is not None) else None
                for i in range(opts.num_agents):
                    o_raw = obs_tensors[i]
                    if z_list is not None:
                        o = torch.cat([o_raw, z_list[i]], dim=1)
                    else:
                        o = o_raw
                    mean, _ = actors[i].forward(o)
                    a = torch.tanh(mean)  # deterministic action in [-1, 1]
                    actions.append(a.cpu().numpy()[0])

            next_obs, rewards, done, _ = env.step(actions)
            obs_list = next_obs
            ep_ret += sum(rewards)
            if done:
                break

        avg_ret += ep_ret

    avg_ret /= opts.val_episodes

    if tb_logger:
        tb_logger.add_scalar('validate/return', avg_ret, step)
        tb_logger.flush()
    return avg_ret

def main():
    opts = Opts()
    
    try:
        dist_net_module = importlib.import_module(opts.env_module)
        DistNetEnv = dist_net_module.DistNetEnv
    except ImportError as e:
        print(f"Error loading {opts.env_module}: {e}")
        return

    run_id = time.strftime("%Y%m%d-%H%M%S")
    if opts.exp_tag:
        log_name = f"GNN-FMASAC_{opts.exp_tag}_{run_id}"
    else:
        log_name = f"GNN-FMASAC_{opts.case_name}_{run_id}"
    log_path = os.path.join(opts.log_dir, log_name)
    tb_logger = SummaryWriter(log_path)
    
    print("=" * 60)
    print(f"🚀 Start Training GNN-FMASAC: {opts.case_name}")
    print(f"   Architecture: Graph Convolutional Mixer (Topology Aware)")
    print(f"   Batch={opts.batch_size}, ActorLR={opts.actor_lr}, CriticLR={opts.critic_lr}, Gamma={opts.gamma}")
    print("=" * 60)
    
    env_kwargs = dict(
        num_agents=opts.num_agents,
        topology_mode=opts.topology_mode,
        outage_k=opts.outage_k,
        outage_policy=opts.outage_policy,
        outage_radius=opts.outage_radius,
        avoid_slack_hops=opts.avoid_slack_hops,
        topology_seed=opts.topology_seed,
    )
    try:
        env = DistNetEnv(**env_kwargs, contiguous_partition=opts.contiguous_partition, partition_seed=opts.partition_seed)
    except TypeError:
        env = DistNetEnv(**env_kwargs)
    val_env_kwargs = dict(
        num_agents=opts.num_agents,
        topology_mode=opts.topology_mode,
        outage_k=opts.outage_k,
        outage_policy=opts.outage_policy,
        outage_radius=opts.outage_radius,
        avoid_slack_hops=opts.avoid_slack_hops,
        topology_seed=opts.topology_seed,
    )
    try:
        val_env = DistNetEnv(**val_env_kwargs, contiguous_partition=opts.contiguous_partition, partition_seed=opts.partition_seed)
    except TypeError:
        val_env = DistNetEnv(**val_env_kwargs)
    
    print("[GNN] Building agent adjacency for GraphMixer...")
    be0 = _base_env(env)
    if getattr(opts, 'mixer_use_base_topology', True) and hasattr(be0, 'net_orig'):
        net_for_adj0 = be0.net_orig
    else:
        net_for_adj0 = be0.net
    adj_matrix = get_agent_adjacency(net_for_adj0, be0.areas, device=opts.device, mode=opts.adj_mode)
    

    # --- Disturbance wrapper (A/B/C scenarios) ---
    if getattr(opts, 'disturbance', 'none') != 'none':
        from scenario_env import DisturbanceConfig, ScenarioWrapper
        cfg = DisturbanceConfig(
            mode=opts.disturbance,
            tidal_period=getattr(opts, 'tidal_period', 96),
            tidal_load_base=getattr(opts, 'tidal_load_base', 1.0),
            tidal_load_amp=getattr(opts, 'tidal_load_amp', 0.2),
            tidal_pv_base=getattr(opts, 'tidal_pv_base', 1.0),
            tidal_pv_amp=getattr(opts, 'tidal_pv_amp', 0.5),
            tidal_phase=getattr(opts, 'tidal_phase', 0.0),
            step_t=getattr(opts, 'step_t', 24),
            step_factor=getattr(opts, 'step_factor', 1.2),
            step_target=getattr(opts, 'step_target', 'random_agent'),
            dist_seed=getattr(opts, 'dist_seed', 0),
            reset_load_mode=getattr(opts, 'reset_load_mode', 'keep'),
            recompute_on_reset=True,
        )
        env = ScenarioWrapper(env, cfg)
        val_env = ScenarioWrapper(val_env, cfg)

    obs_dims = [space.shape[0] for space in env.observation_space]
    act_dims = [space.shape[0] for space in env.action_space]

        # =============== Structure-1: bus-level GNN encoder ===============
    # Scheme-B (recommended): one shared encoder on the *full* bus graph + per-agent readout.
    if opts.use_bus_gnn:
        if getattr(opts, 'bus_gnn_scope', 'global') == 'global':
            bus_encoders = build_global_bus_encoder(
                env,
                device=opts.device,
                embed_dim=opts.bus_gnn_embed_dim,
                hidden_dim=opts.bus_gnn_hidden_dim,
                num_layers=opts.bus_gnn_layers,
                dropout=opts.bus_gnn_dropout,
                weight_mode=getattr(opts, 'bus_gnn_weight_mode', 'inv_z'),
                use_base_topology=getattr(opts, 'bus_gnn_use_base_topology', True),
            )
            target_bus_encoders = build_global_bus_encoder(
                env,
                device=opts.device,
                embed_dim=opts.bus_gnn_embed_dim,
                hidden_dim=opts.bus_gnn_hidden_dim,
                num_layers=opts.bus_gnn_layers,
                dropout=opts.bus_gnn_dropout,
                weight_mode=getattr(opts, 'bus_gnn_weight_mode', 'inv_z'),
                use_base_topology=getattr(opts, 'bus_gnn_use_base_topology', True),
            )
            target_bus_encoders.load_state_dict(bus_encoders.state_dict(), strict=False)
        else:
            # Legacy: per-area encoders (each agent only sees its local subgraph)
            bus_encoders = build_bus_encoders(
                _base_env(env).net,
                _base_env(env).areas,
                device=opts.device,
                embed_dim=opts.bus_gnn_embed_dim,
                hidden_dim=opts.bus_gnn_hidden_dim,
                num_layers=opts.bus_gnn_layers,
                dropout=opts.bus_gnn_dropout,
                weight_mode=getattr(opts, 'bus_gnn_weight_mode', 'inv_z'),
            )
            target_bus_encoders = build_bus_encoders(
                _base_env(env).net,
                _base_env(env).areas,
                device=opts.device,
                embed_dim=opts.bus_gnn_embed_dim,
                hidden_dim=opts.bus_gnn_hidden_dim,
                num_layers=opts.bus_gnn_layers,
                dropout=opts.bus_gnn_dropout,
                weight_mode=getattr(opts, 'bus_gnn_weight_mode', 'inv_z'),
            )
            for te, e in zip(target_bus_encoders, bus_encoders):
                te.load_state_dict(e.state_dict(), strict=False)

        obs_dims_aug = [int(d) + int(opts.bus_gnn_embed_dim) for d in obs_dims]
    else:
        bus_encoders = None
        target_bus_encoders = None
        obs_dims_aug = [int(d) for d in obs_dims]

    actors = [LocalActor(o, a, hidden_dim=opts.hidden_dim).to(opts.device) for o, a in zip(obs_dims_aug, act_dims)]
    critics = [LocalCritic(o, a, hidden_dim=opts.hidden_dim).to(opts.device) for o, a in zip(obs_dims_aug, act_dims)]
    target_critics = [LocalCritic(o, a, hidden_dim=opts.hidden_dim).to(opts.device) for o, a in zip(obs_dims_aug, act_dims)]
    proto_source = str(getattr(opts, 'fed_proto_source', 'hybrid')).lower()
    obs_proto_weight = float(getattr(opts, 'fed_obs_proto_weight', 0.35)) if proto_source in {'obs', 'hybrid'} else 0.0
    gnn_proto_weight = float(getattr(opts, 'fed_gnn_proto_weight', 0.65)) if (proto_source in {'gnn', 'hybrid'} and opts.use_bus_gnn and bus_encoders is not None) else 0.0
    if proto_source == 'obs':
        obs_proto_weight, gnn_proto_weight = 1.0, 0.0
    elif proto_source == 'gnn' and gnn_proto_weight > 0.0:
        obs_proto_weight, gnn_proto_weight = 0.0, 1.0
    elif gnn_proto_weight <= 0.0 and obs_proto_weight <= 0.0:
        obs_proto_weight, gnn_proto_weight = 1.0, 0.0
    proto_bank = HybridPrototypeBank(
        opts.num_agents,
        obs_feature_dim=8,
        gnn_feature_dim=max(1, int(getattr(opts, 'bus_gnn_embed_dim', 32))),
        momentum=float(getattr(opts, 'fed_proto_momentum', 0.95)),
        obs_weight=obs_proto_weight,
        gnn_weight=gnn_proto_weight,
    )
    fed_last_stats = {}
    fed_staleness = torch.zeros(opts.num_agents, dtype=torch.float32)
    fed_dropout_rng = np.random.RandomState(int(getattr(opts, 'topology_seed', 0)) + 997 * int(getattr(opts, 'fed_dropout_seed', 0)) + 17)
    fed_attack_rng = np.random.RandomState(int(getattr(opts, 'topology_seed', 0)) + 1499 * int(getattr(opts, 'fed_attack_seed', 0)) + 29)
    
    # 使用 GraphMixer
    # GAT branch scale scheduling: start from near-MLP and ramp up for stability
    if getattr(opts, 'mixer_disable_gat', False):
        init_gat_scale = 0.0
    else:
        init_gat_scale = 0.0 if int(getattr(opts, 'mixer_gat_ramp_epochs', 0)) > 0 else 1.0

    mixer_dim = 64 if opts.hidden_dim < 256 else 128
    ctx_dim = 4 if opts.use_context else 0
    node_feat_dim = 5 if getattr(opts, 'mixer_node_feat', False) else 0
    mixer = GraphMixer(
        opts.num_agents,
        adj_matrix,
        hidden_dim=mixer_dim,
        id_dim=8,
        node_feat_dim=node_feat_dim,
        dropout=0.0,
        ctx_dim=ctx_dim,
        edge_drop=getattr(opts, 'edge_drop', 0.0),
        gate_init_bias=float(getattr(opts, 'mixer_gate_init_bias', -5.0)),
        gat_scale_init=float(init_gat_scale),
    ).to(opts.device)
    target_mixer = GraphMixer(
        opts.num_agents,
        adj_matrix,
        hidden_dim=mixer_dim,
        id_dim=8,
        node_feat_dim=node_feat_dim,
        dropout=0.0,
        ctx_dim=ctx_dim,
        edge_drop=getattr(opts, 'edge_drop', 0.0),
        gate_init_bias=float(getattr(opts, 'mixer_gate_init_bias', -5.0)),
        gat_scale_init=float(init_gat_scale),
    ).to(opts.device)
    
    if opts.auto_alpha:
        target_entropy = -np.mean(act_dims) * opts.entropy_ratio
        log_alpha = torch.zeros(1, requires_grad=True, device=opts.device)
        with torch.no_grad():
            log_alpha.fill_(np.log(opts.init_alpha))
        alpha_optim = optim.Adam([log_alpha], lr=opts.actor_lr)
    else:
        alpha_val = opts.init_alpha
    
    actor_optims = [optim.Adam(a.parameters(), lr=opts.actor_lr) for a in actors]
    critic_optims = [optim.Adam(c.parameters(), lr=opts.critic_lr) for c in critics]

    # Bus-GNN optimizers (learn a bit slower than the critic by default)
    if bus_encoders is not None:
        enc_lr = float(opts.critic_lr) * float(getattr(opts, 'bus_gnn_lr_scale', 0.3))
        if isinstance(bus_encoders, GlobalBusGCNEncoder):
            enc_optims = [optim.Adam(bus_encoders.parameters(), lr=enc_lr)]
        else:
            enc_optims = [optim.Adam(e.parameters(), lr=enc_lr) for e in bus_encoders]
    else:
        enc_optims = []
    # Mixer uses per-branch LR scaling for stability (GAT/gate learn slower than the MLP branch)
    mixer_optim = optim.Adam(
        mixer.param_groups(
            base_lr=opts.critic_lr,
            gnn_lr_scale=getattr(opts, 'mixer_gnn_lr_scale', 0.3),
            gate_lr_scale=getattr(opts, 'mixer_gate_lr_scale', 0.3),
            weight_decay=getattr(opts, 'mixer_weight_decay', 0.0),
        )
    )
    
    actor_schedulers = [CosineAnnealingLR(opt, T_max=opts.epochs, eta_min=opts.actor_lr * 0.01) for opt in actor_optims]
    critic_schedulers = [CosineAnnealingLR(opt, T_max=opts.epochs, eta_min=opts.critic_lr * 0.01) for opt in critic_optims]

    if enc_optims:
        enc_schedulers = [CosineAnnealingLR(opt, T_max=opts.epochs, eta_min=(opt.param_groups[0]['lr'] * 0.01)) for opt in enc_optims]
    else:
        enc_schedulers = []
    mixer_scheduler = CosineAnnealingLR(mixer_optim, T_max=opts.epochs, eta_min=opts.critic_lr * 0.01)
    if opts.auto_alpha:
        alpha_scheduler = CosineAnnealingLR(alpha_optim, T_max=opts.epochs, eta_min=opts.actor_lr * 0.01)
    
    hard_update(target_mixer, mixer)
    for tc, c in zip(target_critics, critics):
        hard_update(tc, c)
        
    buffer = MultiAgentReplayBuffer(opts.buffer_size, opts.num_agents, obs_dims, act_dims, ctx_dim=ctx_dim)
    best_ret = -float('inf')
    total_steps = 0
    
    # ================= 训练循环 =================
    for epoch in range(opts.epochs):
        obs_list = env.reset()
        # Topology may change on reset (random outages) -> refresh adjacency
        refresh_adjacency(env, mixer, target_mixer, opts)
        refresh_bus_encoders(env, bus_encoders, target_bus_encoders)
        # Ramp the topology-aware GAT branch gradually (stabilizes SAC)
        if getattr(opts, 'mixer_disable_gat', False):
            gat_scale = 0.0
        else:
            r = int(getattr(opts, 'mixer_gat_ramp_epochs', 0))
            gat_scale = min(1.0, max(0.0, float(epoch) / float(r))) if r > 0 else 1.0
        mixer.set_gat_scale(gat_scale)
        target_mixer.set_gat_scale(gat_scale)
        epoch_loss_sum = 0.0
        epoch_critic_loss_sum = 0.0 # [新增] 记录 Critic Loss
        epoch_gate_mean_sum = 0.0
        epoch_gate_mean_cnt = 0
        epoch_vviol_lin_sum = 0.0
        epoch_vviol_sq_sum = 0.0
        epoch_ncomp_sum = 0.0
        current_ep_reward = 0
        finished_ep_rewards = []
        update_counts = 0
        
        for t in range(opts.steps_per_epoch):
            actions = []
            
            if total_steps < opts.start_steps:
                for i in range(opts.num_agents):
                    actions.append(env.action_space[i].sample())
            else:
                with torch.no_grad():
                    obs_tensors = [torch.FloatTensor(obs_list[i]).unsqueeze(0).to(opts.device) for i in range(opts.num_agents)]
                    z_list = compute_bus_embeddings(bus_encoders, obs_tensors, detach=True) if (opts.use_bus_gnn and bus_encoders is not None) else None
                    for i in range(opts.num_agents):
                        o_raw = obs_tensors[i]
                        if z_list is not None:
                            o = torch.cat([o_raw, z_list[i]], dim=1)
                        else:
                            o = o_raw
                        a, _ = actors[i].sample(o)
                        actions.append(a.cpu().numpy()[0])
            
            # Context features for this transition (global, shared across agents)
            if opts.use_context:
                with torch.no_grad():
                    ctx = context_from_obs_list([torch.FloatTensor(x) for x in obs_list]).squeeze(0).cpu().numpy()
            else:
                ctx = None

            next_obs, rewards, done, info = env.step(actions)
            if getattr(opts, 'fed_proto_source', 'hybrid') in {'obs', 'hybrid'}:
                proto_bank.update_from_obs_list(obs_list)
            if getattr(opts, 'fed_proto_source', 'hybrid') in {'gnn', 'hybrid'} and opts.use_bus_gnn and bus_encoders is not None:
                with torch.no_grad():
                    proto_obs_tensors = [torch.FloatTensor(obs_list[i]).unsqueeze(0).to(opts.device) for i in range(opts.num_agents)]
                    proto_z_list = compute_bus_embeddings(bus_encoders, proto_obs_tensors, detach=True)
                if proto_z_list is not None:
                    proto_bank.update_from_embeddings(proto_z_list)
            proto_bank.update_rewards(rewards)

            if opts.use_context:
                with torch.no_grad():
                    next_ctx = context_from_obs_list([torch.FloatTensor(x) for x in next_obs]).squeeze(0).cpu().numpy()
            else:
                next_ctx = None
            
            if "p_loss" in info: epoch_loss_sum += info["p_loss"]
            if "v_viol_lin_total" in info: epoch_vviol_lin_sum += float(info["v_viol_lin_total"])
            if "v_viol_sq_total" in info: epoch_vviol_sq_sum += float(info["v_viol_sq_total"])
            if "n_components" in info: epoch_ncomp_sum += float(info["n_components"])
            current_ep_reward += sum(rewards)

            buffer.add(obs_list, actions, rewards, next_obs, done, ctx=ctx, next_ctx=next_ctx)
            obs_list = next_obs
            total_steps += 1
            
            if done:
                obs_list = env.reset()
                refresh_adjacency(env, mixer, target_mixer, opts)
                refresh_bus_encoders(env, bus_encoders, target_bus_encoders)
                finished_ep_rewards.append(current_ep_reward)
                current_ep_reward = 0
            
            if total_steps > opts.update_after and total_steps % opts.update_every == 0:
                for _ in range(opts.update_times):
                    update_counts += 1
                    if opts.use_context:
                        b_obs, b_act, b_rew, b_next_obs, b_done, b_ctx, b_next_ctx = buffer.sample(opts.batch_size)
                        b_ctx = b_ctx.to(opts.device)
                        b_next_ctx = b_next_ctx.to(opts.device)
                    else:
                        b_obs, b_act, b_rew, b_next_obs, b_done = buffer.sample(opts.batch_size)
                        b_ctx = None
                        b_next_ctx = None
                    b_obs = [x.to(opts.device) for x in b_obs]
                    b_act = [x.to(opts.device) for x in b_act]
                    b_rew = b_rew.to(opts.device)
                    b_next_obs = [x.to(opts.device) for x in b_next_obs]
                    b_done = b_done.to(opts.device)
                    
                    if opts.auto_alpha:
                        alpha = log_alpha.exp()
                    else:
                        alpha = opts.init_alpha

                    # Per-agent node features for the mixer (derived from observations)
                    if getattr(opts, 'mixer_node_feat', False):
                        node_feat = agent_node_features_from_obs_list(b_obs)
                        node_feat_next = agent_node_features_from_obs_list(b_next_obs)
                    else:
                        node_feat = None
                        node_feat_next = None
                    
                    # --- Critic 更新 ---
                    # Build augmented observations for actor/critic with bus-level encoder
                    if opts.use_bus_gnn and bus_encoders is not None:
                        # Scheme-B: global encoder returns z_list for all agents at once
                        b_obs_c, b_obs_a = [], []
                        b_next_obs_policy, b_next_obs_target = [], []
                        z_c_list = compute_bus_embeddings(bus_encoders, b_obs, detach=False)
                        for i in range(opts.num_agents):
                            z_c = z_c_list[i]  # grads -> encoder updated via critic loss
                            b_obs_c.append(torch.cat([b_obs[i], z_c], dim=1))
                            b_obs_a.append(torch.cat([b_obs[i], z_c.detach()], dim=1))
                        with torch.no_grad():
                            z_pol_list = compute_bus_embeddings(bus_encoders, b_next_obs, detach=False)
                            z_tgt_list = compute_bus_embeddings(target_bus_encoders, b_next_obs, detach=False) if target_bus_encoders is not None else z_pol_list
                            for i in range(opts.num_agents):
                                b_next_obs_policy.append(torch.cat([b_next_obs[i], z_pol_list[i]], dim=1))
                                b_next_obs_target.append(torch.cat([b_next_obs[i], z_tgt_list[i]], dim=1))
                    else:
                        b_obs_c = b_obs
                        b_obs_a = b_obs
                        b_next_obs_policy = b_next_obs
                        b_next_obs_target = b_next_obs

                    with torch.no_grad():
                        tc_list, te_list, next_lp_list = [], [], []
                        for i in range(opts.num_agents):
                            na, nlp = actors[i].sample(b_next_obs_policy[i])
                            tc, te = target_critics[i](b_next_obs_target[i], na)
                            tc_list.append(tc); te_list.append(te); next_lp_list.append(nlp)
                        
                        tf = target_mixer(torch.cat(tc_list, dim=1), ctx=b_next_ctx, node_feat=node_feat_next)
                        q_next = tf + sum(te_list) - alpha * sum(next_lp_list)
                        q_target = b_rew.sum(1, keepdim=True) + opts.gamma * (1-b_done) * q_next
                    
                    lc_list, le_list = [], []
                    for i in range(opts.num_agents):
                        c, e = critics[i](b_obs_c[i], b_act[i])
                        lc_list.append(c); le_list.append(e)
                    
                    q_pred = mixer(torch.cat(lc_list, dim=1), ctx=b_ctx, node_feat=node_feat) + sum(le_list)
                    loss_q = F.mse_loss(q_pred, q_target)
                    epoch_critic_loss_sum += loss_q.item() # [记录]
                    
                    mixer_optim.zero_grad()
                    for opt in critic_optims: opt.zero_grad()
                    for opt in enc_optims: opt.zero_grad()
                    loss_q.backward()
                    
                    if opts.grad_clip > 0:
                        torch.nn.utils.clip_grad_norm_(mixer.parameters(), opts.grad_clip)
                        for c in critics:
                            torch.nn.utils.clip_grad_norm_(c.parameters(), opts.grad_clip)
                        # Scheme-B global encoder is a single nn.Module, not a list
                        if bus_encoders is not None:
                            if isinstance(bus_encoders, GlobalBusGCNEncoder):
                                torch.nn.utils.clip_grad_norm_(bus_encoders.parameters(), opts.grad_clip)
                            else:
                                for e in bus_encoders:
                                    torch.nn.utils.clip_grad_norm_(e.parameters(), opts.grad_clip)
                            
                    mixer_optim.step()
                    for opt in critic_optims: opt.step()
                    for opt in enc_optims: opt.step()
                    
                    # --- Actor 更新 ---
                    current_log_prob_sum = 0
                    for i in range(opts.num_agents):
                        curr_a, curr_lp = actors[i].sample(b_obs_a[i])
                        current_log_prob_sum += curr_lp.mean()
                        
                        c_new, e_new = critics[i](b_obs_a[i], curr_a)
                        c_inputs = [c.detach() for c in lc_list]
                        c_inputs[i] = c_new
                        
                        f_val = mixer(torch.cat(c_inputs, dim=1), ctx=b_ctx, node_feat=node_feat)
                        
                        loss_actor = - (f_val + e_new - alpha.detach() * curr_lp).mean()
                        
                        actor_optims[i].zero_grad()
                        loss_actor.backward()
                        if opts.grad_clip > 0:
                            torch.nn.utils.clip_grad_norm_(actors[i].parameters(), opts.grad_clip)
                        actor_optims[i].step()
                        
                    # --- Alpha 更新 ---
                    if opts.auto_alpha:
                        avg_log_prob = current_log_prob_sum / opts.num_agents
                        alpha_loss = -(log_alpha * (avg_log_prob.detach() + target_entropy)).mean()
                        alpha_optim.zero_grad()
                        alpha_loss.backward()
                        alpha_optim.step()
                        with torch.no_grad():
                            log_alpha.clamp_(min=-3.0)

                    # Soft Update
                    for i in range(opts.num_agents):
                        soft_update(target_critics[i], critics[i], opts.tau)
                    soft_update(target_mixer, mixer, opts.tau)
                    if target_bus_encoders is not None and bus_encoders is not None:
                        if isinstance(bus_encoders, GlobalBusGCNEncoder):
                            soft_update(target_bus_encoders, bus_encoders, opts.tau)
                        else:
                            for te, e in zip(target_bus_encoders, bus_encoders):
                                soft_update(te, e, opts.tau)
        
        # Scheduler
        for sched in actor_schedulers: sched.step()
        for sched in critic_schedulers: sched.step()
        for sched in enc_schedulers: sched.step()
        mixer_scheduler.step()
        if opts.auto_alpha: alpha_scheduler.step()
        
        # Logging
        avg_loss_mw = epoch_loss_sum / opts.steps_per_epoch
        if len(finished_ep_rewards) > 0:
            avg_ep_reward = np.mean(finished_ep_rewards)
        else:
            avg_ep_reward = current_ep_reward
            
        avg_critic_loss = epoch_critic_loss_sum / update_counts if update_counts > 0 else 0.0
        current_alpha_val = log_alpha.exp().item() if opts.auto_alpha else opts.init_alpha

        # [全面对齐 Tag]
        tb_logger.add_scalar('train/loss_mw', avg_loss_mw, epoch)
        tb_logger.add_scalar('train/epoch_reward', avg_ep_reward, epoch)
        tb_logger.add_scalar('train/v_viol_lin_mean', epoch_vviol_lin_sum / opts.steps_per_epoch, epoch)
        tb_logger.add_scalar('train/v_viol_sq_mean', epoch_vviol_sq_sum / opts.steps_per_epoch, epoch)
        tb_logger.add_scalar('train/n_components_mean', epoch_ncomp_sum / opts.steps_per_epoch, epoch)
        tb_logger.add_scalar('train/alpha', current_alpha_val, epoch)
        tb_logger.add_scalar('train/mixer_gat_scale', float(getattr(mixer, 'gat_scale', torch.tensor(1.0)).item()), epoch)
        if epoch_gate_mean_cnt > 0:
            tb_logger.add_scalar('train/mixer_gate_mean', epoch_gate_mean_sum / float(epoch_gate_mean_cnt), epoch)
        tb_logger.add_scalar('train/actor_lr', actor_schedulers[0].get_last_lr()[0], epoch)
        tb_logger.add_scalar('train/critic_lr', mixer_scheduler.get_last_lr()[0], epoch) # [找回LR]
        tb_logger.add_scalar('train/loss_critic', avg_critic_loss, epoch) # [新增CriticLoss]
        if fed_last_stats:
            tb_logger.add_scalar('fed/weight_entropy', float(fed_last_stats.get('weight_entropy', 0.0)), epoch)
            tb_logger.add_scalar('fed/proto_sim_mean', float(fed_last_stats.get('proto_sim_mean', 0.0)), epoch)
            tb_logger.add_scalar('fed/topo_sim_mean', float(fed_last_stats.get('topo_sim_mean', 0.0)), epoch)
            tb_logger.add_scalar('fed/trust_mean', float(fed_last_stats.get('trust_mean', 0.0)), epoch)
            tb_logger.add_scalar('fed/trust_min', float(fed_last_stats.get('trust_min', 0.0)), epoch)
            tb_logger.add_scalar('fed/trust_max', float(fed_last_stats.get('trust_max', 0.0)), epoch)
            tb_logger.add_scalar('fed/proto_drift', float(fed_last_stats.get('proto_drift', 0.0)), epoch)
            tb_logger.add_scalar('fed/stale_mean', float(fed_last_stats.get('stale_mean', 0.0)), epoch)
            tb_logger.add_scalar('fed/active_frac', float(fed_last_stats.get('active_frac', 1.0)), epoch)
            tb_logger.add_scalar('fed/byzantine_count', float(fed_last_stats.get('byzantine_count', 0.0)), epoch)
            
        tb_logger.flush()
        
        status_msg = "WARMUP" if total_steps < opts.start_steps else "TRAIN"
        print(
            f"Epoch {epoch} [{status_msg}]: RewardSum {avg_ep_reward:.2f} | Reward/Step {avg_ep_reward/opts.steps_per_epoch:.2f}, "
            f"Loss {avg_loss_mw:.4f} MW, Alpha {current_alpha_val:.3f}"
        )
        
        # =============== Structure-2: FedGrid-v2 federated aggregation ===============
        if opts.fed_mode != 'none' and opts.fed_round_every > 0 and ((epoch + 1) % opts.fed_round_every == 0):
            active_mask = sample_active_clients(
                opts.num_agents,
                float(getattr(opts, 'fed_client_dropout', 0.0)),
                rng=fed_dropout_rng,
            )
            active_ids = [int(i) for i, flag in enumerate(active_mask.tolist()) if bool(flag)]

            byzantine_ids = []
            byz_mode = str(getattr(opts, 'fed_byzantine_mode', 'none')).lower()
            byz_frac = float(getattr(opts, 'fed_byzantine_frac', 0.0))
            if byz_mode != 'none' and byz_frac > 0.0:
                byzantine_ids = select_byzantine_clients(active_mask, byz_frac, rng=fed_attack_rng)
                if byzantine_ids:
                    attack_seed = int(fed_attack_rng.randint(0, 2**31 - 1))
                    inject_module_perturbation(
                        actors,
                        byzantine_ids,
                        mode=byz_mode,
                        strength=float(getattr(opts, 'fed_byzantine_strength', 0.5)),
                        exclude_prefixes=('l1.', 'mean_layer.', 'log_std_layer.'),
                        seed=attack_seed,
                    )
                    inject_module_perturbation(
                        critics,
                        byzantine_ids,
                        mode=byz_mode,
                        strength=float(getattr(opts, 'fed_byzantine_strength', 0.5)),
                        exclude_prefixes=('l1.', 'c_head.', 'e_head.'),
                        seed=attack_seed + 1,
                    )
                    if bus_encoders is not None and (not isinstance(bus_encoders, GlobalBusGCNEncoder)):
                        inject_module_perturbation(
                            bus_encoders,
                            byzantine_ids,
                            mode=byz_mode,
                            strength=float(getattr(opts, 'fed_byzantine_strength', 0.5)),
                            exclude_keys=('adj_norm',),
                            seed=attack_seed + 2,
                        )

            be = _base_env(env)
            if bool(getattr(opts, 'fed_use_base_topology', True)) and hasattr(be, 'net_orig'):
                net_for_w = be.net_orig
            else:
                net_for_w = be.net
            with torch.no_grad():
                W_topo = get_agent_adjacency(net_for_w, be.areas, device='cpu', mode=opts.adj_mode)
                if opts.fed_mode == 'fedavg':
                    W_topo = torch.ones_like(W_topo)
                W, fed_stats = build_federated_weight_matrix(
                    topology_w=W_topo,
                    prototype_bank=proto_bank,
                    actor_modules=actors,
                    critic_modules=critics,
                    mode=opts.fed_mode,
                    reward_ema=getattr(proto_bank, 'reward_ema', None),
                    staleness=fed_staleness,
                    topo_weight=float(getattr(opts, 'fed_topo_weight', 0.45)),
                    proto_weight=float(getattr(opts, 'fed_proto_weight', 0.35)),
                    trust_weight=float(getattr(opts, 'fed_trust_weight', 0.20)),
                    stale_weight=float(getattr(opts, 'fed_stale_weight', 0.10)),
                    trust_temperature=float(getattr(opts, 'fed_trust_temp', 4.0)),
                    active_mask=active_mask,
                    consensus_eta=float(getattr(opts, 'fed_consensus_eta', 0.50)),
                )
                W = apply_participation_mask(
                    W,
                    active_mask,
                    freeze_inactive=bool(getattr(opts, 'fed_freeze_inactive', True)),
                )
                fed_last_stats = dict(fed_stats)
                fed_last_stats['active_frac'] = float(active_mask.float().mean().item())
                fed_last_stats['active_count'] = float(active_mask.float().sum().item())
                fed_last_stats['active_ids'] = active_ids
                fed_last_stats['byzantine_count'] = float(len(byzantine_ids))
                fed_last_stats['byzantine_ids'] = byzantine_ids
                trust_vec = fed_stats.get('trust_vector', torch.ones(opts.num_agents))
                trust_vec = trust_vec.detach().float().cpu()
                next_staleness = fed_staleness + 1.0
                if active_ids:
                    active_tensor = active_mask.to(dtype=torch.bool)
                    active_trust = trust_vec[active_tensor]
                    trust_threshold = float(torch.median(active_trust).item()) if active_trust.numel() > 0 else float(torch.median(trust_vec).item())
                    reset_mask = active_tensor & (trust_vec >= trust_threshold)
                    next_staleness = torch.where(reset_mask, torch.zeros_like(next_staleness), next_staleness)
                fed_staleness = next_staleness

            if bus_encoders is not None and (not isinstance(bus_encoders, GlobalBusGCNEncoder)):
                adaptive_parameter_mix(
                    bus_encoders, W, alpha=float(opts.fed_alpha),
                    exclude_keys=('adj_norm',),
                    active_mask=active_mask,
                    update_clip=float(getattr(opts, 'fed_update_clip', 0.0)),
                    trim_ratio=float(getattr(opts, 'fed_trim_ratio', 0.0)),
                    source_gate=fed_stats.get('trust_vector', None),
                )

            adaptive_parameter_mix(
                actors, W, alpha=float(opts.fed_alpha),
                exclude_prefixes=('l1.', 'mean_layer.', 'log_std_layer.'),
                active_mask=active_mask,
                update_clip=float(getattr(opts, 'fed_update_clip', 0.0)),
                trim_ratio=float(getattr(opts, 'fed_trim_ratio', 0.0)),
                source_gate=fed_stats.get('trust_vector', None),
            )
            adaptive_parameter_mix(
                critics, W, alpha=float(opts.fed_alpha),
                exclude_prefixes=('l1.', 'c_head.', 'e_head.'),
                active_mask=active_mask,
                update_clip=float(getattr(opts, 'fed_update_clip', 0.0)),
                trim_ratio=float(getattr(opts, 'fed_trim_ratio', 0.0)),
                source_gate=fed_stats.get('trust_vector', None),
            )

            for tc, c in zip(target_critics, critics):
                hard_update(tc, c)
            if target_bus_encoders is not None and bus_encoders is not None:
                if isinstance(bus_encoders, GlobalBusGCNEncoder):
                    target_bus_encoders.load_state_dict(bus_encoders.state_dict(), strict=False)
                else:
                    for te, e in zip(target_bus_encoders, bus_encoders):
                        te.load_state_dict(e.state_dict(), strict=False)

            reset_optimizers_state(actor_optims)
            reset_optimizers_state(critic_optims)
            reset_optimizers_state(enc_optims)
            reset_optimizers_state([mixer_optim])

        if epoch % opts.val_interval == 0:
            val_ret = validate(val_env, actors, bus_encoders, opts, epoch, tb_logger)
            print(
                f"  --> Validation: Sum {val_ret:.2f} | PerStep {val_ret/opts.steps_per_epoch:.2f} (Best: {best_ret:.2f})"
            )
            
            if val_ret > best_ret:
                best_ret = val_ret
                if not os.path.exists(opts.save_dir): os.makedirs(opts.save_dir)
                save_dict = {
                    'mixer': mixer.state_dict(),
                    'actors': [a.state_dict() for a in actors],
                    'bus_encoders': (bus_encoders.state_dict() if isinstance(bus_encoders, GlobalBusGCNEncoder) else [e.state_dict() for e in bus_encoders]) if bus_encoders is not None else None,
                    'bus_gnn_cfg': {
                        'embed_dim': int(getattr(opts, 'bus_gnn_embed_dim', 0)),
                        'hidden_dim': int(getattr(opts, 'bus_gnn_hidden_dim', 0)),
                        'num_layers': int(getattr(opts, 'bus_gnn_layers', 0)),
                        'weight_mode': str(getattr(opts, 'bus_gnn_weight_mode', 'inv_z')),
                    } if bus_encoders is not None else None,
                }
                legacy_path = os.path.join(opts.save_dir, f'best_model_gnn_{opts.case_name}.pth')
                if opts.exp_tag:
                    exp_path = os.path.join(opts.save_dir, f'best_{opts.exp_tag}.pth')
                    torch.save(save_dict, exp_path)
                    if exp_path != legacy_path:
                        torch.save(save_dict, legacy_path)
                else:
                    torch.save(save_dict, legacy_path)

if __name__ == "__main__":
    main()