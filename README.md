# TimeTable Converting Project

A Python-based timetable management system for schools that handles Excel-to-JSON conversion and intelligent substitute teacher assignment.

## Features

- ✅ Convert Excel timetables (.xlsm) to structured JSON format
- ✅ Intelligent substitute teacher assignment algorithm
- ✅ Workload balancing across teachers
- ✅ Level-based matching (elementary/middle school)
- ✅ Subject qualification validation
- ✅ Comprehensive test suite
- ✅ **Google Sheets integration for cloud-based leave log management**
- ✅ **LINE Bot integration for automated leave requests and notifications**
- ✅ **AI-powered message parsing (OpenRouter/Gemini)**

## Installation

### Prerequisites
- Python 3.7 or higher

### Setup

1. Clone this repository or download the files

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Excel to JSON Conversion

Convert your Excel timetable to JSON format:

```bash
python -m src.timetable.converter <excel_file> [output_file]
```

**Examples:**
```bash
# Using default output file (timetable_output.json)
python -m src.timetable.converter timetable.xlsm

# Specifying custom output file
python -m src.timetable.converter timetable.xlsm my_output.json
```

**Features:**
- Validates input file existence
- Reports unknown teachers and subjects
- Handles merged cells automatically
- UTF-8 encoding for Thai characters
- Progress feedback during processing

### LINE Bot Integration (NEW!)

Automated teacher absence management through LINE messaging with AI-powered parsing and Google Sheets integration.

#### System Architecture

```
Teacher → LINE Message → Webhook → AI Parser → Google Sheets
                                                      ↓
Daily Cron → Process Leaves → Find Substitutes → Update Sheets → Notify via LINE
```

#### Initial Setup

1. **Install dependencies** (already included in requirements.txt):
```bash
pip install gspread google-auth line-bot-sdk Flask python-dotenv requests
```

2. **Set up Google Cloud Console:**
   - Go to https://console.cloud.google.com/
   - Create a new project
   - Enable **Google Sheets API** and **Google Drive API**
   - Create a service account
   - Download credentials as `credentials.json` and place in project root

3. **Set up LINE Bot:**
   - Go to https://developers.line.biz/console/
   - Create a Messaging API channel
   - Get Channel Secret and Channel Access Token
   - Set webhook URL: `http://your-server:5000/callback`

4. **Create Google Sheet:**
   - Go to https://sheets.google.com
   - Create sheet named "School Timetable - Leave Management"
   - Create two worksheets:
     - "Leave_Requests" (raw incoming requests)
     - "Leave_Logs" (enriched final assignments)
   - Share with service account email from credentials.json
   - Or use the template creation script:
     ```bash
     python -m scripts.create_sheets_template
     ```

5. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in all required values:
     ```
     SPREADSHEET_ID=your_spreadsheet_id_here
     LINE_CHANNEL_SECRET=your_channel_secret
     LINE_CHANNEL_ACCESS_TOKEN=your_access_token
     LINE_GROUP_ID=your_group_id
     OPENROUTER_API_KEY=your_openrouter_key
     ```

#### Using the LINE Bot

**Sending Leave Requests:**

Teachers send messages in the LINE group:
```
ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3
(Teacher Sukrit requests leave tomorrow, periods 1-3)
```

The bot automatically:
1. Parses the message using AI
2. Logs to Google Sheets "Leave_Requests" tab
3. Sends confirmation to the group

**Daily Processing with Admin Verification:**

The system uses a two-stage workflow for improved accountability:

1. **Automated Processing (8:55 AM):**
   - System finds substitutes for today's leave requests
   - Writes assignments to "Pending_Assignments" worksheet
   - Generates report with `[REPORT] YYYY-MM-DD` prefix
   - Sends report to admin LINE group

2. **Admin Verification (Manual):**
   - Admin reviews substitute assignments in report
   - Admin can edit message to adjust assignments if needed
   - Admin copies entire message (including `[REPORT]` prefix)
   - Admin sends to teacher LINE group

3. **System Finalization (Automatic):**
   - System detects `[REPORT]` prefix in teacher group
   - Validates date (rejects future dates, warns if >7 days old)
   - Finalizes assignments to "Leave_Logs" worksheet
   - Records who verified (LINE User ID) and when
   - Sends confirmation to admin group

Run manually for testing:
```bash
# Process today's leaves (writes to Pending_Assignments)
python -m src.utils.daily_leave_processor

# Process specific date
python -m src.utils.daily_leave_processor 2025-11-21

# Send report to LINE admin group
python -m src.utils.daily_leave_processor --send-line

# Test mode (no Sheets updates)
python -m src.utils.daily_leave_processor --test
```

