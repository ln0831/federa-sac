#!/usr/bin/env python
"""Aggregate topology-shift summaries across multiple seeds.

This script reads multiple `summary_<case>_k<k>_seed<seed>.csv` files produced by
`evaluate_topology_shift.py` and computes mean±std across seeds for each group:
(algo, case, topology_mode, outage_k).

Usage (PowerShell):
  python aggregate_shift_results.py --search_dir .\eval_shift --out_csv .\eval_shift\agg.csv

Or specify exact files:
  python aggregate_shift_results.py --inputs .\eval_shift_seed0\summary_141_k4_seed0.csv `
                                   .\eval_shift_seed1\summary_141_k4_seed1.csv `
                                   .\eval_shift_seed2\summary_141_k4_seed2.csv `
                                   --out_csv .\eval_shift\agg.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np


NUM_FIELDS = [
    "return_mean",
    "return_std",  # this is per-episode std; we will aggregate it separately
    "v_viol_lin_mean",
    "p_loss_mean",
    "n_components_mean",
]


def _to_float(x, default=np.nan) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="*", default=None, help="Explicit list of summary CSV files.")
    ap.add_argument("--search_dir", type=str, default=".", help="Directory to search for summary_*.csv")
    ap.add_argument("--pattern", type=str, default="summary_*_seed*.csv", help="Glob pattern under search_dir")
    ap.add_argument("--out_csv", type=str, default="agg_summary.csv", help="Output aggregated CSV path")
    args = ap.parse_args()

    files: List[str] = []
    if args.inputs:
        files = list(args.inputs)
    else:
        files = glob.glob(os.path.join(args.search_dir, args.pattern))

    files = [f for f in files if os.path.isfile(f)]
    if not files:
        raise SystemExit(f"No files found. search_dir={args.search_dir} pattern={args.pattern}")

    rows_all: List[Dict] = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            rd = csv.DictReader(fh)
            for r in rd:
                r["_src"] = os.path.basename(f)
                rows_all.append(r)

    # group by algo/case/topology/outage_k
    groups: Dict[Tuple[str, str, str, str], List[Dict]] = defaultdict(list)
    for r in rows_all:
        key = (
            str(r.get("algo", "")),
            str(r.get("case", "")),
            str(r.get("topology_mode", "")),
            str(r.get("outage_k", "")),
        )
        groups[key].append(r)

    out_rows: List[Dict] = []
    for (algo, case, topo, ok), rs in sorted(groups.items()):
        out: Dict[str, object] = {
            "algo": algo,
            "case": case,
            "topology_mode": topo,
            "outage_k": ok,
            "n_seeds": len(rs),
        }
        # aggregate: mean±std across seeds of each metric's mean value
        for f in NUM_FIELDS:
            vals = [_to_float(r.get(f, np.nan)) for r in rs]
            vals = [v for v in vals if np.isfinite(v)]
            if vals:
                out[f"{f}_across_seeds_mean"] = float(np.mean(vals))
                out[f"{f}_across_seeds_std"] = float(np.std(vals))
            else:
                out[f"{f}_across_seeds_mean"] = np.nan
                out[f"{f}_across_seeds_std"] = np.nan

        out_rows.append(out)

    os.makedirs(os.path.dirname(args.out_csv) or ".", exist_ok=True)
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    print(f"Aggregated {len(files)} files -> {args.out_csv}")
    # Quick console summary
    for r in out_rows:
        print(
            f"{r['algo']:8s} case={r['case']} topo={r['topology_mode']:12s} k={r['outage_k']} "
            f"return={r['return_mean_across_seeds_mean']:.4f}±{r['return_mean_across_seeds_std']:.4f} "
            f"p_loss={r['p_loss_mean_across_seeds_mean']:.5f}±{r['p_loss_mean_across_seeds_std']:.5f}"
        )


if __name__ == "__main__":
    main()
