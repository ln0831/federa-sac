param(
    [string]$RootDir = ".",
    [string]$PythonExe = "python",
    [string]$QueueJson = "",
    [string]$LogPrefix = "fedgrid_autopilot"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$root = (Resolve-Path $RootDir).Path

$args = @(
    (Join-Path $root "scripts\fedgrid_autopilot.py"),
    "--project_root", $root,
    "--python_exe", $PythonExe,
    "--log_prefix", $LogPrefix,
    "--status_only"
)

if ($QueueJson) {
    $args += "--queue_json"
    $args += (Resolve-Path $QueueJson).Path
}

& $PythonExe @args
