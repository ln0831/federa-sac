param(
    [string]$RootDir = ".",
    [string]$SuiteName = "case141_fedgrid_main_rr",
    [int]$IntervalSec = 60,
    [int]$MaxChecks = 720
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = (Resolve-Path $RootDir).Path
$suiteRoot = Join-Path $root ("outputs\suites\" + $SuiteName)
$logDir = Join-Path $root "outputs\automation_logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$snapshotPath = Join-Path $logDir ($SuiteName + ".monitor.json")
$historyPath = Join-Path $logDir ($SuiteName + ".monitor.log")
$stdoutPath = Join-Path $logDir ($SuiteName + ".utf8.stdout.log")
$stderrPath = Join-Path $logDir ($SuiteName + ".utf8.stderr.log")

function Get-ShortTail {
    param(
        [string]$Path,
        [int]$Tail = 20
    )
    if (-not (Test-Path $Path)) {
        return @()
    }
    return @(
        Get-Content $Path -Tail $Tail -ErrorAction SilentlyContinue |
            ForEach-Object { [string]$_ }
    )
}

function Get-EntryCount {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return 0
    }
    return @(
        Get-ChildItem $Path -Recurse -File -ErrorAction SilentlyContinue
    ).Count
}

function Get-ProcessSummary {
    param([object[]]$Processes)
    return @(
        $Processes | ForEach-Object {
            $cmd = [string]$_.CommandLine
            if ($cmd.Length -gt 220) {
                $cmd = $cmd.Substring(0, 220)
            }
            [ordered]@{
                pid = $_.ProcessId
                name = $_.Name
                cmd = $cmd
            }
        }
    )
}

for ($check = 1; $check -le $MaxChecks; $check++) {
    $procMatches = @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                ($_.CommandLine -match [regex]::Escape($SuiteName)) -or
                ($_.CommandLine -match 'run_case141_fedgrid_v6.py') -or
                ($_.CommandLine -match 'train_gnn_fedgrid.py') -or
                ($_.CommandLine -match 'evaluate_topology_shift_deterministic.py') -or
                ($_.CommandLine -match 'summarize_fedgrid_suite_v6.py') -or
                ($_.CommandLine -match 'export_fedgrid_tables_v6.py') -or
                ($_.CommandLine -match 'make_fedgrid_figures_v6.py') -or
                ($_.CommandLine -match 'make_fedgrid_report_v6.py')
            } |
            Select-Object ProcessId, Name, CommandLine
    )

    $payload = [ordered]@{
        timestamp = (Get-Date).ToString("s")
        suite_name = $SuiteName
        suite_root = $suiteRoot
        running = ($procMatches.Count -gt 0)
        process_count = $procMatches.Count
        processes = Get-ProcessSummary -Processes $procMatches
        checkpoints = Get-EntryCount (Join-Path $suiteRoot "checkpoints")
        eval_files = Get-EntryCount (Join-Path $suiteRoot "eval")
        agg_files = Get-EntryCount (Join-Path $suiteRoot "agg")
        report_files = Get-EntryCount (Join-Path $suiteRoot "reports")
        manifest_files = Get-EntryCount (Join-Path $suiteRoot "manifests")
        log_files = Get-EntryCount (Join-Path $suiteRoot "logs")
        stdout_tail = Get-ShortTail -Path $stdoutPath -Tail 8
        stderr_tail = Get-ShortTail -Path $stderrPath -Tail 8
    }

    $json = $payload | ConvertTo-Json -Depth 4 -Compress
    Set-Content -Path $snapshotPath -Value $json -Encoding UTF8

    $historyLine = "[{0}] running={1} checkpoints={2} eval={3} agg={4} reports={5}" -f `
        $payload.timestamp, $payload.running, $payload.checkpoints, $payload.eval_files, $payload.agg_files, $payload.report_files
    Add-Content -Path $historyPath -Value $historyLine -Encoding UTF8

    if (-not $payload.running) {
        break
    }

    Start-Sleep -Seconds $IntervalSec
}
