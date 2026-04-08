# Decision Log

## 2026-03-26: Adopt the autopilot workspace

Decision:

- Create a dedicated `project/` workspace inside the runtime bundle.

Reason:

- The repository already contains working code and outputs, but the paper process was not organized into one auditable workflow.

## 2026-03-26: Keep the repository root as the operational source of truth

Decision:

- Treat the root scripts as the authoritative implementation for this research cycle.

Reason:

- The active runner and postprocess chain already exist and should not be destabilized by early refactors.

## 2026-03-26: Choose an empirical-first primary paper route

Decision:

- Make the primary paper route a strong empirical and evaluation study, not an unconditional method-superiority claim.

Reason:

- Current local evidence does not justify that claim yet.

## 2026-03-26: Use `tianshou_env` before creating a new environment

Decision:

- Validate the current project with `D:\Anaconda\envs\tianshou_env\python.exe` first.

Reason:

- This interpreter already imports `torch`, which is the immediate blocker for full test validation.

## 2026-03-26: Stop the fresh CPU-only duplicate main rerun after baseline validation

Decision:

- Stop the live `case141_fedgrid_main_rr_20260326` rerun after validation and use the existing completed `case141_fedgrid_main_rr` suite as the main evidence package.

Reason:

- The fresh rerun was only needed to validate the current workspace and manifests.
- On the observed CPU-only setup, a full duplicate rerun would take many hours and delay higher-value packaging work.

## 2026-03-26: Prioritize robustness as the next live suite

Decision:

- Launch `case141_fedgrid_robust_rr_20260326` next instead of immediately forcing a full duplicate main rerun.

Reason:

- Robustness evidence is still missing from the current paper package.
- It is higher-value for paper positioning than redoing an already completed main suite.

## 2026-03-26: Fresh run outputs should use dated suite names

Decision:

- Use `case141_fedgrid_main_rr_20260326` for the current live rerun instead of reusing the older `case141_fedgrid_main_rr` directory.

Reason:

- This avoids mixing fresh manifests and outputs with older artifacts while we clean up historical path drift.

## 2026-03-26: Add a local autopilot orchestration layer

Decision:

- Add `scripts/fedgrid_autopilot.py` and `scripts/launch_fedgrid_autopilot.ps1` as the orchestration layer for this project cycle.

Reason:

- The repository already had a solid single-suite runner plus postprocess chain, but it still lacked a safe way to wait on a live suite, recover postprocess, and queue the next experiment automatically.
- Keeping the orchestration logic outside the runner preserves the validated training path while reducing manual babysitting.

## 2026-03-26: Queue the custom ablation suite after robustness and keep `full` opt-in

Decision:

- Set `case141_fedgrid_ablation_custom_rr_20260326` as the next automated suite after robustness.
- Do not put `full` into the default queue for this cycle.

Reason:

- The stock `ablation` preset currently duplicates `main`, so the higher-value follow-up is a custom multi-seed ablation using `fedgrid_v4_cluster_nodistill` and `fedgrid_v4_cluster_gentle`.
- An immediate `full` sweep would cost much more compute while adding less near-term paper value than the robustness-plus-custom-ablation path.

## 2026-03-26: Add a human-readable task status board

Decision:

- Generate a markdown status board at `outputs/automation_logs/fedgrid_status.md` and expose a one-shot viewer through `scripts/show_fedgrid_status.ps1`.

Reason:

- The JSON state is useful for automation, but it is not pleasant to inspect during long runs.
- The markdown board shows the active suite, latest epoch, latest validation, queue position, and recent log tail in one place.

## 2026-03-27: Bypass the broken PowerShell suite launcher inside autopilot

Decision:

- Change `scripts/fedgrid_autopilot.py` so queued suites are launched more directly instead of relying on the fragile suite-chain launcher path.

Reason:

- The custom ablation queue item could pass `dry_run`, but the earlier background PowerShell launch path was silently failing after startup and left only empty automation logs.
- Reducing orchestration layers made the launch path easier to debug.

## 2026-03-27: Add recent-log activity as a fallback running signal

Decision:

- Treat a suite as running when its automation stdout or stderr log was updated recently, even if process enumeration is unavailable.

Reason:

- In the current Windows sandbox, direct process enumeration is not consistently reliable.
- The recent-log heuristic prevents duplicate launches and keeps the human-readable status board accurate enough for long runs.

