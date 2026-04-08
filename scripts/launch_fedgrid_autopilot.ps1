param(
    [string]$RootDir = ".",
    [string]$PythonExe = "python",
    [int]$IntervalSec = 300,
    [switch]$AllowFull,
    [string]$QueueJson = "",
    [string]$LogPrefix = "fedgrid_autopilot"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$root = (Resolve-Path $RootDir).Path
$logDir = Join-Path $root "outputs\automation_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$stdoutPath = Join-Path $logDir ($LogPrefix + ".stdout.log")
$stderrPath = Join-Path $logDir ($LogPrefix + ".stderr.log")

$args = @(
    (Join-Path $root "scripts\fedgrid_autopilot.py"),
    "--project_root", $root,
    "--python_exe", $PythonExe,
    "--log_prefix", $LogPrefix,
    "--loop",
    "--interval_sec", $IntervalSec
)

if ($AllowFull) {
    $args += "--allow_full"
}

if ($QueueJson) {
    $args += "--queue_json"
    $args += (Resolve-Path $QueueJson).Path
}

$proc = Start-Process `
    -FilePath $PythonExe `
    -ArgumentList $args `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath `
    -PassThru

Write-Host ("[STARTED] FedGrid autopilot pid={0}" -f $proc.Id)
Write-Host ("[STDOUT]  {0}" -f $stdoutPath)
Write-Host ("[STDERR]  {0}" -f $stderrPath)
