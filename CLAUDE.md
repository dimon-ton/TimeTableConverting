# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TimeTableConverting is a **production-ready Python-based school timetable management system** with two main components:

1. **Core System** - Excel-to-JSON conversion, intelligent substitute teacher assignment, and automated leave management via LINE Bot
2. **Google Apps Script Webapp** - Teacher working hours dashboard (production-ready, mobile-responsive)

**Current Status:** PRODUCTION-READY (A++) - Zero mock data, comprehensive testing (100+ tests, 85%+ coverage)

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt       # Production
pip install -r requirements-dev.txt   # Development/testing
```

### Core Application Commands
```bash
# Convert Excel timetable to JSON
python -m src.timetable.converter <excel_file.xlsm> [output.json]

# Run LINE webhook server
python -m src.web.webhook

# Daily leave processing (with admin verification workflow)
python -m src.utils.daily_leave_processor              # Process today
python -m src.utils.daily_leave_processor 2025-01-15   # Specific date
python -m src.utils.daily_leave_processor --test       # Dry run
python -m src.utils.daily_leave_processor --send-line  # Send to LINE admin
```

### Testing Commands
```bash
# Run all tests (unified runner)
python tests/run_tests.py

# Run specific test suites
pytest tests/test_webhook.py -v
pytest tests/test_ai_parser.py -v
pytest tests/test_substitute.py -v

# LINE integration tests
python scripts/run_line_tests.py

# Coverage report
pytest tests/ --cov=src.web --cov=src.timetable.ai_parser --cov-report=html
```

### Database/Sheets Utilities
```bash
# Create Google Sheets template
python -m scripts.create_sheets_template

# Create Pending_Assignments worksheet for admin verification
python -m scripts.create_pending_sheet
```

## Architecture Overview

### Core System Components

```
src/
├── config.py                    # Centralized configuration with .env validation
├── timetable/
│   ├── converter.py            # Excel (.xlsm) to JSON conversion
│   ├── ai_parser.py            # AI-powered Thai message parsing (OpenRouter/Gemini)
│   └── substitute.py           # 6-factor substitute teacher algorithm
├── utils/
│   ├── sheet_utils.py          # Google Sheets API integration
│   ├── daily_leave_processor.py # Daily workflow orchestration
│   ├── report_parser.py        # Admin edit detection & message parsing
│   └── build_teacher_data.py   # Generate teacher mapping JSON files
└── web/
    ├── webhook.py              # Flask webhook server (LINE Bot)
    └── line_messaging.py       # LINE notification formatting
```

### Data Flow Architecture

**Incoming Leave Requests:**
```
Teacher (LINE) → Webhook → AI Parser → Google Sheets (Leave_Requests)
```

**Daily Processing (8:55 AM cron):**
```
Leave_Requests → Daily Processor → Substitute Algorithm → Pending_Assignments
                                                              ↓
                                                    LINE Admin Group (review)
                                                              ↓
                          Teacher Group → Report Parser → Edit Detection → Leave_Logs
```

### Substitute Teacher Algorithm

**Hard Constraints** (automatic exclusion):
- Teacher is absent
- Already teaching that period
- Daily workload ≥4 periods (MAX_DAILY_PERIODS)

**Scoring Criteria**:
- +2: Can teach subject (bonus, not required)
- +5: Level match (lower_elementary/upper_elementary/middle)
- -2: Level mismatch penalty
- -2 per period: Daily teaching load
- -1 per substitution: Historical count
- -0.5 per period: Total term load
- -50: Last resort teachers (institutional knowledge)

### Thai Language Support

- **UTF-8 encoding** throughout
- 26+ Thai subject mappings (Math, Science, คณิตศาสตร์, วิทยาศาสตร์, etc.)
- Native date expressions: พรุ่งนี้, วันนี้, วันจันทร์, ทั้งวัน, เข้าสาย
- Teacher name validation with fuzzy matching (4-tier system)

## Environment Configuration

Required `.env` variables:
```bash
# Google Sheets
SPREADSHEET_ID=your_spreadsheet_id

# LINE Bot
LINE_CHANNEL_SECRET=your_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_access_token
LINE_TEACHER_GROUP_ID=teacher_group_id    # Leave requests submitted here
LINE_ADMIN_GROUP_ID=admin_group_id        # Reports sent here

# AI Services (OpenRouter/Gemini)
OPENROUTER_API_KEY=your_api_key
OPENROUTER_MODEL=deepseek/deepseek-r1

# Admin Edit Detection
AI_MATCH_CONFIDENCE_THRESHOLD=0.85
USE_AI_MATCHING=True

