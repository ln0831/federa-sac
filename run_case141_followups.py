#!/usr/bin/env python3
"""Run next-stage case141 experiments without modifying the original codebase.

This script is a thin orchestration layer around the existing project entrypoints:
  - train_fmasac.py
  - train_gnn.py
  - evaluate_topology_shift.py
  - aggregate_shift_results.py

Supported suites
----------------
1) rr_k6
   Train on random_reset with outage_k=6, then evaluate on static + random_reset.
   Compares: baseline vs gnn_global, and baseline vs gnn_nobus.

2) static_k6_shift
   Train on static topology, then evaluate on static + random_reset with outage_k=6.
   Compares: baseline vs gnn_global, and baseline vs gnn_nobus.

3) fed_rr_k4
   Train on random_reset with outage_k=4 and compare GNN-global under
   fed_mode in {none, fedavg, topo}. Baseline is kept as the anchor.

4) fed_static_k4
   Train on static topology and compare GNN-global under
   fed_mode in {none, fedavg, topo}. Baseline is kept as the anchor.

Notes
-----
- No original project file is edited.
- All checkpoints/logs/evaluations are written into a separate output root.
- The best current GNN settings are baked in as defaults but can be overridden.
"""
from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence


GNN_STABLE_FLAGS: List[str] = [
    "--bus_gnn_scope", "global",
    "--bus_gnn_use_base_topology",
    "--mixer_use_base_topology",
    "--mixer_gat_ramp_epochs", "50",
    "--mixer_gate_init_bias", "-5",
    "--mixer_gnn_lr_scale", "0.1",
    "--mixer_gate_lr_scale", "0.1",
    "--edge_drop", "0.1",
]


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


def build_baseline_cmd(
    python_exec: str,
    project_root: Path,
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
    return cmd


def build_gnn_cmd(
    python_exec: str,
    project_root: Path,
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
        *GNN_STABLE_FLAGS,
    ]
    if no_bus_gnn:
        cmd.append("--no_bus_gnn")
    if epochs is not None:
        cmd += ["--epochs", str(epochs)]
    return cmd


def build_eval_cmd(
    python_exec: str,
    baseline_ckpt: Path,
    compare_ckpt: Path,
    compare_label: str,
    out_dir: Path,
    gpu: str,
    eval_seed: int,
    outage_k: int,
    outage_policy: str,
    outage_radius: int,
    avoid_slack_hops: int,
    episodes: int,
    steps: int | None,
) -> List[str]:
    cmd = [
        python_exec, "evaluate_topology_shift.py",
        "--case", "141",
        "--baseline_ckpt", str(baseline_ckpt),
        "--gnn_ckpt", str(compare_ckpt),
        "--baseline_name", "baseline",
        "--gnn_name", compare_label,
        "--episodes", str(episodes),
        "--topology_seed", str(eval_seed),
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
    ap.add_argument("--gpu", type=str, default="0")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--episodes", type=int, default=20)
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--outage_policy", type=str, default="local", choices=["global", "local"])
    ap.add_argument("--outage_radius", type=int, default=2)
    ap.add_argument("--avoid_slack_hops", type=int, default=1)
    ap.add_argument("--epochs", type=int, default=None, help="Optional override for pilot runs.")
    ap.add_argument("--skip_existing", action="store_true", default=False)
    ap.add_argument("--skip_train", action="store_true", default=False)
    ap.add_argument("--skip_eval", action="store_true", default=False)
    ap.add_argument("--dry_run", action="store_true", default=False)
    args = ap.parse_args()

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

    # Keep track of per-compare summary csvs for aggregation
    summary_map: Dict[str, List[Path]] = {label: [] for label in compare_labels}

    for seed in args.seeds:
        baseline_exp = f"fmasac_{args.suite}_seed{seed}"
        baseline_ckpt = expected_ckpt(ckpt_dir, baseline_exp)

        if not args.skip_train:
            if not (args.skip_existing and baseline_ckpt.exists()):
                cmd = build_baseline_cmd(
                    python_exec=args.python_exec,
                    project_root=project_root,
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
                )
                run(cmd, cwd=project_root, dry_run=args.dry_run)
            else:
                print(f"[SKIP] baseline checkpoint exists: {baseline_ckpt}")

        # Compare jobs differ by suite
        compare_specs: List[Dict[str, object]] = []
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
                        project_root=project_root,
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
                        baseline_ckpt=baseline_ckpt,
                        compare_ckpt=gnn_ckpt,
                        compare_label=label,
                        out_dir=eval_dir,
                        gpu=args.gpu,
                        eval_seed=seed,
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

    # Aggregate per compare label
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