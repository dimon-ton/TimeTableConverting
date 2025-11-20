# GEMINI.md

This file provides guidance to Google Gemini when working with code in this repository.

## Overview
School timetable management system with complete automation:
1. Converting Excel timetables (.xlsm) to JSON
2. Finding substitute teachers based on intelligent scoring
3. LINE Bot integration for automated leave requests
4. Google Sheets integration for cloud-based data management

## Running the Scripts

### Convert Excel to JSON
```bash
python -m src.timetable.converter <excel_file> [output_file]
```
**Examples:**
```bash
# Using default output file (data/timetable_output.json)
python -m src.timetable.converter timetable.xlsm

# Specifying custom output file
python -m src.timetable.converter timetable.xlsm my_output.json
```

**Features:**
- Command-line argument support for file paths
- Input file validation (checks if file exists)
- Reports unknown teachers and subjects with warnings
- Handles merged cells automatically
- UTF-8 encoding for Thai characters
- Progress feedback during processing

### Find Substitutes
```python
from src.timetable.substitute import find_best_substitute_teacher, assign_substitutes_for_day
```
The module provides importable functions. See `tests/test_substitute.py` for usage examples.

### Test with Real Timetable
```bash
python -m tests.test_real_timetable
```
Comprehensive test script using real school timetable data.

## Project Structure

```
src/
├── config.py                    # Centralized configuration
├── timetable/
│   ├── converter.py             # Excel to JSON conversion
│   ├── substitute.py            # Substitute teacher finding
│   └── ai_parser.py             # AI-powered leave request parsing
├── utils/
│   ├── build_teacher_data.py    # Generate teacher data files
│   ├── daily_leave_processor.py # Daily workflow orchestration
│   └── sheet_utils.py           # Google Sheets operations (read/write)
└── web/
    ├── webhook.py               # LINE webhook server
    └── line_messaging.py        # LINE notifications
```

## LINE Bot System

**Complete automated leave request and substitute assignment system.**

### System Architecture

```
[Teachers] → [LINE Group] → [webhook.py] → [ai_parser.py] → [Google Sheets]
                                                                     ↓
[LINE Group] ← [line_messaging.py] ← [daily_leave_processor.py] ← [Cron Job]
                                              ↓
                                     [substitute.py]
```

### Core Components

**src/config.py** - Centralized configuration
- Loads environment variables from .env file
- Validates all required credentials
- Uses PROJECT_ROOT for absolute paths

**src/web/webhook.py** - Flask server for LINE webhooks
- HTTP server on port 5000 (configurable)
- `/callback` endpoint receives LINE events
- Verifies LINE signatures (HMAC-SHA256)
- Calls ai_parser for message parsing
- Logs to Google Sheets via sheet_utils

**src/timetable/ai_parser.py** - AI-powered message parsing
- Uses OpenRouter API (DeepSeek R1 Free model)
- Extracts: teacher_name, date, periods, reason
- Handles Thai date expressions
- Fallback regex-based parser

**src/web/line_messaging.py** - Outgoing notifications
- send_message_to_group() - Generic messaging
- send_daily_report() - Substitute teacher reports
- Uses LINE SDK v3 MessagingApi

**src/utils/daily_leave_processor.py** - Daily orchestration
- Reads from Google Sheets Leave_Requests
- Enriches with timetable data
- Finds substitutes
- Logs to Leave_Logs sheet
- Sends LINE report

**src/utils/sheet_utils.py** - Google Sheets operations (NEW in Nov 2025)
- get_sheets_client() - Authenticated gspread client
- load_requests_from_sheet() - Read Leave_Requests
- log_request_to_sheet() - Write incoming requests
- add_absence() - Log final assignments to Leave_Logs
- Consolidated from previous add_absence_to_sheets.py and leave_log_sync.py

**src/utils/build_teacher_data.py** - Data file generator
- Analyzes timetable to extract teacher info
- Generates 5 JSON files in data/ directory
- Run once during setup

### Data Flow

**Incoming Leave Request:**
1. Teacher sends message: "ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3"
2. LINE platform → webhook.py POST /callback
3. ai_parser.py extracts {teacher_name, date, periods, reason}
4. sheet_utils.log_request_to_sheet() → Google Sheets "Leave_Requests"
5. webhook.py sends confirmation reply

