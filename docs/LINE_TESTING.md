# LINE Integration Testing Guide

Complete guide for testing LINE Bot functionality in the TimeTableConverting project.

## Overview

This project has **100+ automated tests** covering all LINE integration components with **85%+ code coverage**. All tests use mocks - no actual LINE API calls are made, making tests fast, reliable, and runnable offline.

## Quick Start

### Install Test Dependencies

```bash
# Install test framework and coverage tools
pip install -r requirements-dev.txt
```

### Run All LINE Tests

```bash
# Recommended: Use the test runner
python scripts/run_line_tests.py

# Alternative: Use pytest directly
pytest tests/test_webhook.py tests/test_ai_parser.py tests/test_line_messaging.py tests/test_line_integration.py tests/test_config.py -v
```

### View Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=src.web --cov=src.timetable.ai_parser --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

## Test Structure

### Test Files (5 files, 100+ tests)

```
tests/
├── test_webhook.py         # Webhook server tests (24+ tests)
├── test_ai_parser.py       # Thai message parsing (40+ tests)
├── test_line_messaging.py  # Outgoing notifications (25+ tests)
├── test_line_integration.py # End-to-end workflows (10+ tests)
└── test_config.py          # Configuration management (6+ tests)
```

### Coverage Targets

| Module | Target | Test Count |
|--------|--------|------------|
| **src/web/webhook.py** | 90%+ | 24+ tests |
| **src/timetable/ai_parser.py** | 95%+ | 40+ tests |
| **src/web/line_messaging.py** | 85%+ | 25+ tests |
| **Integration** | N/A | 10+ tests |

## Running Tests

### Run Specific Test Suite

```bash
# Webhook tests only
pytest tests/test_webhook.py -v

# AI Parser tests only
pytest tests/test_ai_parser.py -v

# LINE Messaging tests only
pytest tests/test_line_messaging.py -v

# Integration tests only
pytest tests/test_line_integration.py -v
```

### Run Specific Test Class

```bash
# Test signature verification only
pytest tests/test_webhook.py::TestSignatureVerification -v

# Test period parsing only
pytest tests/test_ai_parser.py::TestPeriodParsing -v
```

### Run Specific Test Method

```bash
# Test single method
pytest tests/test_ai_parser.py::TestPeriodParsing::test_period_range_1_to_3 -v
```

### Run with Different Output Levels

```bash
# Minimal output
pytest tests/test_webhook.py -q

# Verbose output
pytest tests/test_webhook.py -v

# Very verbose with full diff
pytest tests/test_webhook.py -vv
```

## Test Categories

### 1. Webhook Tests (`test_webhook.py`)

**Purpose:** Test Flask webhook server security and message processing

**Test Classes:**
- `TestSignatureVerification` - HMAC-SHA256 security
- `TestCallbackEndpoint` - HTTP endpoint handling
- `TestLeaveKeywordDetection` - Leave request identification
- `TestGroupFiltering` - Two-group architecture
- `TestErrorHandling` - Exception handling
- `TestHealthEndpoints` - Monitoring endpoints
- `TestSuccessfulWorkflow` - Complete request flow

**Key Tests:**
```python
# Test valid signature accepted
test_valid_signature_accepted()

# Test invalid signature rejected
test_invalid_signature_rejected()

# Test leave keywords detected
test_keyword_la_detected()
test_keyword_kho_la_detected()

# Test wrong group ignored
test_wrong_group_ignored()
```

### 2. AI Parser Tests (`test_ai_parser.py`)

**Purpose:** Test Thai natural language processing for leave requests

**Test Classes:**
- `TestTeacherNameExtraction` - Extract teacher names
- `TestDateParsing` - Thai date expressions (พรุ่งนี้, วันนี้)
- `TestPeriodParsing` - Period ranges and lists
- `TestLateArrivalDetection` - Late vs regular leave (NEW Nov 25)
- `TestReasonExtraction` - Reason parsing
- `TestFallbackParser` - Regex-based fallback
- `TestRealWorldMessages` - Production message validation
- `TestEdgeCases` - Error handling

**Key Tests:**
```python
# Test Thai date expressions
test_prung_nee_tomorrow()  # พรุ่งนี้
test_wan_nee_today()       # วันนี้

# Test period parsing
test_period_range_1_to_3()     # คาบ 1-3 → [1,2,3]
test_full_day_tang_wan()       # ทั้งวัน → [1-8]

# Test late arrival (NEW)
test_kao_sai_detected_as_late()  # เข้าสาย
test_ma_sai_detected_as_late()   # มาสาย

# Test fallback parser
test_fallback_on_api_failure()
```