Set up database for verification workflow:
```bash
# Create Pending_Assignments worksheet and add verification columns
python scripts/create_pending_sheet.py
```

Or set up cron job (runs at 8:55 AM Monday-Friday):
```bash
55 8 * * 1-5 cd /path/to/project && python -m src.utils.daily_leave_processor --send-line
```

#### Running the Webhook Server

**Development (with ngrok):**
```bash
# Terminal 1: Start webhook
python -m src.web.webhook

# Terminal 2: Expose to internet
ngrok http 5000

# Update LINE webhook URL to ngrok URL + /callback
```

**Production (Raspberry Pi):**
```bash
# Create systemd service (see docs/LINE_BOT_SETUP.md)
sudo systemctl start timetable-webhook
sudo systemctl enable timetable-webhook

# Check status
sudo systemctl status timetable-webhook
```

#### Direct Google Sheets Access

**Load leave requests:**
```python
from src.utils.sheet_utils import load_requests_from_sheet

# Get requests for a specific date
requests = load_requests_from_sheet("2025-11-21")
```

**Add a leave request manually:**
```python
from src.utils.sheet_utils import log_request_to_sheet

log_request_to_sheet(
    raw_message="ครูสมชาย ลาวันจันทร์ คาบ 2-4",
    leave_data={
        "teacher_name": "สมชาย",
        "date": "2025-11-21",
        "periods": [2, 3, 4],
        "reason": "ลากิจ"
    },
    status="Success (Manual)"
)
```

**Add enriched absence to Leave_Logs:**
```python
from src.utils.sheet_utils import add_absence

add_absence(
    date="2025-11-21",
    absent_teacher="T001",
    day="Mon",
    period=3,
    class_id="ป.4",
    subject="Math",
    substitute_teacher="T005",
    notes="AI assigned substitute"
)
```

#### Benefits of LINE Bot Integration
- ✅ **Fully Automated**: From message to substitute assignment
- ✅ **AI-Powered**: Natural Thai language understanding
- ✅ **Cloud-Based**: Google Sheets accessible anywhere
- ✅ **Real-Time**: Instant confirmations and daily reports
- ✅ **Reliable**: Fallback parser if AI fails
- ✅ **Audit Trail**: Complete request and assignment history

For detailed LINE Bot setup instructions, see [docs/LINE_BOT_SETUP.md](docs/LINE_BOT_SETUP.md).

#### Testing LINE Bot Components

Test individual components:

```bash
# Test configuration
python -m src.config

# Test AI parser (requires OPENROUTER_API_KEY)
python -m src.timetable.ai_parser

# Test LINE messaging (requires LINE credentials)
python -m src.web.line_messaging

# Test daily processing (read-only)
python -m src.utils.daily_leave_processor --test
```

**AI Parser Features (Enhanced Nov 25, 2025):**
- Handles formal Thai greetings ("เรียนท่าน ผอ.")
- Supports multiple full-day expressions (ทั้งวัน, เต็มวัน, 1 วัน, หนึ่งวัน)
- Distinguishes late arrivals ("เข้าสาย") from full absences
- Extracts specific reasons when provided
- Works with informal typing (no spacing between words)
- 100% feature parity between AI and fallback parsers

**Integration Points:**
1. LINE → Webhook → AI Parser → Google Sheets (incoming)
2. Google Sheets → Daily Processor → Substitute Finder → Google Sheets (processing)
3. Google Sheets → LINE Messaging (outgoing reports)

#### Benefits

- ✅ **Zero manual data entry**: Teachers send requests via LINE
- ✅ **Natural language**: No forms or structured input required
- ✅ **Automated processing**: Daily substitute assignment at 8:55 AM
- ✅ **Instant notifications**: Reports delivered to LINE group
- ✅ **AI-powered parsing**: Handles Thai language nuances
- ✅ **Cloud-based**: Works on Raspberry Pi or any server
- ✅ **Scalable**: Add more teachers or classes easily

### Finding Substitute Teachers

Use the `find_substitute` module programmatically:

