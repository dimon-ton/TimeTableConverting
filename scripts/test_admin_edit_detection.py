"""
Test Admin Edit Detection

This script tests the admin message edit detection and database update functionality.

Usage:
    python scripts/test_admin_edit_detection.py
"""

import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.report_parser import (
    parse_edited_assignments,
    match_teacher_name_to_id,
    detect_assignment_changes,
    generate_confirmation_message,
    load_teacher_name_map,
    load_teacher_full_names
)
from src.config import config


# Sample edited report message (simulating admin editing substitute teacher)
SAMPLE_REPORT = """[REPORT] 2025-11-28

📝 รายงานผลการจัดหาครูสอนแทน 📝
ประจำวันที่ 28 พฤศจิกายน 2568
==============================

สรุปผล:
👩‍🏫 ครูที่ลา: 2 ท่าน
📚 จำนวนคาบทั้งหมด: 5 คาบ
✅ หาครูสอนแทนได้: 5 คาบ (100.0%)

วันศุกร์:
  คาบที่ 1:
    - วิชาคณิตศาสตร์ (ป.1): ครูอำพร (ลา) ➡️ ครูสุจิตร (สอนแทน)
    - วิชาภาษาไทย (ป.2): ครูกฤตชยากร (ลา) ➡️ ครูพิมล (สอนแทน)
  คาบที่ 2:
    - วิชาคณิตศาสตร์ (ป.3): ครูอำพร (ลา) ➡️ ครูจรรยาภรณ์ (สอนแทน)
  คาบที่ 3:
    - วิชาวิทยาศาสตร์ (ป.4): ครูกฤตชยากร (ลา) ➡️ ครูปาณิสรา (สอนแทน)
  คาบที่ 4:
    - วิชาภาษาอังกฤษ (ป.5): ครูอำพร (ลา) ➡️ ครูวิยะดา (สอนแทน)
"""

# Sample pending assignments (what's in the database)
SAMPLE_PENDING = [
    {
        'Date': '2025-11-28',
        'Absent_Teacher': 'T002',  # ครูอำพร
        'Day': 'Fri',
        'Period': '1',
        'Class_ID': 'ป.1',
        'Subject': 'Math',
        'Substitute_Teacher': 'T017',  # ครูจรรยาภรณ์ (ORIGINAL - will be changed to T005)
        'Status': 'pending'
    },
    {
        'Date': '2025-11-28',
        'Absent_Teacher': 'T003',  # ครูกฤตชยากร
        'Day': 'Fri',
        'Period': '1',
        'Class_ID': 'ป.2',
        'Subject': 'Thai',
        'Substitute_Teacher': 'T004',  # ครูพิมล (SAME)
        'Status': 'pending'
    },
    {
        'Date': '2025-11-28',
        'Absent_Teacher': 'T002',  # ครูอำพร
        'Day': 'Fri',
        'Period': '2',
        'Class_ID': 'ป.3',
        'Subject': 'Math',
        'Substitute_Teacher': 'T017',  # ครูจรรยาภรณ์ (SAME)
        'Status': 'pending'
    },
    {
        'Date': '2025-11-28',
        'Absent_Teacher': 'T003',  # ครูกฤตชยากร
        'Day': 'Fri',
        'Period': '3',
        'Class_ID': 'ป.4',
        'Subject': 'Science',
        'Substitute_Teacher': 'T006',  # ครูปาณิสรา (SAME)
        'Status': 'pending'
    },
    {
        'Date': '2025-11-28',
        'Absent_Teacher': 'T002',  # ครูอำพร
        'Day': 'Fri',
        'Period': '4',
        'Class_ID': 'ป.5',
        'Subject': 'English',
        'Substitute_Teacher': 'T007',  # ครูวิยะดา (SAME)
        'Status': 'pending'
    }
]


def test_parsing():
    """Test 1: Parse edited assignments from message"""
    print("=" * 60)
    print("TEST 1: Parsing Edited Assignments")
    print("=" * 60)

    parsed = parse_edited_assignments(SAMPLE_REPORT)

    print(f"\nParsed {len(parsed)} assignments from message:")
    for i, assignment in enumerate(parsed, 1):
        print(f"\n{i}. {assignment['subject_thai']} ({assignment['class_id']}) - {assignment['day']} คาบ {assignment['period']}")
        print(f"   ครูที่ลา: {assignment['absent_teacher_name']}")
        print(f"   ครูสอนแทน: {assignment['substitute_teacher_name']}")

    return parsed


def test_teacher_matching():
    """Test 2: Match teacher names to IDs"""
    print("\n" + "=" * 60)
    print("TEST 2: Teacher Name Matching")
    print("=" * 60)

    teacher_name_map = load_teacher_name_map()
    teacher_full_names = load_teacher_full_names()

    test_names = [
        "ครูอำพร",  # Exact match
        "ครูสุจิตร",  # Exact match
        "อำพร",  # Normalized (without ครู)
        "ครู อำพร",  # Extra space
        "ครูสุจิร",  # Misspelled (missing final ต)
    ]

    print("\nTesting name matching:")
    for name in test_names:
        teacher_id, confidence, method = match_teacher_name_to_id(
            name,
            teacher_name_map,
            teacher_full_names,
            use_ai=False  # Don't use AI for basic tests
        )

        status = "[PASS]" if teacher_id else "[FAIL]"
        print(f"\n{status} \"{name}\"")
        print(f"   Match: {teacher_id or 'Not Found'} ({teacher_full_names.get(teacher_id, 'N/A')})")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Method: {method}")


