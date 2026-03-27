#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple
import random

import pandas as pd

TOPOS = ["static", "random_reset"]


def bootstrap_ci(xs: List[float], n_boot: int = 10000, alpha: float = 0.05, seed: int = 1234) -> Tuple[float, float]:
    if not xs:
        return float("nan"), float("nan")
    if len(xs) == 1:
        return xs[0], xs[0]
    rng = random.Random(seed)
    means = []
    n = len(xs)
    for _ in range(int(n_boot)):
        sample = [xs[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_idx = max(0, int((alpha / 2.0) * len(means)) - 1)
    hi_idx = min(len(means) - 1, int((1.0 - alpha / 2.0) * len(means)) - 1)
    return means[lo_idx], means[hi_idx]


def read_seed_eval(eval_dir: Path, compare_label: str, topo: str) -> Dict[str, float]:
    b = eval_dir / f"per_episode_baseline_141_{topo}_k"  # prefix only
    g = eval_dir / f"per_episode_{compare_label}_141_{topo}_k"
    b_files = sorted(eval_dir.glob(f"per_episode_baseline_141_{topo}_k*_seed*.csv"))
    g_files = sorted(eval_dir.glob(f"per_episode_{compare_label}_141_{topo}_k*_seed*.csv"))
    if not b_files or not g_files:
        raise FileNotFoundError(f"Missing per_episode files in {eval_dir} for compare_label={compare_label} topo={topo}")
    df_b = pd.read_csv(b_files[0])
    df_g = pd.read_csv(g_files[0])
    merged = df_b.merge(df_g, on="episode", suffixes=("_b", "_g"))
    if merged.empty:
        raise ValueError(f"No matched episodes in {eval_dir} topo={topo}")
    ret_diff = (merged["return_g"] - merged["return_b"]).mean()
    pl_diff = (merged["p_loss_mean_g"] - merged["p_loss_mean_b"]).mean()
    vv_diff = (merged["v_viol_lin_mean_g"] - merged["v_viol_lin_mean_b"]).mean()
    return {
        "episodes": int(len(merged)),
        "return_diff_mean": float(ret_diff),
        "ploss_diff_mean": float(pl_diff),
        "vviol_diff_mean": float(vv_diff),
        "baseline_return_mean": float(merged["return_b"].mean()),
        "compare_return_mean": float(merged["return_g"].mean()),
        "baseline_ploss_mean": float(merged["p_loss_mean_b"].mean()),
        "compare_ploss_mean": float(merged["p_loss_mean_g"].mean()),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute paired seed-level stats from deterministic per-episode evaluation CSVs.")
    ap.add_argument("--suite_eval_root", required=True, type=str,
                    help="Root containing eval/<compare_label>_seed*/per_episode_*.csv, e.g. followup_runs/rr_k6_det40")
    ap.add_argument("--compare_label", required=True, type=str)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--n_boot", type=int, default=10000)
    ap.add_argument("--out_csv", type=str, default=None)
    args = ap.parse_args()

    root = Path(args.suite_eval_root).resolve()
    eval_root = root / "eval"
    out_csv = Path(args.out_csv).resolve() if args.out_csv else root / "agg" / f"paired_seed_stats_{args.compare_label}.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, object]] = []
    for topo in TOPOS:
        seed_rows = []
        ret_seed_means = []
        pl_seed_means = []
        vv_seed_means = []
        for seed in args.seeds:
            eval_dir = eval_root / f"{args.compare_label}_seed{seed}"
            if not eval_dir.exists():
                continue
            r = read_seed_eval(eval_dir, args.compare_label, topo)
            r["seed"] = seed
            r["topology_mode"] = topo
            seed_rows.append(r)
            ret_seed_means.append(float(r["return_diff_mean"]))
            pl_seed_means.append(float(r["ploss_diff_mean"]))
            vv_seed_means.append(float(r["vviol_diff_mean"]))

        if not seed_rows:
            continue

        ret_lo, ret_hi = bootstrap_ci(ret_seed_means, n_boot=args.n_boot, seed=1234)
        pl_lo, pl_hi = bootstrap_ci(pl_seed_means, n_boot=args.n_boot, seed=2234)
        vv_lo, vv_hi = bootstrap_ci(vv_seed_means, n_boot=args.n_boot, seed=3234)

        rows.append({
            "topology_mode": topo,
            "n_seeds": len(seed_rows),
            "episodes_per_seed": seed_rows[0]["episodes"],
            "return_diff_mean_across_seeds": sum(ret_seed_means) / len(ret_seed_means),
            "return_diff_ci95_lo": ret_lo,
            "return_diff_ci95_hi": ret_hi,
            "return_positive_seed_count": sum(x > 0 for x in ret_seed_means),
            "ploss_diff_mean_across_seeds": sum(pl_seed_means) / len(pl_seed_means),
            "ploss_diff_ci95_lo": pl_lo,
            "ploss_diff_ci95_hi": pl_hi,
            "ploss_negative_seed_count": sum(x < 0 for x in pl_seed_means),
            "vviol_diff_mean_across_seeds": sum(vv_seed_means) / len(vv_seed_means),
            "vviol_diff_ci95_lo": vv_lo,
            "vviol_diff_ci95_hi": vv_hi,
            "vviol_negative_seed_count": sum(x < 0 for x in vv_seed_means),
        })

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[SAVED] {out_csv}")
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
