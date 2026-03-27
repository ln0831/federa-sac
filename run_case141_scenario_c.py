#!/usr/bin/env python3
"""Run a quantitative Scenario-C stress test without editing the original code.

This script wraps the existing project entrypoints:
  - export_rollout.py
  - plot_results.py

It exports rollout CSVs for baseline and one comparison model across multiple seeds,
then aggregates full-episode and post-step metrics into paper-friendly CSV files.

Typical use:
  python run_case141_scenario_c.py \
      --project_root ./codes-v10 \
      --baseline_ckpt_template ./followup_runs/rr_k6/checkpoints/best_fmasac_rr_k6_seed{seed}.pth \
      --compare_ckpt_template ./followup_runs/rr_k6/checkpoints/best_gnn_global_rr_k6_seed{seed}.pth \
      --compare_label gnn_global \
      --output_root ./scenario_c_runs
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


def run(cmd: Sequence[str], cwd: Path, dry_run: bool = False) -> None:
    pretty = " ".join(str(x) for x in cmd)
    print(f"\n[RUN] {pretty}")
    if dry_run:
        return
    subprocess.run(list(map(str, cmd)), cwd=str(cwd), check=True)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def mean(xs: List[float]) -> float:
    return float(sum(xs) / len(xs)) if xs else float("nan")


def pstdev(xs: List[float]) -> float:
    return float(statistics.pstdev(xs)) if len(xs) > 1 else 0.0


def as_float(x: str, default: float = math.nan) -> float:
    try:
        return float(x)
    except Exception:
        return default


def as_int(x: str, default: int = 0) -> int:
    try:
        return int(float(x))
    except Exception:
        return default


def summarize_rollout_csv(path: Path) -> Dict[str, float]:
    by_episode: Dict[int, List[Dict[str, str]]] = defaultdict(list)
    with path.open("r", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for row in rd:
            by_episode[as_int(row.get("episode", "0"))].append(row)

    ep_return: List[float] = []
    ep_ploss: List[float] = []
    ep_vviol: List[float] = []
    ep_ncomp: List[float] = []
    ep_vmin: List[float] = []
    ep_vmax: List[float] = []

    post_return: List[float] = []
    post_ploss: List[float] = []
    post_vviol: List[float] = []
    post_ncomp: List[float] = []

    for ep, rows in sorted(by_episode.items()):
        rewards = [as_float(r.get("reward_sum", "nan")) for r in rows]
        ploss = [as_float(r.get("p_loss", "nan")) for r in rows]
        vviol = [as_float(r.get("v_viol_lin_total", "nan")) for r in rows]
        ncomp = [as_float(r.get("n_components", "nan")) for r in rows]
        vmin = [as_float(r.get("v_min", "nan")) for r in rows]
        vmax = [as_float(r.get("v_max", "nan")) for r in rows]

        ep_return.append(sum(rewards))
        ep_ploss.append(mean(ploss))
        ep_vviol.append(mean(vviol))
        ep_ncomp.append(mean(ncomp))
        ep_vmin.append(mean(vmin))
        ep_vmax.append(mean(vmax))

        rows_post = [r for r in rows if as_int(r.get("step_active", "0"), 0) == 1]
        if not rows_post:
            # fallback for cases where step_active is unavailable: use second half of episode
            half = len(rows) // 2
            rows_post = rows[half:]

        post_rewards = [as_float(r.get("reward_sum", "nan")) for r in rows_post]
        post_pl = [as_float(r.get("p_loss", "nan")) for r in rows_post]
        post_vv = [as_float(r.get("v_viol_lin_total", "nan")) for r in rows_post]
        post_nc = [as_float(r.get("n_components", "nan")) for r in rows_post]

        post_return.append(sum(post_rewards))
        post_ploss.append(mean(post_pl))
        post_vviol.append(mean(post_vv))
        post_ncomp.append(mean(post_nc))

    return {
        "episode_return_mean": mean(ep_return),
        "episode_return_std": pstdev(ep_return),
        "p_loss_mean": mean(ep_ploss),
        "v_viol_lin_mean": mean(ep_vviol),
        "n_components_mean": mean(ep_ncomp),
        "v_min_mean": mean(ep_vmin),
        "v_max_mean": mean(ep_vmax),
        "post_step_return_mean": mean(post_return),
        "post_step_return_std": pstdev(post_return),
        "post_step_p_loss_mean": mean(post_ploss),
        "post_step_v_viol_lin_mean": mean(post_vviol),
        "post_step_n_components_mean": mean(post_ncomp),
        "n_episodes": float(len(by_episode)),
    }


def aggregate_per_seed_rows(rows: List[Dict[str, object]], key: str = "algo") -> List[Dict[str, object]]:
    metrics = [
        "episode_return_mean",
        "episode_return_std",
        "p_loss_mean",
        "v_viol_lin_mean",
        "n_components_mean",
        "v_min_mean",
        "v_max_mean",
        "post_step_return_mean",
        "post_step_return_std",
        "post_step_p_loss_mean",
        "post_step_v_viol_lin_mean",
        "post_step_n_components_mean",
    ]
    groups: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for r in rows:
        groups[str(r[key])].append(r)

    out_rows: List[Dict[str, object]] = []
    for algo, rs in sorted(groups.items()):
        out: Dict[str, object] = {"algo": algo, "n_seeds": len(rs)}
        for m in metrics:
            vals = [float(r[m]) for r in rs]
            out[f"{m}_across_seeds_mean"] = mean(vals)
            out[f"{m}_across_seeds_std"] = pstdev(vals)
        out_rows.append(out)
    return out_rows


def save_csv(rows: List[Dict[str, object]], path: Path) -> None:
    if not rows:
        raise ValueError(f"No rows to save: {path}")
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[SAVE] {path}")


def make_pairwise_report(agg_rows: List[Dict[str, object]], compare_label: str) -> List[Dict[str, object]]:
    by_algo = {str(r["algo"]): r for r in agg_rows}
    b = by_algo["baseline"]
    g = by_algo[compare_label]

    def f(row: Dict[str, object], name: str) -> float:
        return float(row[name])

    b_ret = f(b, "episode_return_mean_across_seeds_mean")
    g_ret = f(g, "episode_return_mean_across_seeds_mean")
    b_pl = f(b, "p_loss_mean_across_seeds_mean")
    g_pl = f(g, "p_loss_mean_across_seeds_mean")
    b_post_ret = f(b, "post_step_return_mean_across_seeds_mean")
    g_post_ret = f(g, "post_step_return_mean_across_seeds_mean")
    b_post_pl = f(b, "post_step_p_loss_mean_across_seeds_mean")
    g_post_pl = f(g, "post_step_p_loss_mean_across_seeds_mean")
    b_vv = f(b, "v_viol_lin_mean_across_seeds_mean")
    g_vv = f(g, "v_viol_lin_mean_across_seeds_mean")
    b_post_vv = f(b, "post_step_v_viol_lin_mean_across_seeds_mean")
    g_post_vv = f(g, "post_step_v_viol_lin_mean_across_seeds_mean")

    return [
        {
            "compare_label": compare_label,
            "episode_return_gain_abs": g_ret - b_ret,
            "episode_return_gain_pct": 100.0 * (g_ret - b_ret) / abs(b_ret) if b_ret != 0 else math.nan,
            "p_loss_delta": g_pl - b_pl,
            "p_loss_reduction_pct": 100.0 * (b_pl - g_pl) / b_pl if b_pl != 0 else math.nan,
            "post_step_return_gain_abs": g_post_ret - b_post_ret,
            "post_step_return_gain_pct": 100.0 * (g_post_ret - b_post_ret) / abs(b_post_ret) if b_post_ret != 0 else math.nan,
            "post_step_p_loss_delta": g_post_pl - b_post_pl,
            "post_step_p_loss_reduction_pct": 100.0 * (b_post_pl - g_post_pl) / b_post_pl if b_post_pl != 0 else math.nan,
            "v_viol_delta": g_vv - b_vv,
            "post_step_v_viol_delta": g_post_vv - b_post_vv,
        }
    ]


def fmt_template(tpl: str, seed: int) -> str:
    return str(tpl).format(seed=seed)


def build_export_cmd(
    python_exec: str,
    algo: str,
    ckpt: str,
    out_dir: Path,
    gpu: str,
    seed: int,
    episodes: int,
    steps: int | None,
    topology_mode: str,
    outage_k: int,
    outage_policy: str,
    outage_radius: int,
    avoid_slack_hops: int,
    reset_load_mode: str,
    tidal_period: int,
    tidal_load_base: float,
    tidal_load_amp: float,
    tidal_pv_base: float,
    tidal_pv_amp: float,
    tidal_phase: float,
    step_t: int,
    step_factor: float,
    step_target: str,
) -> List[str]:
    cmd = [
        python_exec, "export_rollout.py",
        "--algo", algo,
        "--case", "141",
        "--ckpt", ckpt,
        "--episodes", str(episodes),
        "--topology_mode", topology_mode,
        "--outage_k", str(outage_k),
        "--outage_policy", outage_policy,
        "--outage_radius", str(outage_radius),
        "--avoid_slack_hops", str(avoid_slack_hops),
        "--topology_seed", str(seed),
        "--disturbance", "tidal_step",
        "--reset_load_mode", reset_load_mode,
        "--tidal_period", str(tidal_period),
        "--tidal_load_base", str(tidal_load_base),
        "--tidal_load_amp", str(tidal_load_amp),
        "--tidal_pv_base", str(tidal_pv_base),
        "--tidal_pv_amp", str(tidal_pv_amp),
        "--tidal_phase", str(tidal_phase),
        "--step_t", str(step_t),
        "--step_factor", str(step_factor),
        "--step_target", step_target,
        "--dist_seed", str(seed),
        "--gpu", gpu,
        "--out_dir", str(out_dir),
    ]
    if steps is not None:
        cmd += ["--steps", str(steps)]
    return cmd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project_root", type=str, default=".")
    ap.add_argument("--output_root", type=str, default="./scenario_c_runs")
    ap.add_argument("--python_exec", type=str, default=sys.executable)
    ap.add_argument("--gpu", type=str, default="0")
    ap.add_argument("--baseline_ckpt_template", type=str, required=True)
    ap.add_argument("--compare_ckpt_template", type=str, required=True)
    ap.add_argument("--compare_label", type=str, default="gnn_global")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--episodes", type=int, default=20)
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--topology_mode", type=str, default="random_reset", choices=["static", "random_reset"])
    ap.add_argument("--outage_k", type=int, default=4)
    ap.add_argument("--outage_policy", type=str, default="local", choices=["global", "local"])
    ap.add_argument("--outage_radius", type=int, default=2)
    ap.add_argument("--avoid_slack_hops", type=int, default=1)
    ap.add_argument("--reset_load_mode", type=str, default="keep", choices=["keep", "base"])
    ap.add_argument("--tidal_period", type=int, default=96)
    ap.add_argument("--tidal_load_base", type=float, default=1.0)
    ap.add_argument("--tidal_load_amp", type=float, default=0.2)
    ap.add_argument("--tidal_pv_base", type=float, default=1.0)
    ap.add_argument("--tidal_pv_amp", type=float, default=0.5)
    ap.add_argument("--tidal_phase", type=float, default=0.0)
    ap.add_argument("--step_t", type=int, default=24)
    ap.add_argument("--step_factor", type=float, default=1.2)
    ap.add_argument("--step_target", type=str, default="random_agent", choices=["all", "random_agent", "agent0", "agent1", "agent2", "agent3"])
    ap.add_argument("--make_plots_seed0", action="store_true", default=False)
    ap.add_argument("--skip_existing", action="store_true", default=False)
    ap.add_argument("--dry_run", action="store_true", default=False)
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    output_root = Path(args.output_root).resolve()
    ensure_dir(output_root)

    per_seed_rows: List[Dict[str, object]] = []
    baseline_csvs: List[Path] = []
    compare_csvs: List[Path] = []

    for seed in args.seeds:
        seed_dir = output_root / f"seed{seed}"
        ensure_dir(seed_dir)

        baseline_ckpt = fmt_template(args.baseline_ckpt_template, seed)
        compare_ckpt = fmt_template(args.compare_ckpt_template, seed)

        baseline_csv = seed_dir / f"rollout_baseline_141_{args.topology_mode}_k{args.outage_k}_seed{seed}_disttidal_step.csv"
        compare_csv = seed_dir / f"rollout_{args.compare_label}_141_{args.topology_mode}_k{args.outage_k}_seed{seed}_disttidal_step.csv"

        if not (args.skip_existing and baseline_csv.exists()):
            cmd = build_export_cmd(
                python_exec=args.python_exec,
                algo="baseline",
                ckpt=baseline_ckpt,
                out_dir=seed_dir,
                gpu=args.gpu,
                seed=seed,
                episodes=args.episodes,
                steps=args.steps,
                topology_mode=args.topology_mode,
                outage_k=args.outage_k,
                outage_policy=args.outage_policy,
                outage_radius=args.outage_radius,
                avoid_slack_hops=args.avoid_slack_hops,
                reset_load_mode=args.reset_load_mode,
                tidal_period=args.tidal_period,
                tidal_load_base=args.tidal_load_base,
                tidal_load_amp=args.tidal_load_amp,
                tidal_pv_base=args.tidal_pv_base,
                tidal_pv_amp=args.tidal_pv_amp,
                tidal_phase=args.tidal_phase,
                step_t=args.step_t,
                step_factor=args.step_factor,
                step_target=args.step_target,
            )
            run(cmd, cwd=project_root, dry_run=args.dry_run)
        else:
            print(f"[SKIP] {baseline_csv}")

        if not (args.skip_existing and compare_csv.exists()):
            cmd = build_export_cmd(
                python_exec=args.python_exec,
                algo=args.compare_label,
                ckpt=compare_ckpt,
                out_dir=seed_dir,
                gpu=args.gpu,
                seed=seed,
                episodes=args.episodes,
                steps=args.steps,
                topology_mode=args.topology_mode,
                outage_k=args.outage_k,
                outage_policy=args.outage_policy,
                outage_radius=args.outage_radius,
                avoid_slack_hops=args.avoid_slack_hops,
                reset_load_mode=args.reset_load_mode,
                tidal_period=args.tidal_period,
                tidal_load_base=args.tidal_load_base,
                tidal_load_amp=args.tidal_load_amp,
                tidal_pv_base=args.tidal_pv_base,
                tidal_pv_amp=args.tidal_pv_amp,
                tidal_phase=args.tidal_phase,
                step_t=args.step_t,
                step_factor=args.step_factor,
                step_target=args.step_target,
            )
            run(cmd, cwd=project_root, dry_run=args.dry_run)
        else:
            print(f"[SKIP] {compare_csv}")

        baseline_csvs.append(baseline_csv)
        compare_csvs.append(compare_csv)

        if args.make_plots_seed0 and seed == args.seeds[0]:
            plot_dir = output_root / "plots_seed0"
            ensure_dir(plot_dir)
            cmd = [
                args.python_exec, "plot_results.py",
                "--baseline", str(baseline_csv),
                "--gnn", str(compare_csv),
                "--baseline_label", "baseline",
                "--gnn_label", args.compare_label,
                "--out_dir", str(plot_dir),
            ]
            run(cmd, cwd=project_root, dry_run=args.dry_run)

    if args.dry_run:
        print("[DONE] dry run only")
        return

    for seed, path in zip(args.seeds, baseline_csvs):
        row = {"algo": "baseline", "seed": seed, **summarize_rollout_csv(path)}
        per_seed_rows.append(row)
    for seed, path in zip(args.seeds, compare_csvs):
        row = {"algo": args.compare_label, "seed": seed, **summarize_rollout_csv(path)}
        per_seed_rows.append(row)

    agg_rows = aggregate_per_seed_rows(per_seed_rows)
    pair_rows = make_pairwise_report(agg_rows, args.compare_label)

    save_csv(per_seed_rows, output_root / "per_seed_summary.csv")
    save_csv(agg_rows, output_root / "agg_summary.csv")
    save_csv(pair_rows, output_root / "pairwise_report.csv")

    print("\n[DONE] Scenario-C suite finished.")
    print(f"  Output root: {output_root}")
    print(f"  Per-seed summary: {output_root / 'per_seed_summary.csv'}")
    print(f"  Aggregate summary: {output_root / 'agg_summary.csv'}")
    print(f"  Pairwise report:  {output_root / 'pairwise_report.csv'}")


if __name__ == "__main__":
    main()