"""
Process Daily Leave Requests (Refactored)

Main orchestration script that:
1. Reads leave requests for a specific date from the 'Leave_Requests' sheet.
2. Enriches the requests with timetable data (class, subject).
3. Finds substitute teachers for each period of absence.
4. Logs the final, detailed assignments to the 'Leave_Logs' sheet.
5. Generates a summary report.
"""

import json
import sys
from datetime import datetime, date
from typing import Dict, List, Tuple
from collections import defaultdict

from src.config import config
from src.utils.sheet_utils import get_sheets_client, load_requests_from_sheet, add_absence, load_substitute_logs_from_sheet, add_pending_assignment
from src.timetable.substitute import assign_substitutes_for_day


def load_data_files() -> Tuple[List[Dict], Dict, Dict, Dict, Dict, Dict]:
    """
    Load all required data files for substitute finding.
    """
    print("Loading data files...")

    with open(config.TIMETABLE_FILE, 'r', encoding='utf-8') as f:
        timetable = json.load(f)
    print(f"  OK Loaded {len(timetable)} timetable entries")

    with open(config.TEACHER_SUBJECTS_FILE, 'r', encoding='utf-8') as f:
        teacher_subjects = json.load(f)
    print(f"  OK Loaded {len(teacher_subjects)} teachers' subject mappings")

    with open(config.TEACHER_LEVELS_FILE, 'r', encoding='utf-8') as f:
        teacher_levels = json.load(f)
    print(f"  OK Loaded {len(teacher_levels)} teachers' level mappings")

    with open(config.CLASS_LEVELS_FILE, 'r', encoding='utf-8') as f:
        class_levels = json.load(f)
    print(f"  OK Loaded {len(class_levels)} class level mappings")

    with open(config.TEACHER_FULL_NAMES_FILE, 'r', encoding='utf-8') as f:
        teacher_full_names = json.load(f)
    print(f"  OK Loaded {len(teacher_full_names)} teacher names")
    
    with open(config.TEACHER_NAME_MAP_FILE, 'r', encoding='utf-8') as f:
        teacher_name_map = json.load(f)
    print(f"  OK Loaded {len(teacher_name_map)} teacher name-to-ID mappings")

    return timetable, teacher_subjects, teacher_levels, class_levels, teacher_full_names, teacher_name_map


def get_and_enrich_leaves(target_date: str, timetable: List[Dict], teacher_name_map: Dict[str, str]) -> List[Dict]:
    """
    Loads leave requests from the 'Leave_Requests' sheet, then enriches them
    with full timetable details for each period of absence.

    NOTE: Only periods where the teacher actually has a class are included.
    This gives us the exact count of teaching periods that need substitutes.

    Returns:
        List of enriched leave entries (only periods with classes)
    """
    print(f"\nFetching and enriching leave requests for {target_date}...")
    raw_requests = load_requests_from_sheet(target_date)
    enriched_leaves = []

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    date_obj = datetime.strptime(target_date, '%Y-%m-%d')
    day_id = day_names[date_obj.weekday()]

    for request in raw_requests:
        teacher_name = request.get('teacher_name')
        teacher_id = teacher_name_map.get(teacher_name)

        if not teacher_id:
            print(f"WARNING: Cannot find ID for teacher '{teacher_name}'. Skipping request.")
            continue

        for period in request.get('periods', []):
            # Find the class and subject for this teacher, day, and period
            timetable_entry = next((
                entry for entry in timetable
                if entry.get('teacher_id') == teacher_id and
                   entry.get('day_id') == day_id and
                   entry.get('period_id') == period
            ), None)

            if timetable_entry:
                enriched_leaves.append({
                    'date': target_date,
                    'teacher_id': teacher_id,
                    'day_id': day_id,
                    'period_id': period,
                    'class_id': timetable_entry.get('class_id'),
                    'subject_id': timetable_entry.get('subject_id'),
                    'reason': request.get('reason')
                })
            # Skip periods where the teacher has no class assigned
            # (e.g., free periods, lunch, etc.)

    print(f"Enriched {len(raw_requests)} requests into {len(enriched_leaves)} teaching periods that need substitutes.")
    return enriched_leaves


