#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import matplotlib.pyplot as plt

CONTEXT_FIELDS = ["case", "outage_k", "outage_policy", "outage_radius"]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(x: object, default: float = float("nan")) -> float:
    try:
        return float(x)
    except Exception:
        return default


def context_tuple(row: Dict[str, str]) -> Tuple[str, str, str, str]:
    return tuple(str(row.get(field, "")) for field in CONTEXT_FIELDS)


def context_label(context: Sequence[str]) -> str:
    case, outage_k, outage_policy, outage_radius = [str(x) for x in context]
    return f"case={case}, k={outage_k}, policy={outage_policy}, radius={outage_radius}"


def require_single_context(rows: List[Dict[str, str]], source_name: str) -> Tuple[str, str, str, str]:
    contexts = sorted({context_tuple(r) for r in rows})
    if len(contexts) > 1:
        preview = "; ".join(context_label(ctx) for ctx in contexts[:4])
        raise SystemExit(
            f"Figure input {source_name} contains multiple evaluation contexts ({len(contexts)}): {preview}. "
            "Restrict figure generation to a single context suite or add context-specific plotting."
        )
    return contexts[0] if contexts else ("", "", "", "")


def save_bar(
    rows: List[Dict[str, str]],
    value_key: str,
    title: str,
    out_path: Path,
    *,
    higher_is_better: bool = True,
) -> None:
    if not rows:
        return
    ctx = require_single_context(rows, out_path.name)
    rows = sorted(rows, key=lambda r: to_float(r.get(value_key)), reverse=higher_is_better)
    labels = [r.get("method", "") for r in rows]
    values = [to_float(r.get(value_key)) for r in rows]
    fig = plt.figure(figsize=(10, 4.8))
    ax = fig.add_subplot(111)
    ax.bar(labels, values)
    title_suffix = f"\n[{context_label(ctx)}]" if any(ctx) else ""
    ax.set_title(title + title_suffix)
    ax.set_ylabel(value_key)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)
    print(f"[SAVED] {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate paper-ready FedGrid-v6 figures")
    ap.add_argument("--suite_root", required=True, type=str)
    args = ap.parse_args()

    suite_root = Path(args.suite_root).resolve()
    agg_dir = suite_root / "agg"
    fig_dir = suite_root / "reports" / "figures"
    rr_rows = read_csv(agg_dir / "suite_paper_table_main_random_reset.csv")
    st_rows = read_csv(agg_dir / "suite_paper_table_appendix_static.csv")
    save_bar(rr_rows, "delta_return", "FedGrid-v6 paired return gain on random_reset", fig_dir / "random_reset_delta_return.png", higher_is_better=True)
    save_bar(rr_rows, "delta_vviol", "FedGrid-v6 paired voltage-violation delta on random_reset", fig_dir / "random_reset_delta_vviol.png", higher_is_better=False)
    save_bar(rr_rows, "delta_ploss", "FedGrid-v6 paired power-loss delta on random_reset", fig_dir / "random_reset_delta_ploss.png", higher_is_better=False)
    save_bar(st_rows, "delta_return", "FedGrid-v6 paired return gain on static", fig_dir / "static_delta_return.png", higher_is_better=True)


if __name__ == "__main__":
    main()
