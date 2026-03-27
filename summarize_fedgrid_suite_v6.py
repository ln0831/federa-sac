#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import random
from collections import defaultdict
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

PAIR_METRICS = [
    ("return", 1.0),
    ("v_viol_lin_mean", -1.0),
    ("p_loss_mean", -1.0),
    ("n_components_mean", -1.0),
]
TOPOLOGIES = ["random_reset", "static"]
CONTEXT_FIELDS = ["case", "outage_k", "outage_policy", "outage_radius", "topology_mode"]
SUMMARY_LONG_FIELDS = ["compare_label", "seed", "algo", "case", "topology_mode", "outage_k", "outage_policy", "outage_radius"]
EPISODE_LONG_FIELDS = SUMMARY_LONG_FIELDS + ["episode"]
SEED_LEVEL_BASE_FIELDS = ["compare_label", "seed", *CONTEXT_FIELDS, "n_episodes", "alignment_drop_frac"]
PAIRED_FIELDS = ["compare_label", *CONTEXT_FIELDS, "n_seeds", "episodes_per_seed", "paper_score"]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(x: object, default: float = float("nan")) -> float:
    try:
        return float(x)
    except Exception:
        return default


def mean(xs: Iterable[float]) -> float:
    vals = [float(x) for x in xs if math.isfinite(float(x))]
    if not vals:
        return float("nan")
    return sum(vals) / len(vals)


