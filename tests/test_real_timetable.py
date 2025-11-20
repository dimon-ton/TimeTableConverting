"""
Test script for real timetable data with simulated teacher absence
"""
import json
from collections import defaultdict
from src.timetable.substitute import find_best_substitute_teacher, assign_substitutes_for_day
from src.config import config


def load_real_timetable(filename):
    """Load timetable from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_timetable(timetable):
    """Analyze timetable to build teacher and class mappings"""
    teacher_subjects = defaultdict(set)
    teacher_levels = defaultdict(set)
    class_levels = {}
    teacher_schedules = defaultdict(lambda: defaultdict(list))

    for entry in timetable:
        teacher_id = entry['teacher_id']
        subject_id = entry['subject_id']
        class_id = entry['class_id']
        day_id = entry['day_id']
        period_id = entry['period_id']

        # Build teacher-subject mapping
        teacher_subjects[teacher_id].add(subject_id)

        # Determine level from class_id
        if class_id.startswith('ป.'):
            # Split elementary into lower (ป.1-3) and upper (ป.4-6)
            grade = class_id.replace('ป.', '')
            if grade in ['1', '2', '3']:
                level = 'lower_elementary'
            else:  # 4, 5, 6
                level = 'upper_elementary'
        elif class_id.startswith('ม.'):
            level = 'middle'
        else:
            level = 'lower_elementary'  # default

        teacher_levels[teacher_id].add(level)
        class_levels[class_id] = level

        # Track teacher's schedule
        teacher_schedules[teacher_id][day_id].append({
            'period': period_id,
            'class': class_id,
            'subject': subject_id
        })

    # Convert sets to lists for compatibility with find_substitute
    teacher_subjects = {k: list(v) for k, v in teacher_subjects.items()}
    teacher_levels = {k: list(v) for k, v in teacher_levels.items()}

    return teacher_subjects, teacher_levels, class_levels, teacher_schedules


def print_teacher_schedule(teacher_id, day, schedule_info):
    """Pretty print a teacher's schedule for a day"""
    print(f"\n{'='*70}")
    print(f"Schedule for {teacher_id} on {day}:")
    print(f"{'='*70}")

    if not schedule_info:
        print("  No classes scheduled")
        return

    # Sort by period
    sorted_schedule = sorted(schedule_info, key=lambda x: x['period'])

    for slot in sorted_schedule:
        print(f"  Period {slot['period']}: {slot['subject']:15s} | Class: {slot['class']}")


