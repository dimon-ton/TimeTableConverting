"""
Build Teacher Data Files

This script analyzes real_timetable.json and generates data files needed for
the leave processing system:
- teacher_subjects.json: Maps teacher IDs to subjects they can teach
- teacher_levels.json: Maps teacher IDs to levels they can teach
- class_levels.json: Maps class IDs to their level category
- teacher_name_map.json: Maps Thai teacher names to teacher IDs
- teacher_full_names.json: Maps teacher IDs to full display names (editable)

Usage:
    python build_teacher_data.py
"""

import json
from typing import Dict, List, Set
from collections import defaultdict

from src.config import config


# Import teacher name mapping from excel_converting.py
TEACHER_NAME_MAP = {
    "ครูสุกฤษฎิ์": "T001",
    "ครูอำพร": "T002",
    "ครูกฤตชยากร": "T003",
    "ครูพิมล": "T004",
    "ครูสุจิตร": "T005",
    "ครูปาณิสรา": "T006",
    "ครูวิยะดา": "T007",
    "ครูดวงใจ": "T008",
    "ครูสุขุมาภรณ์": "T009",
    "ครูพัฒนศักดิ์": "T010",
    "ครูบัวลอย": "T011",
    "ครูอภิชญา": "T012",
    "ครูสรัญญา": "T013",
    "ครูณัฏฐเศรษฐาวิชญ์": "T014",
    "ครูจุฑารัตน์": "T015",
    "ครูจิตยาภรณ์": "T016",
    "ครูจรรยาภรณ์": "T017",
    "ครูสิทธิศักดิ์": "T018"
}


def classify_class_level(class_id: str) -> str:
    """
    Classify a class ID into its level category.

    Args:
        class_id: Class identifier (e.g., "ป.1", "ป.4", "ม.1")

    Returns:
        Level category: "lower_elementary", "upper_elementary", or "middle"
    """
    # Extract grade number
    if class_id.startswith("ป."):
        grade = int(class_id[2:])
        if grade <= 3:
            return "lower_elementary"  # Grades 1-3
        else:
            return "upper_elementary"  # Grades 4-6
    elif class_id.startswith("ม."):
        return "middle"  # Grades 7-9
    else:
        return "unknown"


