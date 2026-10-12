# Register the weekly Reading Radar task with the Windows Task Scheduler.
#
# Monday 06:00 (the cadence in meta/profile.json). The task runs under the current user and only
# while that user is logged on, so that no password is stored. A missed start runs as soon as
# possible afterwards.
param(
    [string]$TaskName = 'ReadingRadarWeekly',
    [string]$Time = '06:00'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$script = Join-Path $PSScriptRoot 'run-weekly.ps1'
$powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'

$action = New-ScheduledTaskAction -Execute $powershell `
    -Argument ('-NoProfile -ExecutionPolicy Bypass -File "' + $script + '"') `
    -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -Description 'Weekly harvest of the Reading Radar. Runs the automatic part and pushes the result.' `
    -Force | Out-Null

Write-Output ('Task registered: ' + $TaskName)
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State
(Get-ScheduledTask -TaskName $TaskName).Triggers | Select-Object StartBoundary, DaysOfWeek
Write-Output ''
Write-Output 'Test it now with:  schtasks /run /tn ReadingRadarWeekly'
Write-Output 'Read the log at:   logs\weekly-YYYY-MM-DD.log'
