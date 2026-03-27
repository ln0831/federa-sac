---
name: fedgrid-runtime-runner
description: run fedgrid case141 experiments locally from the unified runtime bundle, verify the project root before execution, use the stable v8 runner and v8.2 postprocess chain, and prepare paper-ready tables, figures, and markdown reports. use when chatgpt needs to help reproduce, launch, resume, validate, or summarize fedgrid training, evaluation, and postprocess workflows on a local machine, especially when coordinating execution with claude or codex.
---

# FedGrid Runtime Runner

## Overview

Use this skill when the working directory is the unified FedGrid runtime bundle root. Treat the root as the only `project_root`.

## Core workflow

1. Run `scripts/check_runtime_bundle.py --project_root .`.
2. Suggest `pytest -q tests` before the first real run.
3. Run `run_case141_fedgrid_v6.py` with `--no_post` first.
4. Run `bash scripts/run_postprocess.sh <python-bin> <suite-root>` after training/eval finish.
5. Check manifests, aggregate CSVs, LaTeX tables, figures, and the markdown report before claiming success.

## Execution rules

- Prefer local `conda` as the primary environment. Support `uv` as a backup path.
- Always recommend a `--dry_run` before the first real run of a preset.
- Do not create a separate external `project_root`; the unified bundle root already contains train, eval, runner, and postprocess scripts.
- Do not mix `v3` with the stable runner; this bundle already uses the `v4` training base because cluster/distill flags are supported there.
- Do not ignore fail-fast errors from summarize or figure generation.
- Do not write paper conclusions from absolute metrics alone when paired metrics are missing.

## Environment setup

Read:
- [environment.md](references/environment.md)

## Command patterns

Read:
- [workflow.md](references/workflow.md)

## Output expectations

Read:
- [outputs.md](references/outputs.md)

## Prompt templates for Claude or Codex

Read:
- [prompts.md](references/prompts.md)

## Troubleshooting

Read:
- [troubleshooting.md](references/troubleshooting.md)

## Resources

### scripts/check_runtime_bundle.py
Run this script before the first execution to verify that the unified bundle root contains the required training, evaluation, runner, and postprocess entrypoints.