def std(xs: Iterable[float]) -> float:
    """Sample standard deviation across finite values (denominator n-1)."""
    vals = [float(x) for x in xs if math.isfinite(float(x))]
    if len(vals) <= 1:
        return 0.0 if vals else float("nan")
    mu = mean(vals)
    return (sum((x - mu) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5


def quantile(sorted_vals: Sequence[float], q: float) -> float:
    vals = [float(x) for x in sorted_vals if math.isfinite(float(x))]
    if not vals:
        return float("nan")
    if len(vals) == 1:
        return vals[0]
    q = min(1.0, max(0.0, float(q)))
    pos = (len(vals) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return vals[lo]
    frac = pos - lo
    return vals[lo] * (1.0 - frac) + vals[hi] * frac


def bootstrap_ci(xs: List[float], n_boot: int = 5000, alpha: float = 0.05, seed: int = 1234) -> Tuple[float, float]:
    vals = [float(x) for x in xs if math.isfinite(float(x))]
    if not vals:
        return float("nan"), float("nan")
    if len(vals) == 1:
        return vals[0], vals[0]
    rng = random.Random(seed)
    means = []
    n = len(vals)
    for _ in range(int(n_boot)):
        sample = [vals[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    return quantile(means, alpha / 2.0), quantile(means, 1.0 - alpha / 2.0)


def infer_outage_policy(row: Dict[str, str]) -> str:
    return str(row.get("outage_policy", ""))


def infer_outage_radius(row: Dict[str, str]) -> str:
    return str(row.get("outage_radius", ""))


def format_run_group(key: Tuple[str, int, str, str, str, str, str]) -> str:
    compare_label, seed, case, outage_k, outage_policy, outage_radius, topo = key
    return (
        f"compare_label={compare_label}, seed={seed}, case={case}, outage_k={outage_k}, "
        f"outage_policy={outage_policy}, outage_radius={outage_radius}, topology_mode={topo}"
    )


def validate_eval_completeness(
    summary_rows: List[Dict[str, object]],
    episode_rows: List[Dict[str, object]],
    *,
    baseline_label: str,
) -> None:
    summary_groups: Dict[Tuple[str, int, str, str, str, str, str], set[str]] = defaultdict(set)
    episode_groups: Dict[Tuple[str, int, str, str, str, str, str], set[str]] = defaultdict(set)
    for row in summary_rows:
        key = (
            str(row.get("compare_label", "")),
            int(row.get("seed", 0)),
            str(row.get("case", "")),
            str(row.get("outage_k", "")),
            str(row.get("outage_policy", "")),
            str(row.get("outage_radius", "")),
            str(row.get("topology_mode", "")),
        )
        summary_groups[key].add(str(row.get("algo", "")))
    for row in episode_rows:
        key = (
            str(row.get("compare_label", "")),
            int(row.get("seed", 0)),
            str(row.get("case", "")),
            str(row.get("outage_k", "")),
            str(row.get("outage_policy", "")),
            str(row.get("outage_radius", "")),
            str(row.get("topology_mode", "")),
        )
        episode_groups[key].add(str(row.get("algo", "")))

    all_keys = sorted(set(summary_groups) | set(episode_groups))
    problems: List[str] = []
    for key in all_keys:
        compare_label = key[0]
        expected = {baseline_label, compare_label}
        summary_algos = summary_groups.get(key, set())
        episode_algos = episode_groups.get(key, set())
        ctx = format_run_group(key)
        if key not in summary_groups:
            problems.append(f"Missing summary rows for {ctx}")
        if key not in episode_groups:
            problems.append(f"Missing per-episode rows for {ctx}")
        missing_summary = sorted(expected - summary_algos)
        if missing_summary:
            problems.append(f"Summary rows missing {missing_summary} for {ctx}")
        missing_episode = sorted(expected - episode_algos)
        if missing_episode:
            problems.append(f"Per-episode rows missing {missing_episode} for {ctx}")

    if problems:
        preview = "\n- ".join(problems[:12])
        more = "" if len(problems) <= 12 else f"\n... and {len(problems) - 12} more integrity issue(s)."
        raise ValueError("Evaluation output completeness check failed:\n- " + preview + more)


def collect_long_rows(suite_root: Path) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    long_summary_rows: List[Dict[str, object]] = []
    long_episode_rows: List[Dict[str, object]] = []
    for summary_path in sorted((suite_root / "eval").glob("*_seed*/summary_*.csv")):
        parts = summary_path.parent.name.rsplit("_seed", 1)
        if len(parts) != 2:
            continue
        compare_label, seed_text = parts
        seed = int(seed_text)
        rows = read_csv(summary_path)
        for row in rows:
            meta = {
                "compare_label": compare_label,
                "seed": seed,
                "algo": row.get("algo", ""),
                "case": str(row.get("case", "141")),
                "topology_mode": str(row.get("topology_mode", "")),
                "outage_k": str(row.get("outage_k", "")),
                "outage_policy": infer_outage_policy(row),
                "outage_radius": infer_outage_radius(row),
            }
            long_summary_rows.append({**meta, **row})
        for per_path in sorted(summary_path.parent.glob("per_episode_*.csv")):
            stem = per_path.stem
            prefix = "per_episode_"
            if not stem.startswith(prefix):
                continue
            body = stem[len(prefix):]
            if "_141_" not in body or "_k" not in body or "_seed" not in body:
                continue
            algo, rest = body.split("_141_", 1)
            topo, rest2 = rest.rsplit("_k", 1)
            outage_k, _seed_text = rest2.split("_seed", 1)
            per_rows = read_csv(per_path)
            for row in per_rows:
                long_episode_rows.append(
                    {
                        "compare_label": compare_label,
                        "seed": seed,
                        "algo": algo,
                        "case": str(row.get("case", "141")),
                        "topology_mode": topo,
                        "outage_k": outage_k,
                        "outage_policy": infer_outage_policy(row),
                        "outage_radius": infer_outage_radius(row),
                        **row,
                    }
                )
    return long_summary_rows, long_episode_rows


def dedupe_absolute_rows(summary_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Deduplicate absolute rows across compare runs while ensuring consistency.

    Each eval/<compare_label>_seed*/summary_*.csv usually contains both the baseline and
    the compare method. When a suite includes multiple compare methods, baseline rows (and
    sometimes shared methods) can appear multiple times for the same
    (algo, seed, case, topology, outage_*) condition. We collapse those duplicates here.
    """
    dedup: Dict[Tuple[str, int, str, str, str, str, str], Dict[str, object]] = {}
    metric_fields = [metric for metric, _ in PAIR_METRICS]
    for row in summary_rows:
        key = (
            str(row["algo"]),
            int(row["seed"]),
            str(row["case"]),
            str(row["topology_mode"]),
            str(row["outage_k"]),
            str(row.get("outage_policy", "")),
            str(row.get("outage_radius", "")),
        )
        prev = dedup.get(key)
        if prev is None:
            dedup[key] = row
            continue
        mismatches = []
        for field in metric_fields:
            a = to_float(prev.get(field))
            b = to_float(row.get(field))
            if math.isnan(a) and math.isnan(b):
                continue
            if abs(a - b) > 1e-9:
                mismatches.append((field, a, b))
        if mismatches:
            preview = ", ".join(f"{field}: {a} vs {b}" for field, a, b in mismatches[:4])
            raise ValueError(
                "Inconsistent duplicate absolute rows for "
                f"algo={key[0]}, seed={key[1]}, case={key[2]}, topology={key[3]}, "
                f"outage_k={key[4]}, outage_policy={key[5]}, outage_radius={key[6]}: {preview}"
            )
    return [dedup[k] for k in sorted(dedup)]


def aggregate_absolute(summary_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    deduped_rows = dedupe_absolute_rows(summary_rows)
    groups: Dict[Tuple[str, str, str, str, str, str], List[Dict[str, object]]] = defaultdict(list)
    for row in deduped_rows:
        key = (
            str(row["algo"]),
            str(row["case"]),
            str(row["topology_mode"]),
            str(row["outage_k"]),
            str(row.get("outage_policy", "")),
            str(row.get("outage_radius", "")),
        )
        groups[key].append(row)
    out_rows: List[Dict[str, object]] = []
    for (algo, case, topo, outage_k, outage_policy, outage_radius), rows in sorted(groups.items()):
        out = {
            "algo": algo,
            "case": case,
            "topology_mode": topo,
            "outage_k": outage_k,
            "outage_policy": outage_policy,
            "outage_radius": outage_radius,
            "n_seeds": len(rows),
        }
        for metric, _ in PAIR_METRICS:
            vals = [to_float(r.get(metric)) for r in rows]
            out[f"{metric}_mean"] = mean(vals)
            out[f"{metric}_std"] = std(vals)
        out_rows.append(out)
    return out_rows


def context_key(row: Dict[str, object]) -> Tuple[str, str, str, str, str]:
    return tuple(str(row.get(field, "")) for field in CONTEXT_FIELDS)


def index_episode_rows(rows: List[Dict[str, object]], *, context: str, algo: str) -> Dict[int, Dict[str, object]]:
    indexed: Dict[int, Dict[str, object]] = {}
    seen_dupes: List[int] = []
    for row in rows:
        episode = int(row["episode"])
        if episode in indexed:
            seen_dupes.append(episode)
        indexed[episode] = row
    if seen_dupes:
        dupes = ", ".join(map(str, sorted(set(seen_dupes))[:10]))
        raise ValueError(f"Duplicate episode ids for {algo} in {context}: {dupes}")
    return indexed


def paired_from_episode_rows(
    long_episode_rows: List[Dict[str, object]],
    baseline_label: str = "fedgrid_none",
    max_episode_drop_frac: float = 0.0,
) -> List[Dict[str, object]]:
    by_group: Dict[Tuple[str, int, str, str, str, str, str], Dict[str, List[Dict[str, object]]]] = defaultdict(dict)
    for row in long_episode_rows:
        key = (str(row["compare_label"]), int(row["seed"]), *context_key(row))
        by_group[key][str(row["algo"])] = by_group[key].get(str(row["algo"]), []) + [row]

    seed_level_rows: List[Dict[str, object]] = []
    for key, algo_map in sorted(by_group.items()):
        compare_label, seed, case, outage_k, outage_policy, outage_radius, topo = key
        baseline_rows = algo_map.get(baseline_label, [])
        compare_rows = algo_map.get(compare_label, [])
        if not baseline_rows or not compare_rows:
            continue
        context = (
            f"compare_label={compare_label}, seed={seed}, case={case}, outage_k={outage_k}, "
            f"outage_policy={outage_policy}, outage_radius={outage_radius}, topology_mode={topo}"
        )
        baseline_by_ep = index_episode_rows(baseline_rows, context=context, algo=baseline_label)
        compare_by_ep = index_episode_rows(compare_rows, context=context, algo=compare_label)
        common_eps = sorted(set(baseline_by_ep) & set(compare_by_ep))
        union_eps = sorted(set(baseline_by_ep) | set(compare_by_ep))
        if not common_eps:
            raise ValueError(f"No aligned episodes for {context}")
        drop_frac = 1.0 - (len(common_eps) / len(union_eps))
        if drop_frac > max_episode_drop_frac:
            baseline_only = sorted(set(baseline_by_ep) - set(compare_by_ep))
            compare_only = sorted(set(compare_by_ep) - set(baseline_by_ep))
            raise ValueError(
                f"Episode alignment mismatch for {context}: common={len(common_eps)}, union={len(union_eps)}, "
                f"drop_frac={drop_frac:.3f}, baseline_only={baseline_only[:10]}, compare_only={compare_only[:10]}"
            )
        row: Dict[str, object] = {
            "compare_label": compare_label,
            "seed": seed,
            "case": case,
            "outage_k": outage_k,
            "outage_policy": outage_policy,
            "outage_radius": outage_radius,
            "topology_mode": topo,
            "n_episodes": len(common_eps),
            "alignment_drop_frac": drop_frac,
        }
        for metric, prefer_sign in PAIR_METRICS:
            diffs = [to_float(compare_by_ep[ep].get(metric)) - to_float(baseline_by_ep[ep].get(metric)) for ep in common_eps]
            base_vals = [to_float(baseline_by_ep[ep].get(metric)) for ep in common_eps]
            cmp_vals = [to_float(compare_by_ep[ep].get(metric)) for ep in common_eps]
            row[f"{metric}_diff_mean"] = mean(diffs)
            row[f"baseline_{metric}_mean"] = mean(base_vals)
            row[f"compare_{metric}_mean"] = mean(cmp_vals)
            denom = abs(row[f"baseline_{metric}_mean"])
            row[f"{metric}_pct_vs_baseline"] = 100.0 * row[f"{metric}_diff_mean"] / float(denom) if math.isfinite(float(denom)) and abs(float(denom)) > 1e-12 else float("nan")
            row[f"{metric}_better_flag"] = 1 if row[f"{metric}_diff_mean"] * prefer_sign > 0 else 0
            row[f"{metric}_preferred_direction"] = int(prefer_sign)
        seed_level_rows.append(row)
    return seed_level_rows


def aggregate_paired(seed_level_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    groups: Dict[Tuple[str, str, str, str, str, str], List[Dict[str, object]]] = defaultdict(list)
    for row in seed_level_rows:
        groups[(str(row["compare_label"]), *context_key(row))].append(row)

    out_rows: List[Dict[str, object]] = []
    for group_key, rows in sorted(groups.items()):
        compare_label, case, outage_k, outage_policy, outage_radius, topo = group_key
        episode_counts = {int(to_float(r["n_episodes"], 0.0)) for r in rows}
        out: Dict[str, object] = {
            "compare_label": compare_label,
            "case": case,
            "outage_k": outage_k,
            "outage_policy": outage_policy,
            "outage_radius": outage_radius,
            "topology_mode": topo,
            "n_seeds": len(rows),
            "episodes_per_seed": min(episode_counts) if episode_counts else 0,
            "alignment_drop_frac_max": max(to_float(r.get("alignment_drop_frac"), 0.0) for r in rows),
        }
        composite_terms = []
        for idx, (metric, prefer_sign) in enumerate(PAIR_METRICS):
            diffs = [to_float(r[f"{metric}_diff_mean"]) for r in rows]
            lo, hi = bootstrap_ci(diffs, seed=1234 + idx * 97)
            out[f"{metric}_diff_mean_across_seeds"] = mean(diffs)
            out[f"{metric}_diff_std_across_seeds"] = std(diffs)
            out[f"{metric}_diff_ci95_lo"] = lo
            out[f"{metric}_diff_ci95_hi"] = hi
            better = sum((d * prefer_sign) > 0 for d in diffs)
            out[f"{metric}_better_seed_count"] = better
            out[f"{metric}_win_rate"] = better / len(diffs) if diffs else float("nan")
            out[f"baseline_{metric}_mean_across_seeds"] = mean([to_float(r[f"baseline_{metric}_mean"]) for r in rows])
            out[f"compare_{metric}_mean_across_seeds"] = mean([to_float(r[f"compare_{metric}_mean"]) for r in rows])
            out[f"{metric}_pct_vs_baseline_mean"] = mean([to_float(r[f"{metric}_pct_vs_baseline"]) for r in rows])
            signed_pct = out[f"{metric}_pct_vs_baseline_mean"] * prefer_sign
            if math.isfinite(float(signed_pct)):
                composite_terms.append(float(signed_pct))
        out["paper_score"] = mean(composite_terms)
        out_rows.append(out)
    return out_rows


def build_main_table(paired_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    out_rows: List[Dict[str, object]] = []
    groups: Dict[Tuple[str, str, str, str], Dict[str, Dict[str, object]]] = defaultdict(dict)
    for row in paired_rows:
        context = (
            str(row.get("case", "")),
            str(row.get("outage_k", "")),
            str(row.get("outage_policy", "")),
            str(row.get("outage_radius", "")),
        )
        groups[(str(row["compare_label"]), *context)][str(row["topology_mode"])] = row
    for (label, case, outage_k, outage_policy, outage_radius), topo_map in sorted(groups.items()):
        row: Dict[str, object] = {
            "method": label,
            "case": case,
            "outage_k": outage_k,
            "outage_policy": outage_policy,
            "outage_radius": outage_radius,
        }
        for topo in TOPOLOGIES:
            src = topo_map.get(topo)
            if not src:
                continue
            short = "rr" if topo == "random_reset" else "st"
            row[f"{short}_return_delta"] = src.get("return_diff_mean_across_seeds")
            row[f"{short}_return_ci95"] = f"[{to_float(src.get('return_diff_ci95_lo')):.3f}, {to_float(src.get('return_diff_ci95_hi')):.3f}]"
            row[f"{short}_vviol_delta"] = src.get("v_viol_lin_mean_diff_mean_across_seeds")
            row[f"{short}_ploss_delta"] = src.get("p_loss_mean_diff_mean_across_seeds")
            row[f"{short}_return_better_seeds"] = src.get("return_better_seed_count")
            row[f"{short}_paper_score"] = src.get("paper_score")
        out_rows.append(row)
    return out_rows


def build_rankings(paired_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    grouped: Dict[Tuple[str, str, str, str], List[Dict[str, object]]] = defaultdict(list)
    for row in paired_rows:
        grouped[(str(row.get("case", "")), str(row.get("outage_k", "")), str(row.get("outage_policy", "")), str(row.get("outage_radius", "")))].append(row)
    for (case, outage_k, outage_policy, outage_radius), rows in sorted(grouped.items()):
        for topo in TOPOLOGIES:
            selected = [r for r in rows if str(r.get("topology_mode")) == topo]
            selected = sorted(
                selected,
                key=lambda r: (
                    to_float(r.get("return_diff_mean_across_seeds")),
                    -to_float(r.get("v_viol_lin_mean_diff_mean_across_seeds")),
                    -to_float(r.get("p_loss_mean_diff_mean_across_seeds")),
                ),
                reverse=True,
            )
            for rank, row in enumerate(selected, start=1):
                out.append(
                    {
                        "case": case,
                        "outage_k": outage_k,
                        "outage_policy": outage_policy,
                        "outage_radius": outage_radius,
                        "topology_mode": topo,
                        "rank": rank,
                        "compare_label": row.get("compare_label", ""),
                        "return_delta": row.get("return_diff_mean_across_seeds"),
                        "return_ci95_lo": row.get("return_diff_ci95_lo"),
                        "return_ci95_hi": row.get("return_diff_ci95_hi"),
                        "vviol_delta": row.get("v_viol_lin_mean_diff_mean_across_seeds"),
                        "ploss_delta": row.get("p_loss_mean_diff_mean_across_seeds"),
                        "paper_score": row.get("paper_score"),
                    }
                )
    return out


def build_paper_table_main(paired_rows: List[Dict[str, object]], topology: str) -> List[Dict[str, object]]:
    selected = [r for r in paired_rows if str(r.get("topology_mode")) == topology]
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
    out: List[Dict[str, object]] = []
    for row in selected:
        out.append(
            {
                "case": row.get("case", ""),
                "outage_k": row.get("outage_k", ""),
                "outage_policy": row.get("outage_policy", ""),
                "outage_radius": row.get("outage_radius", ""),
                "topology_mode": row.get("topology_mode", ""),
                "method": row.get("compare_label", ""),
                "delta_return": f"{to_float(row.get('return_diff_mean_across_seeds')):.3f}",
                "ci95_return": f"[{to_float(row.get('return_diff_ci95_lo')):.3f}, {to_float(row.get('return_diff_ci95_hi')):.3f}]",
                "delta_vviol": f"{to_float(row.get('v_viol_lin_mean_diff_mean_across_seeds')):.4f}",
                "delta_ploss": f"{to_float(row.get('p_loss_mean_diff_mean_across_seeds')):.5f}",
                "better_seeds": f"{int(to_float(row.get('return_better_seed_count'), 0.0))}/{int(to_float(row.get('n_seeds'), 0.0))}",
                "paper_score": f"{to_float(row.get('paper_score')):.3f}",
            }
        )
    return out


def write_csv(rows: List[Dict[str, object]], path: Path, fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered_fields: List[str] = list(fieldnames or [])
    seen = set(ordered_fields)
    for row in rows:
        for key in row.keys():
            key = str(key)
            if key not in seen:
                seen.add(key)
                ordered_fields.append(key)
    if not ordered_fields:
        raise ValueError(f"Cannot infer CSV schema for {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in ordered_fields})
    print(f"[SAVED] {path}")


def fieldnames_for_seed_level() -> List[str]:
    fields = list(SEED_LEVEL_BASE_FIELDS)
    for metric, _ in PAIR_METRICS:
        fields += [
            f"{metric}_diff_mean",
            f"baseline_{metric}_mean",
            f"compare_{metric}_mean",
            f"{metric}_pct_vs_baseline",
            f"{metric}_better_flag",
            f"{metric}_preferred_direction",
        ]
    return fields


def fieldnames_for_paired() -> List[str]:
    fields = list(PAIRED_FIELDS) + ["alignment_drop_frac_max"]
    for metric, _ in PAIR_METRICS:
        fields += [
            f"{metric}_diff_mean_across_seeds",
            f"{metric}_diff_std_across_seeds",
            f"{metric}_diff_ci95_lo",
            f"{metric}_diff_ci95_hi",
            f"{metric}_better_seed_count",
            f"{metric}_win_rate",
            f"baseline_{metric}_mean_across_seeds",
            f"compare_{metric}_mean_across_seeds",
            f"{metric}_pct_vs_baseline_mean",
        ]
    return fields


def main() -> None:
    ap = argparse.ArgumentParser(description="Aggregate and pair FedGrid-v6 suite results")
    ap.add_argument("--suite_root", required=True, type=str)
    ap.add_argument("--baseline_label", type=str, default="fedgrid_none")
    ap.add_argument("--max_episode_drop_frac", type=float, default=0.0)
    args = ap.parse_args()

    suite_root = Path(args.suite_root).resolve()
    summary_rows, episode_rows = collect_long_rows(suite_root)
    if not summary_rows:
        raise SystemExit(f"No summary CSVs found under {suite_root / 'eval'}")
    if not episode_rows:
        raise SystemExit(f"No per-episode CSVs found under {suite_root / 'eval'}")
    try:
        validate_eval_completeness(summary_rows, episode_rows, baseline_label=args.baseline_label)
    except ValueError as exc:
        raise SystemExit(str(exc))

    agg_dir = suite_root / "agg"
    write_csv(summary_rows, agg_dir / "suite_summary_long.csv", fieldnames=SUMMARY_LONG_FIELDS)
    write_csv(episode_rows, agg_dir / "suite_per_episode_long.csv", fieldnames=EPISODE_LONG_FIELDS)
    deduped_absolute = dedupe_absolute_rows(summary_rows)
    write_csv(deduped_absolute, agg_dir / "suite_absolute_long_dedup.csv", fieldnames=SUMMARY_LONG_FIELDS)
    write_csv(aggregate_absolute(summary_rows), agg_dir / "suite_absolute_metrics.csv")
    seed_level = paired_from_episode_rows(
        episode_rows,
        baseline_label=args.baseline_label,
        max_episode_drop_frac=args.max_episode_drop_frac,
    )
    paired_rows = aggregate_paired(seed_level)
    write_csv(seed_level, agg_dir / "suite_seed_level_paired.csv", fieldnames=fieldnames_for_seed_level())
    write_csv(paired_rows, agg_dir / "suite_paired_metrics.csv", fieldnames=fieldnames_for_paired())
    write_csv(build_main_table(paired_rows), agg_dir / "suite_main_table.csv")
    write_csv(build_rankings(paired_rows), agg_dir / "suite_rankings.csv")
    write_csv(
        build_paper_table_main(paired_rows, topology="random_reset"),
        agg_dir / "suite_paper_table_main_random_reset.csv",
        fieldnames=["case", "outage_k", "outage_policy", "outage_radius", "topology_mode", "method", "delta_return", "ci95_return", "delta_vviol", "delta_ploss", "better_seeds", "paper_score"],
    )
    write_csv(
        build_paper_table_main(paired_rows, topology="static"),
        agg_dir / "suite_paper_table_appendix_static.csv",
        fieldnames=["case", "outage_k", "outage_policy", "outage_radius", "topology_mode", "method", "delta_return", "ci95_return", "delta_vviol", "delta_ploss", "better_seeds", "paper_score"],
    )


if __name__ == "__main__":
    main()