# Flask
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=5000
```

Copy `.env.example` to `.env` and fill in values.

## Google Sheets Structure

Three worksheets:
1. **Leave_Requests** - Raw incoming requests (Timestamp, Raw_Message, Teacher_Name, Date, Periods, Reason, Status)
2. **Leave_Logs** - Final assignments (Date, Absent_Teacher, Day, Period, Class, Subject, Substitute_Teacher, Notes)
3. **Teacher_Hours_Tracking** - Workload snapshots (Date, Teacher_ID, Teacher_Name, Regular_Periods_Today, Daily_Workload, Updated_At)

## Key Integration Points

### LINE Bot Webhook
- **Entry point**: `src/web/webhook.py`
- **Signature verification**: HMAC-SHA256
- **Leave keywords**: ลา, ขอลา, หยุด, ไม่มา
- **Teacher validation**: Real-time via `is_valid_teacher()`

### AI Message Parsing
- **Primary**: OpenRouter/Gemini API (configurable model)
- **Fallback**: Regex-based parser (100% feature parity)
- **Teacher names**: Loaded from `teacher_name_map.json`
- **Token limit**: 1000 tokens (enhanced from 500)

### Admin Verification Workflow
1. Daily processor writes to `Pending_Assignments` worksheet
2. Sends two-balloon message to admin LINE group
3. Admin can edit substitute teacher names in message
4. Admin sends edited message to teacher group with `[REPORT]` prefix
5. System detects prefix, parses edits, updates database (4-tier name matching)
6. Finalizes to `Leave_Logs` with verification audit trail

## Testing Strategy

### Test Suites
- **Webhook** (24+ tests): Signature verification, message handling, group filtering
- **AI Parser** (40+ tests): Thai NLP, date/period extraction, teacher names
- **LINE Messaging** (25+ tests): Group routing, report formatting, Thai text
- **Integration** (10+ tests): End-to-end workflows
- **Substitute Algorithm** (10+ tests): Scoring, workload balancing, constraints
- **Real Data** (6+ tests): Actual timetable validation
- **Performance** (4+ tests): <100ms query response, <1s full day processing

### Coverage Targets
- `src/web/webhook.py`: 90%+
- `src/timetable/ai_parser.py`: 95%+
- `src/web/line_messaging.py`: 85%+

### Mock-Based Testing
All tests use mocks - no actual API calls (LINE, Google Sheets, OpenRouter)

## Production Deployment

### Platform
- Raspberry Pi (recommended) or Linux server
- Python 3.7+
- Static IP or DDNS for LINE webhook
- Port 5000 forwarded

### Services
```bash
# systemd service for webhook
sudo systemctl enable timetable-webhook
sudo systemctl start timetable-webhook

# Cron job (8:55 AM, Mon-Fri)
55 8 * * 1-5 cd /path/to/TimeTableConverting && /path/to/venv/bin/python -m src.utils.daily_leave_processor --send-line
```

### Pre-Deployment Checklist
- [ ] All tests pass: `python tests/run_tests.py`
- [ ] `.env` configured with all credentials
- [ ] Google Sheets shared with service account
- [ ] LINE webhook URL configured
- [ ] Tested with ngrok locally
- [ ] Thai text encoding verified (UTF-8)

## Important Constraints

### Thai Language
- Never break UTF-8 encoding
- Preserve Thai text in all APIs
- Teacher name matching must handle ครู prefix and spacing variations

### Substitute Algorithm
- Max 4 periods/day per teacher (hard constraint)
- Historical data from Google Sheets drives fair distribution
- No double-booking (same teacher, same period)
- Level matching prioritized but not required

### Google Sheets
- Single source of truth for leave data
- Batch writes when possible (API rate limits)
- All writes include audit trail (timestamp, user ID)

### LINE Bot
- Two-group architecture (teacher + admin)
- All notifications in Thai language
- Admin group receives all system events
- Teacher group only receives final assignments

## Common Development Tasks

### Adding New Subject Mappings
Edit `src/timetable/converter.py` - add to `THAI_SUBJECT_MAPPING` dictionary

### Modifying Substitute Scoring
Edit `src/timetable/substitute.py` - modify scoring factors in `find_best_substitute_teacher()`

### Adding New AI Parser Features
Edit `src/timetable/ai_parser.py` - update prompt templates and extraction logic
- Remember to add fallback regex support in `parse_with_fallback()`

### Updating Google Sheets Schema
Edit `src/utils/sheet_utils.py` - modify worksheet initialization and data structures

### Adding New Test Cases
- Webhook/AI tests: `tests/test_webhook.py`, `tests/test_ai_parser.py`
- Substitute tests: `tests/test_substitute.py`
- Always use mocks (no real API calls)

## Troubleshooting

### Module Not Found
```bash
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Google Sheets Access Denied
- Verify `credentials.json` is valid
- Share spreadsheet with service account email
- Check `SPREADSHEET_ID` in `.env`

### LINE Bot Not Responding
- Test webhook with ngrok: `ngrok http 5000`
- Verify `LINE_CHANNEL_SECRET` and `LINE_CHANNEL_ACCESS_TOKEN`
- Check signature verification logs

### Thai Text Encoding
- Ensure all `.py` files declare `# coding: utf-8` (Python 3 default)
- Verify `.env` file is UTF-8 encoded
- Check terminal/console supports UTF-8

### AI Parser Failures
- Verify `OPENROUTER_API_KEY` has credits
- Check `OPENROUTER_MODEL` is valid
- Fallback regex parser should handle failures gracefully
- Test with: `python -m src.timetable.ai_parser`

## Data Files

Generated by `src/utils/build_teacher_data.py`:
- `data/teacher_name_map.json` - Thai name to ID mapping
- `data/teacher_full_names.json` - Display names
- `data/teacher_subjects.json` - Subject qualifications
- `data/teacher_levels.json` - Level assignments
- `data/class_levels.json` - Class level mappings

## Security Notes

- Never commit `.env` or `credentials.json` to Git
- HMAC-SHA256 verification for LINE webhooks
- Service account with minimal Google Sheets permissions
- API key rotation recommended quarterly
- All assignments include audit trail in Google Sheets

## Documentation Files

- `README.md` - Main project documentation
- `AGENTS.md` - Repository guidelines (commit style, structure)
- `docs/CLAUDE.md` - Backup of this file (synchronized)
- `docs/GEMINI.md` - Google Gemini context (synchronized)
- `docs/LINE_BOT_SETUP.md` - LINE Bot setup guide
- `docs/TESTING.md` - Testing guide
- `docs/GAS_WEBAPP_PLAN.md` - Google Apps Script webapp plan
