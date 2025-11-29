# Google Apps Script Web App: Teacher Working Hours Dashboard

## Project Overview

Build a responsive web application using Google Apps Script that displays teacher working hours accumulation, showing regular teaching periods, substitute periods, and absences in an easy-to-read infographic format.

## Requirements Summary

**Metrics to Display:**
- Regular periods scheduled today (from timetable for current day of week)
- Cumulative substitute periods taught (from school year start to current date)
- Cumulative absence periods (from school year start to current date)
- Net total teaching burden: `all_regular_periods_taught + cumulative_substitute - cumulative_absence`

**Tracking System:**
- New worksheet: `Teacher_Hours_Tracking` for persistent storage
- Daily snapshots recorded at 8:55 AM with existing Python processor
- Historical tracking allows trend analysis over time
- Web app displays latest snapshot as "current state"

**Visualization:**
- Leaderboard/ranking table (sortable)
- Individual teacher statistics cards
- Summary statistics cards
- Trend charts (optional future enhancement)

**Interactivity:**
- Filter by teacher, date range, subject, class
- Sortable columns
- Responsive Bootstrap design (mobile/tablet/desktop)

**Data Sources:**
- Regular timetable: `data/real_timetable.json` (222 entries)
- Leave logs: Google Sheets `Leave_Logs` worksheet
- Teacher tracking: Google Sheets `Teacher_Hours_Tracking` worksheet (NEW)
- Teacher names: `data/teacher_full_names.json` (16 teachers)

## Architecture Decision

### Data Integration Strategy

**Timetable Data (real_timetable.json):**
- **Approach:** Hardcode as JavaScript constant in `DataConstants.gs`
- **Rationale:** 222 entries is small, timetable is relatively static, eliminates external dependencies, faster access (no I/O)

**Teacher Names:**
- **Approach:** Hardcode as JavaScript object in `DataConstants.gs`
- **Rationale:** Only 16 teachers, simple mapping, no API calls needed

**Leave Logs (Google Sheets):**
- **Approach:** Read dynamically using SpreadsheetApp API with 5-minute cache
- **Rationale:** Data changes frequently, needs to be current, caching improves performance

**Teacher Hours Tracking (NEW - Google Sheets):**
- **Approach:** New worksheet `Teacher_Hours_Tracking` with daily snapshots
- **Write Method:** Python `daily_leave_processor.py` writes snapshot after processing
- **Read Method:** Apps Script reads latest snapshot for web app display
- **Schema:**
  ```
  Date | Teacher_ID | Teacher_Name | Day_of_Week | Regular_Periods_Today | Cumulative_Substitute | Cumulative_Absence | Net_Total_Burden | Updated_At
  ```
- **Field Definitions:**
  - `Regular_Periods_Today`: Scheduled periods for that specific day (e.g., 5 on Monday)
  - `Cumulative_Substitute`: Total substitute periods from start of school year to snapshot date
  - `Cumulative_Absence`: Total absence periods from start of school year to snapshot date
  - `Net_Total_Burden`: Sum of all regular periods taught (all working days) + cumulative_substitute - cumulative_absence
- **Rationale:** Persistent tracking enables historical analysis, reduces calculation overhead in web app, shows current teaching burden

### Technology Stack
- **Backend:** Google Apps Script (JavaScript ES5/V8)
- **Frontend:** HTML5 + Bootstrap 5.3 + Vanilla JavaScript
- **Data Storage:** Google Sheets (spreadsheet ID: `1KpQZlrJk03ZS_Q0bTWvxHjG9UFiD1xPZGyIsQfRkRWo`)
- **Development:** clasp (Command Line Apps Script Projects)
- **Deployment:** Google Apps Script Web App

## Project Structure

