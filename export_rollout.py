"""Export deterministic rollouts to CSV for plotting.

This script is for *testing/evaluation*.

Supports:
- static topology or random_reset line-outage topology
- disturbance scenarios for A/B/C:
  A) tidal
  B) outage (handled via topology_mode=random_reset)
  C) tidal_step (tidal + a localized step change)

Outputs a CSV with per-step metrics (reward, voltage bounds, loss, connectivity)
that you can plot with plot_results.py.
"""

import argparse
import csv
import importlib
import os
from typing import Dict, List

import numpy as np
import torch

from scenario_env import DisturbanceConfig, ScenarioWrapper
from bus_gnn_encoder import build_bus_encoders

try:
    from global_bus_gnn_encoder import build_global_bus_encoder, GlobalBusGCNEncoder
except Exception:
    build_global_bus_encoder = None
    GlobalBusGCNEncoder = None


def _base_env(env):
    return getattr(env, 'env', env)


def _refresh_bus_encoders(env, bus_encoders):
    if bus_encoders is None:
        return
    be = _base_env(env)
    try:
        if GlobalBusGCNEncoder is not None and isinstance(bus_encoders, GlobalBusGCNEncoder):
            # refresh adjacency only when using current topology
            net_cur = getattr(be, 'net', None)
            net_base = getattr(be, 'net_orig', net_cur)
            net_to_use = net_base if getattr(bus_encoders, 'use_base_topology', True) else net_cur
            if net_to_use is not None:
                bus_encoders.refresh(net_to_use)
        else:
            for e in bus_encoders:
                try:
                    e.refresh(be.net)
                except Exception:
                    pass
    except Exception:
        pass


def infer_num_agents(case: str) -> int:
    return {'33': 2, '69': 4, '141': 4, 'ober': 4, 'cartpole': 1}[case]


def default_steps(case: str) -> int:
    return 200 if case == 'cartpole' else 96


def load_env(
    case: str,
    num_agents: int,
    topology_mode: str,
    outage_k: int,
    outage_policy: str,
    outage_radius: int,
    avoid_slack_hops: int,
    topology_seed: int,
    contiguous_partition: bool,
    partition_seed: int,
):
    env_module = {
        '33': 'env_33',
        '69': 'env_69',
        '141': 'env_141',
        'ober': 'env_oberrhein',
        'cartpole': 'env_cartpole',
    }[case]
    mod = importlib.import_module(env_module)

    if case == 'cartpole':
        return mod.DistNetEnv(num_agents=num_agents)

    kwargs = dict(
        num_agents=num_agents,
        topology_mode=topology_mode,
        outage_k=outage_k,
        outage_policy=outage_policy,
        outage_radius=outage_radius,
        avoid_slack_hops=avoid_slack_hops,
        topology_seed=topology_seed,
    )
    try:
        return mod.DistNetEnv(**kwargs, contiguous_partition=contiguous_partition, partition_seed=partition_seed)
    except TypeError:
        # Backward compatibility: some env versions do not support partition args
        return mod.DistNetEnv(**kwargs)



