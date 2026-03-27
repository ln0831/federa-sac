#!/usr/bin/env python3
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


def build_common_flags(args) -> List[str]:
    flags = [
        "--case", "141",
        "--gpu", str(args.gpu),
        "--epochs", str(args.epochs),
        "--val_episodes", str(args.val_episodes),
        "--topology_mode", str(args.train_topology_mode),
        "--outage_k", str(args.outage_k),
        "--outage_policy", str(args.outage_policy),
        "--outage_radius", str(args.outage_radius),
        "--avoid_slack_hops", str(args.avoid_slack_hops),
        "--topology_seed", str(args.seed),
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


def build_method_cmd(project_root: Path, args, exp_name: str, method: Dict[str, str]) -> List[str]:
    save_dir = project_root / "outputs" / "checkpoints"
    log_dir = project_root / "outputs" / "logs"
    ensure_dir(save_dir)
    ensure_dir(log_dir)
    cmd = [
        sys.executable,
        "train_gnn_fedgrid_v2.py",
        "--save_dir", str(save_dir),
        "--log_dir", str(log_dir),
        "--exp_name", exp_name,
        *build_common_flags(args),
        "--fed_mode", str(method.get("fed_mode", "none")),
    ]
    if method.get("no_bus_gnn", False):
        cmd.append("--no_bus_gnn")
    if "fed_proto_source" in method:
        cmd += ["--fed_proto_source", str(method["fed_proto_source"])]
    if "fed_client_dropout" in method:
        cmd += ["--fed_client_dropout", str(method["fed_client_dropout"])]
    if "fed_byzantine_frac" in method:
        cmd += ["--fed_byzantine_frac", str(method["fed_byzantine_frac"])]
    if "fed_byzantine_mode" in method:
        cmd += ["--fed_byzantine_mode", str(method["fed_byzantine_mode"])]
    if "fed_byzantine_strength" in method:
        cmd += ["--fed_byzantine_strength", str(method["fed_byzantine_strength"])]
    if "fed_topo_weight" in method:
        cmd += ["--fed_topo_weight", str(method["fed_topo_weight"])]
    if "fed_proto_weight" in method:
        cmd += ["--fed_proto_weight", str(method["fed_proto_weight"])]
    return cmd


def build_eval_cmd(project_root: Path, args, baseline_ckpt: Path, compare_ckpt: Path, compare_label: str) -> List[str]:
    out_dir = project_root / "outputs" / "eval" / compare_label
    ensure_dir(out_dir)
    cmd = [
        sys.executable,
        str(project_root / args.eval_script),
        "--case", "141",
        "--baseline_ckpt", str(baseline_ckpt),
        "--gnn_ckpt", str(compare_ckpt),
        "--baseline_name", "fedgrid_none",
        "--gnn_name", compare_label,
        "--episodes", str(args.eval_episodes),
        "--topology_seed", str(args.eval_seed),
        "--eval_seed_base", str(args.eval_seed_base),
        "--outage_k", str(args.outage_k),
        "--outage_policy", str(args.outage_policy),
        "--outage_radius", str(args.outage_radius),
        "--avoid_slack_hops", str(args.avoid_slack_hops),
        "--gpu", str(args.gpu),
        "--out_dir", str(out_dir),
    ]
    if args.eval_steps is not None:
        cmd += ["--steps", str(args.eval_steps)]
    return cmd


def default_methods() -> List[Dict[str, str]]:
    return [
        {"label": "fedgrid_none", "fed_mode": "none", "fed_proto_source": "hybrid"},
        {"label": "fedgrid_topo", "fed_mode": "topo", "fed_proto_source": "hybrid"},
        {"label": "fedgrid_topo_proto", "fed_mode": "topo_proto", "fed_proto_source": "hybrid"},
        {"label": "fedgrid_consensus", "fed_mode": "consensus", "fed_proto_source": "hybrid"},
        {"label": "fedgrid_dropout", "fed_mode": "topo_proto", "fed_proto_source": "hybrid", "fed_client_dropout": 0.25},
        {"label": "fedgrid_byzantine", "fed_mode": "topo_proto", "fed_proto_source": "hybrid", "fed_byzantine_frac": 0.25, "fed_byzantine_mode": "noise", "fed_byzantine_strength": 0.5},
    ]


def save_matrix(project_root: Path, rows: List[Dict[str, object]]) -> Path:
    out_csv = project_root / "outputs" / "fedgrid_v2_matrix.csv"
    ensure_dir(out_csv.parent)
    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(str(key))
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    print(f"[MATRIX] saved {out_csv}")
    return out_csv


def main() -> None:
    ap = argparse.ArgumentParser(description="Case141 FedGrid-v2 runner")
    ap.add_argument("--project_root", type=str, default=".")
    ap.add_argument("--gpu", type=str, default="0")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--val_episodes", type=int, default=5)
    ap.add_argument("--train_topology_mode", type=str, default="random_reset", choices=["static", "random_reset"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--outage_k", type=int, default=6)
    ap.add_argument("--outage_policy", type=str, default="local", choices=["global", "local"])
    ap.add_argument("--outage_radius", type=int, default=2)
    ap.add_argument("--avoid_slack_hops", type=int, default=1)
    ap.add_argument("--bus_gnn_scope", type=str, default="global", choices=["global", "local"])
    ap.add_argument("--bus_gnn_use_base_topology", action="store_true", default=True)
    ap.add_argument("--mixer_use_base_topology", action="store_true", default=True)
    ap.add_argument("--mixer_gat_ramp_epochs", type=int, default=50)
    ap.add_argument("--mixer_gate_init_bias", type=float, default=-5.0)
    ap.add_argument("--mixer_gnn_lr_scale", type=float, default=0.1)
    ap.add_argument("--mixer_gate_lr_scale", type=float, default=0.1)
    ap.add_argument("--edge_drop", type=float, default=0.10)
    ap.add_argument("--bus_gnn_lr_scale", type=float, default=0.1)
    ap.add_argument("--eval_script", type=str, default="evaluate_topology_shift_deterministic.py")
    ap.add_argument("--eval_episodes", type=int, default=20)
    ap.add_argument("--eval_seed", type=int, default=123)
    ap.add_argument("--eval_seed_base", type=int, default=1000)
    ap.add_argument("--eval_steps", type=int, default=None)
    ap.add_argument("--dry_run", action="store_true")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    methods = default_methods()
    matrix_rows: List[Dict[str, object]] = []
    ckpts: Dict[str, Path] = {}

    for method in methods:
        label = str(method["label"])
        exp_name = f"case141_{label}_seed{args.seed}"
        run(build_method_cmd(project_root, args, exp_name, method), cwd=project_root, dry_run=args.dry_run)
        ckpts[label] = expected_ckpt(project_root / "outputs" / "checkpoints", exp_name)
        row = {"label": label, **{k: v for k, v in method.items() if k != 'label'}, "ckpt": str(ckpts[label])}
        matrix_rows.append(row)

    save_matrix(project_root, matrix_rows)

    baseline = ckpts["fedgrid_none"]
    for label, ckpt in ckpts.items():
        if label == "fedgrid_none":
            continue
        run(build_eval_cmd(project_root, args, baseline, ckpt, label), cwd=project_root, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