def group_leaves_by_day(leaves: List[Dict]) -> Dict[str, List[str]]:
    """
    Group leave entries by day and extract absent teacher IDs.
    """
    absent_by_day = defaultdict(set)
    for leave in leaves:
        day_id = leave['day_id']
        teacher_id = leave['teacher_id']
        absent_by_day[day_id].add(teacher_id)
    return {day: list(teachers) for day, teachers in absent_by_day.items()}


def log_assignments_to_pending(substitutes: List[Dict], target_date: str, test_mode: bool = False):
    """
    Appends the substitute assignments to the 'Pending_Assignments' sheet.
    These will be finalized to Leave_Logs after admin verification.
    """
    if test_mode:
        print("\nTEST MODE: Skipping logging to 'Pending_Assignments' sheet.")
        return

    if not substitutes:
        print("\nNo assignments to log.")
        return

    print(f"\nLogging {len(substitutes)} assignments to '{config.PENDING_ASSIGNMENTS_WORKSHEET}' sheet (pending verification)...")

    # Current timestamp for processed_at
    processed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logged_count = 0
    for sub_assignment in substitutes:
        # Extract substitute teacher ID, handling None case
        sub_teacher = sub_assignment.get('substitute_teacher_id')
        if sub_teacher is None:
            sub_teacher = 'Not Found'

        success = add_pending_assignment(
            date=target_date,
            absent_teacher=sub_assignment['absent_teacher_id'],
            day=sub_assignment['day_id'],
            period=sub_assignment['period_id'],
            class_id=sub_assignment['class_id'],
            subject=sub_assignment['subject_id'],
            substitute_teacher=sub_teacher,
            notes=sub_assignment.get('reason', 'ลากิจ'),
            processed_at=processed_at
        )
        if success:
            logged_count += 1

    print(f"  OK - Successfully logged {logged_count}/{len(substitutes)} pending assignments.")


