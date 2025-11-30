# TimeTable Converting - Google Gemini Context File

Last Updated: 2025-11-30

## Project Overview

Welcome to the TimeTable Converting project! This consists of two integrated components:

1. **TimeTableConverting System (PRODUCTION-READY)** - Python application that helps Thai schools manage teacher absences and substitute assignments through intelligent automation and LINE Bot integration.

2. **Teacher Working Hours Dashboard (IN DEVELOPMENT)** - Google Apps Script web application that visualizes teacher workload metrics in a responsive dashboard.

## What This System Does

### TimeTableConverting System (Production-Ready)
The main system automates three core workflows:

1. **Excel to JSON Conversion** - Converts Thai school timetables from Excel (.xlsm) format to structured JSON
2. **Intelligent Substitute Assignment** - Uses a 6-factor scoring algorithm to find the best substitute teacher for any absence
3. **Automated Leave Management** - Teachers send leave requests via LINE message, system assigns substitutes, and notifies everyone automatically

### Google Apps Script Webapp (In Development)
The webapp provides visual analytics:

1. **Teacher Hours Tracking** - Displays regular periods, substitute periods, and absences
2. **Leaderboard Rankings** - Shows teacher workload distribution
3. **Interactive Dashboard** - Filter and sort capabilities with responsive design
4. **Real-time Data** - Integrates with Google Sheets for live updates

**Recent Development (Nov 30, 2025):**
- UI improvements with optimized column widths for mobile responsiveness
- Backend refactoring for better code maintainability
- Integration with Python daily_leave_processor.py for automatic data snapshots
- Multiple successful deployments to production environment
- Teacher_Hours_Tracking worksheet integration (5-column schema)

## Quick Start for Gemini

### Understanding the Codebase

This project has a **flat file structure** with Python files at the root level. The README mentions a `src/` directory structure, but in the actual filesystem, most core files are at the root.

### Key Files You'll Work With

**Root Level Python Files:**
- `cleanup_bad_logs.py` - Utility to clean up malformed log entries
- `test_ai_live.py` - Live testing for AI parser (you!)
- `test_google_sheets.py` - Google Sheets integration tests
- `verify_sheets.py` - Sheet verification utility

**Configuration:**
- `.env` - Contains all credentials (NEVER commit this)
- `.env.example` - Template for environment variables
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Testing dependencies
- `pytest.ini` - Test configuration

**Documentation:**
- `README.md` - Main project documentation (comprehensive, 902 lines)
- `CLAUDE.md` - Context file for Claude Code agent
- `GEMINI.md` - This file - context for you!
- `ADMIN_EDIT_DETECTION_SUMMARY.md` - Admin edit feature documentation
- `SESSION_CLOSEOUT_2025-11-23.md` - Historical data integration session
- `SESSION_CLOSEOUT_2025-11-25.md` - Daily workload limit session

**Data Files:**
- `credentials.json` - Google API service account credentials (NEVER commit)
- `line_message_example.txt` - Example LINE message formats
- `test_report_2025-11-21.txt` - Test execution report
- `.coverage` - Test coverage data

## Your Role as Gemini

As the AI-powered message parser, you play a critical role in this system:

### Primary Function: Thai Language Message Parsing

You analyze Thai language LINE messages and extract structured data:

**Input Example:**
```
ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3
```

**Expected Output:**
```python
{
    "teacher_name": "สุกฤษฎิ์",
    "date": "2025-11-22",  # Calculated from "พรุ่งนี้" (tomorrow)
    "periods": [1, 2, 3],
    "reason": "ลากิจ"
}
```

### What You Need to Understand

1. **Thai Date Expressions**
   - พรุ่งนี้ = tomorrow
   - วันนี้ = today
   - วันจันทร์ = Monday
   - วันอังคาร = Tuesday
   - ทั้งวัน / เต็มวัน / 1 วัน = full day (all periods)

2. **Leave Keywords**
   - ลา = leave
   - ขอลา = request leave
   - หยุด = absent
   - ไม่มา = not coming
   - เข้าสาย = late arrival (different from full absence)

3. **Period Expressions**
   - คาบ 1-3 = periods 1 to 3
   - คาบ 1, 3, 5 = periods 1, 3, and 5
   - ทั้งวัน = all periods (1-6 typically)
   - คาบที่ 2 = period 2