```
C:\Users\Phontan-Chang\Documents\TTAccumalatingTime\gas-webapp\
│
├── .clasp.json              # clasp configuration
├── appsscript.json          # Apps Script manifest
│
├── Code.gs                  # Main server-side logic (doGet, API functions)
├── DataConstants.gs         # Hardcoded timetable & teacher names
├── Calculations.gs          # Helper calculation functions
│
├── Index.html              # Main HTML structure
├── Filters.html            # Filter controls component
├── Leaderboard.html        # Leaderboard table component
├── JavaScript.html         # Client-side JavaScript logic
└── Stylesheet.html         # Custom CSS styles
```

## Implementation Plan

### Phase 0: Database Setup (30 min)

**Create Teacher_Hours_Tracking Worksheet:**

1. Open Google Sheets (ID: `1KpQZlrJk03ZS_Q0bTWvxHjG9UFiD1xPZGyIsQfRkRWo`)
2. Create new worksheet: `Teacher_Hours_Tracking`
3. Add headers:
   ```
   Date | Teacher_ID | Teacher_Name | Day_of_Week | Regular_Periods_Today | Cumulative_Substitute | Cumulative_Absence | Net_Total_Burden | Updated_At
   ```
4. Add note in cell A2: "Regular_Periods_Today = scheduled periods for this day of week; Net_Total_Burden = all regular periods taught + cumulative substitutes - cumulative absences"

**Modify Python Daily Processor:**

**File: `C:\Users\Phontan-Chang\Documents\TimeTableConverting\src\utils\daily_leave_processor.py`**

Add function to write daily snapshot:
```python
def write_teacher_hours_snapshot(date_str: str):
    """
    Calculate and write cumulative teacher hours snapshot.
    Called at end of daily processing.

    Calculation:
    - Regular_Periods_Today: Scheduled periods for this day of week
    - Cumulative_Substitute: Total substitutes from school year start to date_str
    - Cumulative_Absence: Total absences from school year start to date_str
    - Net_Total_Burden: Sum of all regular periods taught + cumulative_substitute - cumulative_absence
    """
    from src.utils.sheet_utils import get_sheets_client
    from src.config import config
    import json
    from datetime import datetime

    # Load timetable for regular periods
    with open(config.TIMETABLE_FILE, 'r', encoding='utf-8') as f:
        timetable = json.load(f)

    # Load teacher names
    with open(config.TEACHER_FULL_NAMES_FILE, 'r', encoding='utf-8') as f:
        teacher_names = json.load(f)

    # Determine day of week for date_str
    from datetime import datetime as dt
    date_obj = dt.strptime(date_str, '%Y-%m-%d')
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_of_week = day_names[date_obj.weekday()]

    # Calculate regular periods for TODAY (this day of week) per teacher
    teacher_stats = {}
    for teacher_id in teacher_names.keys():
        # Count periods scheduled for this specific day of week
        regular_today = sum(1 for entry in timetable
                          if entry['teacher_id'] == teacher_id
                          and entry['day_id'] == day_of_week)

        teacher_stats[teacher_id] = {
            'teacher_id': teacher_id,
            'teacher_name': teacher_names[teacher_id],
            'day_of_week': day_of_week,
            'regular_periods_today': regular_today,
            'cumulative_substitute': 0,
            'cumulative_absence': 0,
            'total_regular_taught': 0  # Will calculate below
        }

    # Load all Leave_Logs to calculate cumulative totals
    client = get_sheets_client()
    spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
    leave_logs_ws = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)
    all_logs = leave_logs_ws.get_all_records()

    # Determine school year start date (adjust as needed for your school)
    # Example: School year starts September 1st
    year = date_obj.year if date_obj.month >= 9 else date_obj.year - 1
    school_year_start = f"{year}-09-01"

    # Count cumulative substitutions and absences from school year start to current date
    for log in all_logs:
        log_date = log.get('Date', '')
        if school_year_start <= log_date <= date_str:  # Within school year up to current date
            # Count absences
            absent_teacher = log.get('Absent_Teacher', '')
            if absent_teacher in teacher_stats:
                teacher_stats[absent_teacher]['cumulative_absence'] += 1

            # Count substitutions
            substitute_teacher = log.get('Substitute_Teacher', '')
            if substitute_teacher and substitute_teacher != "Not Found" and substitute_teacher in teacher_stats:
                teacher_stats[substitute_teacher]['cumulative_substitute'] += 1

    # Calculate total regular periods taught (number of working days * periods per day)
    # Count working days from school year start to current date
    from datetime import timedelta
    start_date = dt.strptime(school_year_start, '%Y-%m-%d')
    current_date = dt.strptime(date_str, '%Y-%m-%d')

    # Count days by day of week
    day_counts = {day: 0 for day in day_names[:5]}  # Mon-Fri only
    temp_date = start_date
    while temp_date <= current_date:
        if temp_date.weekday() < 5:  # Monday=0 to Friday=4
            day_counts[day_names[temp_date.weekday()]] += 1
        temp_date += timedelta(days=1)

    # Calculate total regular periods taught for each teacher
    for teacher_id, stats in teacher_stats.items():
        total_regular = 0
        for day in day_names[:5]:  # Mon-Fri
            periods_on_day = sum(1 for entry in timetable
                               if entry['teacher_id'] == teacher_id
                               and entry['day_id'] == day)
            total_regular += periods_on_day * day_counts[day]

        stats['total_regular_taught'] = total_regular

    # Write snapshot to Teacher_Hours_Tracking
    tracking_ws = spreadsheet.worksheet('Teacher_Hours_Tracking')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for teacher_id, stats in teacher_stats.items():
        # Net Total Burden = all regular periods taught + cumulative substitutes - cumulative absences
        net_total_burden = (stats['total_regular_taught'] +
                          stats['cumulative_substitute'] -
                          stats['cumulative_absence'])

        row = [
            date_str,
            teacher_id,
            stats['teacher_name'],
            stats['day_of_week'],
            stats['regular_periods_today'],
            stats['cumulative_substitute'],
            stats['cumulative_absence'],
            net_total_burden,
            timestamp
        ]

        tracking_ws.append_row(row, value_input_option='USER_ENTERED')

    print(f"✓ Written teacher hours snapshot for {date_str} ({day_of_week}) - {len(teacher_stats)} teachers")
    print(f"  School year: {school_year_start} to {date_str}")
    print(f"  Working days: {sum(day_counts.values())} total")
```