def main():
    print("="*70)
    print("REAL TIMETABLE SUBSTITUTE TESTING")
    print("="*70)

    # Load real timetable
    print("\n[1] Loading real timetable data...")
    timetable = load_real_timetable(config.TIMETABLE_FILE)
    print(f"    Loaded {len(timetable)} timetable entries")

    # Analyze timetable
    print("\n[2] Analyzing timetable structure...")
    teacher_subjects, teacher_levels, class_levels, teacher_schedules = analyze_timetable(timetable)
    print(f"    Found {len(teacher_subjects)} teachers")
    print(f"    Found {len(class_levels)} classes")
    print(f"    Teachers teaching multiple levels: {sum(1 for levels in teacher_levels.values() if len(levels) > 1)}")

    # Find a teacher with a busy schedule for testing
    print("\n[3] Selecting a teacher to simulate absence...")

    # Let's pick a teacher with multiple classes on Monday
    test_day = "Mon"
    busy_teachers = [(t, len(schedule[test_day]))
                     for t, schedule in teacher_schedules.items()
                     if test_day in schedule]
    busy_teachers.sort(key=lambda x: x[1], reverse=True)

    if not busy_teachers:
        print("    ERROR: No teachers found with classes on Monday")
        return

    absent_teacher = busy_teachers[0][0]
    num_classes = busy_teachers[0][1]

    print(f"    Selected: {absent_teacher} (has {num_classes} periods on {test_day})")
    print(f"    Subjects they teach: {', '.join(teacher_subjects[absent_teacher])}")
    print(f"    Levels: {', '.join(teacher_levels[absent_teacher])}")

    # Show absent teacher's schedule
    print_teacher_schedule(absent_teacher, test_day, teacher_schedules[absent_teacher][test_day])

    # Get all periods where absent teacher is scheduled
    print(f"\n[4] Finding substitutes for {absent_teacher}'s {test_day} classes...")
    absent_periods = [entry for entry in timetable
                     if entry['teacher_id'] == absent_teacher and entry['day_id'] == test_day]

    leave_logs = []  # Empty for this test, but you could add historical data here

    # Get all teacher IDs
    all_teacher_ids = list(teacher_subjects.keys())

    # Find substitutes for each period
    substitutes_found = []
    substitutes_not_found = []
    substitute_logs = []  # Track new assignments to prevent double-booking

    print(f"\n{'='*70}")
    print("SUBSTITUTE ASSIGNMENT RESULTS")
    print(f"{'='*70}")

    for i, period_entry in enumerate(sorted(absent_periods, key=lambda x: x['period_id']), 1):
        period = period_entry['period_id']
        class_id = period_entry['class_id']
        subject = period_entry['subject_id']

        print(f"\n[Period {period}] {subject} for {class_id}")
        print("-" * 70)

        substitute = find_best_substitute_teacher(
            subject_id=subject,
            day_id=test_day,
            period_id=period,
            class_id=class_id,
            timetables=timetable,
            teacher_subjects=teacher_subjects,
            substitute_logs=substitute_logs,
            all_teacher_ids=all_teacher_ids,
            absent_teacher_ids=[absent_teacher],
            leave_logs=leave_logs,
            teacher_levels=teacher_levels,
            class_levels=class_levels
        )

        # Add to substitute logs to prevent double-booking
        if substitute:
            substitute_logs.append({
                'teacher_id': substitute,
                'day_id': test_day,
                'period_id': period,
                'class_id': class_id,
                'subject_id': subject
            })

        if substitute:
            substitutes_found.append({
                'period': period,
                'class': class_id,
                'subject': subject,
                'substitute': substitute
            })
            print(f"  [OK] SUBSTITUTE FOUND: {substitute}")
            print(f"       - Teaches: {', '.join(teacher_subjects[substitute])}")
            print(f"       - Levels: {', '.join(teacher_levels[substitute])}")

            # Check if substitute can teach the subject
            can_teach = subject in teacher_subjects[substitute]
            level_match = class_levels[class_id] in teacher_levels[substitute]
            print(f"       - Can teach {subject}: {'Yes' if can_teach else 'No (assigned anyway)'}")
            print(f"       - Level match: {'Yes' if level_match else 'No (cross-level assignment)'}")
        else:
            substitutes_not_found.append({
                'period': period,
                'class': class_id,
                'subject': subject
            })
            print(f"  [X] NO SUBSTITUTE AVAILABLE")
            print(f"      (All teachers are busy or no one can teach {subject})")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total periods needing coverage: {len(absent_periods)}")
    print(f"Substitutes found: {len(substitutes_found)}")
    print(f"No substitute available: {len(substitutes_not_found)}")
    print(f"Success rate: {len(substitutes_found)/len(absent_periods)*100:.1f}%")

    if substitutes_found:
        print(f"\n{'='*70}")
        print("FINAL SUBSTITUTE ASSIGNMENTS")
        print(f"{'='*70}")
        for sub in substitutes_found:
            print(f"Period {sub['period']}: {sub['substitute']:8s} -> {sub['subject']:15s} for {sub['class']}")

    # Test the batch assignment function
    print(f"\n{'='*70}")
    print("TESTING BATCH ASSIGNMENT FUNCTION")
    print(f"{'='*70}")

    assignments = assign_substitutes_for_day(
        day_id=test_day,
        timetable=timetable,
        teacher_subjects=teacher_subjects,
        substitute_logs=[],  # Fresh start for batch function
        all_teacher_ids=all_teacher_ids,
        absent_teacher_ids=[absent_teacher],
        leave_logs=leave_logs,
        teacher_levels=teacher_levels,
        class_levels=class_levels
    )

    print(f"\nBatch function assigned {len(assignments)} substitutes:")
    for assignment in assignments:
        print(f"  {assignment['teacher_id']:8s} -> Period {assignment['period_id']}: "
              f"{assignment['subject_id']:15s} for {assignment['class_id']}")


if __name__ == '__main__':
    main()