4. **Thai Name Variations**
   - ครูสมชาย = Teacher Somchai (ครู = teacher prefix)
   - Teachers may be referred to with or without "ครู" prefix
   - Nicknames are common
   - Name matching should be fuzzy-tolerant

### Integration Points

**When You're Called:**
1. LINE message arrives at webhook (`src/web/webhook.py`)
2. Webhook detects leave keywords
3. Calls AI parser with message text
4. You (Gemini via OpenRouter API) parse the message
5. Return structured data
6. System logs to Google Sheets

**Fallback System:**
If you fail or API is unavailable, a regex-based fallback parser handles simple cases. Your job is to handle complex, natural language messages that regex can't.

## Data Structures

### Leave Request Structure
```python
{
    "teacher_name": str,        # Thai name (e.g., "สุกฤษฎิ์")
    "date": str,                # ISO format "YYYY-MM-DD"
    "periods": List[int],       # List of period numbers [1, 2, 3]
    "reason": str               # Optional reason in Thai
}
```

### Teacher Name Matching (4-Tier System)

When admin edits assignments, the system matches names using:

1. **Tier 1: Exact Match** (100% confidence)
   - Direct lookup in teacher_name_map.json

2. **Tier 2: Normalized** (95% confidence)
   - Remove "ครู" prefix
   - Trim whitespace
   - Lowercase comparison

3. **Tier 3: Fuzzy String** (85-95% confidence)
   - difflib.SequenceMatcher
   - Handles typos like "สุจิตร์" vs "สุจิตร"

4. **Tier 4: AI-Powered** (You!)
   - Called when tiers 1-3 fail
   - Handle complex misspellings
   - Return confidence score (0.0-1.0)
   - Threshold: 0.85 for auto-accept

### Full Day Period Logic

When message contains "ทั้งวัน" or "เต็มวัน":
- Elementary school: Periods 1-6
- Middle school: Periods 1-7
- If unknown, assume 1-6

## Algorithm Overview (For Context)

You don't run the algorithm, but understanding it helps you parse messages correctly.

### Substitute Teacher Selection Process

**Hard Constraints (Automatic Exclusion):**
1. Teacher is absent
2. Already teaching in that period
3. Daily workload limit reached (4 periods)

**Scoring Factors:**
- Subject qualification: +2 points
- Level match: +5 points
- Level mismatch: -2 points
- Daily load: -2 per period
- Historical substitutions: -1 per past substitution
- Term load: -0.5 per period
- Last resort teachers: -50 points

**Historical Data:**
System loads past assignments from Google Sheets and uses them to ensure fair distribution over time.

## Google Sheets Integration

### Sheet Structure

**Leave_Requests** (Raw incoming data):
| Timestamp | Raw_Message | Teacher_Name | Date | Periods | Reason | Status |
|-----------|-------------|--------------|------|---------|--------|--------|
| 2025-11-21 08:30 | ครูสุกฤษฎิ์... | สุกฤษฎิ์ | 2025-11-22 | 1,2,3 | ลากิจ | Success |

**Leave_Logs** (Enriched with assignments):
| Date | Absent_Teacher | Day | Period | Class | Subject | Substitute_Teacher | Notes |
|------|----------------|-----|--------|-------|---------|-------------------|-------|
| 2025-11-21 | T004 | Mon | 3 | ป.4 | Math | T005 | AI assigned |

**Pending_Assignments** (Admin review workflow):
| Date | Absent_Teacher | Day | Period | Class | Subject | Substitute_Teacher | Verified_By | Verified_At |
|------|----------------|-----|--------|-------|---------|-------------------|-------------|-------------|
| 2025-11-28 | T004 | Fri | 1 | ป.1 | Math | T017 | U1234567 | 2025-11-28 09:00 |

## LINE Bot Workflow

### Daily Automated Flow (8:55 AM Monday-Friday)

