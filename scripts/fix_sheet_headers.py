"""
Fix Google Sheets Headers

This script adds the missing "Day" column to the Leave_Logs sheet.
"""

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1KpQZlrJk03ZS_Q0bTWvxHjG9UFiD1xPZGyIsQfRkRWo"
WORKSHEET_NAME = "Leave_Logs"
CREDENTIALS_FILE = "credentials.json"

def fix_headers():
    """Fix the headers to include the Day column."""
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    print("Connecting to Google Sheets...")
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

    # Get current data
    print("Reading current data...")
    all_values = worksheet.get_all_values()

    if not all_values:
        print("Sheet is empty!")
        return

    print(f"Current headers: {all_values[0]}")

    # Clear the sheet
    print("Clearing sheet...")
    worksheet.clear()

    # Set correct headers
    correct_headers = [
        "Date",
        "Absent Teacher",
        "Day",
        "Period",
        "Class",
        "Subject",
        "Substitute Teacher",
        "Notes"
    ]

    print(f"Setting correct headers: {correct_headers}")
    worksheet.update('A1:H1', [correct_headers])

    # Format header
    worksheet.format('A1:H1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })

    # If there was data, we need to reorganize it
    if len(all_values) > 1:
        print(f"\nFound {len(all_values)-1} data rows to reorganize...")

        # Old structure: Date, Absent Teacher, Period, Class, Subject, Substitute Teacher, Notes
        # New structure: Date, Absent Teacher, Day, Period, Class, Subject, Substitute Teacher, Notes
        # The data got shifted, so: Mon is in Period position, 3 is in Class position, etc.

        new_rows = []
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) < 7:
                print(f"  Skipping row {i}: insufficient data")
                continue

            # Reorganize: Old row was [Date, Teacher, Mon, 3, ป.4, Math, "", "Test..."]
            # Should be: [Date, Teacher, Mon, 3, ป.4, Math, "", "Test..."]
            new_row = [
                row[0],  # Date
                row[1],  # Absent Teacher
                row[2],  # Day (was in old Period position)
                row[3],  # Period (was in old Class position)
                row[4],  # Class (was in old Subject position)
                row[5],  # Subject (was in old Substitute position)
                row[6] if len(row) > 6 else "",  # Substitute Teacher
                row[7] if len(row) > 7 else ""   # Notes
            ]
            new_rows.append(new_row)
            print(f"  Row {i}: {new_row}")

        if new_rows:
            print(f"\nWriting {len(new_rows)} reorganized rows...")
            worksheet.append_rows(new_rows, value_input_option='USER_ENTERED')

    print("\nDone! Headers fixed.")
    print(f"Sheet URL: {spreadsheet.url}")

if __name__ == "__main__":
    fix_headers()
