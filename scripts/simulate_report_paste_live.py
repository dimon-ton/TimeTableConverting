import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import config
from src.web.webhook import process_substitution_report

# The exact report message format expected (reconstructed from previous test output)
REPORT_MESSAGE = """[REPORT] 2025-11-28

📝 รายงานผลการจัดหาครูสอนแทน 📝
ประจำวันที่ 28 พฤศจิกายน 2568
==============================

สรุปผล:
👩‍🏫 ครูที่ลา: 2 ท่าน
📚 จำนวนคาบทั้งหมด: 6 คาบ
✅ หาครูสอนแทนได้: 6 คาบ (100.0%)

ตารางสอนแทน:

วันศุกร์:
  คาบที่ 1:
    - วิชาคณิตศาสตร์ (ป.1): ครูอำพร (ลา) ➡️ ครูจรรยาภรณ์ (สอนแทน)
  คาบที่ 2:
    - วิชาภาษาไทย (ป.1): ครูอำพร (ลา) ➡️ ครูวิยะดา (สอนแทน)
    - วิชาคณิตศาสตร์ (ป.5): ครูสุกฤษฎิ์ (ลา) ➡️ ครูสุขุมาภรณ์ (สอนแทน)
  คาบที่ 3:
    - วิชาคณิตศาสตร์ (ป.5): ครูสุกฤษฎิ์ (ลา) ➡️ ครูจรรยาภรณ์ (สอนแทน)
  คาบที่ 4:
    - วิชาคณิตศาสตร์ (ป.1): ครูอำพร (ลา) ➡️ ครูสุจิตร (สอนแทน)
    - วิชาคณิตศาสตร์ (ป.5): ครูสุกฤษฎิ์ (ลา) ➡️ ครูจิตยาภรณ์ (สอนแทน)
"""

def main():
    print("="*60)
    print("TEST: Simulate Admin 'Paste Report' Action")
    print("="*60)
    print("Simulating: User 'U_ADMIN_TEST' posting [REPORT] to Teacher Group")
    print("-" * 60)

    # Mock group IDs to match what we might have in config or be generic
    # We need to ensure process_substitution_report accepts the group_id
    teacher_group_id = config.LINE_TEACHER_GROUP_ID or config.LINE_GROUP_ID
    
    if not teacher_group_id:
        print("⚠️ LINE_TEACHER_GROUP_ID or LINE_GROUP_ID is not set.")
        print("Please set it in .env to run this test effectively.")
        # Proceeding might fail the check in process_substitution_report
        teacher_group_id = "C_TEACHER_GROUP_TEST" 
        # Force config to have it for this test session
        config.LINE_TEACHER_GROUP_ID = teacher_group_id

    print(f"Target Group ID: {teacher_group_id}")
    print(f"Admin User ID: U_ADMIN_TEST")
    print("-" * 60)

    # Call the function directly
    # This mimics what webhook.py does when it receives the message
    try:
        process_substitution_report(
            text=REPORT_MESSAGE,
            group_id=teacher_group_id,
            user_id="U_ADMIN_TEST"
        )
        print("\n✅ Function call completed.")
    except Exception as e:
        print(f"\n❌ Function call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
