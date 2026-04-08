# Project State

## Date

2026-04-08

## Current Stage

Active stage:

- Q1 queue execution and post-replica evidence interpretation

Completed foundations:

- workspace created
- provisional scope selected
- local evidence and risks recorded
- full `pytest -q tests` passed in `tianshou_env`
- the main evidence suite was packaged for paper-facing use
- the robustness suite completed and wrote its reports
- a clean current-workspace `main` rerun completed as `case141_fedgrid_main_rr_20260402_clean`

Current focus:

- stop the old Q1 queue after the 2026-04-08 failure-mode audit, repair the execution path, and use the repaired main replica as the new live source of truth
- keep the repaired `case141_fedgrid_main_rr_20260408_auditfix5` suite alive under system-level scheduling until it completes cleanly
- use the repaired run, not the older mixed launcher state, to judge whether the main benchmark remains mixed-sign after the seed, validation, and federation fixes
- keep the running `case141_fedgrid_topoproto_power_rr_20260407` suite alive and let the queued multi-seed robustness upgrade fire afterward
- update the project narrative so the finished fresh main replica, not the older clean rerun alone, drives the current paper stance
- treat `fedgrid_topo_proto` as mixed-sign evidence that still needs higher-power confirmation rather than a frozen positive headline
- refresh the Q1 evidence package and manuscript inputs once the remaining queue items complete

## One-Sentence Thesis

Deterministic, context-aligned evaluation shows that clustered distillation remains unstable, while simple prototype-sharing has mixed-sign results under topology shift and therefore needs higher-power confirmation rather than a strong superiority claim.

## Primary Direction

Primary paper route:

- strong empirical analysis plus evaluation protocol paper around the current FedGrid-v4 method family on case141

Backup routes:

- narrower method paper around `fedgrid_topo_proto` only if the already-running higher-power follow-up re-establishes a clearly positive result
- robustness or negative-results paper if method gains remain weak but failure modes are informative

## Established Local Evidence

- The repository contains a unified runtime bundle with train, eval, summarize, export, figure, and report stages.
- `scripts/check_runtime_bundle.py --project_root .` passes in the current workspace.
- `D:\Anaconda\envs\tianshou_env\python.exe` imports `torch`.
- `D:\Anaconda\envs\tianshou_env\python.exe -m pytest -q tests` passes in the current workspace.
- `main --dry_run --no_post` completed for `case141_fedgrid_main_rr_20260326` and wrote fresh manifests under the current workspace path.
- Existing suites already contain manifests, checkpoints, aggregate CSVs, LaTeX tables, figures, and markdown reports.
- `case141_fedgrid_robust_rr_20260326` completed with verified aggregate and report artifacts.
- `case141_fedgrid_ablation_custom_rr_20260327` completed, but it only contains one seed because the old PowerShell launch wrapper truncated the seed list.
- `case141_fedgrid_ablation_custom_rr_20260327_ms3` completed end to end after manual postprocess recovery and now has manifests, aggregate CSVs, LaTeX tables, figures, and markdown report.
- `case141_fedgrid_main_rr_20260402_clean` first completed an end-to-end `seed0` reproduction with manifests, aggregate CSVs, LaTeX tables, figures, and markdown report.
- In `case141_fedgrid_ablation_custom_rr_20260327_ms3`, `fedgrid_topo_proto` is the only positive ablation result, with mean paired return gain about `+0.091` on `random_reset` and `+0.092` on `static` across 3 seeds.
- In `case141_fedgrid_ablation_custom_rr_20260327_ms3`, `fedgrid_v4_cluster_distill`, `fedgrid_v4_cluster_nodistill`, and `fedgrid_v4_cluster_gentle` all underperform the baseline on paired return.
- In the older `case141_fedgrid_main_rr` suite, `fedgrid_topo_proto` is negative on paired return on both `random_reset` and `static`.
- In the clean rerun `case141_fedgrid_main_rr_20260402_clean`, `fedgrid_topo_proto` becomes weakly positive on paired return on both `random_reset` and `static`, while `fedgrid_v4_cluster_distill` remains negative.
- `case141_fedgrid_main_rr_20260407_replica` completed end to end with manifests, aggregate CSVs, LaTeX tables, figures, and markdown report.
- In `case141_fedgrid_main_rr_20260407_replica`, `fedgrid_topo_proto` is slightly negative on paired return on both `random_reset` and `static` (`-0.019` and `-0.021` mean delta return respectively) even though it still wins `2/3` seeds, which confirms the sign is unstable at the current main-benchmark scale.
- In `case141_fedgrid_main_rr_20260407_replica`, `fedgrid_v4_cluster_distill` is clearly negative on paired return on both `random_reset` and `static` (`-0.187` and `-0.188` mean delta return) with `0/3` winning seeds.
- The clean rerun aggregate outputs are clearly 3-seed, but the suite manifest only records the last resumed seed because the suite was finished through explicit single-seed continuation launches.

