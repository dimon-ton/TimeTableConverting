"""
Process Daily Leave Requests

Main orchestration script that:
1. Reads leave requests for a specific date from Google Sheets
2. Finds substitute teachers for each absence
3. Updates Google Sheets with substitute assignments
4. Generates a summary report

Usage:
    # Process today's leaves
    python process_daily_leaves.py

    # Process specific date
    python process_daily_leaves.py 2025-11-21

    # Process and send to LINE
    python process_daily_leaves.py --send-line

    # Test mode (read-only, no Sheets update)
    python process_daily_leaves.py --test
"""

import json
import sys
from datetime import datetime, date
from typing import Dict, List, Tuple
from collections import defaultdict

from src.config import config
from src.utils.leave_log_sync import get_sheets_client, load_leave_logs_from_sheets
from src.timetable.substitute import assign_substitutes_for_day


def load_data_files() -> Tuple[List[Dict], Dict, Dict, Dict, Dict]:
    """
    Load all required data files for substitute finding.

    Returns:
        Tuple of (timetable, teacher_subjects, teacher_levels, class_levels, teacher_full_names)

    Raises:
        FileNotFoundError: If any required file is missing
        json.JSONDecodeError: If any file contains invalid JSON
    """
    print("Loading data files...")

    # Load timetable
    with open(config.TIMETABLE_FILE, 'r', encoding='utf-8') as f:
        timetable = json.load(f)
    print(f"  OK Loaded {len(timetable)} timetable entries")

    # Load teacher subjects
    with open(config.TEACHER_SUBJECTS_FILE, 'r', encoding='utf-8') as f:
        teacher_subjects = json.load(f)
    print(f"  OK Loaded {len(teacher_subjects)} teachers' subject mappings")

    # Load teacher levels
    with open(config.TEACHER_LEVELS_FILE, 'r', encoding='utf-8') as f:
        teacher_levels = json.load(f)
    print(f"  OK Loaded {len(teacher_levels)} teachers' level mappings")

    # Load class levels
    with open(config.CLASS_LEVELS_FILE, 'r', encoding='utf-8') as f:
        class_levels = json.load(f)
    print(f"  OK Loaded {len(class_levels)} class level mappings")

    # Load teacher full names
    with open(config.TEACHER_FULL_NAMES_FILE, 'r', encoding='utf-8') as f:
        teacher_full_names = json.load(f)
    print(f"  OK Loaded {len(teacher_full_names)} teacher names")

    return timetable, teacher_subjects, teacher_levels, class_levels, teacher_full_names


def get_leaves_for_date(target_date: str) -> List[Dict]:
    """
    Get all leave requests for a specific date from Google Sheets.

    Args:
        target_date: Date string in YYYY-MM-DD format

    Returns:
        List of leave log entries for the specified date
    """
    print(f"\nFetching leave requests for {target_date}...")

    # Load all leave logs from Sheets
    all_leaves = load_leave_logs_from_sheets()

    # Filter for target date
    leaves_for_date = [
        leave for leave in all_leaves
        if leave.get('date') == target_date
    ]

    print(f"  Found {len(leaves_for_date)} leave entries for {target_date}")

    return leaves_for_date


def group_leaves_by_day(leaves: List[Dict]) -> Dict[str, List[str]]:
    """
    Group leave entries by day and extract absent teacher IDs.

    Args:
        leaves: List of leave log entries

    Returns:
        Dictionary mapping day_id to list of absent teacher IDs
    """
    absent_by_day = defaultdict(set)

    for leave in leaves:
        day_id = leave['day_id']
        teacher_id = leave['teacher_id']
        absent_by_day[day_id].add(teacher_id)

    # Convert sets to lists
    return {day: list(teachers) for day, teachers in absent_by_day.items()}


