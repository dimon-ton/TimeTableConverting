import sys
import os
from unittest.mock import patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.daily_leave_processor import process_leaves

# Mock data
MOCK_REQUESTS = [
    {
        "timestamp": "2025-11-27 20:00:00",
        "teacher_name": "ครูสุกฤษฎิ์",
        "date": "2025-11-28",
        "periods": [2, 3, 4],  # Periods actually taught by T001 on Fri
        "reason": "ลาป่วย",
        "line_user_id": "U123456",
        "status": "Pending"
    },
    {
        "timestamp": "2025-11-27 20:05:00",
        "teacher_name": "ครูอำพร",
        "date": "2025-11-28",
        "periods": [1, 2, 4],  # Periods actually taught by T002 on Fri
        "reason": "ลากิจ",
        "line_user_id": "U654321",
        "status": "Pending"
    }
]

def mock_load_requests(date_str):
    print(f"[MOCK] Loading requests for {date_str}: Returning 2 mock requests.")
    return MOCK_REQUESTS

def mock_load_logs(limit_date=None):
    print(f"[MOCK] Loading substitute logs: Returning empty list.")
    return []

def mock_add_pending(*args, **kwargs):
    # print(f"[MOCK] Adding pending assignment: {kwargs.get('substitute_teacher', 'Unknown')}")
    return True

if __name__ == "__main__":
    print("="*60)
    print("TEST: Two Teachers Absent (Fixed Periods) -> LINE Report")
    print("="*60)
    print("Teachers absent:")
    print("1. ครูสุกฤษฎิ์ (T001) - Periods 2, 3, 4")
    print("2. ครูอำพร (T002) - Periods 1, 2, 4")
    print("Target Date: 2025-11-28 (Friday)")
    print("-" * 60)

    # Patching the functions where they are used (imported) in daily_leave_processor
    with patch('src.utils.daily_leave_processor.load_requests_from_sheet', side_effect=mock_load_requests), \
         patch('src.utils.daily_leave_processor.load_substitute_logs_from_sheet', side_effect=mock_load_logs), \
         patch('src.utils.daily_leave_processor.add_pending_assignment', side_effect=mock_add_pending):
        
        try:
            # Enable send_line=True to actually send the message
            process_leaves(target_date="2025-11-28", test_mode=False, send_line=True)
            print("\n✅ Test completed successfully.")
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