## 2026-03-27: Accept the completed robustness suite as supporting evidence, not headline proof

Decision:

- Treat `case141_fedgrid_robust_rr_20260326` as completed and verified, but keep it as supporting evidence rather than the main paper headline.

Reason:

- The suite produced the required manifests, aggregate CSVs, figures, LaTeX tables, and markdown report.
- It is still a single-seed robustness suite, so it is useful for mechanism probing but not strong enough to overturn the main multi-seed benchmark posture by itself.

## 2026-03-27: Recover the custom ablation under a clean suite name

Decision:

- Move the live custom ablation to `case141_fedgrid_ablation_custom_rr_20260327` and treat `case141_fedgrid_ablation_custom_rr_20260326` only as a failed launch artifact.

Reason:

- The original queue item was repeatedly "launched" but did not persist a real background run.
- A clean dated suite name avoids mixing failed launch remnants with the recovered live ablation.

## 2026-03-27: Keep the paper framing empirical-first during the live ablation

Decision:

- Continue writing the paper as an empirical-analysis and evaluation-protocol study while the multi-seed ablation is still running.

Reason:

- The completed main suite still shows negative mean paired return for the current headline methods.
- The completed robustness suite is encouraging but not sufficient to justify a broad method-superiority story.
- Drafting the paper now around the evidence-backed framing reduces risk and keeps the project moving while experiments finish.

## 2026-03-27: Do not accept the first recovered ablation as final evidence

Decision:

- Treat `case141_fedgrid_ablation_custom_rr_20260327` as exploratory only and rerun the ablation under `case141_fedgrid_ablation_custom_rr_20260327_ms3`.

Reason:

- The suite completed cleanly, but its manifest recorded only seed `0`, so it is not the intended multi-seed ablation.
- Using it as final ablation evidence would quietly downgrade the paper's evidence quality.

## 2026-03-27: Fix the PowerShell wrapper to preserve the full seed list

Decision:

- Replace the wrapper variable name `$args` with `$runnerArgs` inside `scripts/fedgrid_autopilot.py` and rerun the custom ablation.

Reason:

- The previous wrapper used PowerShell's special `$args` variable name, which led to the launched suite behaving like a single-seed run.
- A wrapper check confirmed that the corrected launch path now writes `seeds: [0, 1, 2]` into a dry-run manifest.

## 2026-03-28: Accept `case141_fedgrid_ablation_custom_rr_20260327_ms3` as the final ablation evidence suite

Decision:

- Treat `case141_fedgrid_ablation_custom_rr_20260327_ms3` as the final ablation evidence package for the current paper cycle.

Reason:

- The suite now has the full artifact set: manifests, aggregate CSVs, LaTeX tables, figures, and markdown report.
- It closes the launch-bug recovery loop by providing the intended 3-seed ablation evidence.
- Its evidence supports a narrower conclusion: `fedgrid_topo_proto` helps, but the clustered distillation variants do not justify a strong positive headline.

## 2026-03-28: Prefer artifact completeness over stale monitor state in status classification

Decision:

- Update `scripts/fedgrid_autopilot.py` so a suite with a complete required artifact set is treated as complete, even if a stale monitor heartbeat still exists.

Reason:

- `case141_fedgrid_ablation_custom_rr_20260327_ms3` had already finished train and eval, and manual postprocess recovery produced the full artifact set.
- The old status logic still surfaced it as `running` because only the monitor process remained, which was misleading for operational tracking.

## 2026-04-07: Treat the legacy-main versus clean-rerun sign flip as the top blocker

Decision:

- Do not freeze the paper thesis until a fresh independent main replica resolves the disagreement between `case141_fedgrid_main_rr` and `case141_fedgrid_main_rr_20260402_clean`.

Reason:

- The older main suite shows `fedgrid_topo_proto` negative on paired return, while the clean rerun shows it weakly positive.
- A Q1 paper cannot rely on a headline result whose sign changes across the two strongest available main-benchmark packages.

## 2026-04-07: Keep the primary paper route empirical-first after the fresh independent main replica

Decision:

- Do not upgrade the project to a method-positive paper route yet, even though the clean rerun was weakly positive for `fedgrid_topo_proto`.

Reason:

