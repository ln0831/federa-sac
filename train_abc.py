"""Convenience launcher for A/B/C training.

This script wraps the existing training entrypoints:
- train_fmasac.py (baseline FMASAC)
- train_gnn.py    (GNN-FMASAC)

It does not change training logic; it only assembles a *consistent*
scenario configuration and passes it through.

Scenarios
---------
A: tidal/QSTS disturbance, static topology
B: topology outages (random_reset), no extra disturbance
C: outages + tidal + localized step disturbance

You can still pass additional args after "--" and they will be forwarded
to the underlying trainer.

Examples
--------
A (tidal, static):
  python train_abc.py --algo baseline --case 141 --scenario A --reset_load_mode base

B (random_reset outages):
  python train_abc.py --algo gnn --case 141 --scenario B --outage_k 4 --outage_policy local

C (outages + tidal_step):
  python train_abc.py --algo gnn --case 141 --scenario C --reset_load_mode base --step_t 24 --step_factor 1.2
"""

import argparse
import os
import subprocess
import sys
from typing import List


def _scenario_flags(scenario: str) -> List[str]:
    sc = scenario.upper()
    if sc == 'A':
        return [
            '--topology_mode', 'static',
            '--disturbance', 'tidal',
        ]
    if sc == 'B':
        return [
            '--topology_mode', 'random_reset',
            '--disturbance', 'none',
        ]
    if sc == 'C':
        return [
            '--topology_mode', 'random_reset',
            '--disturbance', 'tidal_step',
        ]
    raise ValueError(f'Unknown scenario: {scenario} (use A/B/C)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--algo', type=str, default='baseline', choices=['baseline', 'gnn'])
    ap.add_argument('--case', type=str, default='141', choices=['33', '69', '141', 'ober', 'cartpole'])
    ap.add_argument('--scenario', type=str, required=True, choices=['A', 'B', 'C'])

    # Common scenario controls (forwarded to underlying trainer)
    ap.add_argument('--outage_k', type=int, default=None)
    ap.add_argument('--outage_policy', type=str, default=None, choices=['global', 'local'])
    ap.add_argument('--outage_radius', type=int, default=None)
    ap.add_argument('--avoid_slack_hops', type=int, default=None)
    ap.add_argument('--topology_seed', type=int, default=None)

    ap.add_argument('--disturbance', type=str, default=None, choices=['none', 'tidal', 'step', 'tidal_step'])
    ap.add_argument('--reset_load_mode', type=str, default=None, choices=['keep', 'base'])
    ap.add_argument('--tidal_period', type=int, default=None)
    ap.add_argument('--tidal_load_base', type=float, default=None)
    ap.add_argument('--tidal_load_amp', type=float, default=None)
    ap.add_argument('--tidal_pv_base', type=float, default=None)
    ap.add_argument('--tidal_pv_amp', type=float, default=None)
    ap.add_argument('--tidal_phase', type=float, default=None)
    ap.add_argument('--step_t', type=int, default=None)
    ap.add_argument('--step_factor', type=float, default=None)
    ap.add_argument('--step_target', type=str, default=None)
    ap.add_argument('--dist_seed', type=int, default=None)

    ap.add_argument('--dry_run', action='store_true', help='Print command only, do not execute.')

    # Everything after -- is forwarded verbatim
    args, extra = ap.parse_known_args()

    trainer = 'train_fmasac.py' if args.algo == 'baseline' else 'train_gnn.py'

    cmd = [sys.executable, trainer, '--case', str(args.case)]
    cmd += _scenario_flags(args.scenario)

    # Allow overriding disturbance explicitly
    if args.disturbance is not None:
        cmd += ['--disturbance', str(args.disturbance)]

    # Optional forwarded flags (only if user sets them)
    opt_pairs = [
        ('outage_k', args.outage_k),
        ('outage_policy', args.outage_policy),
        ('outage_radius', args.outage_radius),
        ('avoid_slack_hops', args.avoid_slack_hops),
        ('topology_seed', args.topology_seed),
        ('reset_load_mode', args.reset_load_mode),
        ('tidal_period', args.tidal_period),
        ('tidal_load_base', args.tidal_load_base),
        ('tidal_load_amp', args.tidal_load_amp),
        ('tidal_pv_base', args.tidal_pv_base),
        ('tidal_pv_amp', args.tidal_pv_amp),
        ('tidal_phase', args.tidal_phase),
        ('step_t', args.step_t),
        ('step_factor', args.step_factor),
        ('step_target', args.step_target),
        ('dist_seed', args.dist_seed),
    ]
    for k, v in opt_pairs:
        if v is None:
            continue
        cmd += [f'--{k}', str(v)]

    if extra:
        cmd += extra

    print('[train_abc] Command:')
    print('  ' + ' '.join(cmd))

    if args.dry_run:
        return

    env = os.environ.copy()
    subprocess.run(cmd, check=True, env=env)


if __name__ == '__main__':
    main()