### 3. LINE Messaging Tests (`test_line_messaging.py`)

**Purpose:** Test outgoing LINE notifications

**Test Classes:**
- `TestMessageSending` - Message delivery
- `TestGroupRouting` - Teacher/admin group routing
- `TestReportFormatting` - Daily report generation
- `TestSpecializedMessages` - Error/test messages
- `TestThaiTextHandling` - Thai character preservation
- `TestFormattedReportGeneration` - Complex reports

**Key Tests:**
```python
# Test group routing
test_send_message_to_admin_group()
test_send_message_to_teacher_group()

# Test report formatting
test_format_substitute_summary_100_percent()
test_format_substitute_summary_partial_success()

# Test Thai text
test_thai_unicode_preserved_in_summary()
test_emoji_in_formatted_messages()
```

### 4. Integration Tests (`test_line_integration.py`)

**Purpose:** Test end-to-end workflows across components

**Test Classes:**
- `TestLeaveRequestWorkflow` - Complete leave request flow
- `TestDailyProcessingWorkflow` - Daily substitute assignment
- `TestErrorPropagation` - Error handling across components
- `TestDataFlowIntegrity` - Data consistency

**Key Tests:**
```python
# Test complete workflow
test_successful_leave_request_complete_flow()

# Test fallback chain
test_ai_parser_failure_triggers_fallback()

# Test error handling
test_sheets_api_failure_propagates_error()

# Test data integrity
test_leave_data_preserves_thai_characters()
```

## Mock Strategy

All tests use mocks to avoid actual API calls:

### Mocking LINE API

```python
from unittest.mock import patch, MagicMock

@patch('src.web.line_messaging.get_line_bot_api')
def test_send_message(mock_get_api):
    # Mock LINE API
    mock_api = MagicMock()
    mock_get_api.return_value = mock_api

    # Call function
    result = send_message_to_group("Test")

    # Verify mock was called
    mock_api.push_message.assert_called_once()
```

### Mocking OpenRouter API

```python
@patch('src.timetable.ai_parser.requests.post')
def test_ai_parser(mock_post):
    # Mock API response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{
            "message": {
                "content": '{"teacher_name": "test", ...}'
            }
        }]
    }
    mock_post.return_value = mock_response

    # Call parser
    result = parse_leave_request("ขอลา")
```

### Mocking Google Sheets

```python
@patch('src.utils.sheet_utils.log_request_to_sheet')
def test_logging(mock_log):
    # Mock successful logging
    mock_log.return_value = None

    # Test workflow
    process_leave_request_message(...)

    # Verify logged
    mock_log.assert_called_once()
```

## Adding New Tests

### 1. Create Test File

```python
"""
Description of what this test file covers
"""

import unittest
from unittest.mock import patch, MagicMock

class TestNewFeature(unittest.TestCase):
    """Test new feature description"""

    def test_feature_works(self):
        """Test that feature works correctly"""
        # Arrange
        setup_data = "test"

        # Act
        result = function_to_test(setup_data)

        # Assert
        self.assertEqual(result, expected_value)
```

### 2. Follow Naming Conventions

- **Test files:** `test_*.py`
- **Test classes:** `Test*`
- **Test methods:** `test_*`
- **Descriptive names:** `test_period_range_1_to_3` not `test1`

### 3. Use Proper Assertions

```python
# Equality
self.assertEqual(result, expected)
self.assertNotEqual(result, unexpected)

# Boolean
self.assertTrue(condition)
self.assertFalse(condition)

# Containment
self.assertIn(item, container)
self.assertNotIn(item, container)

# Exceptions
with self.assertRaises(ValueError):
    function_that_should_raise()

# None checks
self.assertIsNone(result)
self.assertIsNotNone(result)
```

### 4. Test Both Success and Failure

```python
class TestFeature(unittest.TestCase):
    def test_success_case(self):
        """Test when everything works"""
        result = function(valid_input)
        self.assertTrue(result)

    def test_failure_case(self):
        """Test when input is invalid"""
        result = function(invalid_input)
        self.assertFalse(result)

    def test_edge_case(self):
        """Test boundary conditions"""
        result = function(edge_case_input)
        self.assertIsNotNone(result)
```

## Interpreting Coverage Reports

### Terminal Coverage Summary

```
---------- coverage: platform win32, python 3.12.0 -----------
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
src/web/webhook.py                  150     12    92%   45-48, 112-115
src/timetable/ai_parser.py          180      8    96%   234, 267-270
src/web/line_messaging.py          140     18    87%   89-92, 156-160
---------------------------------------------------------------
TOTAL                               470     38    92%
```

