#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

CONTEXT_FIELDS = ["case", "outage_k", "outage_policy", "outage_radius"]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(x: object, default: float = float("nan")) -> float:
    try:
        return float(x)
    except Exception:
        return default


def fmt(x: object, ndigits: int = 4) -> str:
    v = to_float(x)
    if v != v:
        return "nan"
    return f"{v:.{ndigits}f}"


def context_tuple(row: Dict[str, str]) -> Tuple[str, str, str, str]:
    return tuple(str(row.get(field, "")) for field in CONTEXT_FIELDS)


def context_label(context: Sequence[str]) -> str:
    case, outage_k, outage_policy, outage_radius = [str(x) for x in context]
    return f"case={case}, k={outage_k}, policy={outage_policy}, radius={outage_radius}"


def best_method(
    rows: List[Dict[str, str]],
    *,
    topo: str,
    context: Tuple[str, str, str, str],
    metric_key: str,
    higher_is_better: bool = True,
) -> Optional[Dict[str, str]]:
    candidates = [r for r in rows if str(r.get("topology_mode")) == topo and context_tuple(r) == context]
    if not candidates:
        return None
    return sorted(candidates, key=lambda r: to_float(r.get(metric_key)), reverse=higher_is_better)[0]


def tradeoff_status(row: Dict[str, str]) -> str:
    dvv = to_float(row.get("v_viol_lin_mean_diff_mean_across_seeds"))
    dpl = to_float(row.get("p_loss_mean_diff_mean_across_seeds"))
    worsened = []
    if dvv > 0:
        worsened.append("voltage violations")
    if dpl > 0:
        worsened.append("power loss")
    if worsened:
        return " with trade-off in " + " and ".join(worsened)
    return ""


