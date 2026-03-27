param(
    [string]$RootDir = ".",
    [string]$PythonExe = "python",
    [string]$SuiteName = "case141_fedgrid_main_rr",
    [string]$Preset = "main",
    [string]$Methods = "preset",
    [string[]]$Seeds = @("0", "1", "2"),
    [string]$TrainTopologyMode = "random_reset",
    [int]$OutageK = 6,
    [string]$OutagePolicy = "local",
    [int]$OutageRadius = 2,
    [int]$Gpu = 0,
    [int]$Epochs = 100,
    [switch]$SkipExisting
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$root = (Resolve-Path $RootDir).Path
Set-Location $root

$suiteRoot = Join-Path $root ("outputs\suites\" + $SuiteName)

$runnerArgs = @(
    "run_case141_fedgrid_v6.py",
    "--project_root", ".",
    "--suite_name", $SuiteName,
    "--preset", $Preset,
    "--methods", $Methods,
    "--train_topology_mode", $TrainTopologyMode,
    "--outage_k", $OutageK,
    "--outage_policy", $OutagePolicy,
    "--outage_radius", $OutageRadius,
    "--gpu", $Gpu,
    "--epochs", $Epochs,
    "--no_post"
)

if ($SkipExisting) {
    $runnerArgs += "--skip_existing"
}

$runnerArgs += "--seeds"
$runnerArgs += $Seeds

& $PythonExe @runnerArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonExe "summarize_fedgrid_suite_v6.py" "--suite_root" $suiteRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonExe "export_fedgrid_tables_v6.py" "--suite_root" $suiteRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonExe "make_fedgrid_figures_v6.py" "--suite_root" $suiteRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PythonExe "make_fedgrid_report_v6.py" "--suite_root" $suiteRoot
exit $LASTEXITCODE