def update_sheets_with_substitutes(substitutes: List[Dict], target_date: str, test_mode: bool = False):
    """
    Update Google Sheets with substitute teacher assignments.

    Args:
        substitutes: List of substitute assignments
        target_date: Date string in YYYY-MM-DD format
        test_mode: If True, skip actual Sheets update (read-only)
    """
    if test_mode:
        print("\nTEST MODE: Skipping Sheets update")
        return

    if not substitutes:
        print("\nNo substitutes to update in Sheets")
        return

    print(f"\nUpdating Google Sheets with {len(substitutes)} substitute assignments...")

    try:
        # Get Sheets client
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)

        # Get all current data
        all_data = worksheet.get_all_values()
        headers = all_data[0] if all_data else []

        # Find rows that match our target date and need substitute updates
        updates_made = 0
        for sub in substitutes:
            # Find matching row in Sheet
            # Match on: Date, Absent Teacher, Day, Period, Class
            for row_idx, row in enumerate(all_data[1:], start=2):  # Start from row 2 (skip header)
                if len(row) < 7:  # Ensure row has enough columns
                    continue

                # Parse row data
                row_date = row[0] if len(row) > 0 else ''
                row_teacher = row[1] if len(row) > 1 else ''
                row_day = row[2] if len(row) > 2 else ''
                row_period = row[3] if len(row) > 3 else ''
                row_class = row[4] if len(row) > 4 else ''

                # Match criteria
                if (row_date == target_date and
                    row_teacher == sub['teacher_id'] and
                    row_day == sub['day_id'] and
                    str(row_period) == str(sub['period_id']) and
                    row_class == sub['class_id']):

                    # Update substitute teacher column (column 7)
                    substitute_teacher = sub.get('substitute_teacher', 'No substitute found')
                    worksheet.update_cell(row_idx, 7, substitute_teacher)
                    updates_made += 1

        print(f"  OK Updated {updates_made} rows in Google Sheets")

    except Exception as e:
        print(f"  ERROR updating Sheets: {e}")
        raise


def generate_report(
    target_date: str,
    leaves: List[Dict],
    substitutes: List[Dict],
    absent_by_day: Dict[str, List[str]],
    teacher_full_names: Dict[str, str]
) -> str:
    """
    Generate a text summary report of substitute assignments in Thai.

    Args:
        target_date: Date string in YYYY-MM-DD format
        leaves: Original leave requests
        substitutes: Substitute assignments
        absent_by_day: Dictionary mapping day to absent teacher IDs
        teacher_full_names: Mapping of teacher IDs to display names

    Returns:
        Formatted report string
    """
    # Import subject map and create a reverse mapping from English ID to Thai name
    from src.timetable.converter import subject_map
    reverse_subject_map = {v: k for k, v in subject_map.items()}

    # Thai month names for date formatting
    thai_months = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    # Mapping from English day abbreviation to full Thai day name
    day_map_thai = {"Mon": "วันจันทร์", "Tue": "วันอังคาร", "Wed": "วันพุธ", "Thu": "วันพฤหัสบดี", "Fri": "วันศุกร์"}

    # Convert and format the date string to Thai format
    try:
        date_obj = datetime.strptime(target_date, '%Y-%m-%d')
        thai_date_str = f"{date_obj.day} {thai_months[date_obj.month - 1]} {date_obj.year + 543}"
    except ValueError:
        thai_date_str = target_date # Fallback to original if format is unexpected

    # --- Build Report ---
    report_lines = []
    report_lines.append("📝 รายงานผลการจัดหาครูสอนแทน 📝")
    report_lines.append(f"ประจำวันที่ {thai_date_str}")
    report_lines.append("="*30)

    if not leaves:
        report_lines.append("\nไม่มีข้อมูลการลาในวันที่ระบุ")
        return "\n".join(report_lines)

    # Summary Section
    total_absent = len(set(leave['teacher_id'] for leave in leaves))
    total_periods = len(leaves)
    found_substitutes = sum(1 for sub in substitutes if sub.get('substitute_teacher'))
    success_rate = (found_substitutes / total_periods * 100) if total_periods > 0 else 0

    report_lines.append("\nสรุปผล:")
    report_lines.append(f"👩‍🏫 ครูที่ลา: {total_absent} ท่าน")
    report_lines.append(f"📚 จำนวนคาบทั้งหมด: {total_periods} คาบ")
    report_lines.append(f"✅ หาครูสอนแทนได้: {found_substitutes} คาบ ({success_rate:.1f}%)")

    # Detailed Assignments Section
    report_lines.append("\nตารางสอนแทน:")

    for day_id in sorted(absent_by_day.keys()):
        day_name_thai = day_map_thai.get(day_id, day_id)
        report_lines.append(f"\n{day_name_thai}:")

        day_subs = [s for s in substitutes if s['day_id'] == day_id]
        if not day_subs:
            report_lines.append("  - ไม่มีคาบสอนแทนในวันนี้")
            continue

        by_period = defaultdict(list)
        for sub in day_subs:
            by_period[sub['period_id']].append(sub)

        for period in sorted(by_period.keys()):
            report_lines.append(f"  คาบที่ {period}:")
            for sub in by_period[period]:
                absent_name = teacher_full_names.get(sub['teacher_id'], sub['teacher_id'])
                sub_teacher_id = sub.get('substitute_teacher')
                
                # Look up Thai subject name, fallback to ID if not found
                subject_thai = reverse_subject_map.get(sub['subject_id'], sub['subject_id'])
                class_name = sub['class_id']

                if sub_teacher_id:
                    sub_name = teacher_full_names.get(sub_teacher_id, sub_teacher_id)
                    report_lines.append(
                        f"    - วิชา{subject_thai} ({class_name}): "
                        f"{absent_name} ➡️ {sub_name}"
                    )
                else:
                    report_lines.append(
                        f"    - วิชา{subject_thai} ({class_name}): "
                        f"{absent_name} ➡️ ❌ ไม่พบครูสอนแทน"
                    )

    report_lines.append("\n" + "="*30)

    return "\n".join(report_lines)


