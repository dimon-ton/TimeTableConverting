# Monitor Windows Task Scheduler Test
# Shows task status and recent log entries

$taskName = "TimeTableTest"
$logFile = "C:\Users\Phontan-Chang\Documents\TimeTableConverting\logs\cron_test.log"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Monitoring Cron Job Test" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if task exists
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "ERROR: Task '$taskName' not found!" -ForegroundColor Red
    Write-Host "Run setup_windows_test_cron.ps1 first to create the task." -ForegroundColor Yellow
    exit 1
}

# Get task info
$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
Write-Host "Task Status" -ForegroundColor Green
Write-Host "  Name: $taskName" -ForegroundColor White
Write-Host "  State: $($task.State)" -ForegroundColor White
Write-Host "  Last Run: $($taskInfo.LastRunTime)" -ForegroundColor White
Write-Host "  Last Result: $($taskInfo.LastTaskResult)" -ForegroundColor White
Write-Host "  Next Run: $($taskInfo.NextRunTime)" -ForegroundColor White
Write-Host ""

# Show log file info
if (Test-Path $logFile) {
    $logSize = (Get-Item $logFile).Length
    $logSizeKB = [math]::Round($logSize / 1KB, 2)

    Write-Host "Log File Status" -ForegroundColor Green
    Write-Host "  Path: $logFile" -ForegroundColor White
    Write-Host "  Size: $logSizeKB KB" -ForegroundColor White
    Write-Host ""

    # Count executions
    $executions = (Select-String -Path $logFile -Pattern "Processing Daily Leave Requests" -AllMatches).Matches.Count
    Write-Host "  Total Executions: $executions" -ForegroundColor White

    # Check for errors
    $errors = (Select-String -Path $logFile -Pattern "ERROR|FATAL|FAIL" -AllMatches).Matches.Count
    if ($errors -gt 0) {
        Write-Host "  Errors Found: $errors" -ForegroundColor Red
    } else {
        Write-Host "  Errors Found: 0" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Recent Log Entries (Last 30 lines)" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    Get-Content $logFile -Tail 30

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "To watch log in real-time, run:" -ForegroundColor Yellow
    Write-Host "  Get-Content '$logFile' -Wait" -ForegroundColor Gray
    Write-Host "============================================================" -ForegroundColor Cyan
} else {
    Write-Host "Log file not found yet. Task may not have run." -ForegroundColor Yellow
    Write-Host "Next run scheduled for: $($taskInfo.NextRunTime)" -ForegroundColor White
}
