"""
Unit tests for find_substitute.py

Run with: python -m pytest test_find_substitute.py -v
Or: python test_find_substitute.py
"""

import unittest
from find_substitute import find_best_substitute_teacher, assign_substitutes_for_day


class TestFindBestSubstituteTeacher(unittest.TestCase):
    """Test cases for find_best_substitute_teacher function"""

    def setUp(self):
        """Set up test data"""
        # Sample timetable
        self.timetables = [
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 1, "class_id": "ป.1"},
            {"teacher_id": "T002", "subject_id": "Science", "day_id": "Mon", "period_id": 1, "class_id": "ป.2"},
            {"teacher_id": "T003", "subject_id": "English", "day_id": "Mon", "period_id": 2, "class_id": "ป.1"},
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 3, "class_id": "ป.3"},
        ]

        # Teacher qualifications
        self.teacher_subjects = {
            "T001": ["Math", "Science"],
            "T002": ["Science", "Physics"],
            "T003": ["English", "Thai"],
            "T004": ["Math", "English"],
            "T005": ["Math", "Science"],
        }

        # Teacher levels
        self.teacher_levels = {
            "T001": ["elementary"],
            "T002": ["elementary", "middle"],
            "T003": ["elementary"],
            "T004": ["middle"],
            "T005": ["elementary"],
        }

        # Class levels
        self.class_levels = {
            "ป.1": "elementary",
            "ป.2": "elementary",
            "ป.3": "elementary",
            "ม.1": "middle",
            "ม.2": "middle",
        }

        self.all_teacher_ids = ["T001", "T002", "T003", "T004", "T005"]
        self.substitute_logs = []
        self.leave_logs = []

    def test_find_substitute_basic(self):
        """Test finding a substitute for a basic scenario"""
        # T001 is absent, need substitute for Math period
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
            class_levels=self.class_levels,
        )

        # Should return T004 or T005 (both can teach Math and are available)
        self.assertIn(result, ["T004", "T005"])

    def test_absent_teacher_not_selected(self):
        """Test that absent teachers are not selected as substitutes"""
        result = find_best_substitute_teacher(
            subject_id="Math",
            day_id="Mon",
            period_id=1,
            class_id="ป.1",
            timetables=self.timetables,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=["T001", "T004"],  # Both Math teachers absent
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels,
        )

        # Should return T005 (only remaining Math teacher)
        self.assertEqual(result, "T005")

    def test_teacher_already_teaching(self):
        """Test that teachers already teaching are not selected"""
        result = find_best_substitute_teacher(
            subject_id="Science",
            day_id="Mon",
            period_id=1,  # T002 already teaches at this period
            class_id="ป.1",
            timetables=self.timetables,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=["T001"],
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels,
        )

        # T002 is already teaching at period 1, so should select T005
        self.assertEqual(result, "T005")

    def test_no_qualified_substitute(self):
        """Test when no qualified substitute is available"""
        result = find_best_substitute_teacher(
            subject_id="History",  # No teacher can teach History
            day_id="Mon",
            period_id=1,
            class_id="ป.1",
            timetables=self.timetables,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=[],
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels,
        )

        # Should return None (no one can teach History)
        self.assertIsNone(result)

    def test_level_matching_preference(self):
        """Test that teachers with matching levels are preferred"""
        result = find_best_substitute_teacher(
            subject_id="Math",
            day_id="Mon",
            period_id=2,  # Free period for most teachers
            class_id="ม.1",  # Middle school class
            timetables=self.timetables,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=[],
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels,
        )

        # T004 is the only one with middle school level, should be preferred
        self.assertEqual(result, "T004")

    def test_workload_balancing(self):
        """Test that substitution history affects selection"""
        # Add history showing T004 has substituted many times
        substitute_logs = [
            {"teacher_id": "T004", "subject_id": "Math", "day_id": "Tue", "period_id": 1, "class_id": "ป.1"},
            {"teacher_id": "T004", "subject_id": "Math", "day_id": "Wed", "period_id": 1, "class_id": "ป.2"},
            {"teacher_id": "T004", "subject_id": "Math", "day_id": "Thu", "period_id": 1, "class_id": "ป.3"},
        ]

        result = find_best_substitute_teacher(
            subject_id="Math",
            day_id="Mon",
            period_id=2,
            class_id="ป.1",
            timetables=self.timetables,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=[],
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels,
        )

        # T005 should be preferred over T004 due to lower substitution history
        self.assertEqual(result, "T005")

    def test_invalid_input_validation(self):
        """Test input validation"""
        with self.assertRaises(ValueError):
            find_best_substitute_teacher(
                subject_id="",  # Empty subject
                day_id="Mon",
                period_id=1,
                class_id="ป.1",
                timetables=self.timetables,
                teacher_subjects=self.teacher_subjects,
                substitute_logs=self.substitute_logs,
                all_teacher_ids=self.all_teacher_ids,
                absent_teacher_ids=[],
                leave_logs=self.leave_logs,
                teacher_levels=self.teacher_levels,
                class_levels=self.class_levels,
            )

        with self.assertRaises(ValueError):
            find_best_substitute_teacher(
                subject_id="Math",
                day_id="Mon",
                period_id=0,  # Invalid period
                class_id="ป.1",
                timetables=self.timetables,
                teacher_subjects=self.teacher_subjects,
                substitute_logs=self.substitute_logs,
                all_teacher_ids=self.all_teacher_ids,
                absent_teacher_ids=[],
                leave_logs=self.leave_logs,
                teacher_levels=self.teacher_levels,
                class_levels=self.class_levels,
            )


