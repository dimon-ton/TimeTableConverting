"""
Diagnostic test to understand scoring behavior
"""

import unittest
from src.timetable.substitute import find_best_substitute_teacher


class TestWorkloadScoring(unittest.TestCase):
    """Diagnostic test to understand scoring"""

    def test_scoring_with_4_periods_vs_2_periods(self):
        """Compare scoring for teachers with different workloads"""

        # T001: 4 periods, qualified (Math, Science), upper_elementary
        # T003: 2 periods, not qualified (English only), middle
        # Need: Science for ป.6 (upper_elementary)

        timetables = [
            # T001 has 4 periods
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 1, "class_id": "ป.1"},
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 2, "class_id": "ป.2"},
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 3, "class_id": "ป.3"},
            {"teacher_id": "T001", "subject_id": "Math", "day_id": "Mon", "period_id": 4, "class_id": "ป.4"},
            # T003 has 2 periods
            {"teacher_id": "T003", "subject_id": "English", "day_id": "Mon", "period_id": 1, "class_id": "ม.1"},
            {"teacher_id": "T003", "subject_id": "English", "day_id": "Mon", "period_id": 2, "class_id": "ม.2"},
            # T002 is absent
            {"teacher_id": "T002", "subject_id": "Science", "day_id": "Mon", "period_id": 6, "class_id": "ป.6"},
        ]

        teacher_subjects = {
            "T001": ["Math", "Science"],
            "T002": ["Science"],
            "T003": ["English"],
        }

        teacher_levels = {
            "T001": ["lower_elementary", "upper_elementary"],
            "T002": ["upper_elementary"],
            "T003": ["middle"],
        }

        class_levels = {
            "ป.1": "lower_elementary",
            "ป.2": "lower_elementary",
            "ป.3": "lower_elementary",
            "ป.4": "upper_elementary",
            "ป.6": "upper_elementary",
            "ม.1": "middle",
            "ม.2": "middle",
        }

        result = find_best_substitute_teacher(
            subject_id="Science",
            day_id="Mon",
            period_id=6,
            class_id="ป.6",
            timetables=timetables,
            teacher_subjects=teacher_subjects,
            substitute_logs=[],
            all_teacher_ids=["T001", "T002", "T003"],
            absent_teacher_ids=["T002"],
            leave_logs=[],
            teacher_levels=teacher_levels,
            class_levels=class_levels
        )

        # Expected scoring:
        # T001: +2 (can teach Science) +5 (level match) -8 (4 periods) -? (term load) = -1 - term_load
        # T003: 0 (cannot teach Science) -2 (level mismatch) -4 (2 periods) -? (term load) = -6 - term_load

        # Assuming similar term loads, T001 should have higher score
        print(f"\nResult: {result}")

        # Let's calculate actual term loads:
        t001_term = sum(1 for e in timetables if e['teacher_id'] == 'T001')
        t003_term = sum(1 for e in timetables if e['teacher_id'] == 'T003')

        print(f"T001: 4 periods (Mon), {t001_term} total periods")
        print(f"  Score components: +2 (subject) +5 (level) -8 (daily) -{t001_term*0.5} (term) = {2+5-8-t001_term*0.5}")

        print(f"T003: 2 periods (Mon), {t003_term} total periods")
        print(f"  Score components: 0 (no subject) -2 (level mismatch) -4 (daily) -{t003_term*0.5} (term) = {0-2-4-t003_term*0.5}")

        # The issue: T001 has 4 term periods, T003 has 2 term periods
        # T001: -1 - 2 = -3
        # T003: -6 - 1 = -7
        # So T001 should win!

        self.assertEqual(result, "T001",
                        f"T001 (qualified, 4 periods, score ~{2+5-8-t001_term*0.5}) should beat "
                        f"T003 (unqualified, 2 periods, score ~{0-2-4-t003_term*0.5})")


if __name__ == '__main__':
    unittest.main()
