# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview
School timetable management system with two main functions:
1. Converting Excel timetables (.xlsm) to JSON
2. Finding substitute teachers based on intelligent scoring

## Running the Scripts

### Convert Excel to JSON
```bash
python excel_converting.py <excel_file> [output_file]
```
**Examples:**
```bash
# Using default output file (timetable_output.json)
python excel_converting.py timetable.xlsm

# Specifying custom output file
python excel_converting.py timetable.xlsm my_output.json
```

**Features:**
- Command-line argument support for file paths
- Input file validation (checks if file exists)
- Reports unknown teachers and subjects with warnings
- Handles merged cells automatically
- UTF-8 encoding for Thai characters
- Progress feedback during processing

**Excel Structure:**
- Row 1: Headers
- Row 2: Period numbers (columns 3+)
- Row 3+: Alternating subject/teacher rows, grouped by day and class
- Columns 1-2: Day and Class (may be merged cells)

### Find Substitutes
```python
from find_substitute import find_best_substitute_teacher, assign_substitutes_for_day
```
The module provides importable functions, not a standalone script. See `test_find_substitute.py` for usage examples.

### Test with Real Timetable
```bash
python test_real_timetable.py
```
Comprehensive test script using real school timetable data. Simulates teacher absence and validates substitute finding with actual constraints. Provides detailed analysis including:
- Teacher schedule visualization
- Substitute assignments with qualification checking
- Success rate calculation
- Level matching validation

## Architecture

### excel_converting.py
Parses Excel worksheets with hardcoded Thai-to-English mappings for days, subjects, and teacher names. Handles merged cells by preserving previous day/class values. Strips numeric characters from subject names during parsing.

**Key Features:**
- Type hints and comprehensive docstrings
- Error handling with descriptive messages
- Input validation (file existence, worksheet presence)
- Unknown entity tracking (warns about unmapped teachers/subjects)
- Command-line interface with usage help
- Windows compatibility: ASCII output, proper file handle cleanup

**Key mappings:** `day_map`, `subject_map`, `teacher_map` (lines 8-44)
- As of Nov 19, 2025: 26+ subject mappings including specialty subjects (Computer, STEM, Anti-Corruption, Applied Math, Music-Drama, Visual Arts, etc.)
- Unknown entities now preserve original Thai text instead of marking "UNKNOWN"

**Recent Fixes (Nov 2025):**
- **Critical Parser Bugs Fixed:**
  - **Time-Range Parsing:** Added support for time-based periods (e.g., "09.00-10.00") used in elementary sheets (lines 97-107)
  - **Lunch Break Filtering:** Skip non-numeric period entries like lunch break text (lines 86-107)
  - **Row Limiting:** Limited parsing to row 32 to avoid duplicate entries from multiple tables per sheet (line 114)
  - **Results:** Fixed missing elementary data (0% to 100% coverage), eliminated scheduling conflicts, reduced duplicate entries from 384 to 222
- Replaced Unicode characters (✓, ⚠️) with ASCII ("OK", "WARNING") for Windows console compatibility
- Added `wb.close()` to prevent file handle leaks and Windows file locking issues

**Period Format Handling:**
- Middle school sheets (ม.1-3): Use numeric periods (1, 2, 3, etc.)
- Elementary sheets (ป.1-6): Use time ranges ("09.00-10.00", "10.00-11.00", etc.)
- Parser automatically detects format and maps time ranges to sequential period numbers
- Intelligently skips invalid entries (lunch break text, empty cells)

### find_substitute.py
Scoring-based algorithm that balances subject qualification, level matching, and workload distribution.

**Core algorithm (find_best_substitute_teacher):**
1. Filter available teachers (not teaching at that period)
2. Score each candidate:
   - +2: Can teach subject (bonus, not required - changed Nov 19, 2025)
   - +5: Teacher's level matches class level
   - -2: Level mismatch penalty
   - -2 per period: Daily load on same day
   - -1 per entry: Historical substitution count
   - -0.5 per period: Total term load (excluding leave days)
   - -50: Last resort teachers (T006, T010, T018 - added Nov 19, 2025)
   - -999: Teacher is absent
3. Select randomly among top-scored candidates (handles ties)

**Note:** As of Nov 19, 2025, subject qualification is a bonus rather than requirement, allowing flexible assignment when no qualified teachers available.