def generate_report(
    target_date: str,
    leaves: List[Dict],
    substitutes: List[Dict],
    absent_by_day: Dict[str, List[str]],
    teacher_full_names: Dict[str, str]
) -> Tuple[str, str]:
    """
    Generate a text summary report of substitute assignments in Thai.

    Returns:
        Tuple of (balloon1, balloon2):
        - balloon1: Main report with [REPORT] prefix and substitute assignments
        - balloon2: Admin instructions for verification
    """
    from src.timetable.converter import subject_map
    reverse_subject_map = {v: k for k, v in subject_map.items()}

    thai_months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    day_map_thai = {"Mon": "วันจันทร์", "Tue": "วันอังคาร", "Wed": "วันพุธ", "Thu": "วันพฤหัสบดี", "Fri": "วันศุกร์"}

    try:
        date_obj = datetime.strptime(target_date, '%Y-%m-%d')
        thai_date_str = f"{date_obj.day} {thai_months[date_obj.month - 1]} {date_obj.year + 543}"
    except ValueError:
        thai_date_str = target_date

    # BALLOON 1: Main report with [REPORT] prefix
    balloon1_lines = []
    balloon1_lines.append(f"[REPORT] {target_date}")
    balloon1_lines.append("")
    balloon1_lines.append("📝 รายงานผลการจัดหาครูสอนแทน 📝")
    balloon1_lines.append(f"ประจำวันที่ {thai_date_str}")
    balloon1_lines.append("="*30)

    if not leaves:
        balloon1_lines.append("\nไม่มีข้อมูลการลาในวันที่ระบุ")
        balloon1 = "\n".join(balloon1_lines)
        balloon2 = ""
        return (balloon1, balloon2)

    # Calculate statistics
    # Note: 'leaves' contains only periods where teachers actually have classes (enriched data)
    # This ensures we count exact teaching periods, not just requested periods
    total_absent = len(set(leave['teacher_id'] for leave in leaves))  # Count unique absent teachers
    total_periods = len(leaves)  # Count exact teaching periods (only periods with classes)
    found_substitutes = sum(1 for sub in substitutes if sub.get('substitute_teacher_id'))  # Count successful substitutions
    success_rate = (found_substitutes / total_periods * 100) if total_periods > 0 else 0

    balloon1_lines.append("\nสรุปผล:")
    balloon1_lines.append(f"👩‍🏫 ครูที่ลา: {total_absent} ท่าน")
    balloon1_lines.append(f"📚 จำนวนคาบทั้งหมด: {total_periods} คาบ")
    balloon1_lines.append(f"✅ หาครูสอนแทนได้: {found_substitutes} คาบ ({success_rate:.1f}%)")
    balloon1_lines.append("\nตารางสอนแทน:")

    for day_id in sorted(absent_by_day.keys()):
        day_name_thai = day_map_thai.get(day_id, day_id)
        balloon1_lines.append(f"\n{day_name_thai}:")
        day_subs = [s for s in substitutes if s['day_id'] == day_id]
        if not day_subs:
            balloon1_lines.append("  - ไม่มีคาบสอนแทนในวันนี้")
            continue

        by_period = defaultdict(list)
        for sub in day_subs:
            by_period[sub['period_id']].append(sub)

        for period in sorted(by_period.keys()):
            balloon1_lines.append(f"  คาบที่ {period}:")
            for sub in by_period[period]:
                absent_name = teacher_full_names.get(sub['absent_teacher_id'], sub['absent_teacher_id'])
                sub_teacher_id = sub.get('substitute_teacher_id')
                subject_thai = reverse_subject_map.get(sub['subject_id'], sub['subject_id'])
                class_name = sub['class_id']
                if sub_teacher_id:
                    sub_name = teacher_full_names.get(sub_teacher_id, sub_teacher_id)
                    balloon1_lines.append(f"    - วิชา{subject_thai} ({class_name}): {absent_name} (ลา) ➡️ {sub_name} (สอนแทน)")
                else:
                    balloon1_lines.append(f"    - วิชา{subject_thai} ({class_name}): {absent_name} (ลา) ➡️ ❌ ไม่พบครูสอนแทน")

    balloon1 = "\n".join(balloon1_lines)

    # BALLOON 2: Admin instructions
    balloon2_lines = []
    balloon2_lines.append("="*30)
    balloon2_lines.append("⏳ รอการยืนยันจากแอดมิน")
    balloon2_lines.append("")
    balloon2_lines.append("📋 คำแนะนำสำหรับแอดมิน:")
    balloon2_lines.append("1. ตรวจสอบรายการสอนแทนข้างต้น")
    balloon2_lines.append("2. คัดลอกข้อความนี้ทั้งหมด (รวม [REPORT] ที่ด้านบน)")
    balloon2_lines.append("3. ส่งไปยังกลุ่มครูเพื่อยืนยันและแจ้งครู")
    balloon2_lines.append("="*30)

    balloon2 = "\n".join(balloon2_lines)

    return (balloon1, balloon2)


