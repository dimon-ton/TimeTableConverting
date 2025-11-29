"""
Test to demonstrate and verify maximum daily workload constraint

This test verifies that teachers with 4+ periods are not assigned as substitutes.
"""

import unittest
from src.timetable.substitute import find_best_substitute_teacher


class TestWorkloadLimit(unittest.TestCase):
    """Test maximum daily workload enforcement"""

    def setUp(self):
        """Set up test scenario with heavily loaded teacher"""
        # Create a scenario where T001 already has 4 periods on Monday
        self.timetables = [
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 1, "class_id": "ป.1"},
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 2, "class_id": "ป.2"},
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 3, "class_id": "ป.3"},
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 4, "class_id": "ป.4"},
            # T002 is the absent teacher
            {"teacher_id": "T002", "subject_id": "Science", "day_id": "Mon", "period_id": 6, "class_id": "ป.6"},
            # T003 has only 2 periods
            {"teacher_id": "T003", "subject_id": "English", "day_id": "Mon", "period_id": 1, "class_id": "ม.1"},
            {"teacher_id": "T003", "subject_id": "English", "day_id": "Mon", "period_id": 2, "class_id": "ม.2"},
        ]

        self.teacher_subjects = {
            "T001": ["Math", "Science"],  # Can teach Science
            "T002": ["Science"],
            "T003": ["English"],  # Cannot teach Science
        }

        self.teacher_levels = {
            "T001": ["lower_elementary", "upper_elementary"],
            "T002": ["upper_elementary"],
            "T003": ["middle"],
        }

        self.class_levels = {
            "ป.1": "lower_elementary",
            "ป.2": "lower_elementary",
            "ป.3": "lower_elementary",
            "ป.4": "upper_elementary",
            "ป.5": "upper_elementary",
            "ป.6": "upper_elementary",
            "ม.1": "middle",
            "ม.2": "middle",
        }

        self.all_teacher_ids = ["T001", "T002", "T003"]
        self.substitute_logs = []
        self.leave_logs = []

    def test_should_not_assign_teacher_with_4_periods(self):
        """Teacher with 4 periods should NOT be assigned as substitute"""
        # T002 is absent for period 6
        # T001 already has 4 periods on Monday
        # T003 cannot teach Science
        # Expected: Should return T003 (unqualified but under limit)

        result = find_best_substitute_teacher(
            subject_id="Science",
            day_id="Mon",
            period_id=6,
            class_id="ป.6",
            timetables=self.timetables,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=["T002"],
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels
        )

        # T001 should NOT be selected despite being qualified
        # because they already have 4 periods (at the limit)
        if result == "T001":
            # Count T001's periods
            t001_periods = sum(
                1 for entry in self.timetables
                if entry["teacher_id"] == "T001" and entry["day_id"] == "Mon"
            )
            self.fail(
                f"ISSUE FOUND: T001 was assigned as substitute but already has {t001_periods} periods on Monday! "
                f"Teachers should not be assigned when they already have 4+ periods in a day."
            )

        # Expected result: T003 (even if not qualified, has only 2 periods)
        print(f"\nResult: {result}")
        if result:
            # Count periods for selected teacher
            periods = sum(
                1 for entry in self.timetables
                if entry["teacher_id"] == result and entry["day_id"] == "Mon"
            )
            print(f"{result} has {periods} periods on Monday (acceptable: <4)")
            self.assertLess(periods, 4,
                          f"{result} has {periods} periods, should be less than 4")

    def test_teacher_with_3_periods_can_be_assigned(self):
        """Teacher with 3 periods should still be available for assignment"""
        # Modify timetable so T001 only has 3 periods on Monday
        timetables_3_periods = [
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 1, "class_id": "ป.1"},
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 2, "class_id": "ป.2"},
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 3, "class_id": "ป.3"},
            {"teacher_id": "T002", "subject_id": "Science", "day_id": "Mon", "period_id": 6, "class_id": "ป.6"},
            {"teacher_id": "T003", "subject_id": "English", "day_id": "Mon", "period_id": 1, "class_id": "ม.1"},
            {"teacher_id": "T003", "subject_id": "English", "day_id": "Mon", "period_id": 2, "class_id": "ม.2"},
        ]

        result = find_best_substitute_teacher(
            subject_id="Science",
            day_id="Mon",
            period_id=6,
            class_id="ป.6",
            timetables=timetables_3_periods,
            teacher_subjects=self.teacher_subjects,
            substitute_logs=self.substitute_logs,
            all_teacher_ids=self.all_teacher_ids,
            absent_teacher_ids=["T002"],
            leave_logs=self.leave_logs,
            teacher_levels=self.teacher_levels,
            class_levels=self.class_levels
        )

        # T001 should be selected (qualified, level match, only 3 periods)
        # Score: +2 (subject) +5 (level) -6 (3 daily) -1.5 (3 term) = -0.5
        # vs T003: 0 (no subject) -2 (level) -4 (2 daily) -1 (2 term) = -7
        self.assertEqual(result, "T001",
                        "Teacher with 3 periods (qualified, level match) should be selected")


if __name__ == '__main__':
    unittest.main()
