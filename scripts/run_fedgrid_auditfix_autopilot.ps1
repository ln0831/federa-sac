param(
    [string]$RootDir = ".",
    [string]$PythonExe = "python",
    [int]$IntervalSec = 300
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$root = (Resolve-Path $RootDir).Path
$queueJson = Join-Path $root "project\experiments\runs\auditfix_queue_20260408.json"

if (-not (Test-Path $queueJson)) {
    throw "Missing queue file: $queueJson"
}

Set-Location $root

& $PythonExe `
    (Join-Path $root "scripts\fedgrid_autopilot.py") `
    --project_root $root `
    --python_exe $PythonExe `
    --queue_json $queueJson `
    --log_prefix "fedgrid_auditfix_autopilot" `
    --loop `
    --interval_sec $IntervalSec

exit $LASTEXITCODE
