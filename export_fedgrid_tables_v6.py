#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List

ROW_END = r"\\"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def escape_tex(text: str) -> str:
    mapping = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(mapping.get(ch, ch) for ch in str(text))


def build_table(rows: List[Dict[str, str]], caption: str, label: str) -> str:
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\small",
        "\\begin{tabular}{lrrrrr}",
        "\\hline",
        f"Method & $\\Delta$Return & 95\\% CI & $\\Delta$VViol & $\\Delta$PLoss & Better Seeds {ROW_END}",
        "\\hline",
    ]
    for row in rows:
        context_prefix = ""
        if any(row.get(k) for k in ["case", "outage_k", "outage_policy", "outage_radius"]):
            context_prefix = (
                f"[case={escape_tex(row.get('case', ''))}, "
                f"k={escape_tex(row.get('outage_k', ''))}, "
                f"policy={escape_tex(row.get('outage_policy', ''))}, "
                f"radius={escape_tex(row.get('outage_radius', ''))}] "
            )
        method_cell = f"{context_prefix}{escape_tex(row['method'])}"
        lines.append(
            f"{method_cell} & {row['delta_return']} & {escape_tex(row['ci95_return'])} & {row['delta_vviol']} & {row['delta_ploss']} & {escape_tex(row['better_seeds'])} {ROW_END}"
        )
    lines += [
        "\\hline",
        "\\end{tabular}",
        f"\\caption{{{escape_tex(caption)}}}",
        f"\\label{{{escape_tex(label)}}}",
        "\\end{table}",
        "",
    ]
    return "\n".join(lines)


def build_delta_only_ablation(rows: List[Dict[str, str]], caption: str, label: str) -> str:
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\small",
        "\\begin{tabular}{lrrrr}",
        "\\hline",
        f"Method & $\\Delta$Return & $\\Delta$VViol & $\\Delta$PLoss & Paper Score {ROW_END}",
        "\\hline",
    ]
    for row in rows:
        context_prefix = ""
        if any(row.get(k) for k in ["case", "outage_k", "outage_policy", "outage_radius"]):
            context_prefix = (
                f"[case={escape_tex(row.get('case', ''))}, "
                f"k={escape_tex(row.get('outage_k', ''))}, "
                f"policy={escape_tex(row.get('outage_policy', ''))}, "
                f"radius={escape_tex(row.get('outage_radius', ''))}] "
            )
        lines.append(
            f"{context_prefix}{escape_tex(row['method'])} & {row['delta_return']} & {row['delta_vviol']} & {row['delta_ploss']} & {row['paper_score']} {ROW_END}"
        )
    lines += [
        "\\hline",
        "\\end{tabular}",
        f"\\caption{{{escape_tex(caption)}}}",
        f"\\label{{{escape_tex(label)}}}",
        "\\end{table}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Export FedGrid-v6 LaTeX tables")
    ap.add_argument("--suite_root", required=True, type=str)
    args = ap.parse_args()

    suite_root = Path(args.suite_root).resolve()
    agg_dir = suite_root / "agg"
    main_rr = read_csv(agg_dir / "suite_paper_table_main_random_reset.csv")
    appendix_static = read_csv(agg_dir / "suite_paper_table_appendix_static.csv")

    tex_dir = suite_root / "reports" / "latex"
    tex_dir.mkdir(parents=True, exist_ok=True)
    (tex_dir / "table_main_random_reset.tex").write_text(
        build_table(
            main_rr,
            caption="Main paired-seed results on the random-reset topology-shift benchmark. Positive DeltaReturn is better; negative DeltaVViol and DeltaPLoss are better.",
            label="tab:fedgrid-main-random-reset",
        ),
        encoding="utf-8",
    )
    (tex_dir / "table_appendix_static.tex").write_text(
        build_table(
            appendix_static,
            caption="Appendix paired-seed results on the static in-distribution setting.",
            label="tab:fedgrid-appendix-static",
        ),
        encoding="utf-8",
    )
    (tex_dir / "table_ablation_random_reset.tex").write_text(
        build_delta_only_ablation(
            main_rr,
            caption="Random-reset ablation summary for FedGrid-v6.",
            label="tab:fedgrid-ablation-random-reset",
        ),
        encoding="utf-8",
    )
    print(f"[SAVED] {tex_dir}")


if __name__ == "__main__":
    main()