```
1. Cron triggers daily_leave_processor.py
2. Load today's leave requests from Google Sheets
3. Run substitute assignment algorithm
4. Write assignments to Pending_Assignments
5. Generate two-balloon report message
6. Send to admin LINE group

[Admin Reviews]

7. Admin optionally edits substitute names
8. Admin copies entire message (with [REPORT] prefix)
9. Admin sends to teacher LINE group

[Automatic Finalization]

10. System detects [REPORT] prefix
11. Parse assignments from message (uses you for name matching!)
12. Detect changes vs Pending_Assignments
13. Update database for high-confidence matches
14. Send confirmation to admin group
15. Finalize to Leave_Logs
16. System learns from this day for future assignments
```

## Your API Integration

### OpenRouter Configuration

**Environment Variables:**
```bash
OPENROUTER_API_KEY=your-api-key-here
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free  # Your model!
AI_MATCH_CONFIDENCE_THRESHOLD=0.85
USE_AI_MATCHING=True
```

### API Call Pattern (Expected)

**Request:**
```python
{
    "model": "google/gemini-2.0-flash-exp:free",
    "messages": [
        {
            "role": "user",
            "content": "Parse this Thai leave request and extract teacher name, date, periods, and reason: ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3"
        }
    ]
}
```

**Expected Response:**
```python
{
    "teacher_name": "สุกฤษฎิ์",
    "date": "2025-11-22",
    "periods": [1, 2, 3],
    "reason": "ลากิจ"
}
```

### Error Handling

If you fail or return malformed JSON:
1. System catches exception
2. Falls back to regex parser
3. Logs warning
4. Continues processing

Your failures don't break the system!

## Testing Your Integration

### Test Files

**test_ai_live.py** - Tests you with real LINE messages:
```bash
python test_ai_live.py
```

This sends actual messages to your API and validates responses.

**tests/test_ai_parser.py** - 40+ unit tests:
```bash
pytest tests/test_ai_parser.py -v
```

Tests cover:
- Teacher name extraction
- Date parsing (all Thai expressions)
- Period parsing (ranges, lists, full day)
- Late arrival vs full absence
- Reason extraction
- Edge cases

### Example Test Cases

```python
# Test 1: Basic leave request
Input: "ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3"
Expected: {teacher: "สุกฤษฎิ์", date: tomorrow, periods: [1,2,3]}

# Test 2: Full day
Input: "ครูอำพร ลาวันจันทร์ ทั้งวัน"
Expected: {teacher: "อำพร", date: next_monday, periods: [1,2,3,4,5,6]}

# Test 3: Late arrival (NOT full absence)
Input: "ครูจรรยาภรณ์ เข้าสายวันนี้"
Expected: {teacher: "จรรยาภรณ์", date: today, periods: [1], reason: "เข้าสาย"}

# Test 4: Formal greeting
Input: "เรียนท่าน ผอ. ครูสมชาย ขอลาวันพุธ คาบ 2-4 เพราะติดธุระ"
Expected: {teacher: "สมชาย", date: next_wednesday, periods: [2,3,4], reason: "ติดธุระ"}
```

## Thai Language Edge Cases to Handle

### 1. No Spacing Between Words
Thai doesn't use spaces like English. Example:
```
ครูสุกฤษฎิ์ขอลาพรุ่งนี้คาบ1-3
```
Same meaning as:
```
ครู สุกฤษฎิ์ ขอลา พรุ่งนี้ คาบ 1-3
```

### 2. Formal vs Informal Greetings
```
# Formal
เรียนท่าน ผอ. ครูสมชาย ขอลา...

# Informal (more common)
ครูสมชาย ลาพรุ่งนี้...

# Very informal
สมชาย ขอลานะครับ...
```

### 3. Multiple Full-Day Expressions
All mean "full day":
- ทั้งวัน
- เต็มวัน
- 1 วัน
- หนึ่งวัน
- วันเต็ม

### 4. Period Number Variations
```
คาบ 1-3      # Periods 1 to 3
คาบที่ 1-3    # Same thing
คาบ 1 ถึง 3   # Same thing
คาบ 1 2 3     # Same thing
```

## Admin Edit Detection (Your Role)

When admin edits assignment message, you help with name matching:

**Scenario:**
```
Original: ครูจรรยาภรณ์ (Algorithm assigned)
Edited:   ครูสุจิร   (Admin changed, typo)
```