def process_leaves(target_date: str, test_mode: bool = False, send_line: bool = False) -> str:
    """
    Main processing function.

    Args:
        target_date: Date string in YYYY-MM-DD format
        test_mode: If True, skip Sheets updates (read-only)
        send_line: If True, send report to LINE (requires line_messaging module)

    Returns:
        Generated report string

    Raises:
        FileNotFoundError: If required data files are missing
        Exception: If processing fails
    """
    print("="*60)
    print("Processing Daily Leave Requests")
    print("="*60)
    print(f"Target Date: {target_date}")
    print(f"Test Mode: {test_mode}")
    print(f"Send to LINE: {send_line}")
    print()

    # Load all required data
    timetable, teacher_subjects, teacher_levels, class_levels, teacher_full_names = load_data_files()

    # Get all teacher IDs from timetable
    all_teacher_ids = list(set(entry['teacher_id'] for entry in timetable))

    # Get leaves for target date
    leaves = get_leaves_for_date(target_date)

    if not leaves:
        report = f"No leave requests found for {target_date}"
        print(f"\n{report}")
        return report

    # Group by day
    absent_by_day = group_leaves_by_day(leaves)

    print(f"\nAbsent teachers by day:")
    for day_id, teachers in absent_by_day.items():
        print(f"  {day_id}: {', '.join(teachers)}")

    # Find substitutes for each day
    all_substitutes = []

    for day_id, absent_teacher_ids in absent_by_day.items():
        print(f"\nProcessing {day_id}...")

        # Find substitutes
        substitutes = assign_substitutes_for_day(
            day_id=day_id,
            timetable=timetable,
            teacher_subjects=teacher_subjects,
            substitute_logs=[],  # No historical substitutes for now
            all_teacher_ids=all_teacher_ids,
            absent_teacher_ids=absent_teacher_ids,
            leave_logs=leaves,
            teacher_levels=teacher_levels,
            class_levels=class_levels
        )

        print(f"  Found {len(substitutes)} substitute assignments for {day_id}")
        all_substitutes.extend(substitutes)

    # Update Google Sheets
    update_sheets_with_substitutes(all_substitutes, target_date, test_mode)

    # Generate report
    report = generate_report(target_date, leaves, all_substitutes, absent_by_day, teacher_full_names)
    print(f"\n{report}")

    # Send to LINE if requested
    if send_line and not test_mode:
        try:
            from line_messaging import send_daily_report
            send_daily_report(report)
            print("\nReport sent to LINE")
        except ImportError:
            print("\nWARNING: line_messaging module not available. Skipping LINE notification.")
        except Exception as e:
            print(f"\nERROR sending to LINE: {e}")

    return report


def main():
    """Command-line interface"""
    # Parse arguments
    target_date = None
    test_mode = False
    send_line = False

    for arg in sys.argv[1:]:
        if arg == '--test':
            test_mode = True
        elif arg == '--send-line':
            send_line = True
        elif arg.startswith('--'):
            print(f"Unknown option: {arg}")
            sys.exit(1)
        else:
            # Assume it's a date
            target_date = arg

    # Use today if no date specified
    if not target_date:
        target_date = date.today().strftime('%Y-%m-%d')

    # Validate date format
    try:
        datetime.strptime(target_date, '%Y-%m-%d')
    except ValueError:
        print(f"ERROR: Invalid date format: {target_date}")
        print("Expected format: YYYY-MM-DD")
        sys.exit(1)

    # Process leaves
    try:
        process_leaves(target_date, test_mode, send_line)
    except FileNotFoundError as e:
        print(f"\nERROR: Required file not found: {e}")
        print("\nMake sure you have run:")
        print("  1. python build_teacher_data.py")
        print("  2. Set up credentials.json for Google Sheets")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