## Current Packaging Decision

- `outputs/suites/case141_fedgrid_main_rr` is the historical main evidence package and still matters because it carries the original negative result.
- `outputs/suites/case141_fedgrid_main_rr_20260402_clean` is the current-workspace reproduction package and remains important because it is the only weakly positive main-benchmark rerun so far.
- `outputs/suites/case141_fedgrid_main_rr_20260407_replica` is the freshest independent main-benchmark evidence package and currently pulls the main conclusion back toward an empirical-first story.
- `outputs/suites/case141_fedgrid_main_rr_20260326` is a partial validation rerun, not the primary evidence suite.
- `outputs/suites/case141_fedgrid_robust_rr_20260326` is a completed supporting suite with verified manifests, aggregate CSVs, figures, and report.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327` is a completed exploratory single-seed ablation and should not be used as the final ablation evidence package.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260327_ms3` is the corrected completed multi-seed ablation suite and is now the final ablation evidence package for this cycle.
- `outputs/suites/case141_fedgrid_ablation_custom_rr_20260326` is only a failed launch artifact and should not be cited.

Reason:

- the fresh rerun validated the current environment and pathing, but a full duplicate CPU-only rerun would consume many hours without improving the strongest available paper package today
- the custom multi-seed ablation adds more paper value per unit of compute than an immediate `full` sweep, so `full` is intentionally left opt-in for this cycle
- the clean rerun still matters because it shows the positive-side evidence that now has to be explained rather than ignored
- the fresh independent replica now matters because it did not repeat the clean rerun's weakly positive sign, so the primary paper route should remain empirical-first until higher-power evidence says otherwise

## Execution Status

Current execution state:

- on 2026-04-08, the active Q1 queue was intentionally stopped after the failure-mode audit identified code-level threats to seed handling, validation stability, federated warmup timing, optimizer resets, trust gating, and default outage severity
- the active training path was then repaired and re-audited before more compute was allowed to continue
- the repaired execution defaults are now: `outage_k=4`, explicit `experiment_seed` and `val_seed_base`, fixed validation episode sets across epochs, federated rounds gated until local learning actually starts, no optimizer reset after federated rounds by default, and no extra trust gate by default
- because ordinary background child processes are reclaimed in the current Codex shell environment, the repaired queue now runs under the Windows scheduled task `CodexFedGridAuditfixAutopilot`
- the current live suite is `case141_fedgrid_main_rr_20260408_auditfix5`
- the current repaired queue file is `project/experiments/runs/auditfix_queue_20260408.json`
- the current repaired status board is `outputs/automation_logs/fedgrid_auditfix_autopilot_status.md`
- the corrected `case141_fedgrid_ablation_custom_rr_20260327_ms3` suite has already completed train, eval, summarize, table export, figure generation, and markdown report generation
- `case141_fedgrid_main_rr_20260402_clean` is complete as a 3-seed package at the artifact level: 10 checkpoints, 30 eval files, aggregate CSVs, LaTeX tables, figures, and markdown report are all present
- `case141_fedgrid_main_rr_20260407_replica` has completed train, eval, summarize, table export, figure generation, and markdown report generation
- on 2026-04-07, the autopilot recovered the replica postprocess automatically after detecting complete checkpoints with missing derived artifacts
- the Q1 queue has now advanced to `case141_fedgrid_topoproto_power_rr_20260407`
- `case141_fedgrid_topoproto_power_rr_20260407` is currently the live suite
- on 2026-04-08, the Q1 queue was recovered from a stalled `resume_needed` state and the live power suite resumed under `--skip_existing`
- `case141_fedgrid_robust_rr_20260407_ms3` remains queued behind the power run
- environment: `D:\Anaconda\envs\tianshou_env\python.exe`
- the next cycle is running under the dedicated Q1 queue file at `project/experiments/runs/q1_queue_20260407.json`
- the Q1 background status board is `outputs/automation_logs/fedgrid_q1_autopilot_status.md`
- after the power run, the queue should continue automatically into `case141_fedgrid_robust_rr_20260407_ms3`