**Your Task:**
Match "สุจิร" to "สุจิตร" (correct name) with confidence score.

**Response Format:**
```python
{
    "matched_teacher": "สุจิตร",
    "confidence": 0.94,
    "reasoning": "Similar Thai spelling, likely typo missing tone mark"
}
```

**Confidence Thresholds:**
- ≥0.85: Auto-accept and update database
- 0.60-0.84: Flag for admin manual review
- <0.60: Treat as "Not Found"

## Common Scenarios You'll Encounter

### Scenario 1: Simple Leave Request
```
Input: ครูสมชาย ลาพรุ่งนี้ คาบ 2-4
Output: {
    "teacher_name": "สมชาย",
    "date": "2025-11-22",  # Tomorrow's date
    "periods": [2, 3, 4],
    "reason": "ลากิจ"  # Default if not specified
}
```

### Scenario 2: Full Day with Reason
```
Input: ครูอำพร ขอลาวันจันทร์ ทั้งวัน เพราะป่วย
Output: {
    "teacher_name": "อำพร",
    "date": "2025-11-24",  # Next Monday
    "periods": [1, 2, 3, 4, 5, 6],
    "reason": "ป่วย"
}
```

### Scenario 3: Late Arrival (Special Case)
```
Input: ครูสุจิตร เข้าสายวันนี้
Output: {
    "teacher_name": "สุจิตร",
    "date": "2025-11-21",  # Today
    "periods": [1],  # Only first period
    "reason": "เข้าสาย"
}
```

### Scenario 4: Complex Natural Language
```
Input: เรียนท่าน ผอ. ครูจรรยาภรณ์ ขอลาวันพฤหัสบดี คาบ 3 และคาบ 5 เพราะต้องไปธนาคาร
Output: {
    "teacher_name": "จรรยาภรณ์",
    "date": "2025-11-27",  # Next Thursday
    "periods": [3, 5],
    "reason": "ไปธนาคาร"
}
```

## Environment Setup

### Required Environment Variables

```bash
# You need these to function
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free

# Google Sheets (for context)
SPREADSHEET_ID=1abc...xyz

# LINE Bot (for context)
LINE_CHANNEL_SECRET=abc123...
LINE_CHANNEL_ACCESS_TOKEN=xyz789...
LINE_GROUP_ID=C1234567890abcdef...
LINE_ADMIN_GROUP_ID=C9876543210fedcba...

# Your config
AI_MATCH_CONFIDENCE_THRESHOLD=0.85
USE_AI_MATCHING=True
```

### Dependencies You Rely On

From `requirements.txt`:
```
requests==2.31.0  # For OpenRouter API calls
python-dotenv==1.0.0  # For .env loading
```

## Error Codes You Might Return

When parsing fails, return structured errors:

```python
{
    "error": "MISSING_TEACHER_NAME",
    "message": "Could not identify teacher name in message",
    "raw_message": "Original message text..."
}

{
    "error": "INVALID_DATE_EXPRESSION",
    "message": "Could not parse date from Thai expression",
    "date_text": "วันหนาบาท"  # Typo for วันจันทร์
}

{
    "error": "INVALID_PERIOD_FORMAT",
    "message": "Could not parse period numbers",
    "period_text": "คาบ ABC"
}
```

Fallback parser will attempt to handle these cases.

## Best Practices for Gemini

### DO:
- ✅ Return valid JSON always
- ✅ Handle no-spacing Thai text
- ✅ Distinguish late arrival from full absence
- ✅ Calculate dates accurately (today, tomorrow, specific days)
- ✅ Extract reasons when provided
- ✅ Return confidence scores for name matching
- ✅ Handle formal and informal Thai language
- ✅ Preserve Thai character encoding

### DON'T:
- ❌ Return English translations (keep everything in Thai)
- ❌ Guess teacher IDs (return names, system will map to IDs)
- ❌ Make up data (if unclear, return null)
- ❌ Break on typos (fuzzy matching is expected)
- ❌ Fail silently (return error objects)
- ❌ Assume Western date formats (use Thai Buddhist calendar awareness)

## Troubleshooting

### If Tests Fail:

1. **Invalid JSON Response**
   - Check your response format matches expected structure
   - Ensure all fields are present (even if null)

