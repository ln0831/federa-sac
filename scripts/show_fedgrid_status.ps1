param(
    [string]$RootDir = ".",
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$root = (Resolve-Path $RootDir).Path

& $PythonExe `
    (Join-Path $root "scripts\fedgrid_autopilot.py") `
    --project_root $root `
    --python_exe $PythonExe `
    --status_only