**Update main processing function:**
```python
# At end of process_daily_leaves() function, add:
write_teacher_hours_snapshot(target_date)
```

### Phase 1: Setup (30 min)

**Install clasp:**
```bash
npm install -g @google/clasp
clasp login
```

**Create project:**
```bash
cd C:\Users\Phontan-Chang\Documents\TTAccumalatingTime
mkdir gas-webapp
cd gas-webapp
clasp create --type webapp --title "Teacher Hours Dashboard"
```

### Phase 2: Backend Development (2 hours)

**File: DataConstants.gs**
- Convert `real_timetable.json` to JavaScript array `REAL_TIMETABLE`
- Convert `teacher_full_names.json` to object `TEACHER_NAMES`
- Define subject/class mappings

**File: Code.gs**
- `doGet()`: Web app entry point, returns HTML template
- `include(filename)`: Helper for HTML partials
- `getTeacherHoursTracking()`: Read latest snapshot from Teacher_Hours_Tracking (MODIFIED)
- `getTeacherMetrics(filters)`: Return metrics from tracking snapshot, apply filters
- `getFilterOptions()`: Return dropdown options (teachers, subjects, classes)
- `getHistoricalTrends(teacherId, days)`: Get historical snapshots for trend charts (optional)

**File: Calculations.gs**
- `calculateRegularPeriods(teacherId)`: Count from timetable
- `matchesFilters(entry, filters)`: Filter validation
- `matchesDateRange(dateStr, filters)`: Date range check

**Calculation Logic (UPDATED):**

The web app now reads pre-calculated data from `Teacher_Hours_Tracking` instead of calculating on-demand:

