param(
    [string]$RootDir = ".",
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path $RootDir).Path
$queueJson = Join-Path $root "project\experiments\runs\q1_queue_20260407.json"

& (Join-Path $root "scripts\show_fedgrid_status.ps1") `
    -RootDir $root `
    -PythonExe $PythonExe `
    -QueueJson $queueJson `
    -LogPrefix "fedgrid_q1_autopilot"