```python
from src.timetable.substitute import find_best_substitute_teacher, assign_substitutes_for_day

# Find substitute for a single period
substitute = find_best_substitute_teacher(
    subject_id="Math",
    day_id="Mon",
    period_id=1,
    class_id="ป.1",
    timetables=timetables,
    teacher_subjects=teacher_subjects,
    substitute_logs=substitute_logs,
    all_teacher_ids=all_teacher_ids,
    absent_teacher_ids=["T001"],
    leave_logs=leave_logs,
    teacher_levels=teacher_levels,
    class_levels=class_levels
)

# Assign substitutes for all absent teachers in a day
substitutes = assign_substitutes_for_day(
    day_id="Mon",
    timetable=timetables,
    teacher_subjects=teacher_subjects,
    substitute_logs=substitute_logs,
    all_teacher_ids=all_teacher_ids,
    absent_teacher_ids=["T001", "T002"],
    leave_logs=leave_logs,
    teacher_levels=teacher_levels,
    class_levels=class_levels
)
```

## Substitute Teacher Algorithm

The algorithm uses a scoring system with hard constraints to find the best substitute:

### Hard Constraints (Teachers Excluded If)
- **Teacher is absent** - Cannot substitute if they're not at school
- **Already teaching** - Cannot be in two places at once
- **Daily workload limit** - Cannot be assigned if already have 4+ periods that day

### Scoring Criteria (For Eligible Teachers)
- **+2 points**: Teacher can teach the subject (bonus, not required)
- **+5 points**: Teacher's level matches class level
- **-2 points**: Level mismatch penalty
- **-2 points per period**: Daily teaching load
- **-1 point per substitution**: Historical substitution count
- **-0.5 points per period**: Total term load (excluding leave days)
- **-50 points**: Last resort teachers (assigned only when no better options)

### Features
- **Daily workload protection:** Teachers cannot be assigned when they already have 4+ periods
- **Prevents double-booking:** Teachers can't be in two places at once
- **Workload balancing:** Considers daily, historical, and term loads
- **Subject qualification bonus:** Prioritizes qualified teachers but can assign unqualified if needed
- **Level-appropriate matching:** Prefers teachers experienced with the class level
- **Historical data integration:** Loads past substitute assignments from Google Sheets for fair distribution
- **Cumulative learning:** Automatically learns from each day's assignments to prevent teacher burnout
- **Fair randomization:** Randomizes selection among equally-scored candidates

## Testing

The project includes a comprehensive testing suite for validating the substitute teacher functionality.

### Quick Start

Run all substitute tests:
```bash
python tests/run_tests.py
```

### Test Suites

**1. Unit Tests** - Core functionality validation (10 tests)
```bash
# Run all unit tests
python tests/run_tests.py

# Or with pytest
pytest tests/test_substitute.py -v
```

**2. Real Data Validation** - Integration tests with actual school data (6 tests)
```bash
# Run comprehensive real data tests
pytest tests/test_real_data_validation.py -v

# Or manually explore with real timetable
python tests/test_real_timetable.py
```

**3. Performance Benchmarks** - Ensure algorithm efficiency (4 tests)
```bash
pytest tests/test_performance.py -v
```

**4. Interactive Testing Tool** - Manual scenario testing
```bash
# Interactive mode
python tools/substitute_simulator.py

# Command-line mode
python tools/substitute_simulator.py --teacher T004 --day Mon --periods 1,2,3

# Use predefined scenarios
python tools/substitute_simulator.py --scenario scenarios/monday_busy.json

# Verbose output with scoring details
python tools/substitute_simulator.py -t T004 -d Mon -p 1-6 --verbose

# Export to JSON
python tools/substitute_simulator.py -t T004 -d Mon -p 1-3 --format json
```

**5. Generate Detailed Reports**
```bash
# Run tests and generate comprehensive report
python tests/test_runner_with_report.py

# Reports saved to test_results/report_YYYY-MM-DD_HHMMSS.txt
```

### Test Coverage

**Unit Tests (tests/test_substitute.py):**
- ✅ Basic substitute finding
- ✅ Absent teacher exclusion
- ✅ Availability checking (no double-booking)
- ✅ Subject qualification handling
- ✅ Level matching preferences
- ✅ Workload balancing
- ✅ Input validation
- ✅ Multiple absent teachers

**Real Data Validation (tests/test_real_data_validation.py):**
- ✅ All teachers coverage testing
- ✅ High-conflict scenarios (multiple absences)
- ✅ Subject distribution analysis
- ✅ Level matching verification
- ✅ Workload fairness over time
- ✅ Edge case handling

**Performance Benchmarks (tests/test_performance.py):**
- ✅ Single substitute query: <100ms
- ✅ Full day assignment: <1s
- ✅ Week simulation: <5s
- ✅ High load scenarios: <2s

