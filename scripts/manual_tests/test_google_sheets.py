#!/usr/bin/env python3
"""
Test Google Sheets integration - recording leave requests.
"""

from dotenv import load_dotenv
import os
from src.utils.sheet_utils import log_request_to_sheet

# Load environment variables
load_dotenv()

def test_google_sheets():
    """Test logging to Google Sheets"""
    print("=" * 70)
    print("Testing Google Sheets Integration")
    print("=" * 70)
    print()

    # Check credentials
    if not os.path.exists('credentials.json'):
        print("[ERROR] credentials.json not found!")
        print("You need to:")
        print("1. Go to Google Cloud Console")
        print("2. Enable Google Sheets API")
        print("3. Download credentials.json")
        print("4. Place it in the project root")
        return False

    spreadsheet_id = os.getenv('SPREADSHEET_ID')
    if not spreadsheet_id:
        print("[ERROR] SPREADSHEET_ID not set in .env")
        return False

    print(f"[OK] Spreadsheet ID: {spreadsheet_id}")
    print(f"[OK] Credentials file exists")
    print()

    # Test data
    test_request = {
        "teacher_name": "สุกฤษฎิ์",
        "date": "2025-11-26",
        "periods": [1, 2, 3],
        "reason": "ป่วย",
        "leave_type": "leave"
    }

    test_message = "เรียนท่าน ผอ. วันนี้ ครูสุกฤษฎิ์ ขอลาป่วย คาบ 1-3"

    print("Attempting to log test request to Google Sheets...")
    print(f"Teacher: {test_request['teacher_name']}")
    print(f"Date: {test_request['date']}")
    print(f"Periods: {test_request['periods']}")
    print(f"Reason: {test_request['reason']}")
    print()

    try:
        result = log_request_to_sheet(
            test_message,
            test_request,
            "AI Success (Test)"
        )

        if result:
            print("[SUCCESS] Logged to Google Sheets!")
            print("Check your spreadsheet to verify the entry was added.")
            return True
        else:
            print("[FAILED] log_request_to_sheet returned False")
            return False

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        print()
        print("Common issues:")
        print("1. credentials.json missing or invalid")
        print("2. Google Sheets API not enabled")
        print("3. Spreadsheet not shared with service account email")
        print("4. SPREADSHEET_ID incorrect in .env")
        return False

if __name__ == "__main__":
    success = test_google_sheets()
    print()
    print("=" * 70)
    if success:
        print("Google Sheets integration is working!")
    else:
        print("Google Sheets integration needs setup.")
    print("=" * 70)
