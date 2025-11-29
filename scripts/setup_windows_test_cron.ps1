# Setup Windows Task Scheduler for Cron Job Testing
# This creates a scheduled task that runs every 5 minutes for 2 hours

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setting up Windows Task Scheduler Test" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$projectPath = "C:\Users\Phontan-Chang\Documents\TimeTableConverting"
$logFile = "$projectPath\logs\cron_test.log"
$taskName = "TimeTableTest"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Task '$taskName' already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Old task removed." -ForegroundColor Green
}

# Create the action (what to run)
Write-Host "Creating scheduled task action..." -ForegroundColor Cyan
$pythonExe = (Get-Command python).Path
$arguments = "-m src.utils.daily_leave_processor --test >> `"$logFile`" 2>&1"
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c cd `"$projectPath`" && `"$pythonExe`" $arguments" -WorkingDirectory $projectPath

# Create the trigger (when to run - every 5 minutes for 2 hours)
Write-Host "Creating trigger (runs every 5 minutes for 2 hours)..." -ForegroundColor Cyan
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Hours 2)

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task
Write-Host "Registering scheduled task..." -ForegroundColor Cyan
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Test TimeTable cron job every 5 minutes" -Force | Out-Null

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "SUCCESS! Scheduled task created" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Task Name: $taskName" -ForegroundColor White
Write-Host "Runs: Every 5 minutes for the next 2 hours" -ForegroundColor White
Write-Host "Log File: $logFile" -ForegroundColor White
Write-Host ""
Write-Host "Monitoring Commands:" -ForegroundColor Yellow
Write-Host "  1. View task status:" -ForegroundColor Gray
Write-Host "     Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Watch log file:" -ForegroundColor Gray
Write-Host "     Get-Content '$logFile' -Wait" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. View recent log entries:" -ForegroundColor Gray
Write-Host "     Get-Content '$logFile' -Tail 50" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Remove task when done:" -ForegroundColor Gray
Write-Host "     Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Gray
Write-Host ""
Write-Host "The task will run for the first time within 5 minutes..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