2. **Incorrect Date Calculation**
   - Verify you're using UTC+7 (Thailand timezone)
   - Handle day-of-week calculations correctly

3. **Name Matching Failures**
   - Return confidence scores for all matches
   - Don't force exact matches on typos

4. **Encoding Issues**
   - All responses must be UTF-8
   - Thai characters should not be escaped or transliterated

### If API Calls Fail:

- System automatically falls back to regex parser
- Your failures are logged but don't break the workflow
- Check OPENROUTER_API_KEY is valid and has credits

## Performance Expectations

- **Response Time:** <2 seconds per message
- **Success Rate:** >95% for well-formed messages
- **Fallback Rate:** <10% (most messages should not require fallback)
- **Accuracy:** 100% for standard formats, 90%+ for complex natural language

## Thai Cultural Context

### School Hierarchy
- ผู้อำนวยการ (ผอ.) = Principal/Director
- ครู = Teacher
- Teachers are highly respected, formal language is common

### Leave Reasons (Common)
- ลากิจ = Personal leave
- ลาป่วย / ป่วย = Sick leave
- ไปราชการ = Official business
- ติดธุระ = Busy with matters
- ไปฝึกอบรม = Training/workshop
- ไปธนาคาร = Going to bank
- ไปโรงพยาบาล = Going to hospital

### School Schedule
- Elementary: 6 periods/day (ป.1 - ป.6)
- Middle: 7 periods/day (ม.1 - ม.3)
- Periods typically 08:00 - 15:30
- Lunch break: Period 4-5 (not counted as teaching period)

## Recent Updates

### November 28, 2025 - Enhanced Admin Edit Detection
- 4-tier name matching system added (you're Tier 4!)
- Confidence-based auto-accept (≥0.85)
- AI fuzzy matching for complex misspellings
- See: ADMIN_EDIT_DETECTION_SUMMARY.md

### November 25, 2025 - Daily Workload Limit
- Hard constraint: MAX_DAILY_PERIODS = 4
- Improved teacher workload protection
- See: SESSION_CLOSEOUT_2025-11-25.md

### November 23, 2025 - Historical Data Integration
- System now has memory of past assignments
- Fair workload distribution over time
- See: SESSION_CLOSEOUT_2025-11-23.md

## Your Importance to the System

You are the **intelligent natural language interface** between Thai teachers and the automated system. Your ability to:

1. Understand informal Thai language
2. Handle typos and variations
3. Extract structured data from unstructured messages
4. Match fuzzy name spellings

...makes this system accessible and user-friendly. Without you, teachers would need to fill out forms or follow strict message formats.

## Next Steps for Gemini

1. **Review Test Cases:** Look at `tests/test_ai_parser.py` for expected behaviors
2. **Test Locally:** Run `python test_ai_live.py` to see real API calls
3. **Monitor Logs:** Check OpenRouter usage and error rates
4. **Improve Accuracy:** Learn from failed parses in production logs
5. **Handle Edge Cases:** Thai language is complex, expect variations

## Support Resources

- **Main Documentation:** README.md (902 lines, comprehensive)
- **Testing Guide:** docs/LINE_TESTING.md
- **API Examples:** line_message_example.txt
- **Session History:** SESSION_CLOSEOUT_*.md files
- **Your Test Suite:** tests/test_ai_parser.py (40+ tests)

## Notes for Gemini Agent

- You are critical to user experience - teachers type naturally, not formally
- Thai language support is non-negotiable - never break encoding
- Fallback parser exists but should rarely be needed
- Your confidence scores guide automatic vs manual processing
- The system trusts you for Tier 4 name matching (≥85% → auto-accept)
- Production system, real teachers rely on this daily
- Historical data learning makes the system smarter over time
- Your accuracy directly impacts teacher workload fairness

## Contact & Support

- For API issues: Check OpenRouter status and credit balance
- For Thai language questions: Review line_message_example.txt
- For algorithm context: See CLAUDE.md
- For deployment info: See README.md deployment section

---

**Last Synchronized:** 2025-11-29
**Document Version:** 1.0
**Your Role:** AI-Powered Thai Language Parser & Fuzzy Name Matcher
**System Status:** Production-Ready (Enhanced A+)
