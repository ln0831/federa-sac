#!/usr/bin/env python3
"""Case141 follow-up runner, v2.

Compared with the original external runner:
1) uses a deterministic evaluator by default;
2) exposes train-time val_episodes so harder tasks can choose more stable model
   selection without touching the original training code;
3) exposes several GNN stabilization flags as CLI args, so case141 k6 tuning can
   be done from the outside;
4) warns when a short pilot compresses the cosine LR schedule too aggressively.
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence


def run(cmd: Sequence[str], cwd: Path, dry_run: bool = False) -> None:
    pretty = " ".join(str(x) for x in cmd)
    print(f"\n[RUN] {pretty}")
    if dry_run:
        return
    subprocess.run(list(map(str, cmd)), cwd=str(cwd), check=True)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def expected_ckpt(save_dir: Path, exp_name: str) -> Path:
    return save_dir / f"best_{exp_name}.pth"


def maybe_warn_short_pilot(epochs: int | None, case: str = "141") -> None:
    default_epochs = {"33": 400, "69": 800, "141": 500, "ober": 1000}.get(str(case), 500)
    if epochs is None:
        return
    if int(epochs) < int(default_epochs):
        print(
            "[WARN] You are overriding --epochs below the project default. "
            "Because the original training code uses CosineAnnealingLR(T_max=epochs), "
            "a short pilot is not just an early stop; it compresses the whole LR schedule. "
            "Use short-epoch pilot only to check pipeline / crashes, not to judge final method ranking."
        )


def build_gnn_flags(args) -> List[str]:
    flags = [
        "--bus_gnn_scope", str(args.bus_gnn_scope),
        "--mixer_gat_ramp_epochs", str(args.mixer_gat_ramp_epochs),
        "--mixer_gate_init_bias", str(args.mixer_gate_init_bias),
        "--mixer_gnn_lr_scale", str(args.mixer_gnn_lr_scale),
        "--mixer_gate_lr_scale", str(args.mixer_gate_lr_scale),
        "--edge_drop", str(args.edge_drop),
        "--bus_gnn_lr_scale", str(args.bus_gnn_lr_scale),
    ]
    if args.bus_gnn_use_base_topology:
        flags.append("--bus_gnn_use_base_topology")
    if args.mixer_use_base_topology:
        flags.append("--mixer_use_base_topology")
    return flags


def build_baseline_cmd(
    python_exec: str,
    save_dir: Path,
    log_dir: Path,
    gpu: str,
    exp_name: str,
    train_topology_mode: str,
    outage_k: int,
    outage_policy: str,
    outage_radius: int,
    avoid_slack_hops: int,
    topology_seed: int,
    epochs: int | None,
    val_episodes: int | None,
) -> List[str]:
    cmd = [
        python_exec, "train_fmasac.py",
        "--case", "141",
        "--gpu", gpu,
        "--save_dir", str(save_dir),
        "--log_dir", str(log_dir),
        "--exp_name", exp_name,
        "--topology_mode", train_topology_mode,
        "--outage_k", str(outage_k),
        "--outage_policy", outage_policy,
        "--outage_radius", str(outage_radius),
        "--avoid_slack_hops", str(avoid_slack_hops),
        "--topology_seed", str(topology_seed),
    ]
    if epochs is not None:
        cmd += ["--epochs", str(epochs)]
    if val_episodes is not None:
        cmd += ["--val_episodes", str(val_episodes)]
    return cmd


def build_gnn_cmd(
    python_exec: str,
    save_dir: Path,
    log_dir: Path,
    gpu: str,
    exp_name: str,
    train_topology_mode: str,
    outage_k: int,
    outage_policy: str,
    outage_radius: int,
    avoid_slack_hops: int,
    topology_seed: int,
    fed_mode: str,
    no_bus_gnn: bool,
    epochs: int | None,
    val_episodes: int | None,
    gnn_flags: List[str],
) -> List[str]:
    cmd = [
        python_exec, "train_gnn.py",
        "--case", "141",
        "--gpu", gpu,
        "--save_dir", str(save_dir),
        "--log_dir", str(log_dir),
        "--exp_name", exp_name,
        "--topology_mode", train_topology_mode,
        "--outage_k", str(outage_k),
        "--outage_policy", outage_policy,
        "--outage_radius", str(outage_radius),
        "--avoid_slack_hops", str(avoid_slack_hops),
        "--topology_seed", str(topology_seed),
        "--fed_mode", fed_mode,
        *gnn_flags,
    ]
    if no_bus_gnn:
        cmd.append("--no_bus_gnn")
    if epochs is not None:
        cmd += ["--epochs", str(epochs)]
    if val_episodes is not None:
        cmd += ["--val_episodes", str(val_episodes)]
    return cmd


def build_eval_cmd(
    python_exec: str,
    eval_script: str,
    baseline_ckpt: Path,
    compare_ckpt: Path,
    compare_label: str,
    out_dir: Path,
    gpu: str,
    eval_seed: int,
    eval_seed_base: int,
    outage_k: int,
    outage_policy: str,
    outage_radius: int,
    avoid_slack_hops: int,
    episodes: int,
    steps: int | None,
) -> List[str]:
    cmd = [
        python_exec, eval_script,
        "--case", "141",
        "--baseline_ckpt", str(baseline_ckpt),
        "--gnn_ckpt", str(compare_ckpt),
        "--baseline_name", "baseline",
        "--gnn_name", compare_label,
        "--episodes", str(episodes),
        "--topology_seed", str(eval_seed),
        "--eval_seed_base", str(eval_seed_base),
        "--outage_k", str(outage_k),
        "--outage_policy", outage_policy,
        "--outage_radius", str(outage_radius),
        "--avoid_slack_hops", str(avoid_slack_hops),
        "--gpu", gpu,
        "--out_dir", str(out_dir),
    ]
    if steps is not None:
        cmd += ["--steps", str(steps)]
    return cmd


def aggregate_one_pair(
    python_exec: str,
    project_root: Path,
    summary_paths: List[Path],
    out_csv: Path,
    dry_run: bool,
) -> None:
    cmd = [
        python_exec,
        "aggregate_shift_results.py",
        "--inputs",
        *[str(p) for p in summary_paths],
        "--out_csv",
        str(out_csv),
    ]
    run(cmd, cwd=project_root, dry_run=dry_run)


def make_pairwise_report(agg_csv: Path, compare_label: str, out_csv: Path) -> None:
    rows: List[Dict[str, str]] = []
    with agg_csv.open("r", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for r in rd:
            rows.append(r)

    by_topo: Dict[str, Dict[str, Dict[str, str]]] = {}
    for r in rows:
        topo = str(r["topology_mode"])
        algo = str(r["algo"])
        by_topo.setdefault(topo, {})[algo] = r

    out_rows: List[Dict[str, object]] = []
    for topo, d in sorted(by_topo.items()):
        if "baseline" not in d or compare_label not in d:
            continue
        b = d["baseline"]
        g = d[compare_label]
        b_ret = float(b["return_mean_across_seeds_mean"])
        g_ret = float(g["return_mean_across_seeds_mean"])
        b_pl = float(b["p_loss_mean_across_seeds_mean"])
        g_pl = float(g["p_loss_mean_across_seeds_mean"])

        ret_gain_abs = g_ret - b_ret
        ret_gain_pct = 100.0 * ret_gain_abs / abs(b_ret) if b_ret != 0 else float("nan")
        ploss_delta = g_pl - b_pl
        ploss_reduction_pct = 100.0 * (b_pl - g_pl) / b_pl if b_pl != 0 else float("nan")

        out_rows.append(
            {
                "topology_mode": topo,
                "baseline_return_mean": b_ret,
                f"{compare_label}_return_mean": g_ret,
                "return_gain_abs": ret_gain_abs,
                "return_gain_pct": ret_gain_pct,
                "baseline_p_loss_mean": b_pl,
                f"{compare_label}_p_loss_mean": g_pl,
                "p_loss_delta": ploss_delta,
                "p_loss_reduction_pct": ploss_reduction_pct,
            }
        )

    ensure_dir(out_csv.parent)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    print(f"[PAIRWISE] Saved {out_csv}")


def suite_compare_labels(suite: str) -> List[str]:
    if suite in {"rr_k6", "static_k6_shift"}:
        return ["gnn_global", "gnn_nobus"]
    if suite in {"fed_rr_k4", "fed_static_k4"}:
        return ["gnn_global_none", "gnn_global_fedavg", "gnn_global_topo"]
    raise ValueError(f"Unknown suite: {suite}")


def suite_train_mode(suite: str) -> str:
    if suite in {"rr_k6", "fed_rr_k4"}:
        return "random_reset"
    if suite in {"static_k6_shift", "fed_static_k4"}:
        return "static"
    raise ValueError(f"Unknown suite: {suite}")


def suite_outage_k(suite: str) -> int:
    if suite in {"rr_k6", "static_k6_shift"}:
        return 6
    if suite in {"fed_rr_k4", "fed_static_k4"}:
        return 4
    raise ValueError(f"Unknown suite: {suite}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", required=True, choices=["rr_k6", "static_k6_shift", "fed_rr_k4", "fed_static_k4"])
    ap.add_argument("--project_root", type=str, default=".")
    ap.add_argument("--output_root", type=str, default="./followup_runs")
    ap.add_argument("--python_exec", type=str, default=sys.executable)
    ap.add_argument("--eval_script", type=str, default="evaluate_topology_shift_deterministic.py")
    ap.add_argument("--gpu", type=str, default="0")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--episodes", type=int, default=40,
                    help="Evaluation episodes per topology mode. Raised from 20 to 40 for more stable k6 comparison.")
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--eval_seed_base", type=int, default=12345)
    ap.add_argument("--outage_policy", type=str, default="local", choices=["global", "local"])
    ap.add_argument("--outage_radius", type=int, default=2)
    ap.add_argument("--avoid_slack_hops", type=int, default=1)
    ap.add_argument("--epochs", type=int, default=None, help="Optional override. Use only for crash-check pilots.")
    ap.add_argument("--val_episodes", type=int, default=None,
                    help="Passed through to training scripts. Recommend 10 for k6 if runtime allows.")
    ap.add_argument("--skip_existing", action="store_true", default=False)
    ap.add_argument("--skip_train", action="store_true", default=False)
    ap.add_argument("--skip_eval", action="store_true", default=False)
    ap.add_argument("--dry_run", action="store_true", default=False)

    ap.add_argument("--bus_gnn_scope", type=str, default="global", choices=["global", "local"])
    ap.add_argument("--bus_gnn_use_base_topology", action="store_true", default=True)
    ap.add_argument("--mixer_use_base_topology", action="store_true", default=True)
    ap.add_argument("--mixer_gat_ramp_epochs", type=int, default=50)
    ap.add_argument("--mixer_gate_init_bias", type=float, default=-5.0)
    ap.add_argument("--mixer_gnn_lr_scale", type=float, default=0.1)
    ap.add_argument("--mixer_gate_lr_scale", type=float, default=0.1)
    ap.add_argument("--bus_gnn_lr_scale", type=float, default=0.1)
    ap.add_argument("--edge_drop", type=float, default=0.1)
    args = ap.parse_args()

    maybe_warn_short_pilot(args.epochs, case="141")

    project_root = Path(args.project_root).resolve()
    output_root = Path(args.output_root).resolve() / args.suite
    ckpt_dir = output_root / "checkpoints"
    log_dir = output_root / "logs"
    eval_root = output_root / "eval"
    agg_root = output_root / "agg"

    for p in [ckpt_dir, log_dir, eval_root, agg_root]:
        ensure_dir(p)

    train_topology_mode = suite_train_mode(args.suite)
    outage_k = suite_outage_k(args.suite)
    compare_labels = suite_compare_labels(args.suite)
    gnn_flags = build_gnn_flags(args)

    summary_map: Dict[str, List[Path]] = {label: [] for label in compare_labels}

    for seed in args.seeds:
        baseline_exp = f"fmasac_{args.suite}_seed{seed}"
        baseline_ckpt = expected_ckpt(ckpt_dir, baseline_exp)

        if not args.skip_train:
            if not (args.skip_existing and baseline_ckpt.exists()):
                cmd = build_baseline_cmd(
                    python_exec=args.python_exec,
                    save_dir=ckpt_dir,
                    log_dir=log_dir,
                    gpu=args.gpu,
                    exp_name=baseline_exp,
                    train_topology_mode=train_topology_mode,
                    outage_k=outage_k,
                    outage_policy=args.outage_policy,
                    outage_radius=args.outage_radius,
                    avoid_slack_hops=args.avoid_slack_hops,
                    topology_seed=seed,
                    epochs=args.epochs,
                    val_episodes=args.val_episodes,
                )
                run(cmd, cwd=project_root, dry_run=args.dry_run)
            else:
                print(f"[SKIP] baseline checkpoint exists: {baseline_ckpt}")

        if args.suite in {"rr_k6", "static_k6_shift"}:
            compare_specs = [
                {"label": "gnn_global", "fed_mode": "none", "no_bus_gnn": False},
                {"label": "gnn_nobus", "fed_mode": "none", "no_bus_gnn": True},
            ]
        else:
            compare_specs = [
                {"label": "gnn_global_none", "fed_mode": "none", "no_bus_gnn": False},
                {"label": "gnn_global_fedavg", "fed_mode": "fedavg", "no_bus_gnn": False},
                {"label": "gnn_global_topo", "fed_mode": "topo", "no_bus_gnn": False},
            ]

        for spec in compare_specs:
            label = str(spec["label"])
            fed_mode = str(spec["fed_mode"])
            no_bus_gnn = bool(spec["no_bus_gnn"])
            gnn_exp = f"{label}_{args.suite}_seed{seed}"
            gnn_ckpt = expected_ckpt(ckpt_dir, gnn_exp)

            if not args.skip_train:
                if not (args.skip_existing and gnn_ckpt.exists()):
                    cmd = build_gnn_cmd(
                        python_exec=args.python_exec,
                        save_dir=ckpt_dir,
                        log_dir=log_dir,
                        gpu=args.gpu,
                        exp_name=gnn_exp,
                        train_topology_mode=train_topology_mode,
                        outage_k=outage_k,
                        outage_policy=args.outage_policy,
                        outage_radius=args.outage_radius,
                        avoid_slack_hops=args.avoid_slack_hops,
                        topology_seed=seed,
                        fed_mode=fed_mode,
                        no_bus_gnn=no_bus_gnn,
                        epochs=args.epochs,
                        val_episodes=args.val_episodes,
                        gnn_flags=gnn_flags,
                    )
                    run(cmd, cwd=project_root, dry_run=args.dry_run)
                else:
                    print(f"[SKIP] compare checkpoint exists: {gnn_ckpt}")

            eval_dir = eval_root / f"{label}_seed{seed}"
            ensure_dir(eval_dir)
            summary_csv = eval_dir / f"summary_141_k{outage_k}_seed{seed}.csv"
            summary_map[label].append(summary_csv)

            if not args.skip_eval:
                if not (args.skip_existing and summary_csv.exists()):
                    cmd = build_eval_cmd(
                        python_exec=args.python_exec,
                        eval_script=args.eval_script,
                        baseline_ckpt=baseline_ckpt,
                        compare_ckpt=gnn_ckpt,
                        compare_label=label,
                        out_dir=eval_dir,
                        gpu=args.gpu,
                        eval_seed=seed,
                        eval_seed_base=int(args.eval_seed_base) + int(seed) * 1000,
                        outage_k=outage_k,
                        outage_policy=args.outage_policy,
                        outage_radius=args.outage_radius,
                        avoid_slack_hops=args.avoid_slack_hops,
                        episodes=args.episodes,
                        steps=args.steps,
                    )
                    run(cmd, cwd=project_root, dry_run=args.dry_run)
                else:
                    print(f"[SKIP] eval summary exists: {summary_csv}")

    if not args.dry_run:
        for label, paths in summary_map.items():
            agg_csv = agg_root / f"agg_{label}.csv"
            aggregate_one_pair(
                python_exec=args.python_exec,
                project_root=project_root,
                summary_paths=paths,
                out_csv=agg_csv,
                dry_run=args.dry_run,
            )
            pair_csv = agg_root / f"pairwise_{label}.csv"
            make_pairwise_report(agg_csv, label, pair_csv)

    print("\n[DONE] Suite finished.")
    print(f"  Output root: {output_root}")
    print("  Aggregated CSVs:")
    for label in compare_labels:
        print(f"    - {agg_root / f'agg_{label}.csv'}")
        print(f"    - {agg_root / f'pairwise_{label}.csv'}")


if __name__ == "__main__":
    main()
