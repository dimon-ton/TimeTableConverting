"""
Google Sheets Template Creator for Leave Logs

This script creates a new Google Sheet with the proper structure for tracking
teacher absences and substitute assignments.

Usage:
    python create_sheets_template.py

The script will:
1. Authenticate using credentials.json
2. Create a new Google Sheet named "School Timetable - Leave Logs"
3. Set up the worksheet with proper column headers
4. Share the sheet with your email (you'll be prompted)
"""

import gspread
from google.oauth2.service_account import Credentials


def create_leave_logs_sheet():
    """Create a new Google Sheet for leave logs with proper structure."""

    # Define the scope for Google Sheets API
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    print("Authenticating with Google Sheets API...")
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        client = gspread.authorize(creds)
        print("OK - Authentication successful")
    except FileNotFoundError:
        print("ERROR: credentials.json not found in current directory")
        print("Please ensure credentials.json is in the same folder as this script")
        return
    except Exception as e:
        print(f"ERROR: Authentication failed: {e}")
        return

    # Create a new spreadsheet
    sheet_name = "School Timetable - Leave Logs"
    print(f"\nCreating new Google Sheet: '{sheet_name}'...")

    try:
        spreadsheet = client.create(sheet_name)
        print(f"OK - Spreadsheet created successfully")
        print(f"Spreadsheet ID: {spreadsheet.id}")
        print(f"URL: {spreadsheet.url}")
    except Exception as e:
        print(f"ERROR: Failed to create spreadsheet: {e}")
        return

    # Get the first worksheet
    worksheet = spreadsheet.sheet1
    worksheet.update_title("Leave_Logs")

    # Set up column headers
    headers = [
        "Date",
        "Absent Teacher",
        "Day",
        "Period",
        "Class",
        "Subject",
        "Substitute Teacher",
        "Notes"
    ]

    print("\nSetting up column headers...")
    worksheet.update('A1:H1', [headers])

    # Format the header row (bold, frozen)
    print("Formatting header row...")
    worksheet.format('A1:H1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })

    # Freeze the header row
    worksheet.freeze(rows=1)

    # Set column widths for better readability
    print("Adjusting column widths...")
    worksheet.set_column_width('A', 120)  # Date
    worksheet.set_column_width('B', 150)  # Absent Teacher
    worksheet.set_column_width('C', 80)   # Day
    worksheet.set_column_width('D', 80)   # Period
    worksheet.set_column_width('E', 80)   # Class
    worksheet.set_column_width('F', 120)  # Subject
    worksheet.set_column_width('G', 150)  # Substitute Teacher
    worksheet.set_column_width('H', 200)  # Notes

    print("OK - Sheet structure created successfully")

    # Share the spreadsheet
    print("\n" + "="*60)
    print("IMPORTANT: Sharing the spreadsheet")
    print("="*60)
    email = input("\nEnter your email address to share this sheet with: ").strip()

    if email:
        try:
            spreadsheet.share(email, perm_type='user', role='writer')
            print(f"OK - Spreadsheet shared with {email}")
        except Exception as e:
            print(f"WARNING: Failed to share automatically: {e}")
            print(f"Please manually share the sheet using this URL:")
            print(f"{spreadsheet.url}")

    # Add example row
    print("\nAdding example data row...")
    example_row = [
        "2025-11-20",
        "T001",
        "Mon",
        "3",
        "ป.4",
        "Math",
        "T005",
        "Sick leave"
    ]
    worksheet.update('A2:H2', [example_row])
    print("OK - Example row added")

    print("\n" + "="*60)
    print("SUCCESS! Google Sheet created and configured")
    print("="*60)
    print(f"\nSheet Name: {sheet_name}")
    print(f"Worksheet: Leave_Logs")
    print(f"URL: {spreadsheet.url}")
    print("\nYou can now:")
    print("1. Open the sheet and review the structure")
    print("2. Delete the example row (row 2) if desired")
    print("3. Start adding leave log entries manually")
    print("4. Use sync_leave_logs.py to read data from this sheet")
    print("\nSave this URL and Spreadsheet ID for future reference!")


if __name__ == "__main__":
    print("="*60)
    print("Google Sheets Leave Logs Template Creator")
    print("="*60)
    create_leave_logs_sheet()
