import subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
cmd = [sys.executable, str(root / 'train_gnn_fedgrid.py'), '--help']
result = subprocess.run(cmd, cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
assert result.returncode == 0, result.stderr
assert 'FedGrid' in result.stdout or 'fed' in result.stdout.lower()
