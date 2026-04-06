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
