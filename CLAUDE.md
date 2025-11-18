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
   - +10: Can teach subject (required, else -999)
   - +5: Teacher's level matches class level
   - -2: Level mismatch penalty
   - -2 per period: Daily load on same day
   - -1 per entry: Historical substitution count
   - -0.5 per period: Total term load (excluding leave days)
3. Select randomly among top-scored candidates (handles ties)

**assign_substitutes_for_day:** Iterates through all absent teachers' slots for a day, calling find_best_substitute_teacher for each. Includes newly assigned substitutes in constraint checking to avoid double-booking.

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
- `teacher_levels`: `{teacher_id: ["elementary", "middle"]}`
- `class_levels`: `{class_id: "elementary" | "middle"}`
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
- Level system: "elementary" (ป.1-ป.6) vs "middle" (ม.1-ม.3) affects substitute matching
- The substitute algorithm intentionally uses randomization for fairness when scores tie
- Workload balancing considers: daily load, historical substitutions, and term load
- Teachers can be assigned outside their level (with penalty) if no better option exists
- Dependencies: Install via `pip install -r requirements.txt` (requires openpyxl)
