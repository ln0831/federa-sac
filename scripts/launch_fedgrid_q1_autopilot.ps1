param(
    [string]$RootDir = ".",
    [string]$PythonExe = "python",
    [int]$IntervalSec = 300
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path $RootDir).Path
$queueJson = Join-Path $root "project\experiments\runs\q1_queue_20260407.json"

& (Join-Path $root "scripts\launch_fedgrid_autopilot.ps1") `
    -RootDir $root `
    -PythonExe $PythonExe `
    -IntervalSec $IntervalSec `
    -QueueJson $queueJson `
    -LogPrefix "fedgrid_q1_autopilot"
