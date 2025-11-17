# Testing Guide

## Quick Start

### 1. Setup (First Time Only)
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Run All Tests
```bash
# Easiest way - run all tests at once
python run_all_tests.py
```

### 3. Run Individual Test Suites
```bash
# Test substitute finding functionality
python test_find_substitute.py

# Test Excel conversion functionality
python test_excel_converting.py
```

## Test Files

| File | Purpose | Tests |
|------|---------|-------|
| `test_find_substitute.py` | Tests substitute teacher assignment algorithm | 10 tests |
| `test_excel_converting.py` | Tests Excel to JSON conversion | 14 tests |
| `run_all_tests.py` | Runs all tests and shows summary | - |

## What's Being Tested?

### Find Substitute Tests
- Basic substitute selection
- Availability checking (no double-booking)
- Level matching (elementary vs middle school)
- Workload balancing
- Edge cases (no qualified substitutes)
- Input validation

### Excel Converting Tests
- File parsing and conversion
- Thai to English mappings (days, subjects, teachers)
- Merged cell handling
- Missing sheet handling
- UTF-8 encoding
- Error handling

## Expected Output

### Successful Run
```
======================================================================
TEST SUMMARY
======================================================================
[PASS] test_find_substitute.py: PASSED
[PASS] test_excel_converting.py: PASSED
======================================================================

All tests passed successfully!
```

### Test Details
Each test suite shows individual test results:
```
test_find_substitute_basic ... ok
test_absent_teacher_not_selected ... ok
test_teacher_already_teaching ... ok
...
----------------------------------------------------------------------
Ran 10 tests in 0.001s

OK
```

## Troubleshooting

### Issue: ModuleNotFoundError
**Solution:** Make sure virtual environment is activated and dependencies are installed
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: Permission errors on Windows
**Solution:** These are harmless warnings from openpyxl library, tests still pass

### Issue: Garbled Thai characters in output
**Solution:** This is a console encoding issue, doesn't affect functionality

## For Developers

### Adding New Tests
1. Add test methods to existing test classes
2. Follow naming convention: `test_description_of_what_is_tested`
3. Use descriptive docstrings
4. Run tests to verify they pass

### Test Structure Example
```python
def test_my_new_feature(self):
    """Test description here"""
    # Setup
    data = {...}

    # Execute
    result = my_function(data)

    # Verify
    self.assertEqual(result, expected_value)
```

## Coverage Report

**Current Coverage:**
- find_substitute.py: High coverage (10 tests)
- excel_converting.py: High coverage (14 tests)

**See TEST_REPORT.md for detailed coverage analysis**

## CI/CD Ready

These tests are ready for continuous integration. See TEST_REPORT.md for recommended GitHub Actions configuration.
