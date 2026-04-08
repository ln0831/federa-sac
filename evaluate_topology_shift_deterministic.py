"""Deterministic topology-shift evaluation for baseline vs GNN checkpoints.

Why this file exists
--------------------
The original evaluate_topology_shift.py evaluates baseline and GNN in separate
random env trajectories. In env_141.reset(), load magnitudes are perturbed by
np.random.uniform(), but that RNG is not seeded inside the environment. As a
result, repeated evaluations of the same checkpoint can produce slightly
changed numbers, and baseline / GNN may see different load perturbations.

This script fixes that without editing the original project code:
- before each episode reset, it seeds python / numpy / torch with a
  deterministic episode seed;
- baseline and GNN therefore see the same load-randomization trajectory for a
  given episode index;
- repeated runs with the same arguments reproduce the same CSV outputs.

It keeps the same checkpoint-loading logic and the same CSV schema as the
original script, so it can be dropped into the current workflow directly.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import os
import random
from typing import Dict, List, Tuple

import numpy as np
import torch

from bus_gnn_encoder import build_bus_encoders

try:
    from global_bus_gnn_encoder import build_global_bus_encoder, GlobalBusGCNEncoder
except Exception:
    build_global_bus_encoder = None
    GlobalBusGCNEncoder = None


def seed_all(seed: int) -> None:
    seed = int(seed)
    random.seed(seed)
    np.random.seed(seed % (2**32 - 1))
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def default_outage_k(case: str) -> int:
    if case in {"33", "69"}:
        return 3
    if case in {"141", "ober"}:
        return 4
    return 0


def infer_num_agents(case: str) -> int:
    return {"33": 2, "69": 4, "141": 4, "ober": 4, "cartpole": 1}[case]


def _base_env(env):
    return getattr(env, "env", env)


def load_env(
    case: str,
    num_agents: int,
    topology_mode: str,
    outage_k: int,
    topology_seed: int,
    outage_policy: str,
    outage_radius: int,
    avoid_slack_hops: int,
):
    env_module = {
        "33": "env_33",
        "69": "env_69",
        "141": "env_141",
        "ober": "env_oberrhein",
        "cartpole": "env_cartpole",
    }[case]
    mod = importlib.import_module(env_module)

    if case == "cartpole":
        return mod.DistNetEnv(num_agents=num_agents)

    return mod.DistNetEnv(
        num_agents=num_agents,
        topology_mode=topology_mode,
        outage_k=outage_k,
        topology_seed=topology_seed,
        outage_policy=str(outage_policy).lower(),
        outage_radius=int(outage_radius),
        avoid_slack_hops=int(avoid_slack_hops),
    )


def _infer_hidden_dim(sd: Dict[str, torch.Tensor]) -> int:
    w = sd.get("l1.weight", None)
    if isinstance(w, torch.Tensor) and w.dim() == 2:
        return int(w.shape[0])
    for k, v in sd.items():
        if k.endswith("l1.weight") and isinstance(v, torch.Tensor) and v.dim() == 2:
            return int(v.shape[0])
    return 256


def _refresh_encoder(env, bus_encoder) -> None:
    if bus_encoder is None:
        return
    be = _base_env(env)
    try:
        if GlobalBusGCNEncoder is not None and isinstance(bus_encoder, GlobalBusGCNEncoder):
            net = getattr(be, "net_orig", None) if getattr(bus_encoder, "use_base_topology", True) else getattr(be, "net", None)
            if net is None:
                net = getattr(be, "net", None)
            if net is not None:
                bus_encoder.refresh(net)
        else:
            for enc in bus_encoder:
                enc.refresh(be.net)
    except Exception:
        pass


def load_policy(env, ckpt_path: str, device):
    ckpt = torch.load(ckpt_path, map_location=device)
    from networks import LocalActor

    act_dims = [sp.shape[0] for sp in env.action_space]
    raw_obs_dims = [sp.shape[0] for sp in env.observation_space]
    hidden_dim = _infer_hidden_dim(ckpt["actors"][0])

    actors = []
    expected_state_dims = []
    for i, sd in enumerate(ckpt["actors"]):
        state_dim = int(sd["l1.weight"].shape[1])
        expected_state_dims.append(state_dim)
        actor = LocalActor(state_dim, act_dims[i], hidden_dim=hidden_dim).to(device)
        actor.load_state_dict(sd, strict=True)
        actor.eval()
        actors.append(actor)

    bus_encoder = None
    bus_blob = ckpt.get("bus_encoders", None)
    if bus_blob is not None:
        bus_cfg = ckpt.get("bus_gnn_cfg", None) or {}
        embed_dim = int(bus_cfg.get("embed_dim", 0))
        hidden_dim_e = int(bus_cfg.get("hidden_dim", 64))
        num_layers = int(bus_cfg.get("num_layers", 2))
        weight_mode = str(bus_cfg.get("weight_mode", "inv_z"))
        use_base_topology = bool(bus_cfg.get("use_base_topology", True))

        if embed_dim <= 0:
            embed_dim = max(0, expected_state_dims[0] - raw_obs_dims[0])

        if embed_dim > 0:
            be = _base_env(env)
            if isinstance(bus_blob, dict):
                if build_global_bus_encoder is None:
                    raise RuntimeError(
                        "Checkpoint looks like Scheme-B global bus-GNN, but global_bus_gnn_encoder.py is not available."
                    )
                bus_encoder = build_global_bus_encoder(
                    be,
                    device=device,
                    embed_dim=embed_dim,
                    hidden_dim=hidden_dim_e,
                    num_layers=num_layers,
                    dropout=0.0,
                    weight_mode=weight_mode,
                    use_base_topology=use_base_topology,
                )
                bus_encoder.load_state_dict(bus_blob, strict=False)
                bus_encoder.eval()
            elif isinstance(bus_blob, list):
                bus_encoder = build_bus_encoders(
                    be.net,
                    be.areas,
                    device=device,
                    embed_dim=embed_dim,
                    hidden_dim=hidden_dim_e,
                    num_layers=num_layers,
                    dropout=0.0,
                    weight_mode=weight_mode,
                )
                for enc, sd_e in zip(bus_encoder, bus_blob):
                    enc.load_state_dict(sd_e, strict=False)
                    enc.eval()

    return actors, bus_encoder, expected_state_dims


def _build_actor_inputs(obs_list, bus_encoder, expected_state_dims, device):
    obs_tensors = [torch.as_tensor(o, dtype=torch.float32, device=device).unsqueeze(0) for o in obs_list]

    z_list = None
    if bus_encoder is not None:
        if GlobalBusGCNEncoder is not None and isinstance(bus_encoder, GlobalBusGCNEncoder):
            z_list = bus_encoder(obs_tensors)
        else:
            z_list = [enc(o) for enc, o in zip(bus_encoder, obs_tensors)]

    actor_inputs = []
    for i, o in enumerate(obs_tensors):
        x = o
        if z_list is not None and expected_state_dims[i] > x.shape[1]:
            x = torch.cat([x, z_list[i]], dim=1)
        if expected_state_dims[i] > x.shape[1]:
            pad = torch.zeros((x.shape[0], expected_state_dims[i] - x.shape[1]), dtype=x.dtype, device=x.device)
            x = torch.cat([x, pad], dim=1)
        actor_inputs.append(x)
    return actor_inputs


def eval_once(
    env,
    actors,
    bus_encoder,
    expected_state_dims,
    device,
    episodes: int,
    steps: int,
    episode_seed_base: int,
) -> Tuple[List[Dict], Dict[str, float]]:
    rows: List[Dict] = []

    ep_returns = []
    ep_vviol = []
    ep_ploss = []
    ep_ncomp = []

    for ep in range(episodes):
        seed_all(int(episode_seed_base) + int(ep))
        obs_list = env.reset()
        _refresh_encoder(env, bus_encoder)
        ret = 0.0
        vv_sum = 0.0
        pl_sum = 0.0
        nc_sum = 0.0
        count = 0

        for _t in range(steps):
            actions = []
            with torch.no_grad():
                actor_inputs = _build_actor_inputs(obs_list, bus_encoder, expected_state_dims, device)
                for i in range(len(actors)):
                    mean, _ = actors[i].forward(actor_inputs[i])
                    a = torch.tanh(mean)
                    actions.append(a.cpu().numpy()[0])

            next_obs, rewards, done, info = env.step(actions)
            ret += float(np.sum(rewards))

            vv_sum += float(info.get("v_viol_lin_total", 0.0))
            pl_sum += float(info.get("p_loss", 0.0))
            nc_sum += float(info.get("n_components", 1.0))
            count += 1

            obs_list = next_obs
            if done:
                break

        ep_returns.append(ret)
        ep_vviol.append(vv_sum / max(count, 1))
        ep_ploss.append(pl_sum / max(count, 1))
        ep_ncomp.append(nc_sum / max(count, 1))

        rows.append(
            {
                "episode": ep,
                "return": ret,
                "v_viol_lin_mean": ep_vviol[-1],
                "p_loss_mean": ep_ploss[-1],
                "n_components_mean": ep_ncomp[-1],
            }
        )

    summary = {
        "return_mean": float(np.mean(ep_returns)),
        "return_std": float(np.std(ep_returns)),
        "v_viol_lin_mean": float(np.mean(ep_vviol)),
        "p_loss_mean": float(np.mean(ep_ploss)),
        "n_components_mean": float(np.mean(ep_ncomp)),
    }
    return rows, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", type=str, default="141", choices=["33", "69", "141", "ober", "cartpole"])
    ap.add_argument("--baseline_ckpt", type=str, required=True)
    ap.add_argument("--gnn_ckpt", type=str, required=True)
    ap.add_argument("--baseline_name", type=str, default="baseline")
    ap.add_argument("--gnn_name", type=str, default="gnn")
    ap.add_argument("--episodes", type=int, default=20)
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--topology_seed", type=int, default=0)
    ap.add_argument("--outage_k", type=int, default=None)
    ap.add_argument("--outage_policy", type=str, default="local", choices=["global", "local"])
    ap.add_argument("--outage_radius", type=int, default=2)
    ap.add_argument("--avoid_slack_hops", type=int, default=1)
    ap.add_argument("--eval_seed_base", type=int, default=12345,
                    help="Base RNG seed used to make per-episode load perturbations reproducible across models.")
    ap.add_argument("--gpu", type=str, default="0")
    ap.add_argument("--out_dir", type=str, default="./eval")
    args = ap.parse_args()

    seed_all(int(args.eval_seed_base))
    device = torch.device(f"cuda:{args.gpu}") if torch.cuda.is_available() else torch.device("cpu")
    num_agents = infer_num_agents(args.case)
    ok = default_outage_k(args.case) if args.outage_k is None else int(args.outage_k)
    steps = 200 if args.case == "cartpole" else 96 if args.steps is None else int(args.steps)

    os.makedirs(args.out_dir, exist_ok=True)
    all_summaries: List[Dict] = []

    for topo_mode in ["static", "random_reset"]:
        env_b = load_env(
            case=args.case,
            num_agents=num_agents,
            topology_mode=topo_mode,
            outage_k=ok,
            topology_seed=int(args.topology_seed),
            outage_policy=str(args.outage_policy).lower(),
            outage_radius=int(args.outage_radius),
            avoid_slack_hops=int(args.avoid_slack_hops),
        )
        env_g = load_env(
            case=args.case,
            num_agents=num_agents,
            topology_mode=topo_mode,
            outage_k=ok,
            topology_seed=int(args.topology_seed),
            outage_policy=str(args.outage_policy).lower(),
            outage_radius=int(args.outage_radius),
            avoid_slack_hops=int(args.avoid_slack_hops),
        )

        actors_b, enc_b, dims_b = load_policy(env_b, args.baseline_ckpt, device)
        rows_b, sum_b = eval_once(
            env_b, actors_b, enc_b, dims_b, device,
            episodes=args.episodes,
            steps=steps,
            episode_seed_base=int(args.eval_seed_base) + (0 if topo_mode == "static" else 100000),
        )

        actors_g, enc_g, dims_g = load_policy(env_g, args.gnn_ckpt, device)
        rows_g, sum_g = eval_once(
            env_g, actors_g, enc_g, dims_g, device,
            episodes=args.episodes,
            steps=steps,
            episode_seed_base=int(args.eval_seed_base) + (0 if topo_mode == "static" else 100000),
        )

        for algo, rows in [(args.baseline_name, rows_b), (args.gnn_name, rows_g)]:
            p = os.path.join(args.out_dir, f"per_episode_{algo}_{args.case}_{topo_mode}_k{ok}_seed{args.topology_seed}.csv")
            with open(p, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)

        all_summaries.extend(
            [
                {"algo": str(args.baseline_name), "case": args.case, "topology_mode": topo_mode, "outage_k": ok, **sum_b},
                {"algo": str(args.gnn_name), "case": args.case, "topology_mode": topo_mode, "outage_k": ok, **sum_g},
            ]
        )
        print(f"[{topo_mode}] {args.baseline_name} return_mean={sum_b['return_mean']:.3f}, {args.gnn_name} return_mean={sum_g['return_mean']:.3f}")

    summary_path = os.path.join(args.out_dir, f"summary_{args.case}_k{ok}_seed{args.topology_seed}.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(all_summaries[0].keys()))
        w.writeheader()
        w.writerows(all_summaries)

    print(f"Saved summary: {summary_path}")


if __name__ == "__main__":
    main()
