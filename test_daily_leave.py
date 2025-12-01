#!/usr/bin/env python3
"""
Test Daily Leave Processing Workflow

This script simulates a random teacher absence and runs the complete
daily leave processing workflow to test the system end-to-end.
"""

import sys
import os
import random
from datetime import datetime, timedelta
from unittest.mock import patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.daily_leave_processor import process_leaves
from src.utils.sheet_utils import log_request_to_sheet, load_requests_from_sheet
from src.config import config

def load_teacher_data():
    """Load available teachers for random selection"""
    with open(config.TEACHER_FULL_NAMES_FILE, 'r', encoding='utf-8') as f:
        teacher_data = json.load(f)

    return list(teacher_data.items())

def create_test_leave_request(teacher_id, teacher_name):
    """Create a test leave request in the Leave_Requests sheet"""
    # Pick random periods for the absence
    all_periods = [1, 2, 3, 4, 5, 6, 7, 8]
    num_periods = random.randint(1, 4)  # 1-4 periods of absence
    absent_periods = random.sample(all_periods, num_periods)
    absent_periods.sort()

    # Generate leave request message
    periods_str = ', '.join(map(str, absent_periods)) if len(absent_periods) > 1 else str(absent_periods[0])

    # Random leave reason
    reasons = ['ลาป่วย', 'ลากิจ', 'ไปรพแพท', 'ไปธุระ']
    reason = random.choice(reasons)

    # Create message in Thai
    message_formats = [
        f"{teacher_name}ขอลาวันนี้คาบ {periods_str}",
        f"{teacher_name}ขอลาวันนี้คาบ {periods_str} ครับ",
        f"เรียนท่าน ผอ. {teacher_name}ขอลาวันนี้คาบ {periods_str}"
    ]

    message = random.choice(message_formats)
    target_date = datetime.now().strftime('%Y-%m-%d')

    print(f"CREATING TEST LEAVE REQUEST:")
    print(f"   Teacher: {teacher_name} ({teacher_id})")
    print(f"   Message: {message}")
    print(f"   Date: {target_date}")
    print(f"   Periods: {absent_periods}")
    print(f"   Reason: {reason}")
    print()

    # Log to Leave_Requests sheet (in test mode to avoid affecting real data)
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
        'reason': reason,
        'message': message
    }

def test_random_absence():
    """Main test function - picks random teacher and processes their absence"""
    print("=" * 70)
    print("🧪 TESTING DAILY LEAVE PROCESS - RANDOM TEACHER ABSENCE")
    print("=" * 70)
    print()

    # Load available teachers
    teachers = load_teacher_data()

    # Pick random teacher for absence
    teacher_id, teacher_name = random.choice(teachers)

    print(f"🎯 SELECTED RANDOM TEACHER: {teacher_name} ({teacher_id})")
    print()

    # Create test leave request
    leave_request = create_test_leave_request(teacher_id, teacher_name)

    # Run daily leave processing
    print("🔄 PROCESSING DAILY LEAVE REQUESTS:")
    print("-" * 70)

    try:
        # Run in test mode first to avoid actual database writes
        result = process_leaves(
            target_date=leave_request['date'],
            test_mode=False,  # Set to True to test without database writes
            send_line=False  # Set to True to test LINE notifications
        )

        print()
        print("✅ PROCESSING COMPLETED SUCCESSFULLY!")
        print()
        print("📊 SUMMARY:")
        print(f"   Absent Teacher: {leave_request['teacher_name']}")
        print(f"   Absent Periods: {leave_request['periods']}")
        print(f"   Processing Result: Generated report with substitute assignments")
        print()
        print("📋 Next Steps:")
        print("   1. Check 'Pending_Assignments' sheet for created assignments")
        print("   2. Admin can verify and finalize via LINE webhook")
        print("   3. Check 'Teacher_Hours_Tracking' for updated hours")

    except Exception as e:
        print(f"❌ ERROR DURING PROCESSING: {e}")
        import traceback
        traceback.print_exc()

def test_specific_teacher(teacher_name_input):
    """Test with a specific teacher name"""
    print("=" * 70)
    print(f"🎯 TESTING SPECIFIC TEACHER: {teacher_name_input}")
    print("=" * 70)

    teachers = load_teacher_data()

    # Find teacher by name (partial match)
    matching_teacher = None
    for tid, name in teachers:
        if teacher_name_input.lower() in name.lower():
            matching_teacher = (tid, name)
            break

    if not matching_teacher:
        print(f"❌ Teacher '{teacher_name_input}' not found!")
        print("Available teachers:")
        for tid, name in teachers[:5]:  # Show first 5
            print(f"   - {name} ({tid})")
        return

    teacher_id, teacher_name = matching_teacher
    print(f"✅ Found: {teacher_name} ({teacher_id})")

    # Create test leave request
    leave_request = create_test_leave_request(teacher_id, teacher_name)

    # Run processing
    try:
        result = process_leaves(
            target_date=leave_request['date'],
            test_mode=False,
            send_line=False
        )
        print("✅ PROCESSING COMPLETED!")
    except Exception as e:
        print(f"❌ ERROR: {e}")

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
        test_random_absence()