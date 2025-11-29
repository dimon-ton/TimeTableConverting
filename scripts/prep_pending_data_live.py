import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.sheet_utils import add_pending_assignment

# Mock pending assignments for 2025-11-28
# Scenario: T001 absent (periods 2,3,4) and T002 absent (periods 1,2,4)
PENDING_DATA = [
    # T002 Assignments (Periods 1, 2, 4)
    {
        "date": "2025-11-28",
        "absent_teacher": "T002",
        "day": "Fri",
        "period": 1,
        "class_id": "ป.1",
        "subject": "Math",
        "substitute_teacher": "T017",  # Mock substitute
        "notes": "ลากิจ"
    },
    {
        "date": "2025-11-28",
        "absent_teacher": "T002",
        "day": "Fri",
        "period": 2,
        "class_id": "ป.1",
        "subject": "Thai",
        "substitute_teacher": "T007", # Mock substitute
        "notes": "ลากิจ"
    },
    {
        "date": "2025-11-28",
        "absent_teacher": "T002",
        "day": "Fri",
        "period": 4,
        "class_id": "ป.1",
        "subject": "Math",
        "substitute_teacher": "T005", # Mock substitute
        "notes": "ลากิจ"
    },
    # T001 Assignments (Periods 2, 3, 4)
    {
        "date": "2025-11-28",
        "absent_teacher": "T001",
        "day": "Fri",
        "period": 2,
        "class_id": "ป.5",
        "subject": "Math",
        "substitute_teacher": "T009", # Mock substitute
        "notes": "ลาป่วย"
    },
    {
        "date": "2025-11-28",
        "absent_teacher": "T001",
        "day": "Fri",
        "period": 3,
        "class_id": "ป.5",
        "subject": "Math",
        "substitute_teacher": "T017", # Mock substitute
        "notes": "ลาป่วย"
    },
    {
        "date": "2025-11-28",
        "absent_teacher": "T001",
        "day": "Fri",
        "period": 4,
        "class_id": "ป.5",
        "subject": "Math",
        "substitute_teacher": "T016", # Mock substitute
        "notes": "ลาป่วย"
    }
]

def main():
    print("="*60)
    print("PREP: Injecting Test Data to 'Pending_Assignments' Sheet")
    print("="*60)
    print(f"Target Date: 2025-11-28")
    print(f"Items to inject: {len(PENDING_DATA)}")
    print("-" * 60)

    processed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = 0

    for item in PENDING_DATA:
        try:
            print(f"Adding pending: {item['absent_teacher']} (P{item['period']}) -> {item['substitute_teacher']}")
            success = add_pending_assignment(
                date=item['date'],
                absent_teacher=item['absent_teacher'],
                day=item['day'],
                period=item['period'],
                class_id=item['class_id'],
                subject=item['subject'],
                substitute_teacher=item['substitute_teacher'],
                notes=item['notes'],
                processed_at=processed_at
            )
            if success:
                count += 1
            else:
                print(f"❌ Failed to add item: {item}")
        except Exception as e:
            print(f"❌ Exception: {e}")

    print("-" * 60)
    if count == len(PENDING_DATA):
        print(f"✅ Successfully injected {count} items to Pending_Assignments.")
    else:
        print(f"⚠️ Warning: Only injected {count}/{len(PENDING_DATA)} items.")

if __name__ == "__main__":
    main()