**Interactive Simulator Features:**
- ✅ Manual scenario input
- ✅ Predefined test scenarios
- ✅ Detailed reasoning explanations
- ✅ Timetable statistics
- ✅ Multiple output formats (text/JSON)
- ✅ Command-line and interactive modes

### Predefined Test Scenarios

Located in `scenarios/` directory:
- **monday_busy.json** - Multiple Math/English teachers absent
- **cross_level_challenge.json** - Elementary teachers absent, tests cross-level assignments
- **specialist_shortage.json** - Specialized subject teachers absent
- **fair_distribution.json** - Week-long workload balancing test

### pytest Integration (Optional)

For advanced testing features:
```bash
# Install pytest
pip install pytest pytest-cov

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_substitute.py -v

# Run specific test
pytest tests/test_substitute.py::TestFindBestSubstituteTeacher::test_workload_balancing -v
```

### Test Results

**Current Status:** All tests passing
- Unit tests: 10/10 ✅
- Real data validation: 6/6 ✅
- Performance benchmarks: 4/4 ✅

For detailed testing documentation, see:
- **docs/TESTING.md** - Complete testing guide (substitute tests)
- **TEST_REPORT.md** - Comprehensive test analysis
- **docs/LINE_TESTING.md** - LINE integration testing guide

### LINE Integration Testing

The project includes **100+ automated tests** for LINE Bot functionality with **85%+ code coverage**.

#### Quick Start

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all LINE tests
python scripts/run_line_tests.py
```

#### Test Suites

**1. Webhook Tests** (24+ tests) - Flask server and security
```bash
pytest tests/test_webhook.py -v
```
- ✅ HMAC-SHA256 signature verification
- ✅ Message event handling
- ✅ Leave keyword detection (ลา, ขอลา, หยุด, ไม่มา)
- ✅ Group filtering (teacher/admin groups)
- ✅ Error handling and propagation
- ✅ Health check endpoints

**2. AI Parser Tests** (40+ tests) - Thai message parsing
```bash
pytest tests/test_ai_parser.py -v
```
- ✅ Teacher name extraction (formal greetings, no-spacing)
- ✅ Thai date parsing (พรุ่งนี้, วันนี้, วันจันทร์)
- ✅ Period extraction (ranges, lists, full day)
- ✅ Late arrival detection (เข้าสาย, มาสาย)
- ✅ Reason extraction
- ✅ Fallback parser (regex-based)
- ✅ Real-world LINE messages
- ✅ Edge cases and error handling

**3. LINE Messaging Tests** (25+ tests) - Outgoing notifications
```bash
pytest tests/test_line_messaging.py -v
```
- ✅ Message sending to groups
- ✅ Two-group architecture routing
- ✅ Daily report formatting
- ✅ Error notifications
- ✅ Thai text preservation
- ✅ Emoji formatting

**4. Integration Tests** (10+ tests) - End-to-end workflows
```bash
pytest tests/test_line_integration.py -v
```
- ✅ Complete leave request flow
- ✅ Daily processing workflow
- ✅ Error propagation across components
- ✅ Data integrity validation

**5. Configuration Tests** (6+ tests) - Environment validation
```bash
pytest tests/test_config.py -v
```

#### Coverage Report

Generate HTML coverage report:
```bash
pytest tests/ --cov=src.web --cov=src.timetable.ai_parser --cov-report=html
open htmlcov/index.html  # View in browser
```

**Coverage Targets:**
- Webhook (src/web/webhook.py): 90%+
- AI Parser (src/timetable/ai_parser.py): 95%+
- LINE Messaging (src/web/line_messaging.py): 85%+

#### Test Features

- **100% Mock-based** - No actual API calls, fast execution (<10 seconds)
- **Thai Language Support** - All tests verify Thai text handling
- **Real-world Messages** - Based on actual LINE production messages
- **Comprehensive Error Scenarios** - Tests all failure paths
- **CI/CD Ready** - Can run in automated pipelines

#### Running Specific Tests

```bash
# Run single test file
pytest tests/test_webhook.py -v

# Run specific test class
pytest tests/test_ai_parser.py::TestPeriodParsing -v

# Run specific test method
pytest tests/test_ai_parser.py::TestPeriodParsing::test_period_range_1_to_3 -v

# Run with verbose output
pytest tests/test_webhook.py -vv

