from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_runner_flags_and_shell_quoting(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    suite_root = tmp_path / "test_runner_flags space"
    cmd = [
        sys.executable,
        str(root / "run_case141_fedgrid_v6.py"),
        "--project_root", str(root),
        "--suite_root", str(suite_root),
        "--seeds", "0",
        "--epochs", "1",
        "--val_episodes", "1",
        "--eval_episodes", "1",
        "--no_bus_gnn_use_base_topology",
        "--no_mixer_use_base_topology",
        "--dry_run",
        "--no_post",
    ]
    out = subprocess.check_output(cmd, text=True)
    assert "--no_bus_gnn_use_base_topology" in out
    assert "--no_mixer_use_base_topology" in out
    sh = (suite_root / "manifests" / "fedgrid_v6_postprocess.sh").read_text(encoding="utf-8")
    assert "--suite_root" in sh
    assert f"'{suite_root}'" in sh


def test_train_only_and_eval_only_are_mutually_exclusive(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    suite_root = tmp_path / "mutually-exclusive"
    cmd = [
        sys.executable,
        str(root / "run_case141_fedgrid_v6.py"),
        "--project_root", str(root),
        "--suite_root", str(suite_root),
        "--seeds", "0",
        "--train_only",
        "--eval_only",
        "--dry_run",
        "--no_post",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    assert proc.returncode != 0
    stderr = (proc.stderr or "")
    assert "not allowed with argument" in stderr or "mutually exclusive" in stderr


def test_tune_seed2_preset_expands_new_cluster_variants(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    suite_root = tmp_path / "tune-seed2"
    cmd = [
        sys.executable,
        str(root / "run_case141_fedgrid_v6.py"),
        "--project_root", str(root),
        "--suite_root", str(suite_root),
        "--preset", "tune_seed2",
        "--methods", "preset",
        "--seeds", "2",
        "--epochs", "1",
        "--val_episodes", "1",
        "--eval_episodes", "1",
        "--dry_run",
        "--no_post",
    ]
    out = subprocess.check_output(cmd, text=True)
    assert "case141_fedgrid_v4_cluster_nodistill_seed2" in out
    assert "case141_fedgrid_v4_cluster_gentle_seed2" in out


def test_runner_forwards_reproducibility_and_federation_safety_flags(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    suite_root = tmp_path / "repro-fed-safety"
    cmd = [
        sys.executable,
        str(root / "run_case141_fedgrid_v6.py"),
        "--project_root", str(root),
        "--suite_root", str(suite_root),
        "--seeds", "0",
        "--epochs", "1",
        "--val_episodes", "1",
        "--eval_episodes", "1",
        "--experiment_seed_base", "7000",
        "--val_seed_base", "17000",
        "--fed_start_after", "2000",
        "--no_fed_reset_optimizers",
        "--no_fed_apply_trust_gate",
        "--dry_run",
        "--no_post",
    ]
    out = subprocess.check_output(cmd, text=True)
    assert "--experiment_seed 7000" in out
    assert "--val_seed_base 17000" in out
    assert "--fed_start_after 2000" in out
    assert "--no_fed_reset_optimizers" in out
    assert "--no_fed_apply_trust_gate" in out