**assign_substitutes_for_day:** Iterates through all absent teachers' slots for a day, calling find_best_substitute_teacher for each. Includes newly assigned substitutes in constraint checking to avoid double-booking.

### LINE Bot System (Nov 2025)

**Complete automated leave request and substitute assignment system with cloud integration.**

#### System Architecture

```
[Teachers] → [LINE Group] → [webhook.py] → [ai_parser.py] → [Google Sheets]
                                                                     ↓
[LINE Group] ← [line_messaging.py] ← [process_daily_leaves.py] ← [Cron Job]
                                              ↓
                                     [find_substitute.py]
```

#### Core Components

**config.py** - Centralized configuration management
- Loads environment variables from .env file using python-dotenv
- Validates all required credentials and file paths
- Provides config.SPREADSHEET_ID, config.LINE_CHANNEL_SECRET, etc.
- Includes config.validate() and config.print_status() methods
- All other modules import configuration from here

**webhook.py** - Flask server for LINE webhooks (lines 1-380)
- HTTP server running on port 5000 (configurable)
- `/callback` endpoint receives LINE message events
- Verifies LINE signatures using HMAC-SHA256 for security
- Filters messages by configured LINE_GROUP_ID
- Checks for leave keywords: ลา, ขอลา, หยุด, ไม่มา
- Calls ai_parser.parse_leave_request() for natural language processing
- Calls add_absence_to_sheets.add_absence() to save to Google Sheets
- Sends confirmation reply using line_bot_api.reply_message()
- Handles errors gracefully with Thai error messages
- Includes /health endpoint for monitoring

**ai_parser.py** - AI-powered message parsing (lines 1-340)
- Uses OpenRouter API to access Gemini free tier model
- Model: google/gemini-2.0-flash-exp:free (configurable)
- System prompt provides parsing rules in Thai (lines 18-44)
- Extracts: teacher_name, date (YYYY-MM-DD), periods (list), reason
- Handles Thai date expressions:
  - พรุ่งนี้ (tomorrow), วันนี้ (today)
  - วันจันทร์ (next Monday), etc.
- Handles period formats:
  - "คาบ 1-3" → [1, 2, 3]
  - "คาบ 1, 3, 5" → [1, 3, 5]
  - "ทั้งวัน" → [1-8]
- parse_leave_request() returns dict or None on failure
- parse_leave_request_fallback() for regex-based parsing without API
- Temperature set to 0.2 for consistent, deterministic parsing

**line_messaging.py** - Outgoing notifications (lines 1-280)
- send_message_to_group() - Generic message sender
- send_daily_report() - Sends substitute teacher report
- send_error_notification() - Sends system errors
- send_test_message() - Verification/health check
- format_substitute_summary() - Creates concise summaries
- send_formatted_report() - Rich text with emojis and formatting
- Uses linebot SDK's push_message API
- Sends to LINE_GROUP_ID from config

**process_daily_leaves.py** - Daily orchestration (lines 1-400)
- Main workflow script, designed for cron job execution
- Command-line interface:
  - `python process_daily_leaves.py` - Process today
  - `python process_daily_leaves.py 2025-11-21` - Specific date
  - `--test` flag for read-only mode (no Sheets updates)
  - `--send-line` flag to enable LINE notification
- Workflow:
  1. load_data_files() - Loads all 5 JSON data files + timetable
  2. get_leaves_for_date() - Reads from Google Sheets via sync_leave_logs.py
  3. group_leaves_by_day() - Groups by day, extracts absent teacher IDs
  4. Calls assign_substitutes_for_day() for each day with absences
  5. update_sheets_with_substitutes() - Writes results back to Sheets
  6. generate_report() - Creates formatted text summary
  7. Optionally sends report via line_messaging.send_daily_report()
- Returns comprehensive report string with success rates

**build_teacher_data.py** - Data file generator (lines 1-208)
- Analyzes real_timetable.json to extract teacher information
- Generates 5 required JSON files:
  1. teacher_subjects.json - Maps teacher_id → [subject_ids]
  2. teacher_levels.json - Maps teacher_id → [level categories]
  3. class_levels.json - Maps class_id → level (lower/upper elementary, middle)
  4. teacher_name_map.json - Maps Thai name → teacher_id
  5. teacher_full_names.json - Maps teacher_id → full display name (editable)