**Interpreting:**
- `Stmts`: Total statements in file
- `Miss`: Statements not executed by tests
- `Cover`: Percentage covered
- `Missing`: Line numbers not covered

### HTML Coverage Report

Open `htmlcov/index.html` for:
- **File-by-file coverage** with color coding
- **Line-by-line highlighting** (green = covered, red = missed)
- **Branch coverage** details
- **Sortable tables** by coverage percentage

## Troubleshooting

### Tests Fail with Import Errors

```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Run from project root
cd C:\Users\Phontan-Chang\Documents\TimeTableConverting

# Or use test runner
python scripts/run_line_tests.py
```

### Mock Not Working

```python
# ❌ Wrong - mocking after import
from src.web import webhook
@patch('src.web.webhook.config')  # Won't work

# ✅ Right - mock the actual location
@patch('src.web.webhook.config')
def test_something(mock_config):
    from src.web import webhook
    # Now it works
```

### Assertion Fails with Thai Text

```python
# Ensure UTF-8 encoding in test file
# -*- coding: utf-8 -*-

# Use raw strings for Thai text
self.assertIn('ครูสมชาย', result)
```

### Coverage Not Showing All Files

```bash
# Make sure to specify all modules
pytest tests/ --cov=src.web --cov=src.timetable.ai_parser
```

## Best Practices

### 1. Test Isolation

Each test should be independent:

```python
class TestExample(unittest.TestCase):
    def setUp(self):
        """Reset state before each test"""
        self.test_data = create_fresh_data()

    def tearDown(self):
        """Clean up after each test"""
        cleanup_resources()
```

### 2. Clear Test Names

```python
# ❌ Bad
def test_1(self):
    pass

# ✅ Good
def test_period_range_1_to_3_returns_list_of_three_integers(self):
    pass
```

### 3. Arrange-Act-Assert Pattern

```python
def test_feature(self):
    # Arrange - Set up test data
    input_data = "test"
    expected = "result"

    # Act - Execute function
    actual = function(input_data)

    # Assert - Verify results
    self.assertEqual(actual, expected)
```

### 4. Test Edge Cases

```python
def test_empty_input(self):
    result = parse("")
    self.assertIsNone(result)

def test_very_large_input(self):
    result = parse("x" * 10000)
    self.assertIsNotNone(result)

def test_special_characters(self):
    result = parse("!@#$%^&*()")
    # Should handle gracefully
```

### 5. Use Fixtures for Complex Data

```python
class TestWithFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Load data once for all tests"""
        cls.sample_messages = load_test_messages()

    def test_with_fixture(self):
        result = parse(self.sample_messages[0])
        self.assertIsNotNone(result)
```

## Testing Checklist

Before deploying changes:

- [ ] All tests pass locally
- [ ] Coverage meets targets (85%+)
- [ ] New code has corresponding tests
- [ ] Edge cases are tested
- [ ] Error handling is tested
- [ ] Thai text handling verified
- [ ] No actual API calls in tests
- [ ] Tests run in <10 seconds
- [ ] Documentation updated

## CI/CD Integration

### GitHub Actions Example

```yaml
name: LINE Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: python scripts/run_line_tests.py

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        files: ./coverage.xml
```

## Performance Tips

### Fast Test Execution

```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto

# Run only failed tests
pytest tests/ --lf

# Stop on first failure
pytest tests/ -x
```

### Skip Slow Tests

```python
import pytest

@pytest.mark.slow
def test_slow_operation(self):
    """This test takes a long time"""
    pass

# Run without slow tests
# pytest tests/ -m "not slow"
```

## Additional Resources

- **pytest documentation:** https://docs.pytest.org/
- **unittest documentation:** https://docs.python.org/3/library/unittest.html
- **Coverage.py documentation:** https://coverage.readthedocs.io/
- **LINE Bot SDK documentation:** https://github.com/line/line-bot-sdk-python

## Support

For questions or issues:

1. Check test output for specific error messages
2. Review this guide for common solutions
3. Check existing test files for examples
4. Run with `-vv` flag for detailed output

## Summary

The LINE integration testing infrastructure provides:

- **✅ 100+ automated tests** covering all LINE components
- **✅ 85%+ code coverage** across webhook, parser, and messaging
- **✅ Fast execution** (<10 seconds for all tests)
- **✅ No external dependencies** (all mocked)
- **✅ CI/CD ready** for automated testing
- **✅ Comprehensive documentation** for maintainability

All LINE functionality is thoroughly tested and ready for production use.
