"""
Performance benchmark tests for substitute teacher assignment

These tests ensure the algorithm performs efficiently for daily processing.

Run with: python -m pytest tests/test_performance.py -v
"""

import unittest
import time
import json
from src.timetable.substitute import find_best_substitute_teacher, assign_substitutes_for_day
from src.config import config


class TestPerformance(unittest.TestCase):
    """Performance benchmark tests"""

    @classmethod
    def setUpClass(cls):
        """Load real data once for all tests"""
        with open(config.TIMETABLE_FILE, 'r', encoding='utf-8') as f:
            cls.timetable = json.load(f)

        with open(config.TEACHER_SUBJECTS_FILE, 'r', encoding='utf-8') as f:
            cls.teacher_subjects = json.load(f)

        with open(config.TEACHER_LEVELS_FILE, 'r', encoding='utf-8') as f:
            cls.teacher_levels = json.load(f)

        with open(config.CLASS_LEVELS_FILE, 'r', encoding='utf-8') as f:
            cls.class_levels = json.load(f)

        cls.all_teacher_ids = list(cls.teacher_subjects.keys())
        cls.substitute_logs = []
        cls.leave_logs = []

    def test_single_substitute_performance(self):
        """Finding a single substitute should be fast (<100ms)"""
        # Find a test entry
        test_entry = next(
            (e for e in self.timetable if e['day_id'] == 'Mon'),
            None
        )

        self.assertIsNotNone(test_entry, "Need at least one Monday entry for testing")

        # Measure execution time
        start_time = time.time()

        substitute = find_best_substitute_teacher(
            subject_id=test_entry['subject_id'],
            day_id='Mon',
            period_id=test_entry['period_id'],
            class_id=test_entry['class_id'],
            timetables=self.timetable,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=[test_entry['teacher_id']],
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels
        )

        duration = time.time() - start_time

        # Assert performance
        self.assertLess(duration, 0.1,
                       f"Single substitute query too slow: {duration*1000:.1f}ms (expected <100ms)")

        # Print timing info
        print(f"\nSingle substitute query: {duration*1000:.2f}ms")

    def test_full_day_performance(self):
        """Assigning substitutes for a full day should be reasonable (<1s)"""
        # Simulate one teacher absent for full day
        test_teacher = self.all_teacher_ids[0]

        # Measure execution time
        start_time = time.time()

        assignments = assign_substitutes_for_day(
            day_id='Mon',
            timetable=self.timetable,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=[test_teacher],
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels
        )

        duration = time.time() - start_time

        # Assert performance
        self.assertLess(duration, 1.0,
                       f"Full day assignment too slow: {duration:.2f}s (expected <1s)")

        # Print timing info
        print(f"\nFull day assignment ({len(assignments)} periods): {duration*1000:.2f}ms")

    def test_week_simulation_performance(self):
        """Processing a full week should be reasonably fast (<5s)"""
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        test_teacher = self.all_teacher_ids[0]

        # Measure execution time
        start_time = time.time()

        total_assignments = 0
        cumulative_logs = []

        for day in days:
            assignments = assign_substitutes_for_day(
                day_id=day,
                timetable=self.timetable,
                teacher_subjects=self.teacher_subjects,
                substitute_logs=cumulative_logs,
                all_teacher_ids=self.all_teacher_ids,
                absent_teacher_ids=[test_teacher],
                leave_logs=self.leave_logs,
                teacher_levels=self.teacher_levels,
                class_levels=self.class_levels
            )
            total_assignments += len(assignments)
            cumulative_logs.extend(assignments)

        duration = time.time() - start_time

        # Assert performance
        self.assertLess(duration, 5.0,
                       f"Week simulation too slow: {duration:.2f}s (expected <5s)")

        # Print timing info
        print(f"\nWeek simulation ({total_assignments} total assignments): {duration*1000:.2f}ms")
        print(f"Average per day: {(duration/5)*1000:.2f}ms")

    def test_high_load_scenario_performance(self):
        """Test performance with multiple teachers absent (realistic worst-case)"""
        # Simulate 5 teachers absent on Monday (realistic high-load scenario)
        absent_teachers = self.all_teacher_ids[:5]

        # Measure execution time
        start_time = time.time()

        assignments = assign_substitutes_for_day(
            day_id='Mon',
            timetable=self.timetable,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=absent_teachers,
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels
        )

        duration = time.time() - start_time

        # High load should still complete in reasonable time (<2s)
        self.assertLess(duration, 2.0,
                       f"High load scenario too slow: {duration:.2f}s (expected <2s)")

        # Print timing info
        print(f"\nHigh load scenario (5 teachers, {len(assignments)} assignments): {duration*1000:.2f}ms")


if __name__ == '__main__':
    unittest.main()