- classify_class_level() determines level based on class_id prefix
- Run once when setting up system, or when timetable changes
- Output files used by find_substitute.py and process_daily_leaves.py

#### Data Flow

**Incoming Leave Request:**
1. Teacher sends message: "ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3"
2. LINE platform sends webhook POST to /callback
3. webhook.py verifies signature and extracts message text
4. ai_parser.py sends to Gemini: extracts {teacher_name, date, periods, reason}
5. add_absence_to_sheets.py adds row to Google Sheets "Leave_Logs" tab
6. webhook.py sends confirmation reply to LINE group

**Daily Processing (8:55 AM cron):**
1. process_daily_leaves.py reads today's leaves from Google Sheets
2. Groups absences by day (Mon, Tue, Wed, Thu, Fri)
3. For each day, calls find_substitute.py's assign_substitutes_for_day()
4. Substitute finder scores all available teachers using algorithm
5. Updates Google Sheets with substitute teacher assignments (column 7)
6. Generates formatted report with success rate statistics
7. line_messaging.py sends report to LINE group

#### Configuration Files

**.env** (created by user from .env.example)
```
SPREADSHEET_ID=1KpQZlrJk03ZS_Q0bTWvxHjG9UFiD1xPZGyIsQfRkRWo
LINE_CHANNEL_SECRET=your_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_access_token
LINE_GROUP_ID=C1234567890abcdef (get from webhook logs)
OPENROUTER_API_KEY=sk-or-v1-...
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=5000
DEBUG_MODE=False
```

**credentials.json** (Google service account)
- Downloaded from Google Cloud Console
- Used by gspread for Sheets API authentication
- Must be shared with service account email

#### Dependencies (requirements.txt)

Google Sheets:
- gspread==6.2.1
- google-auth==2.41.1

LINE Bot:
- line-bot-sdk==3.9.0
- Flask==3.0.0

Configuration & AI:
- python-dotenv==1.0.0
- requests==2.31.0 (for OpenRouter API)

Excel:
- openpyxl==3.1.2

#### Deployment

**Development (Windows with ngrok):**
1. Run `python webhook.py` locally
2. Run `ngrok http 5000` to expose webhook
3. Set LINE webhook URL to ngrok URL + /callback
4. Test with real LINE messages

**Production (Raspberry Pi):**
1. Deploy code to `/home/pi/TimeTableConverting`
2. Create systemd service for webhook.py (runs on boot)
3. Add cron job: `55 8 * * 1-5` for process_daily_leaves.py
4. Configure router port forwarding (port 5000)
5. Set LINE webhook URL to public IP/domain + /callback

#### Error Handling

- Webhook validates signatures, returns 400 on invalid
- AI parser has fallback regex-based parser if OpenRouter fails
- Config validation checks all required credentials before starting
- Google Sheets operations wrapped in try-except with error messages
- LINE messaging handles API errors gracefully
- process_daily_leaves.py has --test mode for safe testing

#### Security

- LINE signatures verified with HMAC-SHA256
- Credentials stored in .env (not committed to git)
- .env added to .gitignore automatically
- Google service account has minimal permissions
- Flask runs on local network (Raspberry Pi) or behind ngrok

## Data Format

All data structures use this timetable entry format:
```python
{
    "teacher_id": str,    # e.g., "T001"
    "subject_id": str,    # e.g., "Math"
    "day_id": str,        # e.g., "Mon"
    "period_id": int,     # 1-based index
    "class_id": str       # e.g., "ป.1" (elementary), "ม.1" (middle)
}
```

**Additional data structures:**
- `teacher_subjects`: `{teacher_id: [subject_ids]}`
- `teacher_levels`: `{teacher_id: ["lower_elementary", "upper_elementary", "middle"]}` (three-tier system as of Nov 19, 2025)
- `class_levels`: `{class_id: "lower_elementary" | "upper_elementary" | "middle"}`
  - lower_elementary: ป.1-3 (ages 6-9)
  - upper_elementary: ป.4-6 (ages 9-12)
  - middle: ม.1-3 (ages 12-15)
- `leave_logs`: List of timetable entries marking leave periods

## Testing

### Running Tests