Current orchestration layer:

- `scripts/fedgrid_autopilot.py` performs queue inspection, safe wait behavior, postprocess recovery, and next-suite launch decisions
- `scripts/launch_fedgrid_autopilot.ps1` can keep the autopilot loop alive in the background for this project cycle
- current queue status: the fresh main replica is complete, `case141_fedgrid_topoproto_power_rr_20260407` is running, and `case141_fedgrid_robust_rr_20260407_ms3` is still queued
- `full` is not in the default queue
- after the 2026-03-27 recovery patch, suite launch uses a durable `Start-Process` path, a clean suite name, recent-log activity as a fallback running signal, and a non-special PowerShell variable name for the runner argument list
- after the 2026-03-28 status patch, a suite with a complete artifact set is treated as complete even if the monitor file still says `running`

## Current Negative Evidence

- In the existing main suite, paired return deltas are negative for `fedgrid_topo_proto` and `fedgrid_v4_cluster_distill` on both `random_reset` and `static`.
- Current local evidence still does not justify a strong "new clustered method beats baseline" headline.
- The completed robustness suite is interesting but still only single-seed, so it does not overturn the main-suite caution by itself.
- In the corrected multi-seed ablation, the cluster variants that matter for the mechanism story are not helping on paired return: `distill`, `nodistill`, and `gentle` are all negative relative to baseline.
- In the fresh replica `case141_fedgrid_main_rr_20260407_replica`, `fedgrid_topo_proto` returns to slightly negative mean paired return on both `random_reset` and `static` despite still winning `2/3` seeds, so the main-benchmark effect is still too unstable for a positive headline.
- The historical main suite and the fresh replica now both argue against freezing a stable positive `fedgrid_topo_proto` story on the main benchmark.

## Unresolved Questions

- The repaired `case141_fedgrid_main_rr_20260408_auditfix5` suite still needs to finish so the post-audit code path has a complete main-benchmark evidence package.
- After the repaired main suite finishes, the next repaired follow-up queue still needs to decide whether to rerun the narrower topo-proto power comparison, the multi-seed robustness upgrade, or both under the corrected defaults.
- Existing artifacts still contain some historical path drift.
- The literature package exists, but it is still a starter set and needs broader coverage of the exact nearest-neighbor task papers.
- The exploratory `case141_fedgrid_ablation_custom_rr_20260327` suite should not be mistaken for the final multi-seed ablation evidence.
- The running `case141_fedgrid_topoproto_power_rr_20260407` suite must show whether the narrower `fedgrid_none` versus `fedgrid_topo_proto` comparison becomes stably positive with 5 seeds or simply confirms that the effect is near zero and unstable.
- The queued `case141_fedgrid_robust_rr_20260407_ms3` suite still needs to finish so the supporting robustness story is no longer single-seed.
- The clean rerun manifest metadata should be repaired or at least documented, because it currently understates the actual seed count used in the aggregate outputs.
- The optional `full` sweep should only be justified if the running power suite plus the queued robustness upgrade still leave the paper thesis ambiguous and broader controls are needed.
- The Q1 queue itself is now running, so the main execution risk is runtime stability of the remaining queue plus eventual interpretation of the mixed-sign `fedgrid_topo_proto` evidence.

## Publication Readiness Snapshot

Readiness today:

- codebase: medium
- experiment packaging: high
- manuscript evidence quality: medium
- reproducibility completeness: medium
- submission readiness: medium
