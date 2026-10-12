# Run one weekly cycle of the Reading Radar.
#
# The scheduled task calls this file. It writes a log next to the repository and returns the exit
# code of tools/weekly.py, so that the Task Scheduler records a failure.
param(
    [switch]$DryRun,
    [switch]$NoPush
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root

$logDir = Join-Path $root 'logs'
if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}
$log = Join-Path $logDir ('weekly-' + (Get-Date -Format 'yyyy-MM-dd') + '.log')

$arguments = @('tools/weekly.py')
if ($DryRun) { $arguments += '--dry-run' }
if ($NoPush) { $arguments += '--no-push' }

"=== Reading Radar weekly cycle, started $(Get-Date -Format 'u') ===" | Out-File -FilePath $log -Append -Encoding utf8
& py -3 @arguments 2>&1 | Tee-Object -FilePath $log -Append
$code = $LASTEXITCODE
"=== finished with exit code $code, $(Get-Date -Format 'u') ===" | Out-File -FilePath $log -Append -Encoding utf8

if ($code -ne 0) {
    Write-Error "The weekly cycle failed with exit code $code. See $log"
}
exit $code