Run all tests (recommended):
```bash
python run_all_tests.py
```

Run individual test suites:
```bash
python test_find_substitute.py   # 10 tests for substitute finding
python test_excel_converting.py  # 14 tests for Excel conversion
python test_real_timetable.py    # Real timetable validation test
```

**Test Coverage:**

**Substitute Finding (10 tests):**
- Basic substitute finding functionality
- Absent teacher exclusion
- Availability checking (prevents double-booking)
- No qualified substitute scenarios
- Level matching preferences
- Workload balancing
- Input validation
- Multiple absent teachers handling

**Excel Conversion (14 tests):**
- File parsing and JSON structure validation
- Thai-English mappings (days, subjects, teachers)
- Merged cell handling
- UTF-8 encoding for Thai characters
- Error cases (missing files, missing worksheets)
- Edge cases (numeric character stripping)

**Test Strategy:**
- Uses programmatic mock creation (no external fixture files)
- unittest framework (Python standard library)
- Proper cleanup of temporary files
- All 24 tests passing

See TESTING.md for quick reference or TEST_REPORT.md for comprehensive analysis.

### Real-World Validation

**Production Testing (Nov 2025):**
- Tested with actual school timetable (ตารางเรียนเทอม2 ปี 68-2 .xlsm)
- Successfully parsed 222 timetable entries covering all 9 classes
- 16 active teachers identified
- Zero scheduling conflicts in parsed data
- Substitute finding algorithm achieves 75% success rate with real data
- All three sheets parsed correctly (ป.1-3, ป.4-6, ม.1-3)

**Diagnostic Tools Created:**
- `diagnose_excel.py` - Inspect Excel structure and period columns
- `check_conflicts.py` - Detect scheduling conflicts in JSON output
- `check_prathom_periods.py` - Validate period format handling
- `test_period_parsing.py` - Test period parsing logic
- `check_t011_duplicates.py` - Verify duplicate resolution

## Important Notes
- Thai encoding: All mappings and output use UTF-8
- Level system (as of Nov 19, 2025): Three-tier system
  - "lower_elementary" (ป.1-3), "upper_elementary" (ป.4-6), "middle" (ม.1-3)
  - Provides more precise age-appropriate teacher matching
- The substitute algorithm intentionally uses randomization for fairness when scores tie
- Workload balancing considers: daily load, historical substitutions, and term load
- Teachers can be assigned outside their level (with penalty) if no better option exists
- Subject qualification is now a bonus (+2) rather than requirement, improving coverage in edge cases
- Last resort teachers (T006, T010, T018) receive -50 penalty, assigned only when necessary
- Unknown subjects/teachers preserve original Thai text instead of "UNKNOWN" label
- Dependencies: Install via `pip install -r requirements.txt` (requires openpyxl)

## Recent Changes

### Nov 20, 2025: LINE Bot Integration
- **Complete automated leave request system:**
  - Added webhook.py Flask server for LINE Messaging API
  - Added ai_parser.py for AI-powered Thai message parsing (OpenRouter/Gemini)
  - Added line_messaging.py for sending reports and notifications
  - Added process_daily_leaves.py for daily workflow orchestration
  - Added config.py for centralized configuration management
  - Added build_teacher_data.py to generate required data files
- **Integration with existing systems:**
  - Links LINE → AI Parser → Google Sheets (incoming requests)
  - Links Google Sheets → Substitute Finder → LINE (daily reports)
  - Full end-to-end automation from teacher message to substitute assignment
- **Dependencies added:**
  - line-bot-sdk==3.9.0 (LINE API)
  - Flask==3.0.0 (webhook server)
  - python-dotenv==1.0.0 (environment variables)
  - requests==2.31.0 (OpenRouter API)
- **Documentation:**
  - Created LINE_BOT_SETUP.md with complete setup guide
  - Updated README.md with LINE Bot usage and architecture
  - Updated CLAUDE.md with system architecture details

### Nov 19, 2025: Algorithm & Parser Enhancements
- Expanded subject mappings from ~8 to 26+ subjects
- Changed subject qualification from requirement to bonus scoring
- Implemented three-tier level system (lower/upper elementary + middle)
- Added last resort teacher penalties for institutional preferences
- Changed unknown entity handling to preserve original Thai text