**Daily Processing (8:55 AM cron):**
1. daily_leave_processor.py reads from Leave_Requests sheet
2. Enriches with timetable data (class, subject)
3. assign_substitutes_for_day() finds best substitutes
4. sheet_utils.add_absence() → Google Sheets "Leave_Logs"
5. line_messaging.py sends report to LINE group

### Configuration Files

**.env** (created from .env.example)
```
SPREADSHEET_ID=your_spreadsheet_id
LINE_CHANNEL_SECRET=your_secret
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_GROUP_ID=your_group_id
OPENROUTER_API_KEY=your_api_key
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=5000
DEBUG_MODE=False
```

**credentials.json** (Google service account)
- Downloaded from Google Cloud Console
- Used by gspread for Sheets API authentication

## Data Format

Timetable entry format:
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
- `teacher_levels`: `{teacher_id: ["lower_elementary", "upper_elementary", "middle"]}`
- `class_levels`: `{class_id: "lower_elementary" | "upper_elementary" | "middle"}`
  - lower_elementary: ป.1-3 (ages 6-9)
  - upper_elementary: ป.4-6 (ages 9-12)
  - middle: ม.1-3 (ages 12-15)

## Testing

### Running Tests

Run all tests:
```bash
python -m unittest discover tests -v
# Or use the script:
python -m scripts.run_all_tests
```

Run individual test suites:
```bash
python -m unittest tests.test_substitute -v   # Substitute finding
python -m unittest tests.test_converter -v    # Excel conversion
python -m tests.test_real_timetable           # Real timetable validation
```

**Test Coverage:**
- 10 tests for substitute finding algorithm
- 14 tests for Excel conversion
- Real-world validation with actual school data
- All 24 tests passing (100%)

## Important Notes

- **Project Structure:** Uses src/ package structure following Python best practices
- **Import Paths:** All imports use `from src.module import ...` format
- **File Paths:** config.py uses PROJECT_ROOT for absolute, cross-platform paths
- **Thai Encoding:** All mappings and output use UTF-8
- **Level System:** Three-tier (lower_elementary, upper_elementary, middle)
- **AI Model:** DeepSeek R1 Free (switched from Gemini to avoid rate limits)
- **Two-Sheet Data Model:** Leave_Requests (raw) and Leave_Logs (enriched)
- **Dependencies:** Install via `pip install -r requirements.txt`

## Recent Changes (Nov 2025)

### Nov 20, 2025: Google Sheets Consolidation & Refactoring
- **Consolidated Google Sheets operations:**
  - Merged add_absence_to_sheets.py and leave_log_sync.py into sheet_utils.py
  - Single source of truth for all Sheets operations
  - Improved maintainability and reduced code duplication
- **Refactored daily_leave_processor.py:**
  - Two-sheet workflow: Leave_Requests (raw) → Leave_Logs (enriched)
  - Added timetable enrichment step
  - Better separation of concerns
- **Updated webhook.py:**
  - Uses sheet_utils.log_request_to_sheet()
  - Added fallback parser integration
  - Enhanced error handling with status tracking
- **Fixed AI parser model:**
  - Corrected from 'deepseek-chat:free' to 'deepseek-r1:free'
  - Resolved 404 errors
  - Improved reliability

### Complete LINE Bot Integration
- Flask webhook server (src/web/webhook.py)
- AI message parser using OpenRouter API
- Google Sheets bidirectional sync
- Automated daily processing with cron
- LINE notifications for reports and confirmations
- Production-ready deployment instructions

### Project Reorganization
- Moved to src/ package structure
- Separated code into timetable/, utils/, web/ subpackages
- Moved data files to data/, docs to docs/, scripts to scripts/
- Centralized configuration in src/config.py
- Updated all imports to src.* format

For complete documentation, see:
- **README.md** - User guide and setup instructions
- **docs/CLAUDE.md** - Detailed technical documentation
- **docs/LINE_BOT_SETUP.md** - LINE Bot setup guide
- **docs/SESSION_SUMMARY.md** - Development history
