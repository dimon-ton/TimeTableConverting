# Cron Job Testing Scripts

These PowerShell scripts help you test the daily leave processor cron job on Windows using Task Scheduler.

## Scripts

### 1. setup_windows_test_cron.ps1
Creates a scheduled task that runs the cron job every 5 minutes for 2 hours.

**Usage:**
```powershell
# Open PowerShell as Administrator
cd C:\Users\Phontan-Chang\Documents\TimeTableConverting\scripts
.\setup_windows_test_cron.ps1
```

**What it does:**
- Creates a scheduled task named "TimeTableTest"
- Runs `python -m src.utils.daily_leave_processor --test` every 5 minutes
- Test mode: No database writes, no LINE messages
- Logs output to `logs\cron_test.log`
- Task expires after 2 hours

### 2. monitor_test_cron.ps1
Monitors the scheduled task and shows recent log entries.

**Usage:**
```powershell
.\monitor_test_cron.ps1
```

**What it shows:**
- Task status (running, ready, disabled)
- Last run time and result
- Next scheduled run
- Total executions
- Error count
- Recent log entries (last 30 lines)

### 3. cleanup_test_cron.ps1
Removes the test scheduled task when you're done testing.

**Usage:**
```powershell
.\cleanup_test_cron.ps1
```

**What it does:**
- Removes the "TimeTableTest" scheduled task
- Preserves the log file for review

## Testing Workflow

### Step 1: Set Up Test
```powershell
# Run as Administrator
.\setup_windows_test_cron.ps1
```

### Step 2: Monitor Execution
Wait 5 minutes for first execution, then:

```powershell
# Check status
.\monitor_test_cron.ps1

# Or watch log in real-time
Get-Content ..\logs\cron_test.log -Wait
```

### Step 3: Verify Results
Check that:
- Task runs every 5 minutes
- No errors in logs
- Console output shows successful processing
- Data loaded correctly
- Substitutes found

### Step 4: Cleanup
When satisfied with testing:

```powershell
.\cleanup_test_cron.ps1
```

## Manual Commands

### View Task Info
```powershell
Get-ScheduledTask -TaskName "TimeTableTest" | Get-ScheduledTaskInfo
```

### View Recent Logs
```powershell
Get-Content ..\logs\cron_test.log -Tail 50
```

### Watch Logs Live
```powershell
Get-Content ..\logs\cron_test.log -Wait
```

### Force Run Task Now
```powershell
Start-ScheduledTask -TaskName "TimeTableTest"
```

### Stop Running Task
```powershell
Stop-ScheduledTask -TaskName "TimeTableTest"
```

## Expected Output

Each execution should show:
```
============================================================
Processing Daily Leave Requests
============================================================
Target Date: 2025-11-29
Test Mode: True
Send to LINE: False

Loading data files...
  OK Loaded 222 timetable entries
  OK Loaded 16 teachers' subject mappings
  ...

OK Loaded 12 historical substitute assignments
============================================================

Fetching and enriching leave requests for 2025-11-29...
...

[REPORT] 2025-11-29
(Thai text report)
```

## Troubleshooting

### Task doesn't run
- Ensure PowerShell was run as Administrator
- Check Task Scheduler app: Task Scheduler Library
- Verify Python is in system PATH

### Errors in log
- Review error messages in `logs\cron_test.log`
- Check `.env` credentials are correct
- Verify Google Sheets access
- Test manually: `python -m src.utils.daily_leave_processor --test`

### Log file empty
- Task may not have run yet (check next run time)
- Check Task Scheduler app for task history
- Verify working directory is correct

## Notes

- Test mode is safe: No database writes, no LINE messages
- Task auto-expires after 2 hours
- Log file accumulates all test runs
- You can run tests multiple times
- Thai text may appear garbled in Windows console but works correctly in LINE