```javascript
function getTeacherHoursTracking() {
  const cache = CacheService.getScriptCache();
  const cached = cache.get('teacher_hours_tracking');

  if (cached) {
    return JSON.parse(cached);
  }

  const ss = SpreadsheetApp.openById('1KpQZlrJk03ZS_Q0bTWvxHjG9UFiD1xPZGyIsQfRkRWo');
  const sheet = ss.getSheetByName('Teacher_Hours_Tracking');
  const data = sheet.getDataRange().getValues();

  // Get latest snapshot for each teacher (most recent date)
  const latestByTeacher = {};
  const headers = data[0];

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const teacherId = row[1]; // Teacher_ID column
    const date = row[0]; // Date column

    if (!latestByTeacher[teacherId] || date > latestByTeacher[teacherId].date) {
      latestByTeacher[teacherId] = {
        date: date,
        teacher_id: row[1],
        teacher_name: row[2],
        day_of_week: row[3],
        regular_periods_today: row[4],
        cumulative_substitute: row[5],
        cumulative_absence: row[6],
        net_total_burden: row[7],
        updated_at: row[8]
      };
    }
  }

  const result = Object.values(latestByTeacher);

  // Cache for 5 minutes
  cache.put('teacher_hours_tracking', JSON.stringify(result), 300);
  return result;
}

function getTeacherMetrics(filters) {
  // Read from tracking snapshot instead of calculating
  let data = getTeacherHoursTracking();

  // Apply filters if provided
  if (filters) {
    if (filters.teacherId) {
      data = data.filter(t => t.teacher_id === filters.teacherId);
    }
    // Date range filtering would query historical snapshots
    // Subject/Class filtering would require joining with timetable data
  }

  return data;
}
```

**Python Calculation (runs daily at 8:55 AM):**
```python
# For each teacher on snapshot date:

# 1. Determine day of week (Mon, Tue, Wed, Thu, Fri)
day_of_week = get_day_of_week(date_str)  # e.g., "Mon"

# 2. Calculate regular periods scheduled for TODAY
regular_periods_today = count(real_timetable.json
                             where teacher_id = T
                             AND day_id = day_of_week)

# 3. Calculate cumulative substitute periods (from school year start)
cumulative_substitute = count(Leave_Logs
                             where Substitute_Teacher = T
                             AND school_year_start <= Date <= date_str)

# 4. Calculate cumulative absence periods (from school year start)
cumulative_absence = count(Leave_Logs
                          where Absent_Teacher = T
                          AND school_year_start <= Date <= date_str)

# 5. Calculate total regular periods taught (all working days to date)
total_regular_taught = 0
for each_day in [Mon, Tue, Wed, Thu, Fri]:
    periods_on_day = count(real_timetable.json
                          where teacher_id = T
                          AND day_id = each_day)
    working_days_count = count_working_days(school_year_start, date_str, each_day)
    total_regular_taught += periods_on_day * working_days_count

# 6. Calculate net total burden
net_total_burden = total_regular_taught + cumulative_substitute - cumulative_absence

# Write row to Teacher_Hours_Tracking worksheet
```

### Phase 3: Frontend Development (3 hours)

**File: Index.html**
- Bootstrap 5.3 layout structure
- Header with title and icon
- Filters section (includes Filters.html)
- Summary cards row (4 cards: total teachers, substitutions, absences, average)
- Leaderboard section (includes Leaderboard.html)
- Teacher cards grid (responsive columns)
- Loading spinner

**File: Filters.html**
- Date range inputs (start/end date)
- Teacher dropdown (populated dynamically)
- Subject dropdown
- Class dropdown
- Submit and reset buttons

**File: Leaderboard.html**
- Bootstrap table (striped, hover effects)
- Sortable columns: rank, name, regular, substitute, absence, net
- Top 3 highlighting (gold, silver, bronze)

