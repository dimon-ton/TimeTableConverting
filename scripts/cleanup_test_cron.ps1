# Cleanup Windows Task Scheduler Test
# Removes the test scheduled task

$taskName = "TimeTableTest"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Cleaning up Cron Job Test" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if task exists
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "Task '$taskName' not found. Nothing to clean up." -ForegroundColor Yellow
    exit 0
}

Write-Host "Removing task '$taskName'..." -ForegroundColor Yellow
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "SUCCESS! Task removed" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "The log file has been preserved at:" -ForegroundColor White
Write-Host "  C:\Users\Phontan-Chang\Documents\TimeTableConverting\logs\cron_test.log" -ForegroundColor Gray
Write-Host ""
Write-Host "You can delete it manually if needed." -ForegroundColor White
