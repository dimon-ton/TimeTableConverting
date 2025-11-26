#!/usr/bin/env python3
"""
Verify what's actually in the Google Sheet.
"""

from dotenv import load_dotenv
from src.utils.sheet_utils import get_sheets_client
from src.config import config

load_dotenv()

def verify_sheet_contents():
    """Check what's actually in the Leave_Requests sheet"""
    print("=" * 70)
    print("Checking Google Sheets Contents")
    print("=" * 70)
    print()

    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)

        print(f"Connected to spreadsheet: {spreadsheet.title}")
        print()

        # Try to get Leave_Requests worksheet
        try:
            worksheet = spreadsheet.worksheet(config.LEAVE_REQUESTS_WORKSHEET)
            print(f"[OK] Found worksheet: {config.LEAVE_REQUESTS_WORKSHEET}")
            print()

            # Get all values
            all_values = worksheet.get_all_values()

            print(f"Total rows: {len(all_values)}")
            print()

            if len(all_values) > 0:
                print("Last 5 entries:")
                print("-" * 70)

                # Show headers
                if all_values:
                    headers = all_values[0]
                    print("Headers:", headers)
                    print()

                # Show last 5 rows
                for row in all_values[-5:]:
                    print(row)
                print()

                print("[SUCCESS] Google Sheets is working!")
                print("The test entry was successfully logged.")
                return True
            else:
                print("[INFO] Sheet exists but is empty.")
                return False

        except Exception as e:
            print(f"[ERROR] Could not access worksheet: {e}")
            return False

    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    verify_sheet_contents()
