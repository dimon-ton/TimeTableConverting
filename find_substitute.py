import random

def find_best_substitute_teacher(
    subject_id,
    day_id,
    period_id,
    class_id,
    timetables,
    teacher_subjects,
    substitute_logs,
    all_teacher_ids,
    absent_teacher_ids,
    leave_logs,
    teacher_levels,
    class_levels
):
    def is_available(teacher_id):
        """Check if the teacher is free at that period"""
        for row in timetables + substitute_logs:
            if (
                row["teacher_id"] == teacher_id
                and row["day_id"] == day_id
                and row["period_id"] == period_id
            ):
                return False
        return True

    def calculate_score(teacher_id):
        """Calculate suitability score for each teacher"""
        if teacher_id in absent_teacher_ids:
            return -999  # Teacher is absent

        score = 0

        # Teacher must be able to teach the subject
        if subject_id in teacher_subjects.get(teacher_id, []):
            score += 10
        else:
            return -999  # Not qualified for subject

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
    day_id,
    timetable,
    teacher_subjects,
    substitute_logs,
    all_teacher_ids,
    absent_teacher_ids,
    leave_logs,
    teacher_levels,
    class_levels
):
    """Assign substitutes for all absent teachers in a given day"""
    new_substitutes = []
    for row in timetable:
        if row["day_id"] == day_id and row["teacher_id"] in absent_teacher_ids:
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

            if substitute:
                new_substitutes.append(
                    {
                        "teacher_id": substitute,
                        "subject_id": subject_id,
                        "day_id": day_id,
                        "period_id": period_id,
                        "class_id": class_id,
                    }
                )

    return new_substitutes
