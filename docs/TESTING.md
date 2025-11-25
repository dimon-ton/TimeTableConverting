# Comprehensive Testing Guide

Complete guide for testing the substitute teacher functionality in the TimeTableConverting project.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Test Suites](#test-suites)
3. [Interactive Testing Tool](#interactive-testing-tool)
4. [Running Tests](#running-tests)
5. [Adding New Tests](#adding-new-tests)
6. [Interpreting Results](#interpreting-results)
7. [Performance Benchmarks](#performance-benchmarks)
8. [Troubleshooting](#troubleshooting)

## Quick Start

```bash
# Run all tests
python tests/run_tests.py

# Run with pytest (if installed)
pytest tests/ -v

# Interactive testing
python tools/substitute_simulator.py
```

## Test Suites

### 1. Unit Tests (`tests/test_substitute.py`)

**Purpose:** Validate core substitute finding algorithm functionality

**Tests (10 total):**
- `test_find_substitute_basic` - Basic substitute assignment
- `test_absent_teacher_not_selected` - Ensures absent teachers excluded
- `test_teacher_already_teaching` - Prevents double-booking
- `test_no_qualified_substitute` - Handles no-qualification scenario
- `test_level_matching_preference` - Validates level matching preference
- `test_workload_balancing` - Tests historical workload impact
- `test_invalid_input_validation` - Input validation
- `test_assign_substitutes_single_absent` - Single teacher absence
- `test_assign_substitutes_multiple_absent` - Multiple teachers absent
- `test_no_double_booking` - Full day double-booking prevention

**Run:**
```bash
python tests/run_tests.py
# or
pytest tests/test_substitute.py -v
```

### 2. Real Data Validation (`tests/test_real_data_validation.py`)

**Purpose:** Integration testing with actual school timetable data

**Tests (6 total):**
- `test_all_teachers_coverage` - Tests substitute finding for each teacher
- `test_high_conflict_scenarios` - Multiple teachers absent simultaneously
- `test_subject_distribution` - Coverage across all subjects
- `test_level_matching` - Level-appropriate assignments
- `test_workload_fairness` - Fair distribution over simulated week
- `test_edge_cases` - Graceful handling of extreme scenarios

**Run:**
```bash
pytest tests/test_real_data_validation.py -v
```

### 3. Performance Benchmarks (`tests/test_performance.py`)

**Purpose:** Ensure algorithm performs efficiently for daily use

**Tests (4 total):**
- `test_single_substitute_performance` - Single query <100ms
- `test_full_day_performance` - Full day assignment <1s
- `test_week_simulation_performance` - Week simulation <5s
- `test_high_load_scenario_performance` - Multiple absences <2s

**Run:**
```bash
pytest tests/test_performance.py -v
```

### 4. Real Timetable Exploration (`tests/test_real_timetable.py`)

**Purpose:** Manual testing with detailed output and validation

**Run:**
```bash
python tests/test_real_timetable.py
```

**Features:**
- Simulates single teacher absence
- Shows period-by-period substitute assignments
- Displays validation checks:
  - Double-booking detection
  - Absent teacher exclusion
  - Subject qualification rate
  - Level matching rate
  - Workload distribution

## Interactive Testing Tool

The substitute simulator (`tools/substitute_simulator.py`) provides interactive and command-line testing.

### Interactive Mode

```bash
python tools/substitute_simulator.py
```

**Features:**
1. Custom scenario input (teacher, day, periods)
2. Timetable statistics analysis
3. User-friendly output with explanations

### Command-Line Mode

```bash
# Basic usage
python tools/substitute_simulator.py --teacher T004 --day Mon --periods 1,2,3

# Verbose output
python tools/substitute_simulator.py -t T004 -d Mon -p 1-3 --verbose

# JSON output
python tools/substitute_simulator.py -t T004 -d Mon -p 1-3 --format json

# Use predefined scenarios
python tools/substitute_simulator.py --scenario scenarios/monday_busy.json
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
python tests/run_tests.py

# With pytest
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### Running Specific Tests

```bash
# Single test file
pytest tests/test_substitute.py -v

# Single test method
pytest tests/test_substitute.py::TestFindBestSubstituteTeacher::test_workload_balancing -v

# Real data tests only
pytest tests/test_real_data_validation.py -v

# Performance tests only
pytest tests/test_performance.py -v
```

### Detailed Reporting

```bash
# Generate comprehensive test report
python tests/test_runner_with_report.py

# Report saved to: test_results/report_YYYY-MM-DD_HHMMSS.txt
```

## Adding New Tests

### Creating Unit Tests

Add test method to `tests/test_substitute.py`:

```python
def test_my_new_feature(self):
    """Test description"""
    result = find_best_substitute_teacher(
        subject_id="Math",
        day_id="Mon",
        period_id=1,
        class_id="ป.1",
        timetables=self.timetables,
        teacher_subjects=self.teacher_subjects,
        substitute_logs=self.substitute_logs,
        all_teacher_ids=self.all_teacher_ids,
        absent_teacher_ids=["T001"],
        leave_logs=self.leave_logs,
        teacher_levels=self.teacher_levels,
        class_levels=self.class_levels
    )

    # Assertions
    self.assertIsNotNone(result)
    self.assertIn(result, self.all_teacher_ids)
```

## Interpreting Results

### Successful Test Output

```
test_find_substitute_basic ... ok
test_absent_teacher_not_selected ... ok
...

Ran 10 tests in 0.003s
OK
```

### Performance Test Output

```
Single substitute query: 25.43ms
PASS: <100ms threshold

Full day assignment (6 periods): 156.78ms
PASS: <1s threshold
```

## Performance Benchmarks

### Expected Performance

- **Single substitute query:** <100ms
- **Full day (6 periods):** <1s
- **Week simulation (5 days):** <5s
- **High load (5+ teachers):** <2s

## Troubleshooting

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Use test runner which sets path correctly
python tests/run_tests.py
```

### Missing Data Files

**Error:** `FileNotFoundError: No such file or directory: 'data/real_timetable.json'`

**Solution:**
```bash
# Verify data files exist
ls data/
```

## Best Practices

1. **Run tests before committing code**
2. **Add tests for new features**
3. **Use descriptive test names**
4. **Keep tests independent**
5. **Test with real data**
6. **Monitor performance**

## Summary

The testing infrastructure provides:
- ✅ **20+ comprehensive tests** covering all functionality
- ✅ **Interactive testing tool** for manual exploration
- ✅ **Performance benchmarks** ensuring efficiency
- ✅ **Real data validation** with actual school timetables
- ✅ **Detailed reporting** for analysis and debugging
- ✅ **CI/CD ready** for automated testing

For questions or issues, consult:
- This guide (docs/TESTING.md)
- Main README.md
- Test source code for examples
