#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: run_postprocess.sh <python-bin> <suite-root>"
  exit 1
fi

PYTHON_BIN="$1"
SUITE_ROOT="$2"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

"$PYTHON_BIN" "$ROOT_DIR/summarize_fedgrid_suite_v6.py" --suite_root "$SUITE_ROOT"
"$PYTHON_BIN" "$ROOT_DIR/export_fedgrid_tables_v6.py" --suite_root "$SUITE_ROOT"
"$PYTHON_BIN" "$ROOT_DIR/make_fedgrid_figures_v6.py" --suite_root "$SUITE_ROOT"
"$PYTHON_BIN" "$ROOT_DIR/make_fedgrid_report_v6.py" --suite_root "$SUITE_ROOT"

echo "[OK] Postprocess completed for $SUITE_ROOT"
