"""
Add Teacher Absence to Google Sheets

This script allows you to add teacher absences to the Google Sheets leave log,
and optionally find and record substitute teachers automatically.

Usage:
    # Interactive mode (prompts for all information)
    python add_absence_to_sheets.py

    # Command-line mode
    python add_absence_to_sheets.py --date 2025-11-20 --teacher T001 --day Mon --period 3 --class ป.4

    # With automatic substitute finding
    python add_absence_to_sheets.py --date 2025-11-20 --teacher T001 --day Mon --period 3 --class ป.4 --find-substitute
"""

import argparse
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import Optional, Dict
import json

from src.config import config


def get_sheets_client():
    """Create and return an authenticated Google Sheets client."""
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    try:
        creds = Credentials.from_service_account_file(config.CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Credentials file '{config.CREDENTIALS_FILE}' not found. "
            "Please ensure credentials.json is in the current directory."
        )
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Sheets: {e}")


def add_absence(
    date: str,
    absent_teacher: str,
    day: str,
    period: int,
    class_id: str,
    subject: str = "",
    substitute_teacher: str = "",
    notes: str = ""
) -> bool:
    """
    Add a teacher absence entry to Google Sheets.

    Args:
        date: Date of absence (YYYY-MM-DD format)
        absent_teacher: Teacher ID (e.g., "T001")
        day: Day of week (e.g., "Mon", "Tue", etc.)
        period: Period number
        class_id: Class ID (e.g., "ป.4", "ม.1")
        subject: Subject name (optional)
        substitute_teacher: Substitute teacher ID (optional)
        notes: Additional notes (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get authenticated client
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)

        # Prepare row data
        row = [
            date,
            absent_teacher,
            day,
            str(period),
            class_id,
            subject,
            substitute_teacher,
            notes
        ]

        # Append the row
        worksheet.append_row(row, value_input_option='USER_ENTERED')

        print(f"OK - Added absence entry for {absent_teacher} on {date}")
        return True

    except Exception as e:
        print(f"ERROR: Failed to add absence: {e}")
        return False


def find_substitute_for_absence(
    timetable_file: str,
    absent_teacher: str,
    day: str,
    period: int,
    class_id: str
) -> Optional[str]:
    """
    Find a substitute teacher for the given absence.

    Args:
        timetable_file: Path to timetable JSON file
        absent_teacher: Teacher ID who is absent
        day: Day of week
        period: Period number
        class_id: Class ID

    Returns:
        str: Substitute teacher ID, or None if not found
    """
    try:
        # Load timetable data
        with open(timetable_file, 'r', encoding='utf-8') as f:
            timetable = json.load(f)

        # Find the entry for this absence
        target_entry = None
        for entry in timetable:
            if (entry['teacher_id'] == absent_teacher and
                entry['day_id'] == day and
                entry['period_id'] == period and
                entry['class_id'] == class_id):
                target_entry = entry
                break

        if not target_entry:
            print(f"WARNING: No timetable entry found for {absent_teacher}, {day} period {period}, class {class_id}")
            return None

        # Import find_substitute module
        try:
            from find_substitute import find_best_substitute_teacher
        except ImportError:
            print("ERROR: find_substitute.py not found. Cannot find substitute automatically.")
            return None

        # Load required data files
        try:
            with open('teacher_subjects.json', 'r', encoding='utf-8') as f:
                teacher_subjects = json.load(f)
            with open('teacher_levels.json', 'r', encoding='utf-8') as f:
                teacher_levels = json.load(f)
            with open('class_levels.json', 'r', encoding='utf-8') as f:
                class_levels = json.load(f)
        except FileNotFoundError as e:
            print(f"ERROR: Required data file not found: {e}")
            return None

        # Find substitute
        leave_logs = [target_entry]  # Mark this period as leave
        substitute = find_best_substitute_teacher(
            timetable=timetable,
            teacher_subjects=teacher_subjects,
            teacher_levels=teacher_levels,
            class_levels=class_levels,
            leave_logs=leave_logs,
            target_entry=target_entry,
            substitutes_assigned_today=[]
        )

        if substitute:
            print(f"OK - Found substitute: {substitute}")
            return substitute
        else:
            print("WARNING - No suitable substitute found")
            return None

    except Exception as e:
        print(f"ERROR: Failed to find substitute: {e}")
        return None


def interactive_mode():
    """Run interactive mode to collect absence information."""
    print("="*60)
    print("Add Teacher Absence - Interactive Mode")
    print("="*60)

    # Get date
    while True:
        date_input = input("\nDate (YYYY-MM-DD) [today]: ").strip()
        if not date_input:
            date = datetime.now().strftime("%Y-%m-%d")
            break
        try:
            datetime.strptime(date_input, "%Y-%m-%d")
            date = date_input
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD")

    # Get teacher ID
    absent_teacher = input("Absent Teacher ID (e.g., T001): ").strip()
    if not absent_teacher:
        print("ERROR: Teacher ID is required")
        return

    # Get day
    day = input("Day (Mon/Tue/Wed/Thu/Fri): ").strip()
    if not day:
        print("ERROR: Day is required")
        return

    # Get period
    while True:
        period_input = input("Period number: ").strip()
        try:
            period = int(period_input)
            break
        except ValueError:
            print("Invalid period number")

    # Get class
    class_id = input("Class ID (e.g., ป.4, ม.1): ").strip()
    if not class_id:
        print("ERROR: Class ID is required")
        return

    # Optional fields
    subject = input("Subject (optional): ").strip()
    notes = input("Notes (optional): ").strip()

    # Ask about finding substitute
    find_sub = input("\nFind substitute automatically? (y/n) [n]: ").strip().lower()
    substitute_teacher = ""

    if find_sub == 'y':
        timetable_file = input("Timetable JSON file [real_timetable.json]: ").strip()
        if not timetable_file:
            timetable_file = "real_timetable.json"

        substitute = find_substitute_for_absence(
            timetable_file, absent_teacher, day, period, class_id
        )
        if substitute:
            substitute_teacher = substitute

    # Add to Google Sheets
    print("\n" + "-"*60)
    print("Adding absence to Google Sheets...")
    success = add_absence(
        date=date,
        absent_teacher=absent_teacher,
        day=day,
        period=period,
        class_id=class_id,
        subject=subject,
        substitute_teacher=substitute_teacher,
        notes=notes
    )

    if success:
        print("\n" + "="*60)
        print("SUCCESS! Absence added to Google Sheets")
        print("="*60)
        print(f"\nDetails:")
        print(f"  Date: {date}")
        print(f"  Absent Teacher: {absent_teacher}")
        print(f"  Day: {day}, Period: {period}")
        print(f"  Class: {class_id}")
        if subject:
            print(f"  Subject: {subject}")
        if substitute_teacher:
            print(f"  Substitute: {substitute_teacher}")
        if notes:
            print(f"  Notes: {notes}")


def command_line_mode(args):
    """Run command-line mode with provided arguments."""
    substitute_teacher = ""

    if args.find_substitute:
        substitute = find_substitute_for_absence(
            args.timetable,
            args.teacher,
            args.day,
            args.period,
            args.class_id
        )
        if substitute:
            substitute_teacher = substitute

    success = add_absence(
        date=args.date,
        absent_teacher=args.teacher,
        day=args.day,
        period=args.period,
        class_id=args.class_id,
        subject=args.subject or "",
        substitute_teacher=substitute_teacher,
        notes=args.notes or ""
    )

    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add teacher absence to Google Sheets leave log"
    )
    parser.add_argument("--date", help="Date of absence (YYYY-MM-DD)")
    parser.add_argument("--teacher", help="Absent teacher ID (e.g., T001)")
    parser.add_argument("--day", help="Day of week (Mon/Tue/Wed/Thu/Fri)")
    parser.add_argument("--period", type=int, help="Period number")
    parser.add_argument("--class", dest="class_id", help="Class ID (e.g., ป.4)")
    parser.add_argument("--subject", help="Subject name (optional)")
    parser.add_argument("--notes", help="Additional notes (optional)")
    parser.add_argument(
        "--find-substitute",
        action="store_true",
        help="Automatically find and assign substitute teacher"
    )
    parser.add_argument(
        "--timetable",
        default="real_timetable.json",
        help="Timetable JSON file (default: real_timetable.json)"
    )

    args = parser.parse_args()

    # If no arguments provided, run interactive mode
    if not args.date and not args.teacher:
        interactive_mode()
    else:
        # Validate required arguments
        if not all([args.date, args.teacher, args.day, args.period, args.class_id]):
            print("ERROR: When using command-line mode, you must provide:")
            print("  --date, --teacher, --day, --period, --class")
            parser.print_help()
        else:
            command_line_mode(args)