def load_actors(env, ckpt_path: str, device):
    """Load actors (and optional bus-level encoders) from a checkpoint.

    Returns:
        actors: list[LocalActor]
        bus_encoders: list[AreaBusGCNEncoder] or None
        expected_state_dims: list[int] input dim expected by each actor
    """
    ckpt = torch.load(ckpt_path, map_location=device)
    from networks import LocalActor

    act_dims = [sp.shape[0] for sp in env.action_space]

    def infer_hidden_dim(sd: Dict[str, torch.Tensor]) -> int:
        w = sd.get('l1.weight', None)
        if isinstance(w, torch.Tensor) and w.dim() == 2:
            return int(w.shape[0])
        return 256

    hidden_dim = infer_hidden_dim(ckpt['actors'][0])

    actors = []
    expected_state_dims = []
    for i, sd in enumerate(ckpt['actors']):
        w = sd['l1.weight']
        state_dim = int(w.shape[1])
        expected_state_dims.append(state_dim)
        actor = LocalActor(state_dim, act_dims[i], hidden_dim=hidden_dim).to(device)
        actor.load_state_dict(sd, strict=True)
        actor.eval()
        actors.append(actor)

    bus_encoders = None
    bus_blob = ckpt.get('bus_encoders', None)
    if bus_blob is not None:
        bus_cfg = ckpt.get('bus_gnn_cfg', None) or {}
        embed_dim = int(bus_cfg.get('embed_dim', 0))
        hidden_dim_e = int(bus_cfg.get('hidden_dim', 64))
        num_layers = int(bus_cfg.get('num_layers', 2))
        weight_mode = str(bus_cfg.get('weight_mode', 'inv_z'))

        if embed_dim <= 0:
            # fallback: infer embed_dim = actor_state_dim - raw_obs_dim
            raw_obs_dims = [sp.shape[0] for sp in env.observation_space]
            embed_dim = max(0, expected_state_dims[0] - raw_obs_dims[0])

        if embed_dim > 0:
            be = _base_env(env)
            # Scheme-B: single shared global encoder stored as one state_dict
            if isinstance(bus_blob, dict):
                if build_global_bus_encoder is None:
                    raise RuntimeError(
                        "Checkpoint looks like Scheme-B global bus-GNN, but global_bus_gnn_encoder.py is not available."
                    )
                bus_encoders = build_global_bus_encoder(
                    be,
                    device=device,
                    embed_dim=embed_dim,
                    hidden_dim=hidden_dim_e,
                    num_layers=num_layers,
                    dropout=0.0,
                    weight_mode=weight_mode,
                    use_base_topology=True,
                )
                bus_encoders.load_state_dict(bus_blob, strict=False)
                bus_encoders.eval()
            # Original local bus encoder: list of per-agent state_dicts
            elif isinstance(bus_blob, list):
                bus_encoders = build_bus_encoders(
                    be.net,
                    be.areas,
                    device=device,
                    embed_dim=embed_dim,
                    hidden_dim=hidden_dim_e,
                    num_layers=num_layers,
                    dropout=0.0,
                    weight_mode=weight_mode,
                )
                for e, sd_e in zip(bus_encoders, bus_blob):
                    e.load_state_dict(sd_e, strict=False)
                    e.eval()

    return actors, bus_encoders, expected_state_dims


