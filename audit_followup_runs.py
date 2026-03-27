#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple

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


def read_baseline_rows(summary_csv: Path) -> Dict[str, Dict[str, float]]:
    rows: Dict[str, Dict[str, float]] = {}
    with summary_csv.open("r", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for r in rd:
            if str(r.get("algo", "")) != "baseline":
                continue
            topo = str(r.get("topology_mode", ""))
            rows[topo] = {
                "return_mean": float(r.get("return_mean", "nan")),
                "p_loss_mean": float(r.get("p_loss_mean", "nan")),
            }
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--followup_root", type=str, default="./followup_runs")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--suites", nargs="*", default=list(SUITES.keys()))
    ap.add_argument("--out_csv", type=str, default=None)
    ap.add_argument("--tol_return", type=float, default=1e-9)
    ap.add_argument("--tol_ploss", type=float, default=1e-12)
    args = ap.parse_args()

    followup_root = Path(args.followup_root).resolve()
    out_csv = Path(args.out_csv).resolve() if args.out_csv else followup_root / "audit_summary.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, object]] = []

    print(f"[AUDIT] followup_root={followup_root}")
    for suite in args.suites:
        if suite not in SUITES:
            print(f"[WARN] unknown suite skipped: {suite}")
            continue
        cfg = SUITES[suite]
        ckpt_dir = followup_root / suite / "checkpoints"
        eval_dir = followup_root / suite / "eval"
        print(f"\n=== {suite} ===")
        for seed in args.seeds:
            baseline_ckpt = ckpt_dir / cfg["baseline_ckpt"].format(seed=seed)
            print(f"seed {seed}: baseline_ckpt={'OK' if baseline_ckpt.exists() else 'MISSING'}")
            baseline_summaries: List[Tuple[str, Path]] = []
            for label in cfg["compare_labels"]:
                compare_ckpt = ckpt_dir / cfg["compare_ckpt"][label].format(seed=seed)
                summary_csv = eval_dir / f"{label}_seed{seed}" / f"summary_141_k{cfg['outage_k']}_seed{seed}.csv"
                status = {
                    "suite": suite,
                    "seed": seed,
                    "label": label,
                    "baseline_ckpt_exists": baseline_ckpt.exists(),
                    "compare_ckpt_exists": compare_ckpt.exists(),
                    "summary_exists": summary_csv.exists(),
                    "summary_path": str(summary_csv),
                }
                rows.append(status)
                print(
                    f"  {label:<17s} ckpt={'OK' if compare_ckpt.exists() else 'MISSING':<7s} "
                    f"eval={'OK' if summary_csv.exists() else 'MISSING'}"
                )
                if summary_csv.exists():
                    baseline_summaries.append((label, summary_csv))

            if len(baseline_summaries) >= 2:
                by_label = {label: read_baseline_rows(path) for label, path in baseline_summaries}
                for topo in ["static", "random_reset"]:
                    rets = []
                    pls = []
                    used = []
                    for label, d in by_label.items():
                        if topo in d:
                            rets.append(d[topo]["return_mean"])
                            pls.append(d[topo]["p_loss_mean"])
                            used.append(label)
                    if len(used) >= 2:
                        d_ret = max(rets) - min(rets)
                        d_pl = max(pls) - min(pls)
                        noisy = (d_ret > args.tol_return) or (d_pl > args.tol_ploss)
                        flag = "WARNING old/non-deterministic eval likely" if noisy else "OK paired"
                        print(
                            f"    baseline consistency @ {topo:<12s}: "
                            f"delta_return={d_ret:.6f}, delta_p_loss={d_pl:.6f} -> {flag}"
                        )

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["suite", "seed", "label"])
        w.writeheader()
        if rows:
            w.writerows(rows)
    print(f"\n[SAVED] {out_csv}")


if __name__ == "__main__":
    main()
