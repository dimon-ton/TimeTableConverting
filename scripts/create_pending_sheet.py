"""
Database Setup Script for Admin Verification Workflow

This script sets up the necessary database schema for the admin verification workflow:
1. Creates 'Pending_Assignments' worksheet with 11 columns
2. Adds 'Verified_By' and 'Verified_At' columns to 'Leave_Logs' worksheet

Usage:
    python scripts/create_pending_sheet.py
"""

import gspread
from google.oauth2.service_account import Credentials
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config


def setup_pending_assignments_sheet():
    """
    Set up the Pending_Assignments worksheet and update Leave_Logs schema.
    """
    print("="*60)
    print("Admin Verification Workflow - Database Setup")
    print("="*60)

    # Authenticate with Google Sheets
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    print("\nAuthenticating with Google Sheets API...")
    try:
        creds = Credentials.from_service_account_file(config.CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        print("✓ Authentication successful")
    except FileNotFoundError:
        print(f"ERROR: credentials.json not found at {config.CREDENTIALS_FILE}")
        print("Please ensure credentials.json is in the project root directory")
        return False
    except Exception as e:
        print(f"ERROR: Authentication failed: {e}")
        return False

    # Open the existing spreadsheet
    print(f"\nOpening spreadsheet ID: {config.SPREADSHEET_ID}...")
    try:
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        print(f"✓ Opened spreadsheet: {spreadsheet.title}")
    except Exception as e:
        print(f"ERROR: Failed to open spreadsheet: {e}")
        print("Please check that SPREADSHEET_ID is correct in your .env file")
        return False

    # ==================== Create Pending_Assignments Worksheet ====================
    print("\n" + "-"*60)
    print("Step 1: Creating 'Pending_Assignments' worksheet")
    print("-"*60)

    try:
        # Check if worksheet already exists
        try:
            pending_ws = spreadsheet.worksheet("Pending_Assignments")
            print("ℹ Worksheet 'Pending_Assignments' already exists")
            print(f"  Current rows: {pending_ws.row_count}, columns: {pending_ws.col_count}")

            overwrite = input("Do you want to recreate it? (y/N): ").strip().lower()
            if overwrite == 'y':
                spreadsheet.del_worksheet(pending_ws)
                print("✓ Deleted existing worksheet")
            else:
                print("⊘ Skipping Pending_Assignments creation")
                pending_ws = None
        except gspread.WorksheetNotFound:
            pending_ws = None

        # Create new worksheet if needed
        if pending_ws is None or overwrite == 'y':
            print("\nCreating 'Pending_Assignments' worksheet...")
            pending_ws = spreadsheet.add_worksheet(
                title="Pending_Assignments",
                rows=100,
                cols=11
            )
            print("✓ Worksheet created")

            # Set up column headers
            headers = [
                "Date",
                "Absent_Teacher",
                "Day",
                "Period",
                "Class_ID",
                "Subject",
                "Substitute_Teacher",
                "Notes",
                "Created_At",
                "Processed_At",
                "Status"
            ]

            print("Setting up column headers...")
            pending_ws.update('A1:K1', [headers], value_input_option='USER_ENTERED')

            # Format header row
            print("Formatting header row...")
            pending_ws.format('A1:K1', {
                'textFormat': {'bold': True, 'fontSize': 10},
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                'horizontalAlignment': 'CENTER'
            })

            # Freeze header row
            pending_ws.freeze(rows=1)

            # Set column widths
            print("Adjusting column widths...")
            pending_ws.set_column_width('A', 120)   # Date
            pending_ws.set_column_width('B', 150)   # Absent_Teacher
            pending_ws.set_column_width('C', 80)    # Day
            pending_ws.set_column_width('D', 80)    # Period
            pending_ws.set_column_width('E', 100)   # Class_ID
            pending_ws.set_column_width('F', 120)   # Subject
            pending_ws.set_column_width('G', 150)   # Substitute_Teacher
            pending_ws.set_column_width('H', 200)   # Notes
            pending_ws.set_column_width('I', 160)   # Created_At
            pending_ws.set_column_width('J', 160)   # Processed_At
            pending_ws.set_column_width('K', 100)   # Status

            print("✓ Pending_Assignments worksheet setup complete")

    except Exception as e:
        print(f"ERROR: Failed to create Pending_Assignments worksheet: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ==================== Update Leave_Logs Worksheet ====================
    print("\n" + "-"*60)
    print("Step 2: Updating 'Leave_Logs' worksheet schema")
    print("-"*60)

    try:
        # Get Leave_Logs worksheet
        try:
            leave_logs_ws = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)
            print(f"✓ Found '{config.LEAVE_LOGS_WORKSHEET}' worksheet")
        except gspread.WorksheetNotFound:
            print(f"ERROR: '{config.LEAVE_LOGS_WORKSHEET}' worksheet not found")
            print("Please create the Leave_Logs worksheet first")
            return False

        # Get current headers
        current_headers = leave_logs_ws.row_values(1)
        print(f"\nCurrent headers ({len(current_headers)} columns):")
        print(f"  {current_headers}")

        # Check if Verified_By and Verified_At already exist
        if 'Verified_By' in current_headers and 'Verified_At' in current_headers:
            print("\n✓ Verified_By and Verified_At columns already exist")
        else:
            # Add the new columns
            print("\nAdding 'Verified_By' and 'Verified_At' columns...")

            # Append the new headers
            new_headers = current_headers + ['Verified_By', 'Verified_At']
            leave_logs_ws.update('A1:J1', [new_headers], value_input_option='USER_ENTERED')

            # Format the new header cells
            col_index_verified_by = len(current_headers) + 1  # 1-indexed
            col_index_verified_at = len(current_headers) + 2

            # Convert column indices to letters
            def col_num_to_letter(n):
                """Convert column number to Excel-style letter (1->A, 2->B, etc.)"""
                string = ""
                while n > 0:
                    n, remainder = divmod(n - 1, 26)
                    string = chr(65 + remainder) + string
                return string

            col_letter_by = col_num_to_letter(col_index_verified_by)
            col_letter_at = col_num_to_letter(col_index_verified_at)

            leave_logs_ws.format(f'{col_letter_by}1:{col_letter_at}1', {
                'textFormat': {'bold': True, 'fontSize': 10},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                'horizontalAlignment': 'CENTER'
            })

            # Set column widths
            leave_logs_ws.set_column_width(col_letter_by, 200)  # Verified_By
            leave_logs_ws.set_column_width(col_letter_at, 160)  # Verified_At

            print(f"✓ Added columns {col_letter_by} (Verified_By) and {col_letter_at} (Verified_At)")

    except Exception as e:
        print(f"ERROR: Failed to update Leave_Logs worksheet: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ==================== Success ====================
    print("\n" + "="*60)
    print("SUCCESS! Database setup complete")
    print("="*60)
    print("\nWorksheets configured:")
    print("  ✓ Pending_Assignments - 11 columns")
    print(f"  ✓ {config.LEAVE_LOGS_WORKSHEET} - Added Verified_By and Verified_At columns")
    print("\nYou can now proceed with code deployment!")
    print("\nNext steps:")
    print("  1. Deploy the modified code files")
    print("  2. Test the new workflow with a sample leave request")
    print("  3. Train admins on the new [REPORT] message format")

    return True


if __name__ == "__main__":
    success = setup_pending_assignments_sheet()
    sys.exit(0 if success else 1)
