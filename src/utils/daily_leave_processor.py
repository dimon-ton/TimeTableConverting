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
from src.utils.sheet_utils import get_sheets_client, load_requests_from_sheet, add_absence, load_substitute_logs_from_sheet
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
            else:
                # Still log the absence, just without class/subject details
                enriched_leaves.append({
                    'date': target_date,
                    'teacher_id': teacher_id,
                    'day_id': day_id,
                    'period_id': period,
                    'class_id': 'N/A',
                    'subject_id': 'N/A',
                    'reason': request.get('reason')
                })

    print(f"Enriched {len(raw_requests)} requests into {len(enriched_leaves)} period-based absences.")
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


def log_assignments_to_leave_logs(substitutes: List[Dict], target_date: str, test_mode: bool = False):
    """
    Appends the final substitute assignments to the 'Leave_Logs' sheet.
    """
    if test_mode:
        print("\nTEST MODE: Skipping final logging to 'Leave_Logs' sheet.")
        return

    if not substitutes:
        print("\nNo assignments to log.")
        return

    print(f"\nLogging {len(substitutes)} final assignments to '{config.LEAVE_LOGS_WORKSHEET}' sheet...")
    
    logged_count = 0
    for sub_assignment in substitutes:
        # Extract substitute teacher ID, handling None case
        sub_teacher = sub_assignment.get('substitute_teacher_id')
        if sub_teacher is None:
            sub_teacher = 'Not Found'

        success = add_absence(
            date=target_date,
            absent_teacher=sub_assignment['absent_teacher_id'],
            day=sub_assignment['day_id'],
            period=sub_assignment['period_id'],
            class_id=sub_assignment['class_id'],
            subject=sub_assignment['subject_id'],
            substitute_teacher=sub_teacher,
            notes=sub_assignment.get('reason', 'ลากิจ')
        )
        if success:
            logged_count += 1
            
    print(f"  OK - Successfully logged {logged_count}/{len(substitutes)} assignments.")


def generate_report(
    target_date: str,
    leaves: List[Dict],
    substitutes: List[Dict],
    absent_by_day: Dict[str, List[str]],
    teacher_full_names: Dict[str, str]
) -> str:
    """
    Generate a text summary report of substitute assignments in Thai.
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

    report_lines = []
    report_lines.append("📝 รายงานผลการจัดหาครูสอนแทน 📝")
    report_lines.append(f"ประจำวันที่ {thai_date_str}")
    report_lines.append("="*30)

    if not leaves:
        report_lines.append("\nไม่มีข้อมูลการลาในวันที่ระบุ")
        return "\n".join(report_lines)

    total_absent = len(set(leave['teacher_id'] for leave in leaves))
    total_periods = len(leaves)
    found_substitutes = sum(1 for sub in substitutes if sub.get('substitute_teacher_id'))
    success_rate = (found_substitutes / total_periods * 100) if total_periods > 0 else 0

    report_lines.append("\nสรุปผล:")
    report_lines.append(f"👩‍🏫 ครูที่ลา: {total_absent} ท่าน")
    report_lines.append(f"📚 จำนวนคาบทั้งหมด: {total_periods} คาบ")
    report_lines.append(f"✅ หาครูสอนแทนได้: {found_substitutes} คาบ ({success_rate:.1f}%)")
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
                absent_name = teacher_full_names.get(sub['absent_teacher_id'], sub['absent_teacher_id'])
                sub_teacher_id = sub.get('substitute_teacher_id')
                subject_thai = reverse_subject_map.get(sub['subject_id'], sub['subject_id'])
                class_name = sub['class_id']
                if sub_teacher_id:
                    sub_name = teacher_full_names.get(sub_teacher_id, sub_teacher_id)
                    report_lines.append(f"    - วิชา{subject_thai} ({class_name}): {absent_name} ➡️ {sub_name}")
                else:
                    report_lines.append(f"    - วิชา{subject_thai} ({class_name}): {absent_name} ➡️ ❌ ไม่พบครูสอนแทน")

    report_lines.append("\n" + "="*30)
    return "\n".join(report_lines)


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

    # ✨ Load historical substitute logs from Google Sheets
    print("\n" + "="*60)
    historical_substitute_logs = load_substitute_logs_from_sheet(limit_date=target_date)
    print(f"✅ Loaded {len(historical_substitute_logs)} historical substitute assignments")
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

    # Log the final assignments to the 'Leave_Logs' sheet
    log_assignments_to_leave_logs(all_substitutes, target_date, test_mode)

    report = generate_report(target_date, leaves, all_substitutes, absent_by_day, teacher_full_names)
    try:
        print(f"\n{report}")
    except UnicodeEncodeError:
        # Windows console encoding issue - print without emojis
        print(f"\n{report.encode('ascii', 'replace').decode('ascii')}")

    if send_line and not test_mode:
        try:
            from src.web.line_messaging import send_daily_report
            send_daily_report(report)
            print("\nReport sent to ADMIN group via LINE")
            print("NOTE: Admins should review and manually forward to teacher group")
        except ImportError:
            print("\nWARNING: line_messaging module not available. Skipping LINE notification.")
        except Exception as e:
            print(f"\nERROR sending to LINE: {e}")

    return report


def main():
    """Command-line interface"""
    # ... (main function remains the same)
    # (code omitted for brevity)

if __name__ == "__main__":
    main()
