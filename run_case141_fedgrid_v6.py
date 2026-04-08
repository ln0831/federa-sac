#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


METHOD_LIBRARY: List[Dict[str, object]] = [
    {"label": "fedgrid_none", "fed_mode": "none", "group": "baseline"},
    {
        "label": "fedgrid_topo_proto",
        "fed_mode": "topo_proto",
        "fed_proto_source": "hybrid",
        "group": "baseline_plus",
    },
    {
        "label": "fedgrid_v4_cluster_distill",
        "fed_mode": "topo_proto",
        "fed_proto_source": "hybrid",
        "fed_clustered": True,
        "fed_cluster_knn": 2,
        "fed_cluster_threshold": 0.58,
        "fed_max_clusters": 4,
        "fed_inter_cluster_scale": 0.08,
        "fed_cluster_self_boost": 0.10,
        "fed_distill_coef": 0.10,
        "fed_distill_steps": 1,
        "fed_distill_batch_size": 128,
        "fed_distill_same_cluster_only": True,
        "group": "main",
    },
    {
        "label": "fedgrid_v4_cluster_nodistill",
        "fed_mode": "topo_proto",
        "fed_proto_source": "hybrid",
        "fed_clustered": True,
        "fed_cluster_knn": 2,
        "fed_cluster_threshold": 0.58,
        "fed_max_clusters": 4,
        "fed_inter_cluster_scale": 0.08,
        "fed_cluster_self_boost": 0.10,
        "fed_distill_coef": 0.0,
        "fed_distill_steps": 1,
        "fed_distill_batch_size": 128,
        "fed_distill_same_cluster_only": True,
        "group": "tune",
    },
    {
        "label": "fedgrid_v4_cluster_gentle",
        "fed_mode": "topo_proto",
        "fed_proto_source": "hybrid",
        "fed_clustered": True,
        "fed_cluster_knn": 2,
        "fed_cluster_threshold": 0.70,
        "fed_max_clusters": 4,
        "fed_inter_cluster_scale": 0.03,
        "fed_cluster_self_boost": 0.15,
        "fed_distill_coef": 0.03,
        "fed_distill_steps": 1,
        "fed_distill_batch_size": 128,
        "fed_distill_same_cluster_only": True,
        "group": "tune",
    },
    {
        "label": "fedgrid_v4_cluster_dropout",
        "fed_mode": "topo_proto",
        "fed_proto_source": "hybrid",
        "fed_clustered": True,
        "fed_cluster_knn": 2,
        "fed_cluster_threshold": 0.58,
        "fed_max_clusters": 4,
        "fed_inter_cluster_scale": 0.08,
        "fed_cluster_self_boost": 0.10,
        "fed_distill_coef": 0.10,
        "fed_distill_steps": 1,
        "fed_distill_batch_size": 128,
        "fed_distill_same_cluster_only": True,
        "fed_client_dropout": 0.25,
        "group": "robustness",
    },
    {
        "label": "fedgrid_v4_cluster_byzantine",
        "fed_mode": "topo_proto",
        "fed_proto_source": "hybrid",
        "fed_clustered": True,
        "fed_cluster_knn": 2,
        "fed_cluster_threshold": 0.58,
        "fed_max_clusters": 4,
        "fed_inter_cluster_scale": 0.08,
        "fed_cluster_self_boost": 0.10,
        "fed_distill_coef": 0.10,
        "fed_distill_steps": 1,
        "fed_distill_batch_size": 128,
        "fed_distill_same_cluster_only": True,
        "fed_byzantine_frac": 0.25,
        "fed_byzantine_mode": "noise",
        "fed_byzantine_strength": 0.5,
        "group": "robustness",
    },
]