def test_change_detection():
    """Test 3: Detect changes between parsed and pending"""
    print("\n" + "=" * 60)
    print("TEST 3: Change Detection")
    print("=" * 60)

    parsed = parse_edited_assignments(SAMPLE_REPORT)
    teacher_name_map = load_teacher_name_map()
    teacher_full_names = load_teacher_full_names()

    changes = detect_assignment_changes(
        target_date='2025-11-28',
        parsed_assignments=parsed,
        pending_assignments=SAMPLE_PENDING,
        teacher_name_map=teacher_name_map,
        teacher_full_names=teacher_full_names,
        use_ai=False,  # Don't use AI for testing
        api_key=None,
        ai_threshold=0.85
    )

    print(f"\n[UPDATED] Updated assignments: {len(changes['updated'])}")
    for change in changes['updated']:
        old_name = teacher_full_names.get(change['old_substitute'], change['old_substitute'])
        new_name = teacher_full_names.get(change['new_substitute'], change['new_substitute'])
        print(f"   - {change['subject']} ({change['class_id']}) period {change['period']}")
        print(f"     {old_name} -> {new_name}")

    print(f"\n[UNCHANGED] Unchanged assignments: {len(changes['unchanged'])}")

    print(f"\n[WARNING] Match errors: {len(changes['match_errors'])}")
    for error in changes['match_errors']:
        print(f"   - {error['teacher_name']}")
        print(f"     Context: {error['context']}")

    print(f"\n[NOT_FOUND] Not found in pending: {len(changes['not_found'])}")
    for nf in changes['not_found']:
        parsed_item = nf['parsed']
        print(f"   - {parsed_item['subject_thai']} ({parsed_item['class_id']}) - {parsed_item['day']} คาบ {parsed_item['period']}")

    return changes


def test_confirmation_message():
    """Test 4: Generate confirmation message"""
    print("\n" + "=" * 60)
    print("TEST 4: Confirmation Message Generation")
    print("=" * 60)

    parsed = parse_edited_assignments(SAMPLE_REPORT)
    teacher_name_map = load_teacher_name_map()
    teacher_full_names = load_teacher_full_names()

    changes = detect_assignment_changes(
        target_date='2025-11-28',
        parsed_assignments=parsed,
        pending_assignments=SAMPLE_PENDING,
        teacher_name_map=teacher_name_map,
        teacher_full_names=teacher_full_names,
        use_ai=False,
        api_key=None,
        ai_threshold=0.85
    )

    confirmation = generate_confirmation_message(
        target_date='2025-11-28',
        changes=changes,
        teacher_full_names=teacher_full_names
    )

    print("\nGenerated confirmation message:")
    print("-" * 60)
    print(confirmation)
    print("-" * 60)


def test_ai_fuzzy_matching():
    """Test 5: AI-powered fuzzy matching (if API key available)"""
    print("\n" + "=" * 60)
    print("TEST 5: AI-Powered Fuzzy Matching")
    print("=" * 60)

    if not config.OPENROUTER_API_KEY:
        print("\n[SKIP] Skipping AI test - OPENROUTER_API_KEY not configured")
        print("   Set OPENROUTER_API_KEY in .env to enable AI matching tests")
        return

    teacher_name_map = load_teacher_name_map()
    teacher_full_names = load_teacher_full_names()

    # Test with intentionally misspelled name
    misspelled_name = "ครูสุจิร"  # Missing final ต (should match "ครูสุจิตร")

    print(f"\nTesting AI matching for misspelled name: \"{misspelled_name}\"")
    print("(This will make an API call to OpenRouter)")

    teacher_id, confidence, method = match_teacher_name_to_id(
        misspelled_name,
        teacher_name_map,
        teacher_full_names,
        use_ai=True,
        api_key=config.OPENROUTER_API_KEY,
        ai_model=config.OPENROUTER_MODEL
    )

    status = "[PASS]" if teacher_id else "[FAIL]"
    matched_name = teacher_full_names.get(teacher_id, 'Not Found')

    print(f"\n{status} Result:")
    print(f"   Input: \"{misspelled_name}\"")
    print(f"   Matched to: {teacher_id} ({matched_name})")
    print(f"   Confidence: {confidence:.2%}")
    print(f"   Method: {method}")

    if confidence >= config.AI_MATCH_CONFIDENCE_THRESHOLD:
        print(f"   [HIGH] High confidence - would auto-accept")
    elif confidence >= 0.60:
        print(f"   [MED] Medium confidence - would flag for admin review")
    else:
        print(f"   [LOW] Low confidence - would treat as 'Not Found'")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ADMIN EDIT DETECTION - TEST SUITE")
    print("=" * 60)

    try:
        # Test 1: Parsing
        test_parsing()

        # Test 2: Teacher matching
        test_teacher_matching()

        # Test 3: Change detection
        test_change_detection()

        # Test 4: Confirmation message
        test_confirmation_message()

        # Test 5: AI fuzzy matching (optional)
        test_ai_fuzzy_matching()

        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS COMPLETED")
        print("=" * 60)

        print("\nNote: This test script uses mock data. To test with real data:")
        print("1. Ensure pending assignments exist in Google Sheets")
        print("2. Send an edited report message through LINE webhook")
        print("3. Check that Pending_Assignments is updated correctly")
        print("4. Verify confirmation message is sent to admin")

    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
