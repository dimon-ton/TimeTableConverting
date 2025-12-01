#!/usr/bin/env python3
"""
Simple Daily Leave Test

Tests the daily leave processing workflow with a random teacher.
"""

import sys
import os
import random
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.daily_leave_processor import process_leaves
from src.utils.sheet_utils import log_request_to_sheet
from src.config import config

def load_teachers():
    """Load available teachers"""
    with open(config.TEACHER_FULL_NAMES_FILE, 'r', encoding='utf-8') as f:
        teacher_data = json.load(f)
    return list(teacher_data.items())

def create_test_request(teacher_id, teacher_name):
    """Create a test leave request"""
    # Pick random periods (1-3 periods)
    all_periods = [1, 2, 3, 4, 5, 6, 7, 8]
    num_periods = random.randint(1, 3)
    absent_periods = random.sample(all_periods, num_periods)
    absent_periods.sort()

    # Random reason
    reasons = ['ลาป่วย', 'ลากิจ', 'ไปรับแพทย์']
    reason = random.choice(reasons)

    # Create message
    periods_str = ', '.join(map(str, absent_periods)) if len(absent_periods) > 1 else str(absent_periods[0])
    message = f"{teacher_name}ขอลาวันนี้คาบ {periods_str} ครับ"
    target_date = datetime.now().strftime('%Y-%m-%d')

    print(f"CREATING TEST LEAVE REQUEST:")
    print(f"   Teacher: {teacher_name} ({teacher_id})")
    print(f"   Periods: {absent_periods}")
    print(f"   Date: {target_date}")
    print(f"   Reason: {reason}")
    print(f"   Message: {message}")
    print()

    # Log to Leave_Requests sheet (test mode to avoid affecting real data)
    log_request_to_sheet(
        raw_message=message,
        leave_data={
            'teacher_name': teacher_name,
            'date': target_date,
            'periods': absent_periods,
            'reason': reason
        },
        status="Success"
    )

    return {
        'teacher_id': teacher_id,
        'teacher_name': teacher_name,
        'date': target_date,
        'periods': absent_periods,
        'message': message
    }

def test_daily_leave_processing():
    """Test the complete daily leave processing workflow"""
    print("=" * 70)
    print("DAILY LEAVE PROCESSING TEST")
    print("=" * 70)
    print()

    # Load available teachers
    teachers = load_teachers()
    print(f"Available teachers: {len(teachers)}")

    # Pick random teacher for absence
    teacher_id, teacher_name = random.choice(teachers)

    print(f"SELECTED RANDOM TEACHER: {teacher_name} ({teacher_id})")
    print()

    # Create test leave request
    leave_request = create_test_request(teacher_id, teacher_name)

    # Run daily leave processing
    print("RUNNING DAILY LEAVE PROCESSING...")
    print("-" * 70)

    try:
        result = process_leaves(
            target_date=leave_request['date'],
            test_mode=True,  # Use test mode to avoid database writes
            send_line=False   # Disable LINE notifications
        )

        print()
        print("PROCESSING COMPLETED SUCCESSFULLY!")
        print()
        print("SUMMARY:")
        print(f"   Absent Teacher: {leave_request['teacher_name']}")
        print(f"   Absent Periods: {leave_request['periods']}")
        print(f"   Processing Result: {result}")
        print()
        print("NEXT STEPS:")
        print("   1. Check 'Pending_Assignments' sheet for created substitute assignments")
        print("   2. Run: python -c \"from src.web.webhook import finalize_pending_assignment; finalize_pending_assignment('{leave_request['date']}', 'test_user')\"")
        print("   3. Check 'Teacher_Hours_Tracking' for updated hours")

        return True

    except Exception as e:
        print(f"ERROR DURING PROCESSING: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_teacher(teacher_name_input):
    """Test with a specific teacher name"""
    print("=" * 70)
    print(f"TESTING SPECIFIC TEACHER: {teacher_name_input}")
    print("=" * 70)

    teachers = load_teachers()

    # Find teacher by name (partial match)
    matching_teacher = None
    for tid, name in teachers:
        if teacher_name_input.lower() in name.lower():
            matching_teacher = (tid, name)
            break

    if not matching_teacher:
        print(f"Teacher '{teacher_name_input}' not found!")
        print("Available teachers:")
        for tid, name in teachers[:5]:  # Show first 5
            print(f"   - {name} ({tid})")
        return

    teacher_id, teacher_name = matching_teacher
    print(f"Found: {teacher_name} ({teacher_id})")

    # Create and process leave request
    leave_request = create_test_request(teacher_id, teacher_name)
    return test_daily_leave_processing()

if __name__ == "__main__":
    import json

    print("Daily Leave Processing Test Tool")
    print("=" * 70)
    print()

    # Check command line arguments
    if len(sys.argv) > 1:
        # Test specific teacher
        teacher_name = ' '.join(sys.argv[1:])
        test_specific_teacher(teacher_name)
    else:
        # Test random teacher
        test_daily_leave_processing()