# Stop on first failure
pytest tests/ -x
```

For complete LINE testing documentation, see **docs/LINE_TESTING.md**.

## Data Structures

### Timetable Entry
```python
{
    "teacher_id": "T001",      # Teacher identifier
    "subject_id": "Math",      # Subject identifier
    "day_id": "Mon",           # Day of week
    "period_id": 1,            # Period number (1-based)
    "class_id": "ป.1"          # Class identifier
}
```

### Teacher Subjects
```python
{
    "T001": ["Math", "Science"],
    "T002": ["English", "Thai"]
}
```

### Teacher Levels
```python
{
    "T001": ["lower_elementary", "upper_elementary", "middle"],
    "ป.1": "lower_elementary",  # Grades 1-3
    "ป.5": "upper_elementary",  # Grades 4-6
    "ม.1": "middle"              # Grades 7-9
}
```

## Project Structure

```
TimeTableConverting/
├── excel_converting.py          # Excel to JSON converter
├── find_substitute.py            # Substitute teacher algorithm
│
├── Google Sheets Integration
├── src/utils/leave_log_sync.py            # Read leave logs from Google Sheets
├── src/utils/add_absence_to_sheets.py      # Add absences to Google Sheets
├── create_sheets_template.py     # Google Sheets setup helper
├── fix_sheet_headers.py          # Google Sheets header fix utility
│
├── LINE Bot System (NEW!)
├── config.py                     # Centralized configuration management
├── webhook.py                    # Flask server for LINE webhooks
├── ai_parser.py                  # AI-powered message parsing (OpenRouter/Gemini)
├── line_messaging.py             # Send notifications to LINE groups
├── process_daily_leaves.py       # Daily orchestration script
├── build_teacher_data.py         # Generate required data files
├── .env.example                  # Environment variables template
├── LINE_BOT_SETUP.md            # Complete LINE Bot setup guide
│
├── Testing
├── test_excel_converting.py      # Excel conversion tests (14 tests)
├── test_find_substitute.py       # Substitute finding tests (10 tests)
├── test_real_timetable.py        # Real timetable validation test
├── run_all_tests.py              # Unified test runner
│
├── Diagnostic Tools
├── diagnose_excel.py             # Excel structure inspection tool
├── check_conflicts.py            # Scheduling conflict detector
├── check_prathom_periods.py      # Period format validator
├── test_period_parsing.py        # Period parsing unit tests
├── check_t011_duplicates.py      # Duplicate verification tool
│
├── Data Files
├── real_timetable.json           # Parsed real school timetable (222 entries)
├── teacher_subjects.json         # Generated by build_teacher_data.py
├── teacher_levels.json           # Generated by build_teacher_data.py
├── class_levels.json             # Generated by build_teacher_data.py
├── teacher_name_map.json         # Generated by build_teacher_data.py
├── teacher_full_names.json       # Generated by build_teacher_data.py
│
├── Configuration (YOU create)
├── credentials.json              # Google API service account credentials
├── .env                          # Environment variables (from .env.example)
│
├── Documentation
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── CLAUDE.md                     # Claude Code instructions
├── GEMINI.md                     # Google Gemini instructions
├── LINE_BOT_SETUP.md            # LINE Bot setup guide
├── TESTING.md                    # Quick testing guide
├── TEST_REPORT.md                # Comprehensive test documentation
├── SESSION_SUMMARY.md            # Work session history
├── NEXT_STEPS.md                 # Recommended next actions
│
└── venv/                         # Virtual environment (created by you)
```

## Improvements Made

### excel_converting.py
- ✅ Added command-line argument support
- ✅ Added comprehensive error handling
- ✅ Added input validation
- ✅ Added warnings for unknown mappings
- ✅ Added type hints
- ✅ Added docstrings
- ✅ Improved user feedback with progress messages
- ✅ Fixed Windows console compatibility (replaced Unicode with ASCII)
- ✅ Added proper Excel file handle cleanup (prevents file locking)
- ✅ **Fixed critical parser bugs (Nov 2025):**
  - Time-range period parsing for elementary sheets (09.00-10.00 format)
  - Lunch break text filtering in middle school sheets
  - Row limiting to avoid duplicate entries from multiple tables
  - Results: 100% elementary data coverage, zero conflicts, clean 222 entries
- ✅ **Expanded subject mappings (Nov 2025):**
  - Added 18 new Thai-to-English subject mappings (26+ total subjects)
  - Changed unknown handling to preserve original Thai text instead of "UNKNOWN"
  - Handles curriculum variations: Computer, Music-Drama, Visual Arts, Anti-Corruption, STEM, Applied Math, etc.

### find_substitute.py
- ✅ Added type hints for all functions
- ✅ Added comprehensive docstrings
- ✅ Added input validation
- ✅ Better documentation of scoring algorithm
- ✅ **Enhanced algorithm flexibility (Nov 2025):**
  - Changed subject qualification from requirement to bonus (+2 points)
  - Can now assign any available teacher when no subject-qualified option exists
  - Added last resort teacher penalties (-50 points for specific teachers)
  - Implements institutional knowledge for better real-world fit

### Testing
- ✅ Created comprehensive test suite for both modules
- ✅ 24 test cases covering all major scenarios (10 + 14)
- ✅ All tests passing
- ✅ Unified test runner (run_all_tests.py)
- ✅ Comprehensive testing documentation (TESTING.md, TEST_REPORT.md)
- ✅ Programmatic mock creation for test isolation
- ✅ **Real-world validation (Nov 2025):**
  - Tested with actual school timetable data
  - 222 entries parsed, 9 classes covered, 16 teachers identified
  - Zero scheduling conflicts
  - 75% substitute finding success rate
  - Comprehensive diagnostic tools created
- ✅ **Enhanced level system (Nov 2025):**
  - Implemented three-tier system: lower_elementary/upper_elementary/middle
  - Provides more precise age-appropriate teacher-class matching

### Google Sheets Integration (Nov 2025)
- ✅ **Cloud-based leave log management:**
  - `src/utils/leave_log_sync.py` - Read leave logs from Google Sheets
  - `src/utils/add_absence_to_sheets.py` - Add absences with optional substitute finding
  - Bidirectional sync with existing timetable system
  - Interactive and command-line modes
- ✅ **Setup utilities:**
  - `create_sheets_template.py` - Automated sheet creation helper
  - `fix_sheet_headers.py` - Header correction utility
- ✅ **Benefits:**
  - Eliminates need for manual JSON editing
  - Accessible from anywhere (cloud-based)
  - Multi-user collaborative editing
  - Familiar spreadsheet interface for school staff
  - Built-in version history and audit trail

### LINE Bot Integration (Nov 2025)
- ✅ **Automated leave request processing:**
  - `webhook.py` - Flask server receives LINE messages with signature verification
  - `ai_parser.py` - OpenRouter/Gemini parses Thai natural language requests
  - Automatically extracts teacher name, date, periods, and reason
  - Adds absences to Google Sheets with confirmation
- ✅ **Daily substitute assignment workflow:**
  - `process_daily_leaves.py` - Orchestrates entire daily workflow
  - Reads leaves from Google Sheets
  - Finds substitutes using existing algorithm
  - Updates Sheets with assignments
  - Sends formatted reports to LINE group
- ✅ **Messaging system:**
  - `line_messaging.py` - Send notifications and reports to LINE
  - Rich text formatting with Thai language support
  - Error notifications and system status updates
- ✅ **Configuration management:**
  - `config.py` - Centralized configuration with validation
  - `.env` support for secure credential storage
  - `build_teacher_data.py` - Generates required data files
- ✅ **Benefits:**
  - Zero-touch leave request submission
  - Natural language interface (no forms!)
  - Automated daily processing with cron jobs
  - Instant notifications to all staff
  - Seamless integration with existing Google Sheets system

## Excel File Format

The Excel file should have the following structure:
- **Row 1**: Headers
- **Row 2**: Period numbers (columns 3 onwards)
  - Middle school sheets: Numeric periods (1, 2, 3, etc.)
  - Elementary sheets: Time ranges (09.00-10.00, 10.00-11.00, etc.)
- **Rows 3+**: Alternating subject/teacher rows
- **Column 1**: Day of week (Thai)
- **Column 2**: Class ID

**Important Notes:**
- Merged cells are supported and handled automatically
- Parser automatically detects and handles both period formats
- Lunch break columns are intelligently filtered out
- Only the first table per sheet is parsed (rows 1-32) to avoid duplicates

## Troubleshooting

### Module Not Found Error
Make sure you've activated the virtual environment and installed dependencies:
```bash
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Excel File Not Found
Ensure the file path is correct and the file exists. Use absolute paths if relative paths don't work.

### Unknown Teachers/Subjects
Check the mappings in `excel_converting.py` (lines 8-44) and add any missing teachers or subjects.

## License

This project is provided as-is for educational and administrative purposes.

## Support

For issues or questions, please check:
1. This README
2. CLAUDE.md for developer documentation
3. Test file for usage examples
