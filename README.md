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

**Daily Processing:**

Run manually for testing:
```bash
# Process today's leaves
python -m src.utils.daily_leave_processor

# Process specific date
python -m src.utils.daily_leave_processor 2025-11-21

# Send report to LINE
python -m src.utils.daily_leave_processor --send-line

# Test mode (no Sheets updates)
python -m src.utils.daily_leave_processor --test
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

The algorithm uses a scoring system to find the best substitute:

### Scoring Criteria
- **+2 points**: Teacher can teach the subject (bonus, not required)
- **+5 points**: Teacher's level matches class level
- **-2 points**: Level mismatch penalty
- **-2 points per period**: Daily teaching load
- **-1 point per substitution**: Historical substitution count
- **-0.5 points per period**: Total term load (excluding leave days)
- **-50 points**: Last resort teachers (assigned only when no better options)
- **-999 points**: Teacher is absent

### Features
- Prevents double-booking (teachers can't be in two places at once)
- Balances workload across teachers based on daily, historical, and term loads
- Prioritizes subject-qualified teachers
- Considers teacher level (elementary vs. middle school)
- **Historical data integration:** Loads past substitute assignments from Google Sheets for fair workload distribution
- **Cumulative learning:** Automatically learns from each day's assignments to prevent teacher burnout
- Randomizes selection among equally-scored candidates for fairness

## Testing

### Running All Tests

Run the complete test suite (24 tests across both modules):

```bash
python run_all_tests.py
```

### Running Individual Test Suites

Run substitute finding tests (10 tests):
```bash
python test_find_substitute.py
```

Run Excel conversion tests (14 tests):
```bash
python test_excel_converting.py
```

Run real timetable validation test:
```bash
python test_real_timetable.py
```

### Test Coverage

**Substitute Finding (test_find_substitute.py):**
- Basic substitute finding
- Absent teacher exclusion
- Availability checking
- No qualified substitute scenarios
- Level matching preferences
- Workload balancing
- Input validation
- Double-booking prevention
- Multiple absent teachers

**Excel Conversion (test_excel_converting.py):**
- Excel file parsing and JSON structure
- Thai-English mappings (days, subjects, teachers)
- Merged cell handling
- UTF-8 encoding validation
- Error handling (missing files, missing sheets)
- Edge cases (numeric character stripping)

**Test Results:** All 24 tests passing

For detailed testing documentation, see:
- **TESTING.md** - Quick reference guide for developers
- **TEST_REPORT.md** - Comprehensive test analysis and recommendations

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
