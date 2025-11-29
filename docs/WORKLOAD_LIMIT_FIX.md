# Daily Workload Limit Implementation

## Issue Discovered

During testing, it was discovered that teachers with 5 periods already scheduled in a day were still being assigned as substitutes. This created an excessive workload for those teachers.

### Root Cause

The algorithm used **soft constraints** (scoring penalties) instead of **hard constraints** for daily workload:

**Before:**
- Teachers with more periods received scoring penalties (-2 per period)
- But could still be selected if they were the "best" available option
- No absolute limit prevented assignment

**Problem Example:**
```
Teacher T001: Has 5 periods on Monday
Need: Substitute for period 6
Result: T001 is assigned → Now has 6 periods (overloaded!)
```

## Solution Implemented

Added a **hard constraint** that enforces a maximum daily workload limit.

### Code Changes

**1. Added constant (line 5):**
```python
MAX_DAILY_PERIODS = 5
```

**2. Added workload check function (lines 87-107):**
```python
def has_reached_daily_limit(teacher_id: str) -> bool:
    """
    Check if teacher has reached maximum daily workload.

    Returns:
        True if teacher already has MAX_DAILY_PERIODS or more periods on this day
    """
    # Count regular timetable periods for this day
    daily_load = sum(
        1
        for row in timetables
        if row["teacher_id"] == teacher_id and row["day_id"] == day_id
    )
    # Add substitute assignments already made for this day
    daily_load += sum(
        1
        for row in substitute_logs
        if row.get("substitute_teacher_id") == teacher_id and row["day_id"] == day_id
    )

    return daily_load >= MAX_DAILY_PERIODS
```

**3. Enforced constraint in candidate selection (lines 177-183):**
```python
# Collect candidates
candidates = []
for teacher_id in all_teacher_ids:
    # Skip teachers who are not available at this period
    if not is_available(teacher_id):
        continue

    # Skip teachers who have reached their daily workload limit
    if has_reached_daily_limit(teacher_id):
        continue

    score = calculate_score(teacher_id)
    if score > -999:
        candidates.append({"teacher_id": teacher_id, "score": score})
```

**4. Updated documentation:**
- Function docstring now lists hard constraints separately
- README.md updated with "Hard Constraints" section
- CLAUDE.md updated with constraint information

## Testing

Created comprehensive tests to verify the fix:

### Test 1: Teachers with 5 periods are NOT assigned
```python
def test_should_not_assign_teacher_with_5_periods(self):
    # Setup: T001 has 5 periods on Monday
    # Need: Substitute for period 6
    # Expected: T001 should NOT be selected

    result = find_best_substitute_teacher(...)

    # Verify T001 was not assigned
    if result == "T001":
        self.fail("T001 was assigned but already has 5 periods!")
```

**Result:** ✅ PASS - T003 (with 2 periods) was selected instead

### Test 2: Teachers with 4 periods CAN be assigned
```python
def test_teacher_with_4_periods_can_be_assigned(self):
    # Setup: T001 has 4 periods on Monday
    # Need: Substitute for period 6
    # Expected: T001 should be eligible and selected (qualified, level match)

    result = find_best_substitute_teacher(...)

    self.assertEqual(result, "T001")
```

**Result:** ✅ PASS - T001 correctly selected

### Test 3: Scoring diagnostic
```python
def test_scoring_with_4_periods_vs_2_periods(self):
    # Compare: T001 (4 periods, qualified) vs T003 (2 periods, unqualified)
    # T001 score: +2 (subject) +5 (level) -8 (daily) -2 (term) = -3
    # T003 score: 0 (no subject) -2 (level) -4 (daily) -1 (term) = -7
    # Expected: T001 should win (-3 > -7)
```

**Result:** ✅ PASS - T001 correctly selected with higher score

## Impact

### Before Fix
- Teachers could be assigned 6, 7, or even 8 periods in a day
- Excessive workload on some teachers
- Unfair distribution of teaching load
- Potential teacher burnout

### After Fix
- **Maximum 5 periods per day** enforced
- Protects teachers from excessive workload
- Forces better distribution across available teachers
- May result in "no substitute found" if all teachers at limit (acceptable trade-off)

## Algorithm Flow

```
For each teacher:
    ├─ Is teacher absent? → Exclude
    ├─ Is teacher already teaching this period? → Exclude
    ├─ Does teacher have 5+ periods today? → Exclude (NEW!)
    └─ Calculate score and add to candidates

Select best from remaining candidates
```

## Configuration

The limit is configurable via the `MAX_DAILY_PERIODS` constant:

```python
# In src/timetable/substitute.py
MAX_DAILY_PERIODS = 5  # Can be changed to 4, 6, etc.
```

**Recommended values:**
- Elementary school: 5 periods (current)
- Middle school: 6 periods (if needed)
- Adjust based on school schedule

## Files Modified

1. `src/timetable/substitute.py`
   - Added MAX_DAILY_PERIODS constant
   - Added has_reached_daily_limit() function
   - Updated candidate selection logic
   - Updated docstring

2. `tests/test_workload_limit.py` (NEW)
   - Test for 5-period limit enforcement
   - Test for 4-period eligibility

3. `tests/test_workload_scoring.py` (NEW)
   - Diagnostic test for scoring verification

4. `README.md`
   - Updated algorithm documentation
   - Added "Hard Constraints" section

5. `docs/WORKLOAD_LIMIT_FIX.md` (NEW)
   - This document

## Verification

Run tests to verify the fix:

```bash
# Test workload limits specifically
python -m unittest tests.test_workload_limit -v

# Run all substitute tests
python tests/run_tests.py
```

**Expected result:** All tests pass ✅

## Conclusion

The daily workload limit is now a **hard constraint** rather than a soft penalty. This ensures teachers are protected from excessive workload and maintains a fair distribution of substitute assignments.

**Key principle:** Better to have no substitute assigned than to overload a teacher beyond 5 periods per day.
