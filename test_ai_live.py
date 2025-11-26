#!/usr/bin/env python3
"""
Simple live test for AI leave message parsing.
Tests the OpenRouter AI with real Thai leave messages.
"""

from dotenv import load_dotenv
from src.timetable.ai_parser import parse_leave_request
import json

# Load environment variables
load_dotenv()

# Test messages (real-world examples)
test_messages = [
    {
        "description": "Simple leave request",
        "message": "เรียนท่าน ผอ. วันนี้ ครูสุกฤษฎิ์ ขอลาป่วย คาบ 1-3"
    },
    {
        "description": "Tomorrow with multiple periods",
        "message": "ครูวิยะดา ขอลาพรุ่งนี้ คาบ 1, 3, 5 เพราะไปหาหมอ"
    },
    {
        "description": "Full day leave",
        "message": "เรียน ผอ. ครูสมชาย ขอลาวันนี้ทั้งวัน เพราะธุระส่วนตัว"
    },
    {
        "description": "Late arrival",
        "message": "ครูนภา เข้าสายวันนี้ คาบ 1-2 เพราะรถติด"
    },
]

def test_ai_parsing():
    """Test AI parsing with real API calls"""
    print("=" * 70)
    print("Testing AI Leave Message Parser")
    print("=" * 70)
    print()

    results = []

    for i, test in enumerate(test_messages, 1):
        print(f"Test {i}: {test['description']}")
        print(f"Message: {test['message']}")
        print("-" * 70)

        try:
            result = parse_leave_request(test['message'])

            if result:
                print("[SUCCESS] AI parsed the message:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                results.append({
                    "test": test['description'],
                    "status": "PASS",
                    "result": result
                })
            else:
                print("[FAILED] AI returned None")
                results.append({
                    "test": test['description'],
                    "status": "FAIL",
                    "error": "Returned None"
                })

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            results.append({
                "test": test['description'],
                "status": "ERROR",
                "error": str(e)
            })

        print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")

    print(f"Total tests: {len(results)}")
    print(f"[PASS] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"[ERROR] Errors: {errors}")
    print()

    if passed == len(results):
        print("All tests passed! AI is working correctly.")
    elif passed > 0:
        print("Some tests passed, but there are issues.")
    else:
        print("All tests failed. Check your OPENROUTER_API_KEY in .env")

    return results

if __name__ == "__main__":
    test_ai_parsing()