**File: JavaScript.html**
- `loadFilterOptions()`: Populate dropdowns via `google.script.run`
- `loadTeacherData(filters)`: Fetch metrics from backend
- `renderDashboard(data)`: Render all components
- `renderSummaryCards(data)`: Calculate totals and averages
- `renderLeaderboard(data)`: Populate table, apply ranking
- `renderTeacherCards(data)`: Create Bootstrap cards for each teacher
- `handleFilterSubmit()`: Apply filters and reload data
- `setupTableSort()`: Implement column sorting
- Loading/error handling

**File: Stylesheet.html**
- Custom CSS for Thai fonts (Sarabun, Noto Sans Thai)
- Card hover effects
- Responsive design adjustments
- Color scheme (Bootstrap primary blue)
- Mobile optimizations

### Phase 4: Integration & Testing (1 hour)

**Test Backend Functions:**
```javascript
// In Apps Script editor
function testDataAccess() {
  Logger.log('Timetable entries: ' + REAL_TIMETABLE.length); // Should be 222
  Logger.log('Teachers: ' + Object.keys(TEACHER_NAMES).length); // Should be 16

  const logs = getLeaveLogsData();
  Logger.log('Leave_Logs rows: ' + logs.length);

  const metrics = getTeacherMetrics();
  Logger.log('Teacher metrics calculated: ' + metrics.length);
}
```

**Test Calculations:**
```javascript
function verifyCalculations() {
  const metrics = getTeacherMetrics();
  const teacher = metrics.find(t => t.teacher_id === 'T002');

  // Verify formula
  const expected = teacher.regular_base_periods + teacher.substitute_periods - teacher.absence_periods;
  Logger.log('Net accumulation matches: ' + (expected === teacher.net_accumulation));
}
```

**Test Web App:**
- Run "Test deployments" in Apps Script editor
- Verify data loads correctly
- Test all filters
- Test table sorting
- Test responsive design (resize browser)

### Phase 5: Deployment (30 min)

**Push Code:**
```bash
clasp push
```

**Deploy Web App:**
```bash
clasp deploy --description "Initial deployment v1.0"
```

**Or via UI:**
1. Run `clasp open`
2. Click "Deploy" > "New deployment"
3. Type: "Web app"
4. Execute as: "Me"
5. Who has access: "Anyone" (or restrict to domain)
6. Click "Deploy"
7. Copy web app URL

**Configure appsscript.json:**
```json
{
  "timeZone": "Asia/Bangkok",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "webapp": {
    "access": "ANYONE",
    "executeAs": "USER_DEPLOYING"
  }
}
```

### Phase 6: Documentation (30 min)

- Create README.md with deployment instructions
- Document calculation formulas
- Create user guide in Thai
- Document update process for timetable changes

## Key Implementation Details

### Backend API Functions

**getTeacherMetrics(filters):**
```javascript
// Returns array of teacher statistics from latest tracking snapshot:
[
  {
    date: "2025-11-29",
    teacher_id: "T002",
    teacher_name: "ครูอำพร",
    day_of_week: "Fri",
    regular_periods_today: 5,  // Scheduled for Friday
    cumulative_substitute: 8,   // Total substitutes since Sept 1
    cumulative_absence: 3,      // Total absences since Sept 1
    net_total_burden: 450,      // All regular taught + subs - absences
    updated_at: "2025-11-29 08:55:23"
  },
  // ... for all 16 teachers
]
```

**Filtering Logic:**
- Date range: Filter Leave_Logs by date column
- Teacher: Filter timetable and logs by teacher_id
- Subject: Filter timetable by subject_id
- Class: Filter timetable by class_id

### Frontend Components

**Summary Cards (4 cards):**
1. Total teachers count
2. Total substitute periods (sum across all teachers)
3. Total absence periods (sum across all teachers)
4. Average net accumulation (mean across all teachers)

**Leaderboard Table:**
- Sortable by all columns (click header)
- Top 3 highlighted with colors
- Badge styling for substitute/absence counts
- Responsive (scrollable on mobile)

