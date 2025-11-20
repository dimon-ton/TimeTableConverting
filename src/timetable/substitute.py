import random
from typing import Dict, List, Optional, Set

def find_best_substitute_teacher(
    subject_id: str,
    day_id: str,
    period_id: int,
    class_id: str,
    timetables: List[Dict],
    teacher_subjects: Dict[str, List[str]],
    substitute_logs: List[Dict],
    all_teacher_ids: List[str],
    absent_teacher_ids: List[str],
    leave_logs: List[Dict],
    teacher_levels: Dict[str, List[str]],
    class_levels: Dict[str, str]
) -> Optional[str]:
    """
    Find the best substitute teacher for a given period based on scoring algorithm.

    Scoring criteria:
        +2 points: Teacher can teach the subject (bonus, not required)
        +5 points: Teacher's level matches class level
        -2 points: Level mismatch penalty
        -2 points per period: Daily teaching load
        -1 point per substitution: Historical substitution count
        -0.5 points per period: Total term load (excluding leave days)
        -50 points: Last resort teachers (T006, T010, T018)
        -999 points: Teacher is absent

    Args:
        subject_id: Subject that needs to be taught
        day_id: Day of the week (e.g., "Mon", "Tue")
        period_id: Period number (1-based index)
        class_id: Class identifier (e.g., "ป.1", "ม.1")
        timetables: Regular timetable entries
        teacher_subjects: Mapping of teachers to subjects they can teach
        substitute_logs: Historical substitution records
        all_teacher_ids: List of all available teacher IDs
        absent_teacher_ids: List of absent teacher IDs
        leave_logs: Teacher leave records
        teacher_levels: Teachers' qualified levels (lower_elementary/upper_elementary/middle)
        class_levels: Class level mapping

    Returns:
        Teacher ID of the best substitute, or None if no suitable substitute found

    Raises:
        ValueError: If required parameters are missing or invalid
    """
    # Input validation
    if not subject_id or not day_id or not class_id:
        raise ValueError("subject_id, day_id, and class_id are required")
    if period_id < 1:
        raise ValueError(f"period_id must be >= 1, got {period_id}")
    if timetables is None or teacher_subjects is None:
        raise ValueError("timetables and teacher_subjects are required")

    def is_available(teacher_id: str) -> bool:
        """Check if the teacher is free at that period"""
        for row in timetables + substitute_logs:
            if (
                row["teacher_id"] == teacher_id
                and row["day_id"] == day_id
                and row["period_id"] == period_id
            ):
                return False
        return True

    def calculate_score(teacher_id: str) -> float:
        """
        Calculate suitability score for each teacher.

        Returns:
            Score for the teacher (higher is better, -999 if unavailable)
        """
        if teacher_id in absent_teacher_ids:
            return -999  # Teacher is absent

        score = 0

        # Last resort teachers penalty (Sitisuk, Panisara, Patanasuk)
        last_resort_teachers = ["T006", "T010", "T018"]
        if teacher_id in last_resort_teachers:
            score -= 50

        # Bonus if teacher can teach the subject
        if subject_id in teacher_subjects.get(teacher_id, []):
            score += 2

        # Consider level suitability
        class_level = class_levels.get(class_id)
        teacher_level_list = teacher_levels.get(teacher_id, [])
        if class_level in teacher_level_list:
            score += 5  # bonus for matching level
        else:
            score -= 2  # penalty for mismatch, but still possible

        # Daily load: fewer periods = more chance
        daily_load = sum(
            1
            for row in timetables
            if row["teacher_id"] == teacher_id and row["day_id"] == day_id
        )
        score -= daily_load * 2

        # History load: fewer substitutions = more chance
        history_load = sum(
            1 for row in substitute_logs if row["teacher_id"] == teacher_id
        )
        score -= history_load * 1

        # Exclude leave days from total term load
        leave_days_set = {
            row["day_id"] for row in leave_logs if row["teacher_id"] == teacher_id
        }

        total_term_load = sum(
            1
            for row in timetables
            if row["teacher_id"] == teacher_id and row["day_id"] not in leave_days_set
        )
        score -= total_term_load * 0.5

        return score

    # Collect candidates
    candidates = []
    for teacher_id in all_teacher_ids:
        if is_available(teacher_id):
            score = calculate_score(teacher_id)
            if score > -999:
                candidates.append({"teacher_id": teacher_id, "score": score})

    if not candidates:
        return None

    # Pick the best candidate(s)
    max_score = max(c["score"] for c in candidates)
    top_candidates = [c["teacher_id"] for c in candidates if c["score"] == max_score]

    # Random if tie
    return random.choice(top_candidates)


def assign_substitutes_for_day(
    day_id: str,
    timetable: List[Dict],
    teacher_subjects: Dict[str, List[str]],
    substitute_logs: List[Dict],
    all_teacher_ids: List[str],
    absent_teacher_ids: List[str],
    leave_logs: List[Dict],
    teacher_levels: Dict[str, List[str]],
    class_levels: Dict[str, str]
) -> List[Dict]:
    """
    Assign substitutes for all absent teachers in a given day.

    This function iterates through all timetable entries for the given day
    and finds substitutes for periods where the assigned teacher is absent.
    Newly assigned substitutes are tracked to prevent double-booking.

    Args:
        day_id: Day of the week (e.g., "Mon", "Tue")
        timetable: Regular timetable entries
        teacher_subjects: Mapping of teachers to subjects they can teach
        substitute_logs: Historical substitution records
        all_teacher_ids: List of all available teacher IDs
        absent_teacher_ids: List of absent teacher IDs
        leave_logs: Teacher leave records
        teacher_levels: Teachers' qualified levels (lower_elementary/upper_elementary/middle)
        class_levels: Class level mapping

    Returns:
        List of newly assigned substitute entries in timetable format
    """
    new_substitutes = []
    for row in timetable:
        if row["day_id"] == day_id and row["teacher_id"] in absent_teacher_ids:
            absent_teacher = row["teacher_id"]  # Store the absent teacher ID
            subject_id = row["subject_id"]
            period_id = row["period_id"]
            class_id = row["class_id"]

            substitute = find_best_substitute_teacher(
                subject_id,
                day_id,
                period_id,
                class_id,
                timetable,
                teacher_subjects,
                substitute_logs + new_substitutes,
                all_teacher_ids,
                absent_teacher_ids,
                leave_logs,
                teacher_levels,
                class_levels,
            )

            # Always log the absence, even if no substitute found
            new_substitutes.append(
                {
                    "teacher_id": absent_teacher,  # Absent teacher (not substitute)
                    "subject_id": subject_id,
                    "day_id": day_id,
                    "period_id": period_id,
                    "class_id": class_id,
                    "substitute_teacher": substitute if substitute else None,  # Separate field
                }
            )

    return new_substitutes
