# FedGrid Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the highest-confidence training and evaluation issues identified by the 2026-04-08 audit, then rerun a clean experiment suite on the repaired pipeline.

**Architecture:** Keep the existing runner and training pipeline, but add reproducibility controls and safer federated defaults around it. Avoid broad algorithm redesign; only change launch metadata, deterministic validation, true experiment seeding, and federated synchronization timing/state handling.

**Tech Stack:** Python, PyTorch, pytest, PowerShell, existing FedGrid runtime bundle scripts.

---

### Task 1: Add test coverage for the repaired control flags

**Files:**
- Modify: `C:\Users\ASUS\Desktop\runtime_bundle\tests\test_v8_runner_flags.py`

- [ ] Add a dry-run test that asserts the runner forwards new reproducibility and federation-stability flags.
- [ ] Verify the new test fails before implementation under the current code.

### Task 2: Add deterministic helper tests for training-side policy

**Files:**
- Modify: `C:\Users\ASUS\Desktop\runtime_bundle\tests\test_fedgrid_v4_core.py`

- [ ] Add unit-level tests for the new gating helpers:
  - federated rounds should not start before configured warmup
  - trust should not be re-applied when disabled
  - experiment seed should deterministically map per-seed launch values
- [ ] Verify these tests fail before implementation.

### Task 3: Implement runner-side reproducibility and safer defaults

**Files:**
- Modify: `C:\Users\ASUS\Desktop\runtime_bundle\run_case141_fedgrid_v6.py`

- [ ] Add runner arguments for experiment seeding, validation seeding, federated warmup, trust double-count control, and optimizer-reset control.
- [ ] Forward those flags into training commands and keep dry-run output readable.
- [ ] Preserve existing method-library behavior and current bigger-capacity defaults.

### Task 4: Implement training-side fixes

**Files:**
- Modify: `C:\Users\ASUS\Desktop\runtime_bundle\train_gnn_fedgrid.py`

- [ ] Add true experiment seeding across Python, NumPy, and Torch.
- [ ] Make validation reproducible by reseeding and isolating validation episode progression.
- [ ] Delay federated rounds until after configurable warmup and disable optimizer resets by default.
- [ ] Stop double-applying trust by default during parameter mixing/distillation.
- [ ] Save enough checkpoint metadata to reconstruct bus-GNN topology mode and seed settings.

### Task 5: Implement evaluator compatibility fix

**Files:**
- Modify: `C:\Users\ASUS\Desktop\runtime_bundle\evaluate_topology_shift_deterministic.py`

- [ ] Load saved bus-GNN topology metadata instead of hardcoding `use_base_topology=True`.
- [ ] Keep backward compatibility with older checkpoints that lack the new metadata.

### Task 6: Verify and re-audit

**Files:**
- Read: `C:\Users\ASUS\Desktop\runtime_bundle\project\analysis\failure_mode_audit_20260408.md`

- [ ] Run targeted pytest under `D:\Anaconda\envs\tianshou_env\python.exe`.
- [ ] Run a runner dry-run and inspect emitted commands.
- [ ] Dispatch a fresh audit pass on the modified code.

### Task 7: Relaunch a clean post-fix experiment

**Files:**
- Modify as needed: `C:\Users\ASUS\Desktop\runtime_bundle\project\project_state.md`
- Modify as needed: `C:\Users\ASUS\Desktop\runtime_bundle\project\todo.md`

- [ ] Launch a fresh suite with an explicit repaired suite name.
- [ ] Confirm background processes and first status snapshot.
- [ ] Update project tracking files only with actual launched artifacts.