**Teacher Cards:**
- Bootstrap grid (col-md-4 col-lg-3)
- Card per teacher showing:
  - Teacher ID and Thai name (header)
  - Regular base periods (book icon)
  - Substitute periods (plus icon, green)
  - Absence periods (minus icon, red)
  - Net accumulation (calculator icon, bold)
  - Subject/class counts (footer)
- Hover effect (shadow, lift)

### Performance Optimizations

1. **Caching:** 5-minute cache for Leave_Logs data
2. **Batch Processing:** Calculate all teachers in one pass
3. **Client-Side Filtering:** Move filter logic to JavaScript after initial load
4. **Lazy Loading:** Only fetch data when page is accessed

## Maintenance Procedures

### Update Timetable Data

When `real_timetable.json` changes:
```bash
# 1. Update DataConstants.gs with new timetable array
# 2. Push changes
clasp push

# 3. Deploy new version
clasp deploy --description "Updated timetable data"
```

### Add New Teacher

1. Add to `TEACHER_NAMES` in DataConstants.gs
2. Ensure teacher exists in `REAL_TIMETABLE`
3. Push and redeploy

### Clear Cache

If data appears stale:
```javascript
function clearCache() {
  CacheService.getScriptCache().removeAll(['leave_logs_data']);
}
```

## Critical Files Reference

**From Existing Project:**
- `C:\Users\Phontan-Chang\Documents\TimeTableConverting\data\real_timetable.json` → Used by Python processor
- `C:\Users\Phontan-Chang\Documents\TimeTableConverting\data\teacher_full_names.json` → Used by Python processor
- `C:\Users\Phontan-Chang\Documents\TimeTableConverting\src\utils\daily_leave_processor.py` → MODIFY to add snapshot writing

**To Create:**
- Google Sheets worksheet: `Teacher_Hours_Tracking` (headers + empty data)
- Python function: `write_teacher_hours_snapshot()` in daily_leave_processor.py or new module
- All files in `gas-webapp/` directory (9 files total)

**To Modify:**
- `daily_leave_processor.py`: Add call to `write_teacher_hours_snapshot()` at end of processing
- `Code.gs`: Change from calculating metrics to reading tracking snapshot

## Success Criteria

- ✅ `Teacher_Hours_Tracking` worksheet created with proper schema
- ✅ Daily processor writes snapshot after processing (runs at 8:55 AM)
- ✅ Snapshots contain cumulative totals up to current date
- ✅ Web app reads latest snapshot (loads in < 2 seconds)
- ✅ All 16 teachers display with correct cumulative metrics
- ✅ Calculations match formula: `regular + cumulative_substitute - cumulative_absence`
- ✅ Historical snapshots preserved for trend analysis
- ✅ Filters work correctly (teacher, date range)
- ✅ Table sorting works on all columns
- ✅ Responsive design works on mobile/tablet/desktop
- ✅ Data refreshes daily after processor runs
- ✅ Bootstrap styling renders correctly

## Estimated Timeline

- Database Setup: 30 minutes (create worksheet, modify Python processor)
- Setup: 30 minutes (install clasp, create project)
- Backend: 2 hours (simplified - reading snapshot vs calculating)
- Frontend: 3 hours (same as before)
- Testing: 1.5 hours (test Python snapshot writing + web app)
- Deployment: 30 minutes
- Documentation: 30 minutes

**Total: ~8.5 hours**

## Benefits of Tracking System

1. **Performance:** Web app loads faster (reads snapshot vs calculating from all historical data)
2. **Historical Analysis:** Daily snapshots enable trend charts and workload analysis over time
3. **Data Integrity:** Single source of truth updated by automated daily process
4. **Scalability:** As Leave_Logs grows, calculation doesn't slow down (pre-calculated)
5. **Audit Trail:** Can review teacher workload at any historical date
6. **Reporting:** Python processor can generate reports based on tracking data