- The fresh independent main replica `case141_fedgrid_main_rr_20260407_replica` did not confirm the clean rerun's weakly positive sign.
- `fedgrid_topo_proto` is now mixed-sign across the three main evidence packages, while `fedgrid_v4_cluster_distill` is clearly unsupported.
- The strongest defensible paper route remains empirical evaluation, reproducibility, and failure analysis unless the higher-power topo-proto follow-up is much cleaner.

## 2026-04-08: Resume the Q1 queue from the stalled topo-proto power suite instead of skipping ahead

Decision:

- Keep `case141_fedgrid_topoproto_power_rr_20260407` as the current live suite, relaunch the Q1 autopilot, and let the queue continue in order into `case141_fedgrid_robust_rr_20260407_ms3`.

Reason:

- The queue had stalled in a `resume_needed` state after a failed resumed run, but the suite still had valid partial checkpoints and `--skip_existing` was working correctly.
- Skipping directly to robustness would leave the main `fedgrid_none` versus `fedgrid_topo_proto` question unresolved.
- Relaunching the Q1 autopilot preserved the intended paper logic: first tighten the mixed-sign topo-proto result, then upgrade robustness from single-seed to multi-seed support.

## 2026-04-07: Narrow any method-positive paper around `fedgrid_topo_proto`, not clustered distillation

Decision:

- If the next fresh replica remains positive, the method-positive route should focus on `fedgrid_topo_proto` and explicitly present clustered distillation as negative or unstable.

Reason:

- The clean rerun and the finished multi-seed ablation both support `fedgrid_topo_proto` more than the clustered-distillation family.
- `fedgrid_v4_cluster_distill`, `fedgrid_v4_cluster_nodistill`, and `fedgrid_v4_cluster_gentle` do not currently justify a positive headline.

## 2026-04-07: Launch a dedicated Q1 experiment queue instead of waiting for manual follow-up

Decision:

- Start a dedicated Q1 background queue with three suites: `case141_fedgrid_main_rr_20260407_replica`, `case141_fedgrid_topoproto_power_rr_20260407`, and `case141_fedgrid_robust_rr_20260407_ms3`.

Reason:

- The user asked for continuous autonomous execution rather than another manual stop-and-plan cycle.
- This queue resolves the highest-value uncertainty first, then increases statistical power, then upgrades supporting robustness evidence.

## 2026-04-07: Keep the primary paper route empirical-first after the fresh main replica

Decision:

- Treat `case141_fedgrid_main_rr_20260407_replica` as the freshest independent main evidence and keep the default paper route empirical-first.

Reason:

- In the fresh replica, `fedgrid_topo_proto` is slightly negative on mean paired return on both `random_reset` and `static`, even though it still wins `2/3` seeds.
- `fedgrid_v4_cluster_distill` is clearly negative in the same replica and goes `0/3` on paired return wins.
- This is enough to reject a stable positive main-benchmark headline for now, even though the narrower topo-proto follow-up is still worth finishing.

## 2026-04-08: Stop the pre-fix live queue before spending more compute

Decision:

- Stop the active Q1 queue, apply the failure-mode fixes, and only then resume experiments on a fresh repaired suite.

Reason:

- The code audit found real execution-path issues affecting the meaning of additional compute: incomplete experiment seeding, unstable validation episode selection, federated rounds starting before local learning, aggressive optimizer resets, double trust gating, and a harder-than-paper default outage setting.
- Continuing the old queue would have mixed new evidence with a code path we no longer trusted.

## 2026-04-08: Use a repaired fresh main replica as the next source-of-truth experiment

Decision:

- Launch `case141_fedgrid_main_rr_20260408_auditfix5` as the first post-audit suite and use it to judge the corrected main-benchmark behavior before restarting narrower follow-up queues.

Reason:

- The main benchmark is still the thesis-setting experiment, so the first repaired rerun should target that benchmark directly.
- A fresh suite name keeps the post-audit evidence clearly separated from the earlier mixed launcher states.

## 2026-04-08: Host the repaired autopilot through Windows Task Scheduler

Decision:

- Run the repaired queue through the scheduled task `CodexFedGridAuditfixAutopilot` instead of relying on ordinary shell-launched background child processes.

Reason:

- In the current Codex shell environment, ordinary background child processes are reclaimed even for trivial delayed-write tests.
- The scheduled task host keeps the long-running experiment alive outside the current shell lifecycle while still using the same workspace and `tianshou_env` interpreter.
