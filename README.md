# TimeTable Converting Project

A Python-based timetable management system for schools that handles Excel-to-JSON conversion and intelligent substitute teacher assignment.

## Features

- ✅ Convert Excel timetables (.xlsm) to structured JSON format
- ✅ Intelligent substitute teacher assignment algorithm
- ✅ Workload balancing across teachers
- ✅ Level-based matching (elementary/middle school)
- ✅ Subject qualification validation
- ✅ Comprehensive test suite

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
- Validates input file existence
- Reports unknown teachers and subjects
- Handles merged cells automatically
- UTF-8 encoding for Thai characters
- Progress feedback during processing

### Finding Substitute Teachers

Use the `find_substitute` module programmatically:

```python
from find_substitute import find_best_substitute_teacher, assign_substitutes_for_day

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
- **+10 points**: Teacher can teach the subject (required)
- **+5 points**: Teacher's level matches class level
- **-2 points**: Level mismatch penalty
- **-2 points per period**: Daily teaching load
- **-1 point per substitution**: Historical substitution count
- **-0.5 points per period**: Total term load (excluding leave days)
- **-999 points**: Teacher is absent or cannot teach subject

### Features
- Prevents double-booking (teachers can't be in two places at once)
- Balances workload across teachers
- Prioritizes subject-qualified teachers
- Considers teacher level (elementary vs. middle school)
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
    "T001": ["elementary", "middle"],
    "ป.1": "elementary",
    "ม.1": "middle"
}
```

## Project Structure

```
TimeTableConverting/
├── excel_converting.py        # Excel to JSON converter
├── find_substitute.py          # Substitute teacher algorithm
├── test_excel_converting.py    # Excel conversion tests (14 tests)
├── test_find_substitute.py     # Substitute finding tests (10 tests)
├── run_all_tests.py            # Unified test runner
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── CLAUDE.md                   # Claude Code instructions
├── GEMINI.md                   # Google Gemini instructions
├── TESTING.md                  # Quick testing guide
├── TEST_REPORT.md              # Comprehensive test documentation
├── SESSION_SUMMARY.md          # Work session history
└── venv/                       # Virtual environment (created by you)
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

### find_substitute.py
- ✅ Added type hints for all functions
- ✅ Added comprehensive docstrings
- ✅ Added input validation
- ✅ Better documentation of scoring algorithm

### Testing
- ✅ Created comprehensive test suite for both modules
- ✅ 24 test cases covering all major scenarios (10 + 14)
- ✅ All tests passing
- ✅ Unified test runner (run_all_tests.py)
- ✅ Comprehensive testing documentation (TESTING.md, TEST_REPORT.md)
- ✅ Programmatic mock creation for test isolation

## Excel File Format

The Excel file should have the following structure:
- **Row 1**: Headers
- **Row 2**: Period numbers (columns 3 onwards)
- **Rows 3+**: Alternating subject/teacher rows
- **Column 1**: Day of week (Thai)
- **Column 2**: Class ID

Merged cells are supported and handled automatically.

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
