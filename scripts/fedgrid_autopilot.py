#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SuiteSpec:
    suite_name: str
    preset: str
    methods: str
    seeds: List[int]
    train_topology_mode: str = "random_reset"
    outage_k: int = 6
    outage_policy: str = "local"
    outage_radius: int = 2
    gpu: int = 0
    epochs: int = 100
    goal: str = ""


DEFAULT_QUEUE: List[SuiteSpec] = [
    SuiteSpec(
        suite_name="case141_fedgrid_robust_rr_20260326",
        preset="robustness",
        methods="preset",
        seeds=[0, 1, 2],
        goal="Fill the robustness evidence gap for dropout and Byzantine variants.",
    ),
    SuiteSpec(
        suite_name="case141_fedgrid_ablation_custom_rr_20260327_ms3",
        preset="main",
        methods="fedgrid_none,fedgrid_topo_proto,fedgrid_v4_cluster_distill,fedgrid_v4_cluster_nodistill,fedgrid_v4_cluster_gentle",
        seeds=[0, 1, 2],
        goal="Run the multi-seed ablation follow-up with nodistill and gentle cluster variants.",
    ),
]

OPTIONAL_FULL = SuiteSpec(
    suite_name="case141_fedgrid_full_rr_20260326",
    preset="full",
    methods="all",
    seeds=[0, 1, 2],
    goal="Optional exhaustive rerun across the full method library.",
)

REQUIRED_MANIFESTS = [
    ("manifests", "fedgrid_v6_run_matrix.csv"),
    ("manifests", "fedgrid_v6_commands.csv"),
    ("manifests", "fedgrid_v6_suite_manifest.json"),
]
REQUIRED_AGG = [
    ("agg", "suite_absolute_metrics.csv"),
    ("agg", "suite_paired_metrics.csv"),
    ("agg", "suite_rankings.csv"),
]
REQUIRED_REPORTS = [
    ("reports", "fedgrid_v6_report.md"),
    ("reports", "latex", "table_main_random_reset.tex"),
    ("reports", "latex", "table_appendix_static.tex"),
    ("reports", "figures", "random_reset_delta_return.png"),
    ("reports", "figures", "random_reset_delta_vviol.png"),
    ("reports", "figures", "random_reset_delta_ploss.png"),
]

KNOWN_PRESET_METHODS: Dict[str, List[str]] = {
    "main": ["fedgrid_none", "fedgrid_topo_proto", "fedgrid_v4_cluster_distill"],
    "ablation": ["fedgrid_none", "fedgrid_topo_proto", "fedgrid_v4_cluster_distill"],
    "robustness": ["fedgrid_none", "fedgrid_v4_cluster_distill", "fedgrid_v4_cluster_dropout", "fedgrid_v4_cluster_byzantine"],
    "full": [
        "fedgrid_none",
        "fedgrid_topo_proto",
        "fedgrid_v4_cluster_distill",
        "fedgrid_v4_cluster_nodistill",
        "fedgrid_v4_cluster_gentle",
        "fedgrid_v4_cluster_dropout",
        "fedgrid_v4_cluster_byzantine",
    ],
}

DETACHED = 0
NEW_GROUP = 0
CREATE_NO_WINDOW = 0
if sys.platform == "win32":
    DETACHED = getattr(subprocess, "DETACHED_PROCESS", 0)
    NEW_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

POWERSHELL_EXE = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" if sys.platform == "win32" else "powershell"

EPOCH_RE = re.compile(
    r"Epoch\s+(?P<epoch>\d+)\s+\[(?P<stage>[A-Z]+)\]: RewardSum\s+(?P<reward_sum>-?\d+(?:\.\d+)?)\s+\|\s+Reward/Step\s+(?P<reward_step>-?\d+(?:\.\d+)?),\s+Loss\s+(?P<loss>[^,]+),\s+Alpha\s+(?P<alpha>-?\d+(?:\.\d+)?)"
)
VAL_RE = re.compile(
    r"Validation:\s+Sum\s+(?P<sum>-?\d+(?:\.\d+)?)\s+\|\s+PerStep\s+(?P<per_step>-?\d+(?:\.\d+)?)\s+\(Best:\s+(?P<best>[-\w.]+)\)"
)


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def load_json(path: Path) -> Optional[Dict[str, object]]:
    if not path.exists():
        return None
    for attempt in range(3):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            if attempt == 2:
                return None
            time.sleep(1)
    return None