def write_teacher_hours_snapshot(date_str: str):
    """
    Calculate and write cumulative teacher hours snapshot to Teacher_Hours_Tracking worksheet.
    Called at end of daily processing.

    Calculation:
    - Regular_Periods_Today: Scheduled periods for this day of week
    - Cumulative_Substitute: Total substitutes from school year start to date_str
    - Cumulative_Absence: Total absences from school year start to date_str
    - Net_Total_Burden: Sum of all regular periods taught + cumulative_substitute - cumulative_absence
    """
    print("\n" + "="*60)
    print("Writing Teacher Hours Snapshot")
    print("="*60)

    from src.utils.sheet_utils import get_sheets_client
    from datetime import datetime as dt, timedelta

    # Load timetable for regular periods
    with open(config.TIMETABLE_FILE, 'r', encoding='utf-8') as f:
        timetable = json.load(f)

    # Load teacher names
    with open(config.TEACHER_FULL_NAMES_FILE, 'r', encoding='utf-8') as f:
        teacher_names = json.load(f)

    # Determine day of week for date_str
    date_obj = dt.strptime(date_str, '%Y-%m-%d')
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_of_week = day_names[date_obj.weekday()]

    # Calculate regular periods for TODAY (this day of week) per teacher
    teacher_stats = {}
    for teacher_id in teacher_names.keys():
        # Count periods scheduled for this specific day of week
        regular_today = sum(1 for entry in timetable
                          if entry['teacher_id'] == teacher_id
                          and entry['day_id'] == day_of_week)

        teacher_stats[teacher_id] = {
            'teacher_id': teacher_id,
            'teacher_name': teacher_names[teacher_id],
            'day_of_week': day_of_week,
            'regular_periods_today': regular_today,
            'cumulative_substitute': 0,
            'cumulative_absence': 0,
            'total_regular_taught': 0  # Will calculate below
        }

    # Load all Leave_Logs to calculate cumulative totals
    client = get_sheets_client()
    spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
    leave_logs_ws = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)
    all_logs = leave_logs_ws.get_all_records()

    # Determine school year start date (adjust as needed for your school)
    # Example: School year starts September 1st
    year = date_obj.year if date_obj.month >= 9 else date_obj.year - 1
    school_year_start = f"{year}-09-01"

    # Count cumulative substitutions and absences from school year start to current date
    for log in all_logs:
        log_date = log.get('Date', '')
        if school_year_start <= log_date <= date_str:  # Within school year up to current date
            # Count absences
            absent_teacher = log.get('Absent_Teacher', '')
            if absent_teacher in teacher_stats:
                teacher_stats[absent_teacher]['cumulative_absence'] += 1

            # Count substitutions
            substitute_teacher = log.get('Substitute_Teacher', '')
            if substitute_teacher and substitute_teacher != "Not Found" and substitute_teacher in teacher_stats:
                teacher_stats[substitute_teacher]['cumulative_substitute'] += 1

    # Calculate total regular periods taught (number of working days * periods per day)
    # Count working days from school year start to current date
    start_date = dt.strptime(school_year_start, '%Y-%m-%d')
    current_date = dt.strptime(date_str, '%Y-%m-%d')

    # Count days by day of week
    day_counts = {day: 0 for day in day_names[:5]}  # Mon-Fri only
    temp_date = start_date
    while temp_date <= current_date:
        if temp_date.weekday() < 5:  # Monday=0 to Friday=4
            day_counts[day_names[temp_date.weekday()]] += 1
        temp_date += timedelta(days=1)

    # Calculate total regular periods taught for each teacher
    for teacher_id, stats in teacher_stats.items():
        total_regular = 0
        for day in day_names[:5]:  # Mon-Fri
            periods_on_day = sum(1 for entry in timetable
                               if entry['teacher_id'] == teacher_id
                               and entry['day_id'] == day)
            total_regular += periods_on_day * day_counts[day]

        stats['total_regular_taught'] = total_regular

    # Write snapshot to Teacher_Hours_Tracking
    tracking_ws = spreadsheet.worksheet('Teacher_Hours_Tracking')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows_added = 0
    for teacher_id, stats in teacher_stats.items():
        # Net Total Burden = all regular periods taught + cumulative substitutes - cumulative absences
        net_total_burden = (stats['total_regular_taught'] +
                          stats['cumulative_substitute'] -
                          stats['cumulative_absence'])

        row = [
            date_str,
            teacher_id,
            stats['teacher_name'],
            stats['day_of_week'],
            stats['regular_periods_today'],
            stats['cumulative_substitute'],
            stats['cumulative_absence'],
            net_total_burden,
            timestamp
        ]

        tracking_ws.append_row(row, value_input_option='USER_ENTERED')
        rows_added += 1

    print(f"OK - Written teacher hours snapshot for {date_str} ({day_of_week})")
    print(f"  Teachers tracked: {len(teacher_stats)}")
    print(f"  School year: {school_year_start} to {date_str}")
    print(f"  Working days: {sum(day_counts.values())} total")
    print(f"  Rows written to Teacher_Hours_Tracking: {rows_added}")
    print("="*60)