def export_rollout(env, actors, bus_encoders, expected_state_dims, device, episodes: int, steps: int) -> List[Dict]:
    rows: List[Dict] = []

    for ep in range(episodes):
        obs_list = env.reset()
        _refresh_bus_encoders(env, bus_encoders)
        for t in range(steps):
            actions = []
            with torch.no_grad():
                obs_tensors = [torch.FloatTensor(obs_list[i]).unsqueeze(0).to(device) for i in range(len(actors))]
                z_list = None
                if bus_encoders is not None:
                    if GlobalBusGCNEncoder is not None and isinstance(bus_encoders, GlobalBusGCNEncoder):
                        z_list = bus_encoders(obs_tensors)
                    else:
                        z_list = [enc(o) for enc, o in zip(bus_encoders, obs_tensors)]

                for i in range(len(actors)):
                    o_raw = obs_tensors[i]
                    o = o_raw
                    if z_list is not None and expected_state_dims[i] > o_raw.shape[1]:
                        o = torch.cat([o_raw, z_list[i]], dim=1)
                    # fallback padding (if checkpoint expects extra dims but no encoder found)
                    if expected_state_dims[i] > o.shape[1]:
                        pad = torch.zeros((o.shape[0], expected_state_dims[i] - o.shape[1]), device=device)
                        o = torch.cat([o, pad], dim=1)
                    mean, _ = actors[i].forward(o)
                    a = torch.tanh(mean)  # deterministic
                    actions.append(a.cpu().numpy()[0])

            next_obs, rewards, done, info = env.step(actions)
            rsum = float(np.sum(rewards))

            # Collect key metrics (env populates these)
            row = {
                'episode': int(ep),
                't': int(t),
                'reward_sum': rsum,
                'v_min': float(info.get('v_min', np.nan)),
                'v_max': float(info.get('v_max', np.nan)),
                'v_viol_lin_total': float(info.get('v_viol_lin_total', np.nan)),
                'v_viol_sq_total': float(info.get('v_viol_sq_total', np.nan)),
                'p_loss': float(info.get('p_loss', np.nan)),
                'n_components': float(info.get('n_components', np.nan)),
            }

            # Disturbance metadata (if ScenarioWrapper is enabled)
            row['disturbance_mode'] = info.get('disturbance_mode', 'none')
            row['dist_t'] = info.get('dist_t', t)
            row['load_scale'] = float(info.get('load_scale', 1.0))
            row['pv_scale'] = float(info.get('pv_scale', 1.0))
            row['step_active'] = int(bool(info.get('step_active', False)))
            row['step_target'] = str(info.get('step_target', ''))

            rows.append(row)

            obs_list = next_obs
            if done:
                break

    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--algo', type=str, default='baseline', help='Label used in output file name (e.g., baseline / gnn / gnn_nobus)')
    ap.add_argument('--case', type=str, default='141', choices=['33', '69', '141', 'ober', 'cartpole'])
    ap.add_argument('--ckpt', type=str, required=True)

    # rollout controls
    ap.add_argument('--episodes', type=int, default=10)
    ap.add_argument('--steps', type=int, default=None)

    # topology shift / outages
    ap.add_argument('--topology_mode', type=str, default='static', choices=['static', 'random_reset'])
    ap.add_argument('--outage_k', type=int, default=0)
    ap.add_argument('--outage_policy', type=str, default='local', choices=['global', 'local'])
    ap.add_argument('--outage_radius', type=int, default=2)
    ap.add_argument('--avoid_slack_hops', type=int, default=1)
    ap.add_argument('--topology_seed', type=int, default=0)

    ap.add_argument('--no_contiguous_partition', action='store_true', default=False)
    ap.add_argument('--partition_seed', type=int, default=0)

    # disturbances (A/B/C)
    ap.add_argument('--disturbance', type=str, default='none', choices=['none', 'tidal', 'step', 'tidal_step'])
    ap.add_argument('--reset_load_mode', type=str, default='keep', choices=['keep', 'base'])
    ap.add_argument('--tidal_period', type=int, default=96)
    ap.add_argument('--tidal_load_base', type=float, default=1.0)
    ap.add_argument('--tidal_load_amp', type=float, default=0.2)
    ap.add_argument('--tidal_pv_base', type=float, default=1.0)
    ap.add_argument('--tidal_pv_amp', type=float, default=0.5)
    ap.add_argument('--tidal_phase', type=float, default=0.0)
    ap.add_argument('--step_t', type=int, default=24)
    ap.add_argument('--step_factor', type=float, default=1.2)
    ap.add_argument('--step_target', type=str, default='random_agent', choices=['all', 'random_agent', 'agent0', 'agent1', 'agent2', 'agent3'])
    ap.add_argument('--dist_seed', type=int, default=0)

    ap.add_argument('--gpu', type=str, default='0')
    ap.add_argument('--out_dir', type=str, default='./rollouts')
    args = ap.parse_args()

    device = torch.device(f'cuda:{args.gpu}') if torch.cuda.is_available() else torch.device('cpu')
    num_agents = infer_num_agents(args.case)
    steps = int(args.steps) if args.steps is not None else default_steps(args.case)

    os.makedirs(args.out_dir, exist_ok=True)

    env = load_env(
        case=args.case,
        num_agents=num_agents,
        topology_mode=str(args.topology_mode).lower(),
        outage_k=int(args.outage_k),
        outage_policy=str(args.outage_policy).lower(),
        outage_radius=int(args.outage_radius),
        avoid_slack_hops=int(args.avoid_slack_hops),
        topology_seed=int(args.topology_seed),
        contiguous_partition=(not args.no_contiguous_partition),
        partition_seed=int(args.partition_seed),
    )

    if str(args.disturbance).lower() != 'none':
        cfg = DisturbanceConfig(
            mode=str(args.disturbance).lower(),
            tidal_period=int(args.tidal_period),
            tidal_load_base=float(args.tidal_load_base),
            tidal_load_amp=float(args.tidal_load_amp),
            tidal_pv_base=float(args.tidal_pv_base),
            tidal_pv_amp=float(args.tidal_pv_amp),
            tidal_phase=float(args.tidal_phase),
            step_t=int(args.step_t),
            step_factor=float(args.step_factor),
            step_target=str(args.step_target),
            dist_seed=int(args.dist_seed),
            reset_load_mode=str(args.reset_load_mode).lower(),
            recompute_on_reset=True,
        )
        env = ScenarioWrapper(env, cfg)

    actors, bus_encoders, expected_state_dims = load_actors(env, args.ckpt, device)

    rows = export_rollout(
        env, actors, bus_encoders, expected_state_dims,
        device, episodes=int(args.episodes), steps=steps
    )

    out_csv = os.path.join(
        args.out_dir,
        f"rollout_{args.algo}_{args.case}_{args.topology_mode}_k{args.outage_k}_seed{args.topology_seed}_dist{args.disturbance}.csv",
    )

    with open(out_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Saved rollout CSV: {out_csv}")


if __name__ == '__main__':
    main()