def build_table(rows: List[Dict[str, str]], topo: str) -> str:
    selected = [r for r in rows if str(r.get("topology_mode")) == topo]
    if not selected:
        return ""
    selected = sorted(
        selected,
        key=lambda r: (
            str(r.get("case", "")),
            str(r.get("outage_k", "")),
            str(r.get("outage_policy", "")),
            str(r.get("outage_radius", "")),
            -to_float(r.get("return_diff_mean_across_seeds")),
        ),
    )
    lines = [
        "| case | k | policy | radius | method | Δreturn | 95% CI | Δvviol | Δploss | better seeds | paper score |",
        "|---|---:|---|---:|---|---:|---|---:|---:|---:|---:|",
    ]
    for r in selected:
        lines.append(
            "| {case} | {k} | {policy} | {radius} | {method} | {dret} | [{lo}, {hi}] | {dvv} | {dpl} | {n} | {score} |".format(
                case=r.get("case", ""),
                k=r.get("outage_k", ""),
                policy=r.get("outage_policy", ""),
                radius=r.get("outage_radius", ""),
                method=r.get("compare_label", ""),
                dret=fmt(r.get("return_diff_mean_across_seeds"), 3),
                lo=fmt(r.get("return_diff_ci95_lo"), 3),
                hi=fmt(r.get("return_diff_ci95_hi"), 3),
                dvv=fmt(r.get("v_viol_lin_mean_diff_mean_across_seeds"), 4),
                dpl=fmt(r.get("p_loss_mean_diff_mean_across_seeds"), 5),
                n=f"{int(to_float(r.get('return_better_seed_count'), 0.0))}/{int(to_float(r.get('n_seeds'), 0.0))}",
                score=fmt(r.get("paper_score"), 3),
            )
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate markdown summary for FedGrid-v6 suite")
    ap.add_argument("--suite_root", required=True, type=str)
    args = ap.parse_args()

    suite_root = Path(args.suite_root).resolve()
    paired_path = suite_root / "agg" / "suite_paired_metrics.csv"
    abs_path = suite_root / "agg" / "suite_absolute_metrics.csv"
    rank_path = suite_root / "agg" / "suite_rankings.csv"
    if not paired_path.exists() or not abs_path.exists() or not rank_path.exists():
        raise SystemExit("Missing aggregated CSVs. Run summarize_fedgrid_suite_v6.py first.")

    paired_rows = read_csv(paired_path)
    rank_rows = read_csv(rank_path)
    contexts = sorted({context_tuple(r) for r in paired_rows})
    rankings_by_context_topo: Dict[Tuple[Tuple[str, str, str, str], str], List[Dict[str, str]]] = defaultdict(list)
    for row in rank_rows:
        rankings_by_context_topo[(context_tuple(row), str(row.get("topology_mode", "")))].append(row)

    lines = [
        "# FedGrid v6 suite report",
        "",
        f"- Suite root: `{suite_root}`",
        f"- Paired metrics source: `{paired_path.name}`",
        f"- Absolute metrics source: `{abs_path.name}`",
        f"- Ranking source: `{rank_path.name}`",
        "",
        "## Headline findings by context",
        "",
    ]
    for context in contexts:
        lines.append(f"### Context: {context_label(context)}")
        lines.append("")
        best_rr = best_method(
            paired_rows,
            topo="random_reset",
            context=context,
            metric_key="return_diff_mean_across_seeds",
            higher_is_better=True,
        )
        best_static = best_method(
            paired_rows,
            topo="static",
            context=context,
            metric_key="return_diff_mean_across_seeds",
            higher_is_better=True,
        )
        best_rr_vviol = best_method(
            paired_rows,
            topo="random_reset",
            context=context,
            metric_key="v_viol_lin_mean_diff_mean_across_seeds",
            higher_is_better=False,
        )
        rr_top3 = rankings_by_context_topo.get((context, "random_reset"), [])[:3]
        if best_rr:
            lines.append(
                f"- Main benchmark best paired return on `random_reset`: **{best_rr['compare_label']}** with paired Δreturn={fmt(best_rr['return_diff_mean_across_seeds'], 3)} and 95% CI [{fmt(best_rr['return_diff_ci95_lo'], 3)}, {fmt(best_rr['return_diff_ci95_hi'], 3)}]{tradeoff_status(best_rr)}."
            )
        if best_static:
            lines.append(
                f"- In-distribution best paired return on `static`: **{best_static['compare_label']}** with paired Δreturn={fmt(best_static['return_diff_mean_across_seeds'], 3)}{tradeoff_status(best_static)}."
            )
        if best_rr_vviol:
            lines.append(
                f"- Best method on `random_reset` by voltage-violation reduction: **{best_rr_vviol['compare_label']}** with Δvviol={fmt(best_rr_vviol['v_viol_lin_mean_diff_mean_across_seeds'], 4)}."
            )
        if rr_top3:
            lines.append(
                "- Top-3 methods on `random_reset` by paired return gain in this context: "
                + ", ".join(f"{r['rank']}) {r['compare_label']}" for r in rr_top3)
                + "."
            )
        if not any([best_rr, best_static, best_rr_vviol, rr_top3]):
            lines.append("- No paired rows were available for this context.")
        lines.append("")

    lines += [
        "## Manuscript-ready claims",
        "",
        "1. Use `random_reset` as the main table because it targets topology-shift generalization rather than in-distribution control.",
        "2. Use paired seed deltas and CIs as the headline statistical evidence; keep absolute means in the appendix or supplementary material.",
        "3. If a method improves return but worsens voltage violations or active-power loss, write it as a control trade-off instead of a strict win.",
        "4. Put `static` in the appendix as an in-distribution sanity check.",
        "",
        "## Random-reset paired table",
        "",
        build_table(paired_rows, topo="random_reset"),
        "",
        "## Static paired table",
        "",
        build_table(paired_rows, topo="static"),
        "",
        "## Suggested results narrative",
        "",
        "Our main comparison should emphasize the random-reset topology-shift benchmark, where the clustered-distillation family is designed to help under client heterogeneity and changing grid structure. The static benchmark should only be used to verify that the stronger federated mechanism does not sacrifice in-distribution performance.",
    ]

    out_path = suite_root / "reports" / "fedgrid_v6_report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"[SAVED] {out_path}")


if __name__ == "__main__":
    main()
