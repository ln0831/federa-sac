#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

SUITES = {
    "rr_k6": {
        "outage_k": 6,
        "compare_labels": ["gnn_global", "gnn_nobus"],
        "baseline_ckpt": "best_fmasac_rr_k6_seed{seed}.pth",
        "compare_ckpt": {
            "gnn_global": "best_gnn_global_rr_k6_seed{seed}.pth",
            "gnn_nobus": "best_gnn_nobus_rr_k6_seed{seed}.pth",
        },
    },
    "static_k6_shift": {
        "outage_k": 6,
        "compare_labels": ["gnn_global", "gnn_nobus"],
        "baseline_ckpt": "best_fmasac_static_k6_shift_seed{seed}.pth",
        "compare_ckpt": {
            "gnn_global": "best_gnn_global_static_k6_shift_seed{seed}.pth",
            "gnn_nobus": "best_gnn_nobus_static_k6_shift_seed{seed}.pth",
        },
    },
    "fed_rr_k4": {
        "outage_k": 4,
        "compare_labels": ["gnn_global_none", "gnn_global_fedavg", "gnn_global_topo"],
        "baseline_ckpt": "best_fmasac_fed_rr_k4_seed{seed}.pth",
        "compare_ckpt": {
            "gnn_global_none": "best_gnn_global_none_fed_rr_k4_seed{seed}.pth",
            "gnn_global_fedavg": "best_gnn_global_fedavg_fed_rr_k4_seed{seed}.pth",
            "gnn_global_topo": "best_gnn_global_topo_fed_rr_k4_seed{seed}.pth",
        },
    },
    "fed_static_k4": {
        "outage_k": 4,
        "compare_labels": ["gnn_global_none", "gnn_global_fedavg", "gnn_global_topo"],
        "baseline_ckpt": "best_fmasac_fed_static_k4_seed{seed}.pth",
        "compare_ckpt": {
            "gnn_global_none": "best_gnn_global_none_fed_static_k4_seed{seed}.pth",
            "gnn_global_fedavg": "best_gnn_global_fedavg_fed_static_k4_seed{seed}.pth",
            "gnn_global_topo": "best_gnn_global_topo_fed_static_k4_seed{seed}.pth",
        },
    },
}


