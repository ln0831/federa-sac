"""Convenience launcher for A/B/C testing (rollout + plots).

This script calls:
  1) export_rollout.py  (baseline & gnn)
  2) plot_results.py    (overlay curves)

You must provide checkpoint paths for both models.

Scenarios
---------
A: tidal/QSTS disturbance, static topology
B: topology outages (random_reset), no extra disturbance
C: outages + tidal_step disturbance

Examples
--------
Scenario A:
  python test_abc.py --case 141 --scenario A \
      --baseline_ckpt .//best_fmasac_141.pth --gnn_ckpt .//best_gnn_141.pth \
      --episodes 20 --reset_load_mode base --out_dir ./eval_abc

Scenario C (paper-style localized outages):
  python test_abc.py --case 141 --scenario C --outage_k 4 --outage_policy local --outage_radius 2 --avoid_slack_hops 1 \
      --step_t 24 --step_factor 1.2 --step_target random_agent \
      --baseline_ckpt .//best_fmasac_141.pth --gnn_ckpt .//best_gnn_141.pth
"""

import argparse
import os
import subprocess
import sys
from typing import Dict, List, Tuple


def _scenario_defaults(sc: str) -> Tuple[str, str]:
    """Return (topology_mode, disturbance) for scenario."""
    sc = sc.upper()
    if sc == 'A':
        return 'static', 'tidal'
    if sc == 'B':
        return 'random_reset', 'none'
    if sc == 'C':
        return 'random_reset', 'tidal_step'
    raise ValueError(sc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--case', type=str, default='141', choices=['33', '69', '141', 'ober', 'cartpole'])
    ap.add_argument('--scenario', type=str, required=True, choices=['A', 'B', 'C'])

    ap.add_argument('--baseline_ckpt', type=str, required=True)
    ap.add_argument('--gnn_ckpt', type=str, required=True)

    ap.add_argument('--baseline_label', type=str, default='baseline', help='Label used in output filenames for the baseline model')
    ap.add_argument('--gnn_label', type=str, default='gnn', help='Label used in output filenames for the compared model (e.g., gnn_nobus)')

    ap.add_argument('--episodes', type=int, default=20)
    ap.add_argument('--steps', type=int, default=None)

    # Topology/outage
    ap.add_argument('--topology_mode', type=str, default=None, choices=['static','random_reset'],
                    help='Optional override for topology mode. If omitted, it is chosen by scenario (A=static, B/C=random_reset).')
    ap.add_argument('--topology_seed', type=int, default=0)
    ap.add_argument('--outage_k', type=int, default=4)
    ap.add_argument('--outage_policy', type=str, default='local', choices=['global', 'local'])
    ap.add_argument('--outage_radius', type=int, default=2)
    ap.add_argument('--avoid_slack_hops', type=int, default=1)

    # Disturbance
    ap.add_argument('--reset_load_mode', type=str, default='keep', choices=['keep', 'base'])
    ap.add_argument('--tidal_period', type=int, default=96)
    ap.add_argument('--tidal_load_base', type=float, default=1.0)
    ap.add_argument('--tidal_load_amp', type=float, default=0.2)
    ap.add_argument('--tidal_pv_base', type=float, default=1.0)
    ap.add_argument('--tidal_pv_amp', type=float, default=0.5)
    ap.add_argument('--tidal_phase', type=float, default=0.0)
    ap.add_argument('--step_t', type=int, default=24)
    ap.add_argument('--step_factor', type=float, default=1.2)
    ap.add_argument('--step_target', type=str, default='random_agent', choices=['all','random_agent','agent0','agent1','agent2','agent3'])
    ap.add_argument('--dist_seed', type=int, default=0)

    ap.add_argument('--no_plots', action='store_true', default=False)
    ap.add_argument('--out_dir', type=str, default='./eval_abc')

    args = ap.parse_args()

    topo_mode, dist = _scenario_defaults(args.scenario)
    if args.topology_mode is not None:
        topo_mode = str(args.topology_mode)

    os.makedirs(args.out_dir, exist_ok=True)

    def run_export(algo: str, ckpt: str) -> str:
        cmd = [
            sys.executable, 'export_rollout.py',
            '--algo', algo,
            '--case', str(args.case),
            '--ckpt', ckpt,
            '--episodes', str(args.episodes),
            '--topology_mode', topo_mode,
            '--outage_k', str(args.outage_k),
            '--topology_seed', str(args.topology_seed),
            '--outage_policy', str(args.outage_policy),
            '--outage_radius', str(args.outage_radius),
            '--avoid_slack_hops', str(args.avoid_slack_hops),
            '--disturbance', dist,
            '--reset_load_mode', str(args.reset_load_mode),
            '--tidal_period', str(args.tidal_period),
            '--tidal_load_base', str(args.tidal_load_base),
            '--tidal_load_amp', str(args.tidal_load_amp),
            '--tidal_pv_base', str(args.tidal_pv_base),
            '--tidal_pv_amp', str(args.tidal_pv_amp),
            '--tidal_phase', str(args.tidal_phase),
            '--step_t', str(args.step_t),
            '--step_factor', str(args.step_factor),
            '--step_target', str(args.step_target),
            '--dist_seed', str(args.dist_seed),
            '--out_dir', str(args.out_dir),
        ]
        if args.steps is not None:
            cmd += ['--steps', str(args.steps)]

        print('[test_abc] Running:', ' '.join(cmd))
        subprocess.run(cmd, check=True)

        # Export script has deterministic file name; re-construct it
        out_csv = os.path.join(
            args.out_dir,
            f"rollout_{algo}_{args.case}_{topo_mode}_k{args.outage_k}_seed{args.topology_seed}_dist{dist}.csv",
        )
        if not os.path.exists(out_csv):
            raise FileNotFoundError(out_csv)
        return out_csv

    csv_b = run_export(str(args.baseline_label), args.baseline_ckpt)
    csv_g = run_export(str(args.gnn_label), args.gnn_ckpt)

    if not args.no_plots:
        cmd = [sys.executable, 'plot_results.py', '--baseline', csv_b, '--gnn', csv_g, '--out_dir', args.out_dir,
               '--baseline_label', str(args.baseline_label), '--gnn_label', str(args.gnn_label)]
        print('[test_abc] Plotting:', ' '.join(cmd))
        subprocess.run(cmd, check=True)

    print('[test_abc] Done.')
    print('  baseline:', csv_b)
    print('  gnn     :', csv_g)


if __name__ == '__main__':
    main()
