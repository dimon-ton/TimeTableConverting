"""
Clean up incorrect Leave_Logs entries from the bug.

This script removes the 3 entries for 2025-11-21 that have wrong teacher IDs
(T007, T017) instead of the correct absent teacher (T004).
"""

from src.config import config
from src.utils.sheet_utils import get_sheets_client

def cleanup_bad_logs():
    """Delete incorrect Leave_Logs entries for 2025-11-21"""
    print("Connecting to Google Sheets...")
    client = get_sheets_client()
    spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)

    print(f"Reading all entries from '{config.LEAVE_LOGS_WORKSHEET}'...")
    all_records = worksheet.get_all_records()

    print(f"Total entries: {len(all_records)}")
    print("\nLooking for entries to delete (2025-11-21 with T007/T017)...")

    # Find rows to delete (need to track row numbers, starting from 2 since row 1 is headers)
    rows_to_delete = []
    for idx, record in enumerate(all_records):
        row_num = idx + 2  # Add 2 because: 1 for header, 1 for 0-based index
        if record.get('Date') == '2025-11-21' and record.get('Absent Teacher') in ['T007', 'T017']:
            rows_to_delete.append(row_num)
            print(f"  Row {row_num}: Date={record.get('Date')}, Absent={record.get('Absent Teacher')}, Period={record.get('Period')}")

    if not rows_to_delete:
        print("\nNo incorrect entries found. Sheet is clean.")
        return

    print(f"\nFound {len(rows_to_delete)} rows to delete.")
    print("Deleting rows (starting from bottom to preserve row numbers)...")

    # Delete from bottom to top to preserve row numbers
    for row_num in sorted(rows_to_delete, reverse=True):
        worksheet.delete_rows(row_num)
        print(f"  Deleted row {row_num}")

    print(f"\nCleanup complete! Deleted {len(rows_to_delete)} incorrect entries.")

if __name__ == "__main__":
    cleanup_bad_logs()
