#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED = [
    'run_case141_fedgrid_v6.py',
    'train_gnn_fedgrid.py',
    'evaluate_topology_shift_deterministic.py',
    'summarize_fedgrid_suite_v6.py',
    'export_fedgrid_tables_v6.py',
    'make_fedgrid_figures_v6.py',
    'make_fedgrid_report_v6.py',
    'env_141.py',
    'fedgrid_federated.py',
]


def status(path: Path) -> str:
    return 'ok' if path.exists() else 'missing'


def main() -> int:
    ap = argparse.ArgumentParser(description='Preflight checker for the unified FedGrid runtime bundle')
    ap.add_argument('--project_root', type=str, default='.')
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    checks = {name: project_root / name for name in REQUIRED}
    report = {name: {'path': str(path), 'status': status(path)} for name, path in checks.items()}
    print(json.dumps(report, ensure_ascii=False, indent=2))

    missing = [name for name, info in report.items() if info['status'] != 'ok']
    if missing:
        print('\n[FAIL] Missing required paths: ' + ', '.join(missing), file=sys.stderr)
        return 1

    print('\n[OK] Unified runtime bundle looks ready.')
    print('[INFO] Suggested next step: run pytest -q tests, then run main preset with --dry_run.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