def build_teacher_data(timetable_file: str = None):
    """
    Build all teacher data files from the timetable.

    Args:
        timetable_file: Path to the timetable JSON file (uses config default if None)
    """
    if timetable_file is None:
        timetable_file = config.TIMETABLE_FILE

    print("="*60)
    print("Building Teacher Data Files")
    print("="*60)

    # Load timetable
    print(f"\n1. Loading timetable from {timetable_file}...")
    try:
        with open(timetable_file, 'r', encoding='utf-8') as f:
            timetable = json.load(f)
        print(f"   OK - Loaded {len(timetable)} entries")
    except FileNotFoundError:
        print(f"   ERROR: File not found: {timetable_file}")
        return
    except json.JSONDecodeError as e:
        print(f"   ERROR: Invalid JSON: {e}")
        return

    # Initialize data structures
    teacher_subjects = defaultdict(set)
    teacher_classes = defaultdict(set)
    teacher_levels = defaultdict(set)
    class_levels = {}

    # Analyze timetable
    print("\n2. Analyzing timetable data...")
    for entry in timetable:
        teacher_id = entry['teacher_id']
        subject_id = entry['subject_id']
        class_id = entry['class_id']

        # Track subjects per teacher
        teacher_subjects[teacher_id].add(subject_id)

        # Track classes per teacher
        teacher_classes[teacher_id].add(class_id)

        # Classify class level
        if class_id not in class_levels:
            class_levels[class_id] = classify_class_level(class_id)

        # Track levels per teacher
        level = class_levels[class_id]
        teacher_levels[teacher_id].add(level)

    # Convert sets to sorted lists for JSON
    teacher_subjects_dict = {
        teacher: sorted(list(subjects))
        for teacher, subjects in teacher_subjects.items()
    }

    teacher_levels_dict = {
        teacher: sorted(list(levels))
        for teacher, levels in teacher_levels.items()
    }

    # Create teacher_full_names.json with placeholders
    # Admin should edit this file to add surnames
    print("\n3. Creating teacher name mappings...")

    # Reverse mapping: ID → Thai name
    id_to_thai_name = {v: k for k, v in TEACHER_NAME_MAP.items()}

    # Full names - use Thai name as default, admin should edit to add surnames
    teacher_full_names = {}
    for teacher_id in teacher_subjects_dict.keys():
        thai_name = id_to_thai_name.get(teacher_id, f"ครู{teacher_id}")
        # Default format: just the first name
        # Admin should edit this file to add surnames, e.g., "ครูสุกฤษฎิ์ ใจดี"
        teacher_full_names[teacher_id] = thai_name

    # Statistics
    print(f"   Teachers found: {len(teacher_subjects_dict)}")
    print(f"   Unique subjects: {len(set(s for subj in teacher_subjects_dict.values() for s in subj))}")
    print(f"   Classes found: {len(class_levels)}")

    # Save files
    print("\n4. Saving data files...")

    # teacher_subjects.json
    with open(config.TEACHER_SUBJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(teacher_subjects_dict, f, ensure_ascii=False, indent=2)
    print(f"   OK {config.TEACHER_SUBJECTS_FILE}")

    # teacher_levels.json
    with open(config.TEACHER_LEVELS_FILE, 'w', encoding='utf-8') as f:
        json.dump(teacher_levels_dict, f, ensure_ascii=False, indent=2)
    print(f"   OK {config.TEACHER_LEVELS_FILE}")

    # class_levels.json
    with open(config.CLASS_LEVELS_FILE, 'w', encoding='utf-8') as f:
        json.dump(class_levels, f, ensure_ascii=False, indent=2)
    print(f"   OK {config.CLASS_LEVELS_FILE}")

    # teacher_name_map.json (Thai name → ID)
    with open(config.TEACHER_NAME_MAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(TEACHER_NAME_MAP, f, ensure_ascii=False, indent=2)
    print(f"   OK {config.TEACHER_NAME_MAP_FILE}")

    # teacher_full_names.json (ID → Full display name)
    with open(config.TEACHER_FULL_NAMES_FILE, 'w', encoding='utf-8') as f:
        json.dump(teacher_full_names, f, ensure_ascii=False, indent=2)
    print(f"   OK {config.TEACHER_FULL_NAMES_FILE}")

    # Display sample data
    print("\n5. Sample data:")
    print("\n   Teacher Subjects (first 3):")
    for i, (teacher, subjects) in enumerate(list(teacher_subjects_dict.items())[:3]):
        print(f"      {teacher}: {', '.join(subjects)}")

    print("\n   Teacher Levels (first 3):")
    for i, (teacher, levels) in enumerate(list(teacher_levels_dict.items())[:3]):
        print(f"      {teacher}: {', '.join(levels)}")

    print("\n   Class Levels (first 6):")
    for i, (class_id, level) in enumerate(list(class_levels.items())[:6]):
        print(f"      {class_id}: {level}")

    print("\n" + "="*60)
    print("SUCCESS! All data files created")
    print("="*60)

    print("\nIMPORTANT: Edit teacher_full_names.json to add surnames")
    print("   Current format: \"ครูสุกฤษฎิ์\"")
    print("   Should be: \"ครูสุกฤษฎิ์ ใจดี\" (add surname)")
    print("   This will be used in LINE reports for better readability")

    print("\nNext steps:")
    print("1. Review and edit teacher_full_names.json")
    print("2. Verify teacher_subjects.json for accuracy")
    print("3. Run create_leave_requests_tab.py to set up Google Sheets")


if __name__ == "__main__":
    build_teacher_data()