def process_leaves(target_date: str, test_mode: bool = False, send_line: bool = False) -> str:
    """
    Main processing function.
    """
    print("="*60)
    print("Processing Daily Leave Requests")
    print("="*60)
    print(f"Target Date: {target_date}")
    print(f"Test Mode: {test_mode}")
    print(f"Send to LINE: {send_line}")
    print()

    # Load all required data
    timetable, teacher_subjects, teacher_levels, class_levels, teacher_full_names, teacher_name_map = load_data_files()
    all_teacher_ids = list(set(entry['teacher_id'] for entry in timetable))

    # Load historical substitute logs from Google Sheets
    print("\n" + "="*60)
    historical_substitute_logs = load_substitute_logs_from_sheet(limit_date=target_date)
    print(f"OK Loaded {len(historical_substitute_logs)} historical substitute assignments")
    print("="*60 + "\n")

    # Get and enrich leaves from 'Leave_Requests' sheet
    leaves = get_and_enrich_leaves(target_date, timetable, teacher_name_map)

    if not leaves:
        report = f"No valid leave requests found for {target_date} to process."
        try:
            print(f"\n{report}")
        except UnicodeEncodeError:
            print(f"\n{report.encode('ascii', 'replace').decode('ascii')}")
        return report

    absent_by_day = group_leaves_by_day(leaves)
    print(f"\nAbsent teachers by day:")
    for day_id, teachers in absent_by_day.items():
        print(f"  {day_id}: {', '.join(teachers)}")

    all_substitutes = []
    for day_id, absent_teacher_ids in absent_by_day.items():
        print(f"\nProcessing {day_id}...")
        substitutes = assign_substitutes_for_day(
            day_id=day_id,
            timetable=timetable,
            teacher_subjects=teacher_subjects,
            substitute_logs=historical_substitute_logs + all_substitutes,  # ✅ Use historical data + today's assignments
            all_teacher_ids=all_teacher_ids,
            absent_teacher_ids=absent_teacher_ids,
            leave_logs=leaves,
            teacher_levels=teacher_levels,
            class_levels=class_levels
        )
        print(f"  Found {len(substitutes)} substitute assignments for {day_id}")
        all_substitutes.extend(substitutes)

    # Log the assignments to 'Pending_Assignments' sheet (awaiting admin verification)
    log_assignments_to_pending(all_substitutes, target_date, test_mode)

    balloon1, balloon2 = generate_report(target_date, leaves, all_substitutes, absent_by_day, teacher_full_names)

    # Print both balloons to console
    try:
        print(f"\n{balloon1}")
        if balloon2:
            print(f"\n{balloon2}")
    except UnicodeEncodeError:
        # Windows console encoding issue - print without emojis
        print(f"\n{balloon1.encode('ascii', 'replace').decode('ascii')}")
        if balloon2:
            print(f"\n{balloon2.encode('ascii', 'replace').decode('ascii')}")

    if send_line and not test_mode:
        try:
            from src.web.line_messaging import send_daily_report
            send_daily_report(balloon1, balloon2)
            print("\nReport sent to ADMIN group via LINE (2 separate messages)")
            print("NOTE: Admins should review and manually forward to teacher group")
        except ImportError:
            print("\nWARNING: line_messaging module not available. Skipping LINE notification.")
        except Exception as e:
            print(f"\nERROR sending to LINE: {e}")

    # Write teacher hours snapshot (unless in test mode)
    if not test_mode:
        try:
            write_teacher_hours_snapshot(target_date)
        except Exception as e:
            print(f"\nERROR writing teacher hours snapshot: {e}")
            import traceback
            traceback.print_exc()

    # Return combined report for backward compatibility
    return f"{balloon1}\n\n{balloon2}" if balloon2 else balloon1


def main():
    """Command-line interface"""
    import argparse
    from datetime import date

    parser = argparse.ArgumentParser(
        description='Process daily leave requests and find substitute teachers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process today's leaves (test mode)
  python -m src.utils.daily_leave_processor --test

  # Process specific date and send to LINE
  python -m src.utils.daily_leave_processor 2025-11-28 --send-line

  # Full production run for today
  python -m src.utils.daily_leave_processor --send-line
        """
    )

    parser.add_argument(
        'date',
        nargs='?',
        default=None,
        help='Date to process (YYYY-MM-DD). Defaults to today.'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode - no database writes, no LINE messages'
    )

    parser.add_argument(
        '--send-line',
        action='store_true',
        help='Send report to LINE admin group'
    )

    args = parser.parse_args()

    # Determine target date
    if args.date:
        target_date = args.date
    else:
        target_date = date.today().strftime('%Y-%m-%d')

    # Run processing
    try:
        process_leaves(
            target_date=target_date,
            test_mode=args.test,
            send_line=args.send_line
        )
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user.")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
