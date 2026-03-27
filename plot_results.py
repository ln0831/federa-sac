"""Plot rollout CSVs produced by export_rollout.py.

Creates PNG figures in the same directory as the input CSV.

Example:
  python plot_results.py --baseline ./rollouts/rollout_baseline_141_random_reset_k4_seed0.csv \
      --gnn ./rollouts/rollout_gnn_141_random_reset_k4_seed0.csv
"""

import argparse
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # ensure sorting
    df = df.sort_values(['episode', 't']).reset_index(drop=True)
    return df


def mean_over_episodes(df: pd.DataFrame, value_col: str) -> pd.Series:
    # align by t (some episodes may end early)
    return df.groupby('t')[value_col].mean()


def plot_two(curve_a, curve_b, label_a: str, label_b: str, title: str, ylabel: str, out_path: str, hlines=None):
    plt.figure()
    plt.plot(curve_a.index, curve_a.values, label=label_a)
    if curve_b is not None:
        plt.plot(curve_b.index, curve_b.values, label=label_b)
    if hlines:
        for y in hlines:
            plt.axhline(y=y, linestyle='--')
    plt.title(title)
    plt.xlabel('t')
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', type=str, required=True)
    ap.add_argument('--gnn', type=str, default=None)
    ap.add_argument('--baseline_label', type=str, default='baseline')
    ap.add_argument('--gnn_label', type=str, default='gnn')
    ap.add_argument('--out_dir', type=str, default=None)
    args = ap.parse_args()

    df_b = load_csv(args.baseline)
    df_g = load_csv(args.gnn) if args.gnn else None

    out_dir = args.out_dir or os.path.dirname(os.path.abspath(args.baseline))
    os.makedirs(out_dir, exist_ok=True)

    # reward
    rb = mean_over_episodes(df_b, 'reward_sum')
    rg = mean_over_episodes(df_g, 'reward_sum') if df_g is not None else None
    plot_two(rb, rg, args.baseline_label, args.gnn_label, 'Reward (mean over episodes)', 'reward_sum', os.path.join(out_dir, 'reward_mean.png'))

    # voltage bounds
    vmin_b = mean_over_episodes(df_b, 'v_min')
    vmin_g = mean_over_episodes(df_g, 'v_min') if df_g is not None else None
    plot_two(vmin_b, vmin_g, args.baseline_label, args.gnn_label, 'Voltage min (mean)', 'v_min (pu)', os.path.join(out_dir, 'vmin_mean.png'), hlines=[0.9])

    vmax_b = mean_over_episodes(df_b, 'v_max')
    vmax_g = mean_over_episodes(df_g, 'v_max') if df_g is not None else None
    plot_two(vmax_b, vmax_g, args.baseline_label, args.gnn_label, 'Voltage max (mean)', 'v_max (pu)', os.path.join(out_dir, 'vmax_mean.png'), hlines=[1.1])

    # violations
    vv_b = mean_over_episodes(df_b, 'v_viol_lin_total')
    vv_g = mean_over_episodes(df_g, 'v_viol_lin_total') if df_g is not None else None
    plot_two(vv_b, vv_g, args.baseline_label, args.gnn_label, 'Voltage violation (linear, mean)', 'v_viol_lin_total', os.path.join(out_dir, 'vviol_lin_mean.png'))

    vvs_b = mean_over_episodes(df_b, 'v_viol_sq_total')
    vvs_g = mean_over_episodes(df_g, 'v_viol_sq_total') if df_g is not None else None
    plot_two(vvs_b, vvs_g, args.baseline_label, args.gnn_label, 'Voltage violation (squared, mean)', 'v_viol_sq_total', os.path.join(out_dir, 'vviol_sq_mean.png'))

    # p_loss
    pl_b = mean_over_episodes(df_b, 'p_loss')
    pl_g = mean_over_episodes(df_g, 'p_loss') if df_g is not None else None
    plot_two(pl_b, pl_g, args.baseline_label, args.gnn_label, 'Line loss p_loss (mean)', 'p_loss', os.path.join(out_dir, 'p_loss_mean.png'))

    # connectivity
    nc_b = mean_over_episodes(df_b, 'n_components')
    nc_g = mean_over_episodes(df_g, 'n_components') if df_g is not None else None
    plot_two(nc_b, nc_g, args.baseline_label, args.gnn_label, 'Connectivity (#components, mean)', 'n_components', os.path.join(out_dir, 'n_components_mean.png'))

    print(f"Saved plots to: {out_dir}")


if __name__ == '__main__':
    main()
