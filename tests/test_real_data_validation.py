"""
Comprehensive real data validation tests for substitute teacher assignment

These tests use actual school timetable data to validate the substitute
finding algorithm under realistic conditions.

Run with: python -m pytest tests/test_real_data_validation.py -v
"""

import unittest
import json
from collections import defaultdict
from src.timetable.substitute import find_best_substitute_teacher, assign_substitutes_for_day
from src.config import config


class TestRealDataValidation(unittest.TestCase):
    """Comprehensive tests using real school timetable data"""

    @classmethod
    def setUpClass(cls):
        """Load real data once for all tests"""
        # Load real timetable
        with open(config.TIMETABLE_FILE, 'r', encoding='utf-8') as f:
            cls.timetable = json.load(f)

        # Load teacher data
        with open(config.TEACHER_SUBJECTS_FILE, 'r', encoding='utf-8') as f:
            cls.teacher_subjects = json.load(f)

        with open(config.TEACHER_LEVELS_FILE, 'r', encoding='utf-8') as f:
            cls.teacher_levels = json.load(f)

        with open(config.CLASS_LEVELS_FILE, 'r', encoding='utf-8') as f:
            cls.class_levels = json.load(f)

        # Get all teacher IDs
        cls.all_teacher_ids = list(cls.teacher_subjects.keys())

        # Initialize empty logs for testing
        cls.substitute_logs = []
        cls.leave_logs = []

    def test_all_teachers_coverage(self):
        """Test substitute finding for each teacher absence on Monday"""
        test_day = "Mon"
        success_rates = {}

        for teacher_id in self.all_teacher_ids:
            # Find all periods where this teacher teaches on Monday
            teacher_periods = [
                entry for entry in self.timetable
                if entry['teacher_id'] == teacher_id and entry['day_id'] == test_day
            ]

            if not teacher_periods:
                continue  # Teacher doesn't teach on Monday

            # Try to find substitutes for all their periods
            substitutes_found = 0
            for entry in teacher_periods:
                substitute = find_best_substitute_teacher(
                    subject_id=entry['subject_id'],
                    day_id=test_day,
                    period_id=entry['period_id'],
                    class_id=entry['class_id'],
                    timetables=self.timetable,
                    teacher_subjects=self.teacher_subjects,
                    substitute_logs=[],
                    all_teacher_ids=self.all_teacher_ids,
                    absent_teacher_ids=[teacher_id],
                    leave_logs=self.leave_logs,
                    teacher_levels=self.teacher_levels,
                    class_levels=self.class_levels
                )
                if substitute:
                    substitutes_found += 1

            # Calculate success rate for this teacher
            total_periods = len(teacher_periods)
            success_rate = (substitutes_found / total_periods) * 100 if total_periods > 0 else 0
            success_rates[teacher_id] = success_rate

        # Assert that most teachers have good coverage (>70%)
        avg_success_rate = sum(success_rates.values()) / len(success_rates) if success_rates else 0
        self.assertGreater(avg_success_rate, 70.0,
                          f"Average success rate too low: {avg_success_rate:.1f}%")

    def test_high_conflict_scenarios(self):
        """Test substitute assignment with multiple teachers absent"""
        test_day = "Mon"
        # Simulate 3 teachers absent (realistic high-conflict scenario)
        absent_teachers = self.all_teacher_ids[:3]

        # Find all periods needing coverage
        periods_needing_coverage = [
            entry for entry in self.timetable
            if entry['teacher_id'] in absent_teachers and entry['day_id'] == test_day
        ]

        # Assign substitutes
        assignments = assign_substitutes_for_day(
            day_id=test_day,
            timetable=self.timetable,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=[],
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=absent_teachers,
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels
        )

        # Count successes
        substitutes_found = sum(1 for a in assignments if a.get('substitute_teacher_id'))
        total_needed = len(periods_needing_coverage)

        if total_needed > 0:
            success_rate = (substitutes_found / total_needed) * 100
            # In high-conflict scenarios, expect at least 50% coverage
            self.assertGreater(success_rate, 50.0,
                             f"Success rate too low in high-conflict scenario: {success_rate:.1f}%")

        # Verify no double-booking
        substitute_counts = {}
        for assignment in assignments:
            sub_id = assignment.get('substitute_teacher_id')
            if sub_id:
                period = assignment['period_id']
                key = (sub_id, period)
                substitute_counts[key] = substitute_counts.get(key, 0) + 1

        # Assert no substitute is double-booked
        self.assertTrue(all(count == 1 for count in substitute_counts.values()),
                       "Double-booking detected in high-conflict scenario")

    def test_subject_distribution(self):
        """Test substitute assignment across different subjects"""
        test_day = "Mon"
        subject_coverage = defaultdict(lambda: {'total': 0, 'found': 0, 'qualified': 0})

        # Get unique subjects from timetable
        subjects = set(entry['subject_id'] for entry in self.timetable)

        for subject in subjects:
            # Find a teacher who teaches this subject on Monday
            subject_entries = [
                entry for entry in self.timetable
                if entry['subject_id'] == subject and entry['day_id'] == test_day
            ]

            if not subject_entries:
                continue

            # Test substitute finding for this subject
            for entry in subject_entries[:3]:  # Test first 3 instances
                absent_teacher = entry['teacher_id']
                substitute = find_best_substitute_teacher(
                    subject_id=subject,
                    day_id=test_day,
                    period_id=entry['period_id'],
                    class_id=entry['class_id'],
                    timetables=self.timetable,
                    teacher_subjects=self.teacher_subjects,
                    substitute_logs=[],
                    all_teacher_ids=self.all_teacher_ids,
                    absent_teacher_ids=[absent_teacher],
                    leave_logs=self.leave_logs,
                    teacher_levels=self.teacher_levels,
                    class_levels=self.class_levels
                )

                subject_coverage[subject]['total'] += 1
                if substitute:
                    subject_coverage[subject]['found'] += 1
                    # Check if substitute can teach the subject
                    if subject in self.teacher_subjects.get(substitute, []):
                        subject_coverage[subject]['qualified'] += 1

        # Assert that substitutes are found for most subjects
        total_tests = sum(data['total'] for data in subject_coverage.values())
        total_found = sum(data['found'] for data in subject_coverage.values())

        if total_tests > 0:
            overall_rate = (total_found / total_tests) * 100
            self.assertGreater(overall_rate, 60.0,
                             f"Overall substitute finding rate too low: {overall_rate:.1f}%")

    def test_level_matching(self):
        """Test that level matching works correctly"""
        test_day = "Mon"

        # Test elementary level matching
        elementary_classes = [cid for cid, level in self.class_levels.items()
                            if 'elementary' in level]

        if elementary_classes:
            elem_class = elementary_classes[0]
            # Find a period for this class
            elem_entries = [
                e for e in self.timetable
                if e['class_id'] == elem_class and e['day_id'] == test_day
            ]

            if elem_entries:
                entry = elem_entries[0]
                substitute = find_best_substitute_teacher(
                    subject_id=entry['subject_id'],
                    day_id=test_day,
                    period_id=entry['period_id'],
                    class_id=elem_class,
                    timetables=self.timetable,
                    teacher_subjects=self.teacher_subjects,
                    substitute_logs=[],
                    all_teacher_ids=self.all_teacher_ids,
                    absent_teacher_ids=[entry['teacher_id']],
                    leave_logs=self.leave_logs,
                    teacher_levels=self.teacher_levels,
                    class_levels=self.class_levels
                )

                if substitute:
                    # Verify substitute has appropriate level
                    sub_levels = self.teacher_levels.get(substitute, [])
                    class_level = self.class_levels[elem_class]
                    # Should have matching or compatible level
                    self.assertTrue(
                        any('elementary' in level for level in sub_levels),
                        f"Substitute {substitute} assigned to elementary class but doesn't teach elementary"
                    )

        # Test middle school level matching
        middle_classes = [cid for cid, level in self.class_levels.items()
                         if level == 'middle']

        if middle_classes:
            middle_class = middle_classes[0]
            middle_entries = [
                e for e in self.timetable
                if e['class_id'] == middle_class and e['day_id'] == test_day
            ]

            if middle_entries:
                entry = middle_entries[0]
                substitute = find_best_substitute_teacher(
                    subject_id=entry['subject_id'],
                    day_id=test_day,
                    period_id=entry['period_id'],
                    class_id=middle_class,
                    timetables=self.timetable,
                    teacher_subjects=self.teacher_subjects,
                    substitute_logs=[],
                    all_teacher_ids=self.all_teacher_ids,
                    absent_teacher_ids=[entry['teacher_id']],
                    leave_logs=self.leave_logs,
                    teacher_levels=self.teacher_levels,
                    class_levels=self.class_levels
                )

                # If a substitute is found, it should ideally teach middle school
                # (but may be cross-level assigned if no middle school teachers available)
                self.assertIsNotNone(substitute, "Should find some substitute for middle school")

    def test_workload_fairness(self):
        """Test workload distribution over simulated week"""
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        absent_teacher = self.all_teacher_ids[0]  # Pick one teacher to be absent all week

        # Simulate week-long substitution
        all_week_assignments = []
        cumulative_substitute_logs = []

        for day in days:
            day_assignments = assign_substitutes_for_day(
                day_id=day,
                timetable=self.timetable,
                teacher_subjects=self.teacher_subjects,
                substitute_logs=cumulative_substitute_logs,  # Pass cumulative history
                all_teacher_ids=self.all_teacher_ids,
                absent_teacher_ids=[absent_teacher],
                leave_logs=self.leave_logs,
                teacher_levels=self.teacher_levels,
                class_levels=self.class_levels
            )
            all_week_assignments.extend(day_assignments)
            cumulative_substitute_logs.extend(day_assignments)

        # Count substitutions per teacher
        substitution_counts = defaultdict(int)
        for assignment in all_week_assignments:
            sub_id = assignment.get('substitute_teacher_id')
            if sub_id:
                substitution_counts[sub_id] += 1

        if substitution_counts:
            # Calculate variance
            counts = list(substitution_counts.values())
            mean = sum(counts) / len(counts)
            variance = sum((x - mean) ** 2 for x in counts) / len(counts)

            # Variance should be reasonable (not too unbalanced)
            # This is a soft check - we expect some variation but not extreme
            max_count = max(counts)
            min_count = min(counts)

            # The difference between max and min shouldn't be more than 2x the mean
            # (allowing for natural variation based on schedule compatibility)
            self.assertLess(max_count - min_count, mean * 2 + 5,
                          f"Workload distribution too unbalanced: max={max_count}, min={min_count}")

    def test_edge_cases(self):
        """Test graceful handling of edge cases"""
        test_day = "Mon"

        # Edge case 1: Try to find substitute when many teachers are absent
        # (simulate extreme scenario)
        many_absent = self.all_teacher_ids[:len(self.all_teacher_ids) // 2]  # Half the teachers

        # Find a period that needs coverage
        test_entry = next(
            (e for e in self.timetable
             if e['teacher_id'] in many_absent and e['day_id'] == test_day),
            None
        )

        if test_entry:
            # Should not crash, even if no substitute available
            try:
                substitute = find_best_substitute_teacher(
                    subject_id=test_entry['subject_id'],
                    day_id=test_day,
                    period_id=test_entry['period_id'],
                    class_id=test_entry['class_id'],
                    timetables=self.timetable,
                    teacher_subjects=self.teacher_subjects,
                    substitute_logs=[],
                    all_teacher_ids=self.all_teacher_ids,
                    absent_teacher_ids=many_absent,
                    leave_logs=self.leave_logs,
                    teacher_levels=self.teacher_levels,
                    class_levels=self.class_levels
                )
                # Should return None or a valid teacher ID
                self.assertTrue(substitute is None or substitute in self.all_teacher_ids)
            except Exception as e:
                self.fail(f"Function crashed with many teachers absent: {e}")

        # Edge case 2: All qualified teachers busy
        # Find a specialized subject (one with few teachers)
        subject_teacher_counts = defaultdict(set)
        for teacher_id, subjects in self.teacher_subjects.items():
            for subject in subjects:
                subject_teacher_counts[subject].add(teacher_id)

        # Find a subject with only 1-2 teachers
        rare_subject = None
        for subject, teachers in subject_teacher_counts.items():
            if 1 <= len(teachers) <= 2:
                rare_subject = subject
                break

        if rare_subject:
            # Find an entry for this rare subject
            rare_entries = [e for e in self.timetable
                           if e['subject_id'] == rare_subject and e['day_id'] == test_day]
            if rare_entries:
                entry = rare_entries[0]
                # Make all teachers of this subject absent
                absent_specialized = list(subject_teacher_counts[rare_subject])

                try:
                    substitute = find_best_substitute_teacher(
                        subject_id=rare_subject,
                        day_id=test_day,
                        period_id=entry['period_id'],
                        class_id=entry['class_id'],
                        timetables=self.timetable,
                        teacher_subjects=self.teacher_subjects,
                        substitute_logs=[],
                        all_teacher_ids=self.all_teacher_ids,
                        absent_teacher_ids=absent_specialized,
                        leave_logs=self.leave_logs,
                        teacher_levels=self.teacher_levels,
                        class_levels=self.class_levels
                    )
                    # Should either find unqualified substitute or return None gracefully
                    self.assertTrue(substitute is None or substitute in self.all_teacher_ids)
                except Exception as e:
                    self.fail(f"Function crashed with no qualified teachers: {e}")


if __name__ == '__main__':
    unittest.main()