def run(cmd: List[str], cwd: Path, dry_run: bool = False) -> None:
    pretty = " ".join(str(x) for x in cmd)
    print(f"\n[RUN] {pretty}")
    if dry_run:
        return
    subprocess.run(list(map(str, cmd)), cwd=str(cwd), check=True)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


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
        out_rows.append({
            "topology_mode": topo,
            "baseline_n_seeds": int(float(b["n_seeds"])),
            f"{compare_label}_n_seeds": int(float(g["n_seeds"])),
            "baseline_return_mean": b_ret,
            f"{compare_label}_return_mean": g_ret,
            "return_gain_abs": g_ret - b_ret,
            "return_gain_pct": 100.0 * (g_ret - b_ret) / abs(b_ret) if b_ret != 0 else float("nan"),
            "baseline_p_loss_mean": b_pl,
            f"{compare_label}_p_loss_mean": g_pl,
            "p_loss_delta": g_pl - b_pl,
            "p_loss_reduction_pct": 100.0 * (b_pl - g_pl) / b_pl if b_pl != 0 else float("nan"),
        })
    ensure_dir(out_csv.parent)
    if out_rows:
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            w.writeheader()
            w.writerows(out_rows)
        print(f"[PAIRWISE] Saved {out_csv}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project_root", type=str, default=".")
    ap.add_argument("--followup_root", type=str, default="./followup_runs")
    ap.add_argument("--suite", required=True, choices=list(SUITES.keys()))
    ap.add_argument("--python_exec", type=str, default=sys.executable)
    ap.add_argument("--eval_script", type=str, default="evaluate_topology_shift_deterministic.py")
    ap.add_argument("--output_tag", type=str, default="det40")
    ap.add_argument("--gpu", type=str, default="0")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--episodes", type=int, default=40)
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--eval_seed_base", type=int, default=12345)
    ap.add_argument("--outage_policy", type=str, default="local", choices=["global", "local"])
    ap.add_argument("--outage_radius", type=int, default=2)
    ap.add_argument("--avoid_slack_hops", type=int, default=1)
    ap.add_argument("--skip_existing", action="store_true", default=False)
    ap.add_argument("--dry_run", action="store_true", default=False)
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    followup_root = Path(args.followup_root).resolve()
    cfg = SUITES[args.suite]
    ckpt_dir = followup_root / args.suite / "checkpoints"
    out_root = followup_root / f"{args.suite}_{args.output_tag}"
    eval_root = out_root / "eval"
    agg_root = out_root / "agg"
    ensure_dir(eval_root)
    ensure_dir(agg_root)

    missing: List[Dict[str, object]] = []
    summary_map: Dict[str, List[Path]] = {label: [] for label in cfg["compare_labels"]}

    for seed in args.seeds:
        baseline_ckpt = ckpt_dir / cfg["baseline_ckpt"].format(seed=seed)
        for label in cfg["compare_labels"]:
            compare_ckpt = ckpt_dir / cfg["compare_ckpt"][label].format(seed=seed)
            if not baseline_ckpt.exists() or not compare_ckpt.exists():
                missing.append({
                    "suite": args.suite,
                    "seed": seed,
                    "label": label,
                    "baseline_ckpt": str(baseline_ckpt),
                    "baseline_exists": baseline_ckpt.exists(),
                    "compare_ckpt": str(compare_ckpt),
                    "compare_exists": compare_ckpt.exists(),
                })
                print(f"[MISS] suite={args.suite} seed={seed} label={label}: checkpoint missing")
                continue

            out_dir = eval_root / f"{label}_seed{seed}"
            ensure_dir(out_dir)
            summary_csv = out_dir / f"summary_141_k{cfg['outage_k']}_seed{seed}.csv"
            summary_map[label].append(summary_csv)
            if args.skip_existing and summary_csv.exists():
                print(f"[SKIP] {summary_csv}")
                continue

            cmd = [
                args.python_exec,
                args.eval_script,
                "--case", "141",
                "--baseline_ckpt", str(baseline_ckpt),
                "--gnn_ckpt", str(compare_ckpt),
                "--baseline_name", "baseline",
                "--gnn_name", label,
                "--episodes", str(args.episodes),
                "--topology_seed", str(seed),
                "--eval_seed_base", str(int(args.eval_seed_base) + int(seed) * 1000),
                "--outage_k", str(cfg["outage_k"]),
                "--outage_policy", str(args.outage_policy),
                "--outage_radius", str(args.outage_radius),
                "--avoid_slack_hops", str(args.avoid_slack_hops),
                "--gpu", str(args.gpu),
                "--out_dir", str(out_dir),
            ]
            if args.steps is not None:
                cmd += ["--steps", str(args.steps)]
            run(cmd, cwd=project_root, dry_run=args.dry_run)

    if not args.dry_run:
        for label, paths in summary_map.items():
            paths_exist = [p for p in paths if p.exists()]
            if not paths_exist:
                continue
            agg_csv = agg_root / f"agg_{label}.csv"
            cmd = [
                args.python_exec,
                "aggregate_shift_results.py",
                "--inputs",
                *[str(p) for p in paths_exist],
                "--out_csv",
                str(agg_csv),
            ]
            run(cmd, cwd=project_root, dry_run=False)
            make_pairwise_report(agg_csv, label, agg_root / f"pairwise_{label}.csv")

        missing_csv = out_root / "missing_items.csv"
        if missing:
            with missing_csv.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(missing[0].keys()))
                w.writeheader()
                w.writerows(missing)
            print(f"[SAVED] {missing_csv}")
        else:
            if missing_csv.exists():
                missing_csv.unlink()

    print(f"\n[DONE] deterministic reevaluation finished: {out_root}")


if __name__ == "__main__":
    main()