PRESETS = {
    "main": ["fedgrid_none", "fedgrid_topo_proto", "fedgrid_v4_cluster_distill"],
    "ablation": ["fedgrid_none", "fedgrid_topo_proto", "fedgrid_v4_cluster_distill"],
    "tune_seed2": [
        "fedgrid_none",
        "fedgrid_topo_proto",
        "fedgrid_v4_cluster_distill",
        "fedgrid_v4_cluster_nodistill",
        "fedgrid_v4_cluster_gentle",
    ],
    "robustness": ["fedgrid_none", "fedgrid_v4_cluster_distill", "fedgrid_v4_cluster_dropout", "fedgrid_v4_cluster_byzantine"],
    "full": [m["label"] for m in METHOD_LIBRARY],
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def shell_join(parts: Sequence[object]) -> str:
    return shlex.join([str(x) for x in parts])


def run(cmd: Sequence[str], cwd: Path, dry_run: bool = False) -> None:
    pretty = shell_join(cmd)
    print(f"\n[RUN] {pretty}")
    if dry_run:
        return
    subprocess.run(list(map(str, cmd)), cwd=str(cwd), check=True)


def expected_ckpt(ckpt_dir: Path, exp_name: str) -> Path:
    return ckpt_dir / f"best_{exp_name}.pth"


def add_flag(cmd: List[str], name: str, value: object) -> None:
    if isinstance(value, bool):
        cmd.append(f"--{name}" if value else f"--no_{name}")
    else:
        cmd.extend([f"--{name}", str(value)])


def add_bool_arg(parser: argparse.ArgumentParser, name: str, default: bool, help_text: str) -> None:
    dest = name.replace("-", "_")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(f"--{name}", dest=dest, action="store_true", help=f"Enable {help_text}.")
    group.add_argument(f"--no_{name}", dest=dest, action="store_false", help=f"Disable {help_text}.")
    parser.set_defaults(**{dest: default})


def build_common_flags(args, seed: int) -> List[str]:
    experiment_seed = int(args.experiment_seed_base) + int(seed)
    val_seed_base = int(args.val_seed_base) + (1000 * int(seed))
    flags = [
        "--case", "141",
        "--gpu", str(args.gpu),
        "--epochs", str(args.epochs),
        "--val_episodes", str(args.val_episodes),
        "--experiment_seed", str(experiment_seed),
        "--val_seed_base", str(val_seed_base),
        "--topology_mode", str(args.train_topology_mode),
        "--outage_k", str(args.outage_k),
        "--outage_policy", str(args.outage_policy),
        "--outage_radius", str(args.outage_radius),
        "--avoid_slack_hops", str(args.avoid_slack_hops),
        "--topology_seed", str(seed),
        "--bus_gnn_scope", str(args.bus_gnn_scope),
        "--mixer_gat_ramp_epochs", str(args.mixer_gat_ramp_epochs),
        "--mixer_gate_init_bias", str(args.mixer_gate_init_bias),
        "--mixer_gnn_lr_scale", str(args.mixer_gnn_lr_scale),
        "--mixer_gate_lr_scale", str(args.mixer_gate_lr_scale),
        "--edge_drop", str(args.edge_drop),
        "--bus_gnn_lr_scale", str(args.bus_gnn_lr_scale),
        "--fed_start_after", str(args.fed_start_after),
    ]
    add_flag(flags, "bus_gnn_use_base_topology", bool(args.bus_gnn_use_base_topology))
    add_flag(flags, "mixer_use_base_topology", bool(args.mixer_use_base_topology))
    add_flag(flags, "fed_reset_optimizers", bool(args.fed_reset_optimizers))
    add_flag(flags, "fed_apply_trust_gate", bool(args.fed_apply_trust_gate))
    return flags


def build_train_cmd(project_root: Path, args, suite_root: Path, exp_name: str, method: Dict[str, object], seed: int) -> List[str]:
    ckpt_dir = suite_root / "checkpoints"
    log_dir = suite_root / "logs"
    ensure_dir(ckpt_dir)
    ensure_dir(log_dir)
    cmd: List[str] = [
        sys.executable,
        str(project_root / args.train_script),
        "--save_dir", str(ckpt_dir),
        "--log_dir", str(log_dir),
        "--exp_name", exp_name,
        *build_common_flags(args, seed),
    ]
    for key, value in method.items():
        if key in {"label", "group"}:
            continue
        add_flag(cmd, key, value)
    return cmd


def build_eval_cmd(project_root: Path, args, suite_root: Path, baseline_ckpt: Path, compare_ckpt: Path, compare_label: str, seed: int) -> List[str]:
    out_dir = suite_root / "eval" / f"{compare_label}_seed{seed}"
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
        "--topology_seed", str(seed),
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


def save_csv(rows: List[Dict[str, object]], out_csv: Path) -> Path:
    ensure_dir(out_csv.parent)
    if not rows:
        raise ValueError(f"Refusing to write empty CSV without schema: {out_csv}")
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
    print(f"[SAVED] {out_csv}")
    return out_csv


def save_json(data: object, out_json: Path) -> Path:
    ensure_dir(out_json.parent)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[SAVED] {out_json}")
    return out_json


def parse_methods(spec: str | None, preset: str) -> List[Dict[str, object]]:
    library = {str(m["label"]): dict(m) for m in METHOD_LIBRARY}
    if spec and spec.strip() and spec.strip() != "preset":
        wanted = [x.strip() for x in str(spec).split(",") if x.strip()]
    else:
        wanted = list(PRESETS[preset])
    if not wanted or wanted == ["all"]:
        return [dict(m) for m in METHOD_LIBRARY]
    missing = [m for m in wanted if m not in library]
    if missing:
        raise SystemExit(f"Unknown methods: {missing}. Available={sorted(library)}")
    return [library[m] for m in wanted]


def ckpt_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    if path.stat().st_size <= 0:
        return "empty"
    return "ready"


def method_labels(methods: Iterable[Dict[str, object]]) -> List[str]:
    return [str(m["label"]) for m in methods]


def write_shell_script(path: Path, commands: List[str]) -> None:
    ensure_dir(path.parent)
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", ""] + commands + [""]
    path.write_text("\n".join(lines), encoding="utf-8")
    path.chmod(0o755)
    print(f"[SAVED] {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Case141 FedGrid-v6 experiment suite runner")
    ap.add_argument("--project_root", type=str, default=".")
    ap.add_argument("--suite_name", type=str, default="case141_fedgrid_v6")
    ap.add_argument("--suite_root", type=str, default=None)
    ap.add_argument("--train_script", type=str, default="train_gnn_fedgrid.py")
    ap.add_argument("--eval_script", type=str, default="evaluate_topology_shift_deterministic.py")
    ap.add_argument("--preset", type=str, default="main", choices=sorted(PRESETS))
    ap.add_argument("--methods", type=str, default="preset", help="Comma-separated labels, 'all', or 'preset'.")
    ap.add_argument("--paper_tag", type=str, default="main_table")
    ap.add_argument("--gpu", type=str, default="0")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--val_episodes", type=int, default=5)
    ap.add_argument("--experiment_seed_base", type=int, default=7000)
    ap.add_argument("--val_seed_base", type=int, default=17000)
    ap.add_argument("--train_topology_mode", type=str, default="random_reset", choices=["static", "random_reset"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--outage_k", type=int, default=4)
    ap.add_argument("--outage_policy", type=str, default="local", choices=["global", "local"])
    ap.add_argument("--outage_radius", type=int, default=2)
    ap.add_argument("--avoid_slack_hops", type=int, default=1)
    ap.add_argument("--bus_gnn_scope", type=str, default="global", choices=["global", "local"])
    add_bool_arg(ap, "bus_gnn_use_base_topology", default=True, help_text="bus GNN base-topology edges")
    add_bool_arg(ap, "mixer_use_base_topology", default=True, help_text="mixer base-topology edges")
    ap.add_argument("--mixer_gat_ramp_epochs", type=int, default=50)
    ap.add_argument("--mixer_gate_init_bias", type=float, default=-5.0)
    ap.add_argument("--mixer_gnn_lr_scale", type=float, default=0.1)
    ap.add_argument("--mixer_gate_lr_scale", type=float, default=0.1)
    ap.add_argument("--edge_drop", type=float, default=0.10)
    ap.add_argument("--bus_gnn_lr_scale", type=float, default=0.1)
    ap.add_argument("--fed_start_after", type=int, default=2000)
    add_bool_arg(ap, "fed_reset_optimizers", default=False, help_text="reset optimizer state after federated rounds")
    add_bool_arg(ap, "fed_apply_trust_gate", default=False, help_text="apply trust gating during parameter mixing and distillation")
    ap.add_argument("--eval_episodes", type=int, default=20)
    ap.add_argument("--eval_seed_base", type=int, default=1000)
    ap.add_argument("--eval_steps", type=int, default=None)
    ap.add_argument("--skip_existing", action="store_true")
    mode_group = ap.add_mutually_exclusive_group()
    mode_group.add_argument("--train_only", action="store_true")
    mode_group.add_argument("--eval_only", action="store_true")
    ap.add_argument("--no_post", action="store_true", help="Skip automatic summarize/report generation.")
    ap.add_argument("--dry_run", action="store_true")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    suite_root = Path(args.suite_root).resolve() if args.suite_root else (project_root / "outputs" / "suites" / args.suite_name)
    ensure_dir(suite_root)
    ensure_dir(suite_root / "manifests")

    methods = parse_methods(args.methods, args.preset)
    labels = method_labels(methods)
    if "fedgrid_none" not in labels:
        raise SystemExit("Methods must include fedgrid_none as the paired baseline.")

    run_rows: List[Dict[str, object]] = []
    command_rows: List[Dict[str, object]] = []
    ckpts: Dict[tuple[str, int], Path] = {}

    for seed in args.seeds:
        for method in methods:
            label = str(method["label"])
            exp_name = f"case141_{label}_seed{seed}"
            ckpt = expected_ckpt(suite_root / "checkpoints", exp_name)
            ckpts[(label, seed)] = ckpt
            train_cmd = build_train_cmd(project_root, args, suite_root, exp_name, method, seed)
            row = {
                "suite_name": args.suite_name,
                "suite_preset": args.preset,
                "paper_tag": args.paper_tag,
                "seed": seed,
                "label": label,
                "group": method.get("group", ""),
                "exp_name": exp_name,
                "ckpt": str(ckpt),
                "ckpt_status_pre": ckpt_status(ckpt),
                **{k: v for k, v in method.items() if k not in {"label", "group"}},
            }
            run_rows.append(row)
            command_rows.append({"stage": "train", "seed": seed, "label": label, "cmd": shell_join(train_cmd)})
            if not args.eval_only:
                if args.skip_existing and ckpt_status(ckpt) == "ready":
                    print(f"[SKIP] checkpoint exists: {ckpt}")
                else:
                    run(train_cmd, cwd=project_root, dry_run=args.dry_run)

        baseline_ckpt = ckpts[("fedgrid_none", seed)]
        if args.train_only:
            continue
        for method in methods:
            label = str(method["label"])
            if label == "fedgrid_none":
                continue
            compare_ckpt = ckpts[(label, seed)]
            eval_dir = suite_root / "eval" / f"{label}_seed{seed}"
            expected_summary = eval_dir / f"summary_141_k{args.outage_k}_seed{seed}.csv"
            eval_cmd = build_eval_cmd(project_root, args, suite_root, baseline_ckpt, compare_ckpt, label, seed)
            command_rows.append({"stage": "eval", "seed": seed, "label": label, "cmd": shell_join(eval_cmd)})
            if args.skip_existing and expected_summary.exists():
                print(f"[SKIP] eval summary exists: {expected_summary}")
            else:
                run(eval_cmd, cwd=project_root, dry_run=args.dry_run)

    for row in run_rows:
        ckpt = Path(str(row["ckpt"]))
        row["ckpt_status_post"] = ckpt_status(ckpt)
        row["ckpt_bytes"] = ckpt.stat().st_size if ckpt.exists() else 0

    matrix_csv = save_csv(run_rows, suite_root / "manifests" / "fedgrid_v6_run_matrix.csv")
    save_csv(command_rows, suite_root / "manifests" / "fedgrid_v6_commands.csv")
    save_json(
        {
            "suite_name": args.suite_name,
            "suite_preset": args.preset,
            "paper_tag": args.paper_tag,
            "project_root": str(project_root),
            "suite_root": str(suite_root),
            "seeds": list(args.seeds),
            "methods": methods,
            "matrix_csv": str(matrix_csv),
        },
        suite_root / "manifests" / "fedgrid_v6_suite_manifest.json",
    )

    summarize_cmd = [sys.executable, str(project_root / "summarize_fedgrid_suite_v6.py"), "--suite_root", str(suite_root)]
    latex_cmd = [sys.executable, str(project_root / "export_fedgrid_tables_v6.py"), "--suite_root", str(suite_root)]
    figure_cmd = [sys.executable, str(project_root / "make_fedgrid_figures_v6.py"), "--suite_root", str(suite_root)]
    report_cmd = [sys.executable, str(project_root / "make_fedgrid_report_v6.py"), "--suite_root", str(suite_root)]
    write_shell_script(
        suite_root / "manifests" / "fedgrid_v6_postprocess.sh",
        [shell_join(summarize_cmd), shell_join(latex_cmd), shell_join(figure_cmd), shell_join(report_cmd)],
    )

    if args.no_post or args.train_only or args.dry_run:
        return

    run(summarize_cmd, cwd=project_root, dry_run=False)
    run(latex_cmd, cwd=project_root, dry_run=False)
    run(figure_cmd, cwd=project_root, dry_run=False)
    run(report_cmd, cwd=project_root, dry_run=False)


if __name__ == "__main__":
    main()