def read_run_matrix_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return sum(1 for _ in reader)


def planned_method_labels(spec: SuiteSpec) -> List[str]:
    if spec.methods and spec.methods.strip() and spec.methods.strip() != "preset":
        return [token.strip() for token in spec.methods.split(",") if token.strip()]
    return list(KNOWN_PRESET_METHODS.get(spec.preset, []))


def expected_run_count(spec: SuiteSpec) -> int:
    labels = planned_method_labels(spec)
    if not labels:
        return 0
    return len(labels) * len(spec.seeds)


def required_file_status(suite_root: Path) -> Dict[str, bool]:
    status: Dict[str, bool] = {}
    for rel in REQUIRED_MANIFESTS + REQUIRED_AGG + REQUIRED_REPORTS:
        key = "/".join(rel)
        status[key] = suite_root.joinpath(*rel).exists()
    return status


def query_process_count(suite_name: str) -> int:
    if sys.platform != "win32":
        return 0
    script = rf"""
$suite = '{suite_name}'
$matches = @(
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {{
            $_.ProcessId -ne $PID -and
            $_.CommandLine -and
            ($_.CommandLine -match [regex]::Escape($suite)) -and
            (
                ($_.CommandLine -match 'launch_case141_suite_chain.ps1') -or
                ($_.CommandLine -match 'monitor_suite.ps1') -or
                ($_.CommandLine -match 'run_case141_fedgrid_v6.py') -or
                ($_.CommandLine -match 'train_gnn_fedgrid.py') -or
                ($_.CommandLine -match 'evaluate_topology_shift_deterministic.py') -or
                ($_.CommandLine -match 'summarize_fedgrid_suite_v6.py') -or
                ($_.CommandLine -match 'export_fedgrid_tables_v6.py') -or
                ($_.CommandLine -match 'make_fedgrid_figures_v6.py') -or
                ($_.CommandLine -match 'make_fedgrid_report_v6.py')
            )
        }}
)
$matches.Count
""".strip()
    try:
        proc = subprocess.run(
            [POWERSHELL_EXE, "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
    except FileNotFoundError:
        return 0
    try:
        return int(proc.stdout.strip() or "0")
    except ValueError:
        return 0


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def suite_log_paths(root: Path, suite_name: str) -> Dict[str, Path]:
    log_dir = root / "outputs" / "automation_logs"
    ensure_dir(log_dir)
    return {
        "stdout": log_dir / f"{suite_name}.utf8.stdout.log",
        "stderr": log_dir / f"{suite_name}.utf8.stderr.log",
        "monitor_json": log_dir / f"{suite_name}.monitor.json",
    }


def read_tail_lines(path: Path, limit: int = 12) -> List[str]:
    if not path.exists():
        return []
    tail: deque[str] = deque(maxlen=limit)
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.rstrip()
            if line:
                tail.append(line)
    return list(tail)


def extract_progress(stdout_path: Path) -> Dict[str, object]:
    tail = read_tail_lines(stdout_path, limit=20)
    epoch_info: Optional[Dict[str, str]] = None
    validation_info: Optional[Dict[str, str]] = None
    for line in tail:
        epoch_match = EPOCH_RE.search(line)
        if epoch_match:
            epoch_info = epoch_match.groupdict()
        val_match = VAL_RE.search(line)
        if val_match:
            validation_info = val_match.groupdict()
    return {
        "tail": tail[-8:],
        "epoch": epoch_info,
        "validation": validation_info,
        "log_mtime": datetime.fromtimestamp(stdout_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        if stdout_path.exists()
        else None,
    }


def latest_log_run(suite_root: Path) -> Optional[str]:
    logs_root = suite_root / "logs"
    if not logs_root.exists():
        return None
    dirs = [path for path in logs_root.iterdir() if path.is_dir()]
    if not dirs:
        return None
    latest = max(dirs, key=lambda path: path.stat().st_mtime)
    return latest.name


def is_recent(path: Path, threshold_sec: int = 180) -> bool:
    if not path.exists():
        return False
    return (time.time() - path.stat().st_mtime) <= threshold_sec


def inspect_suite(root: Path, spec: SuiteSpec) -> Dict[str, object]:
    suite_root = root / "outputs" / "suites" / spec.suite_name
    logs = suite_log_paths(root, spec.suite_name)
    monitor = load_json(logs["monitor_json"])
    process_count = query_process_count(spec.suite_name)
    recent_stdout = is_recent(logs["stdout"])
    recent_stderr = is_recent(logs["stderr"], threshold_sec=300)
    running = bool(monitor and monitor.get("running")) or process_count > 0 or recent_stdout or recent_stderr
    required = required_file_status(suite_root)
    has_required = all(required.values())
    # If the full artifact set exists, prefer the artifact truth over a stale monitor heartbeat.
    if has_required:
        running = False
    expected_runs = read_run_matrix_rows(suite_root / "manifests" / "fedgrid_v6_run_matrix.csv") or expected_run_count(spec)
    checkpoint_count = count_files(suite_root / "checkpoints")
    eval_count = count_files(suite_root / "eval")
    agg_count = count_files(suite_root / "agg")
    report_count = count_files(suite_root / "reports")
    postprocess_ready = expected_runs > 0 and checkpoint_count >= expected_runs and not running
    if not suite_root.exists() and not logs["monitor_json"].exists():
        phase = "missing"
    elif running:
        phase = "running"
    elif has_required:
        phase = "complete"
    elif postprocess_ready:
        phase = "postprocess_needed"
    elif checkpoint_count > 0 or expected_runs > 0 or eval_count > 0:
        phase = "resume_needed"
    else:
        phase = "missing"
    return {
        "suite_name": spec.suite_name,
        "suite_root": str(suite_root),
        "phase": phase,
        "running": running,
        "process_count": process_count,
        "recent_stdout": recent_stdout,
        "recent_stderr": recent_stderr,
        "expected_runs": expected_runs,
        "checkpoints": checkpoint_count,
        "eval_files": eval_count,
        "agg_files": agg_count,
        "report_files": report_count,
        "required_outputs": required,
        "monitor": monitor,
        "goal": spec.goal,
        "latest_log_run": latest_log_run(suite_root),
    }


class Autopilot:
    def __init__(self, root: Path, python_exe: str, interval_sec: int, allow_full: bool) -> None:
        self.root = root
        self.python_exe = python_exe
        self.interval_sec = interval_sec
        self.queue = list(DEFAULT_QUEUE)
        if allow_full:
            self.queue.append(OPTIONAL_FULL)
        self.log_dir = self.root / "outputs" / "automation_logs"
        ensure_dir(self.log_dir)
        self.state_path = self.log_dir / "fedgrid_autopilot_state.json"
        self.history_path = self.log_dir / "fedgrid_autopilot.log"
        self.status_md_path = self.log_dir / "fedgrid_status.md"

    def log(self, message: str) -> None:
        line = f"[{timestamp()}] {message}"
        print(line)
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def build_payload(
        self,
        action: str,
        current_suite: Optional[str],
        statuses: List[Dict[str, object]],
    ) -> Dict[str, object]:
        return {
            "action": action,
            "current_suite": current_suite,
            "statuses": statuses,
        }

    def write_state(self, payload: Dict[str, object]) -> None:
        payload = dict(payload)
        payload["timestamp"] = timestamp()
        self.state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.status_md_path.write_text(self.render_status_markdown(payload), encoding="utf-8")

    def render_status_markdown(self, payload: Dict[str, object]) -> str:
        lines = [
            "# FedGrid Task Status",
            "",
            f"- Updated: `{payload['timestamp']}`",
            f"- Autopilot action: `{payload['action']}`",
            f"- Current suite: `{payload['current_suite'] or 'none'}`",
            "",
            "## Queue",
        ]
        statuses = payload.get("statuses", [])
        for status in statuses:
            suite_name = str(status["suite_name"])
            phase = str(status["phase"])
            checkpoints = status.get("checkpoints", 0)
            expected_runs = status.get("expected_runs", 0)
            goal = str(status.get("goal", ""))
            lines.extend(
                [
                    f"### {suite_name}",
                    f"- Phase: `{phase}`",
                    f"- Running: `{status.get('running', False)}`",
                    f"- Checkpoints: `{checkpoints}`",
                    f"- Expected runs: `{expected_runs}`",
                    f"- Goal: {goal}",
                ]
            )
            latest_log_run_name = status.get("latest_log_run")
            if latest_log_run_name:
                lines.append(f"- Latest run dir: `{latest_log_run_name}`")
            progress = extract_progress(suite_log_paths(self.root, suite_name)["stdout"])
            epoch_info = progress.get("epoch")
            if epoch_info:
                lines.append(
                    "- Latest epoch: "
                    f"`{epoch_info['epoch']}` [{epoch_info['stage']}] "
                    f"RewardSum `{epoch_info['reward_sum']}` "
                    f"Reward/Step `{epoch_info['reward_step']}` "
                    f"Loss `{epoch_info['loss']}` "
                    f"Alpha `{epoch_info['alpha']}`"
                )
            validation_info = progress.get("validation")
            if validation_info:
                lines.append(
                    "- Latest validation: "
                    f"Sum `{validation_info['sum']}` "
                    f"PerStep `{validation_info['per_step']}` "
                    f"Best `{validation_info['best']}`"
                )
            if progress.get("log_mtime"):
                lines.append(f"- Training log updated: `{progress['log_mtime']}`")
            tail = progress.get("tail") or []
            if tail:
                lines.extend(["- Recent log tail:", "```text", *tail, "```"])
            lines.append("")

        lines.extend(
            [
                "## Files",
                f"- State JSON: `{self.state_path}`",
                f"- Status Markdown: `{self.status_md_path}`",
                f"- History Log: `{self.history_path}`",
            ]
        )
        return "\n".join(lines) + "\n"

    def run_cmd(self, cmd: List[str], label: str) -> None:
        self.log(f"{label}: {' '.join(cmd)}")
        subprocess.run(cmd, cwd=str(self.root), check=True)

    def run_postprocess(self, spec: SuiteSpec) -> None:
        suite_root = self.root / "outputs" / "suites" / spec.suite_name
        commands = [
            [self.python_exe, str(self.root / "summarize_fedgrid_suite_v6.py"), "--suite_root", str(suite_root)],
            [self.python_exe, str(self.root / "export_fedgrid_tables_v6.py"), "--suite_root", str(suite_root)],
            [self.python_exe, str(self.root / "make_fedgrid_figures_v6.py"), "--suite_root", str(suite_root)],
            [self.python_exe, str(self.root / "make_fedgrid_report_v6.py"), "--suite_root", str(suite_root)],
        ]
        for cmd in commands:
            self.run_cmd(cmd, f"postprocess[{spec.suite_name}]")

    def launch_monitor(self, spec: SuiteSpec) -> None:
        cmd = [
            POWERSHELL_EXE,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.root / "scripts" / "monitor_suite.ps1"),
            "-RootDir",
            str(self.root),
            "-SuiteName",
            spec.suite_name,
            "-IntervalSec",
            str(self.interval_sec),
            "-MaxChecks",
            "720",
        ]
        subprocess.Popen(
            cmd,
            cwd=str(self.root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )

    def launch_suite(self, spec: SuiteSpec, resume: bool) -> None:
        logs = suite_log_paths(self.root, spec.suite_name)
        ensure_dir(logs["stdout"].parent)
        runner_args = [
            str(self.root / "run_case141_fedgrid_v6.py"),
            "--project_root",
            ".",
            "--suite_name",
            spec.suite_name,
            "--preset",
            spec.preset,
            "--methods",
            spec.methods,
            "--train_topology_mode",
            spec.train_topology_mode,
            "--outage_k",
            str(spec.outage_k),
            "--outage_policy",
            spec.outage_policy,
            "--outage_radius",
            str(spec.outage_radius),
            "--gpu",
            str(spec.gpu),
            "--epochs",
            str(spec.epochs),
            "--no_post",
            "--seeds",
        ]
        runner_args.extend([str(seed) for seed in spec.seeds])
        if resume:
            runner_args.append("--skip_existing")
        args_literal = ", ".join(ps_quote(arg) for arg in runner_args)
        script = "\n".join(
            [
                "if (Test-Path Env:PATH) { Remove-Item Env:PATH -ErrorAction SilentlyContinue }",
                f"$runnerArgs = @({args_literal})",
                f"$proc = Start-Process -FilePath {ps_quote(self.python_exe)} -ArgumentList $runnerArgs -WorkingDirectory {ps_quote(str(self.root))} -WindowStyle Hidden -RedirectStandardOutput {ps_quote(str(logs['stdout']))} -RedirectStandardError {ps_quote(str(logs['stderr']))} -PassThru",
                "$proc.Id",
            ]
        )
        result = subprocess.run(
            [POWERSHELL_EXE, "-NoProfile", "-Command", script],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
        if result.returncode != 0:
            mode = "resume" if resume else "launch"
            stderr_text = (result.stderr or "").strip()
            self.log(f"{mode}_failed[{spec.suite_name}] Start-Process wrapper failed with code {result.returncode}: {stderr_text}")
            return
        pid_text = (result.stdout or "").strip().splitlines()
        pid_value = pid_text[-1].strip() if pid_text else "unknown"
        time.sleep(2)
        mode = "resume" if resume else "launch"
        if not (query_process_count(spec.suite_name) > 0 or is_recent(logs["stdout"], threshold_sec=30) or is_recent(logs["stderr"], threshold_sec=30)):
            self.log(f"{mode}_failed[{spec.suite_name}] runner did not stay alive after Start-Process launch (pid={pid_value}).")
            return
        self.launch_monitor(spec)
        self.log(f"{mode}[{spec.suite_name}] started in background with pid={pid_value}.")

    def inspect_all(self) -> List[Dict[str, object]]:
        return [inspect_suite(self.root, spec) for spec in self.queue]

    def step_once(self) -> str:
        statuses = self.inspect_all()
        running = [entry for entry in statuses if entry["phase"] == "running"]
        if running:
            current = running[0]
            self.write_state(self.build_payload("wait", str(current["suite_name"]), statuses))
            self.log(f"wait[{current['suite_name']}] suite is still running.")
            return "wait"

        for spec, status in zip(self.queue, statuses):
            phase = str(status["phase"])
            if phase == "complete":
                continue
            if phase == "postprocess_needed":
                self.log(f"postprocess[{spec.suite_name}] required outputs are missing but checkpoints look complete.")
                self.run_postprocess(spec)
                refreshed = inspect_suite(self.root, spec)
                statuses = self.inspect_all()
                self.write_state(self.build_payload("postprocess", spec.suite_name, statuses))
                if refreshed["phase"] != "complete":
                    raise RuntimeError(f"Postprocess completed but {spec.suite_name} is still not complete.")
                continue
            if phase == "resume_needed":
                self.launch_suite(spec, resume=True)
                statuses = self.inspect_all()
                self.write_state(self.build_payload("resume", spec.suite_name, statuses))
                return "resume"
            if phase == "missing":
                self.launch_suite(spec, resume=False)
                statuses = self.inspect_all()
                self.write_state(self.build_payload("launch", spec.suite_name, statuses))
                return "launch"
            raise RuntimeError(f"Unknown phase {phase!r} for {spec.suite_name}")

        self.write_state(self.build_payload("queue_complete", None, statuses))
        self.log("queue_complete all configured suites are complete.")
        return "queue_complete"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autopilot for the FedGrid paper experiment queue.")
    parser.add_argument("--project_root", type=Path, default=Path("."))
    parser.add_argument("--python_exe", type=str, default="python")
    parser.add_argument("--interval_sec", type=int, default=300)
    parser.add_argument("--max_cycles", type=int, default=0, help="0 means unbounded in loop mode.")
    parser.add_argument("--allow_full", action="store_true", help="Append the expensive full suite to the queue.")
    parser.add_argument("--loop", action="store_true", help="Keep polling until the queue completes or max_cycles is reached.")
    parser.add_argument("--status_only", action="store_true", help="Refresh and print the human-readable status board without taking queue actions.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.project_root.resolve()
    autopilot = Autopilot(root=root, python_exe=args.python_exe, interval_sec=args.interval_sec, allow_full=args.allow_full)

    if args.status_only:
        statuses = autopilot.inspect_all()
        current_suite = next((str(entry["suite_name"]) for entry in statuses if entry["phase"] == "running"), None)
        payload = autopilot.build_payload("status_only", current_suite, statuses)
        autopilot.write_state(payload)
        print(autopilot.status_md_path.read_text(encoding="utf-8"))
        return 0

    if not args.loop:
        autopilot.step_once()
        return 0

    cycles = 0
    while True:
        cycles += 1
        action = autopilot.step_once()
        if action == "queue_complete":
            return 0
        if args.max_cycles and cycles >= args.max_cycles:
            autopilot.log("max_cycles reached before queue completion.")
            return 0
        time.sleep(args.interval_sec)


if __name__ == "__main__":
    raise SystemExit(main())