class TestAssignSubstitutesForDay(unittest.TestCase):
    """Test cases for assign_substitutes_for_day function"""

    def setUp(self):
        """Set up test data"""
        self.timetables = [
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 1, "class_id": "ป.1"},
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 2, "class_id": "ป.2"},
            {"teacher_id": "T002", "subject_id": "Science", "day_id": "Mon", "period_id": 1, "class_id": "ป.3"},
        ]

        self.teacher_subjects = {
            "T001": ["Math"],
            "T002": ["Science"],
            "T003": ["Math", "Science"],
            "T004": ["Math", "Science"],
        }

        self.teacher_levels = {
            "T001": ["elementary"],
            "T002": ["elementary"],
            "T003": ["elementary"],
            "T004": ["elementary"],
        }

        self.class_levels = {
            "ป.1": "elementary",
            "ป.2": "elementary",
            "ป.3": "elementary",
        }

        self.all_teacher_ids = ["T001", "T002", "T003", "T004"]
        self.substitute_logs = []
        self.leave_logs = []

    def test_assign_substitutes_single_absent(self):
        """Test assigning substitutes when one teacher is absent"""
        result = assign_substitutes_for_day(
            day_id="Mon",
            timetable=self.timetables,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=["T001"],
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels,
        )

        # Should have 2 substitutes (T001 teaches 2 periods on Monday)
        self.assertEqual(len(result), 2)

        # All substitutes should be for Monday
        for sub in result:
            self.assertEqual(sub["day_id"], "Mon")

        # All substitutes should be different from absent teacher
        for sub in result:
            self.assertNotEqual(sub["teacher_id"], "T001")

    def test_assign_substitutes_multiple_absent(self):
        """Test assigning substitutes when multiple teachers are absent"""
        result = assign_substitutes_for_day(
            day_id="Mon",
            timetable=self.timetables,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=["T001", "T002"],
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels,
        )

        # Should have 3 substitutes (all Monday periods)
        self.assertEqual(len(result), 3)

        # Check that no substitute is assigned to an absent teacher
        for sub in result:
            self.assertNotIn(sub["teacher_id"], ["T001", "T002"])

    def test_no_double_booking(self):
        """Test that substitutes are not double-booked"""
        result = assign_substitutes_for_day(
            day_id="Mon",
            timetable=self.timetables,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=["T001", "T002"],
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels,
        )

        # Check for double-booking at period 1
        period_1_subs = [s for s in result if s["period_id"] == 1]
        teachers_at_period_1 = [s["teacher_id"] for s in period_1_subs]

        # Should not have duplicate teachers at same period
        self.assertEqual(len(teachers_at_period_1), len(set(teachers_at_period_1)))


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    print("Running tests for find_substitute.py...")
    print("=" * 70)
    run_tests()
