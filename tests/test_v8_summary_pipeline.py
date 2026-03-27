from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from export_fedgrid_tables_v6 import escape_tex


def write_csv(path: Path, rows: list[dict[str, object]], *, fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fieldnames:
        raise ValueError(f"Need fieldnames when writing empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames or list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_suite(
    root: Path,
    *,
    compare_labels: list[str] | None = None,
    mismatch: bool = False,
    duplicate_episode: bool = False,
    missing_per_episode_labels: set[str] | None = None,
) -> Path:
    compare_labels = compare_labels or ["fedgrid_topo_proto"]
    missing_per_episode_labels = missing_per_episode_labels or set()
    suite = root / "outputs" / "suites" / "test_summary_pipeline"
    if suite.exists():
        shutil.rmtree(suite)
    for label in compare_labels:
        for seed in [0, 1]:
            d = suite / "eval" / f"{label}_seed{seed}"
            summary_rows = [
                {"algo": "fedgrid_none", "case": "141", "topology_mode": "random_reset", "outage_k": "6", "outage_policy": "local", "outage_radius": "2", "return": "10", "v_viol_lin_mean": "1.0", "p_loss_mean": "0.50", "n_components_mean": "1"},
                {"algo": label, "case": "141", "topology_mode": "random_reset", "outage_k": "6", "outage_policy": "local", "outage_radius": "2", "return": "12", "v_viol_lin_mean": "0.8", "p_loss_mean": "0.45", "n_components_mean": "1"},
            ]
            write_csv(d / f"summary_141_k6_seed{seed}.csv", summary_rows)
            baseline_rows = [
                {"episode": 0, "return": "10.0", "v_viol_lin_mean": "1.0", "p_loss_mean": "0.50", "n_components_mean": "1", "outage_policy": "local", "outage_radius": "2"},
                {"episode": 1, "return": "10.1", "v_viol_lin_mean": "1.0", "p_loss_mean": "0.50", "n_components_mean": "1", "outage_policy": "local", "outage_radius": "2"},
            ]
            compare_rows = [
                {"episode": 0, "return": "12.0", "v_viol_lin_mean": "0.8", "p_loss_mean": "0.45", "n_components_mean": "1", "outage_policy": "local", "outage_radius": "2"},
                {"episode": 1, "return": "12.1", "v_viol_lin_mean": "0.8", "p_loss_mean": "0.45", "n_components_mean": "1", "outage_policy": "local", "outage_radius": "2"},
            ]
            if mismatch:
                compare_rows = compare_rows[:1]
            if duplicate_episode:
                compare_rows.append(compare_rows[-1].copy())
            write_csv(d / f"per_episode_fedgrid_none_141_random_reset_k6_seed{seed}.csv", baseline_rows)
            if label not in missing_per_episode_labels:
                write_csv(d / f"per_episode_{label}_141_random_reset_k6_seed{seed}.csv", compare_rows)
    return suite


def run_script(script_name: str, *args: str, cwd_root: Path | None = None) -> subprocess.CompletedProcess[str]:
    root = cwd_root or ROOT
    return subprocess.run(
        [sys.executable, str(root / script_name), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_report_inputs(suite: Path) -> None:
    agg = suite / "agg"
    write_csv(
        agg / "suite_paired_metrics.csv",
        [
            {
                "compare_label": "fedgrid_topo_proto",
                "case": "141",
                "outage_k": "6",
                "outage_policy": "local",
                "outage_radius": "2",
                "topology_mode": "random_reset",
                "return_diff_mean_across_seeds": "1.200",
                "return_diff_ci95_lo": "0.900",
                "return_diff_ci95_hi": "1.500",
                "v_viol_lin_mean_diff_mean_across_seeds": "-0.1000",
                "p_loss_mean_diff_mean_across_seeds": "-0.02000",
                "return_better_seed_count": "2",
                "n_seeds": "2",
                "paper_score": "12.0",
            },
            {
                "compare_label": "fedgrid_v4_cluster_distill",
                "case": "141",
                "outage_k": "8",
                "outage_policy": "global",
                "outage_radius": "1",
                "topology_mode": "random_reset",
                "return_diff_mean_across_seeds": "1.500",
                "return_diff_ci95_lo": "1.100",
                "return_diff_ci95_hi": "1.800",
                "v_viol_lin_mean_diff_mean_across_seeds": "-0.0500",
                "p_loss_mean_diff_mean_across_seeds": "0.01000",
                "return_better_seed_count": "2",
                "n_seeds": "2",
                "paper_score": "10.0",
            },
        ],
    )
    write_csv(
        agg / "suite_absolute_metrics.csv",
        [
            {"algo": "fedgrid_none", "case": "141", "topology_mode": "random_reset", "outage_k": "6", "outage_policy": "local", "outage_radius": "2", "n_seeds": "2", "return_mean": "10.0", "return_std": "0.1"}
        ],
    )
    write_csv(
        agg / "suite_rankings.csv",
        [
            {"case": "141", "outage_k": "6", "outage_policy": "local", "outage_radius": "2", "topology_mode": "random_reset", "rank": "1", "compare_label": "fedgrid_topo_proto", "return_delta": "1.200", "paper_score": "12.0"},
            {"case": "141", "outage_k": "8", "outage_policy": "global", "outage_radius": "1", "topology_mode": "random_reset", "rank": "1", "compare_label": "fedgrid_v4_cluster_distill", "return_delta": "1.500", "paper_score": "10.0"},
        ],
    )


def build_multi_context_figure_inputs(suite: Path) -> None:
    agg = suite / "agg"
    write_csv(
        agg / "suite_paper_table_main_random_reset.csv",
        [
            {"case": "141", "outage_k": "6", "outage_policy": "local", "outage_radius": "2", "topology_mode": "random_reset", "method": "fedgrid_topo_proto", "delta_return": "1.2", "ci95_return": "[0.9,1.5]", "delta_vviol": "-0.1", "delta_ploss": "-0.02", "better_seeds": "2/2", "paper_score": "12.0"},
            {"case": "141", "outage_k": "8", "outage_policy": "global", "outage_radius": "1", "topology_mode": "random_reset", "method": "fedgrid_v4_cluster_distill", "delta_return": "1.5", "ci95_return": "[1.1,1.8]", "delta_vviol": "-0.05", "delta_ploss": "0.01", "better_seeds": "2/2", "paper_score": "10.0"},
        ],
    )
    write_csv(
        agg / "suite_paper_table_appendix_static.csv",
        [
            {"case": "141", "outage_k": "6", "outage_policy": "local", "outage_radius": "2", "topology_mode": "static", "method": "fedgrid_topo_proto", "delta_return": "0.5", "ci95_return": "[0.2,0.8]", "delta_vviol": "-0.02", "delta_ploss": "-0.01", "better_seeds": "2/2", "paper_score": "8.0"}
        ],
    )


def test_escape_tex_does_not_double_escape_generated_sequences() -> None:
    assert escape_tex(r"\{}") == r"\textbackslash{}\{\}"


def test_summary_pipeline_end_to_end(tmp_path: Path) -> None:
    suite = build_suite(tmp_path)
    subprocess.check_call([sys.executable, str(ROOT / "summarize_fedgrid_suite_v6.py"), "--suite_root", str(suite)])
    subprocess.check_call([sys.executable, str(ROOT / "export_fedgrid_tables_v6.py"), "--suite_root", str(suite)])
    subprocess.check_call([sys.executable, str(ROOT / "make_fedgrid_figures_v6.py"), "--suite_root", str(suite)])
    subprocess.check_call([sys.executable, str(ROOT / "make_fedgrid_report_v6.py"), "--suite_root", str(suite)])
    paired = (suite / "agg" / "suite_paired_metrics.csv").read_text(encoding="utf-8")
    assert "outage_policy" in paired and "outage_radius" in paired
    tex = (suite / "reports" / "latex" / "table_main_random_reset.tex").read_text(encoding="utf-8")
    assert "\\caption{" in tex
    report = (suite / "reports" / "fedgrid_v6_report.md").read_text(encoding="utf-8")
    assert "Headline findings by context" in report


def test_absolute_metrics_dedup_baseline(tmp_path: Path) -> None:
    suite = build_suite(tmp_path, compare_labels=["fedgrid_topo_proto", "fedgrid_v4_cluster_distill"])
    subprocess.check_call([sys.executable, str(ROOT / "summarize_fedgrid_suite_v6.py"), "--suite_root", str(suite)])
    abs_rows = read_csv_rows(suite / "agg" / "suite_absolute_metrics.csv")
    baseline = [r for r in abs_rows if r["algo"] == "fedgrid_none" and r["topology_mode"] == "random_reset"]
    assert len(baseline) == 1
    assert baseline[0]["n_seeds"] == "2"
    dedup_long = read_csv_rows(suite / "agg" / "suite_absolute_long_dedup.csv")
    baseline_seed_rows = [r for r in dedup_long if r["algo"] == "fedgrid_none"]
    assert len(baseline_seed_rows) == 2


def test_summary_missing_per_episode_rows_fails_fast(tmp_path: Path) -> None:
    suite = build_suite(tmp_path, compare_labels=["fedgrid_topo_proto", "fedgrid_v4_cluster_distill"], missing_per_episode_labels={"fedgrid_v4_cluster_distill"})
    proc = run_script("summarize_fedgrid_suite_v6.py", "--suite_root", str(suite))
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "Evaluation output completeness check failed" in combined
    assert "Per-episode rows missing ['fedgrid_v4_cluster_distill']" in combined


def test_episode_alignment_mismatch_raises(tmp_path: Path) -> None:
    suite = build_suite(tmp_path, mismatch=True)
    proc = run_script("summarize_fedgrid_suite_v6.py", "--suite_root", str(suite))
    assert proc.returncode != 0
    assert "Episode alignment mismatch" in (proc.stderr + proc.stdout)


def test_duplicate_episode_ids_raises(tmp_path: Path) -> None:
    suite = build_suite(tmp_path, duplicate_episode=True)
    proc = run_script("summarize_fedgrid_suite_v6.py", "--suite_root", str(suite))
    assert proc.returncode != 0
    assert "Duplicate episode ids" in (proc.stderr + proc.stdout)


def test_report_scopes_headlines_by_context(tmp_path: Path) -> None:
    suite = tmp_path / "outputs" / "suites" / "report_contexts"
    build_report_inputs(suite)
    subprocess.check_call([sys.executable, str(ROOT / "make_fedgrid_report_v6.py"), "--suite_root", str(suite)])
    report = (suite / "reports" / "fedgrid_v6_report.md").read_text(encoding="utf-8")
    assert "### Context: case=141, k=6, policy=local, radius=2" in report
    assert "### Context: case=141, k=8, policy=global, radius=1" in report
    assert "Top-3 methods on `random_reset` by paired return gain in this context" in report


def test_figure_multi_context_input_raises(tmp_path: Path) -> None:
    suite = tmp_path / "outputs" / "suites" / "figure_multicontext"
    build_multi_context_figure_inputs(suite)
    proc = run_script("make_fedgrid_figures_v6.py", "--suite_root", str(suite))
    assert proc.returncode != 0
    assert "contains multiple evaluation contexts" in (proc.stdout + proc.stderr)
