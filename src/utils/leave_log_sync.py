"""
Google Sheets Leave Logs Sync Module

This module provides functionality to read teacher absence and leave logs
from Google Sheets and convert them to the format used by find_substitute.py.

Usage:
    from sync_leave_logs import load_leave_logs_from_sheets

    leave_logs = load_leave_logs_from_sheets()
    # Returns list of timetable entries marking leave periods
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict

from src.config import config


def get_sheets_client():
    """
    Create and return an authenticated Google Sheets client.

    Returns:
        gspread.Client: Authenticated client for accessing Google Sheets

    Raises:
        FileNotFoundError: If credentials.json is not found
        Exception: If authentication fails
    """
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    try:
        creds = Credentials.from_service_account_file(config.config.CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Credentials file '{config.CREDENTIALS_FILE}' not found. "
            "Please ensure credentials.json is in the current directory."
        )
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Sheets: {e}")


def load_leave_logs_from_sheets() -> List[Dict]:
    """
    Load leave logs from Google Sheets and convert to timetable entry format.

    Returns:
        List[Dict]: List of timetable entries in the format:
            {
                "teacher_id": str,
                "subject_id": str,
                "day_id": str,
                "period_id": int,
                "class_id": str
            }

    Raises:
        Exception: If unable to access the spreadsheet or worksheet
    """
    try:
        # Get authenticated client
        client = get_sheets_client()

        # Open the spreadsheet
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)

        # Get all records (returns list of dictionaries)
        # First row is assumed to be headers
        records = worksheet.get_all_records()

        # Convert to leave log format
        leave_logs = []
        for record in records:
            # Skip empty rows or rows without required data
            if not record.get('Absent Teacher') or not record.get('Day'):
                continue

            try:
                # Convert to timetable entry format
                entry = {
                    "teacher_id": str(record['Absent Teacher']).strip(),
                    "subject_id": str(record.get('Subject', '')).strip(),
                    "day_id": str(record['Day']).strip(),
                    "period_id": int(record['Period']),
                    "class_id": str(record.get('Class', '')).strip()
                }
                leave_logs.append(entry)
            except (ValueError, KeyError) as e:
                # Skip rows with invalid data
                print(f"WARNING: Skipping invalid row: {record} - Error: {e}")
                continue

        return leave_logs

    except gspread.exceptions.SpreadsheetNotFound:
        raise Exception(
            f"Spreadsheet with ID '{config.SPREADSHEET_ID}' not found. "
            "Please check the config.SPREADSHEET_ID in this file."
        )
    except gspread.exceptions.WorksheetNotFound:
        raise Exception(
            f"Worksheet '{config.LEAVE_LOGS_WORKSHEET}' not found in spreadsheet. "
            "Please ensure the worksheet exists and the name is correct."
        )
    except Exception as e:
        raise Exception(f"Failed to load leave logs from Google Sheets: {e}")


def get_leave_logs_summary() -> Dict:
    """
    Get summary statistics about leave logs in Google Sheets.

    Returns:
        Dict: Summary with keys:
            - total_entries: Total number of leave log entries
            - teachers: Set of unique teacher IDs with leaves
            - days: Set of unique days with leaves
            - date_range: Earliest and latest dates (if available)
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)
        records = worksheet.get_all_records()

        # Filter out empty rows
        valid_records = [r for r in records if r.get('Absent Teacher') and r.get('Day')]

        summary = {
            "total_entries": len(valid_records),
            "teachers": set(str(r['Absent Teacher']).strip() for r in valid_records),
            "days": set(str(r['Day']).strip() for r in valid_records),
            "classes": set(str(r.get('Class', '')).strip() for r in valid_records if r.get('Class')),
        }

        # Try to get date range if dates are available
        dates = [r.get('Date') for r in valid_records if r.get('Date')]
        if dates:
            summary['date_range'] = {
                'earliest': min(dates),
                'latest': max(dates)
            }

        return summary

    except Exception as e:
        raise Exception(f"Failed to get leave logs summary: {e}")


def test_connection():
    """
    Test the connection to Google Sheets and print diagnostic information.

    This is useful for verifying the setup is working correctly.
    """
    print("="*60)
    print("Google Sheets Connection Test")
    print("="*60)

    print(f"\nSpreadsheet ID: {config.SPREADSHEET_ID}")
    print(f"Worksheet Name: {config.LEAVE_LOGS_WORKSHEET}")
    print(f"Credentials File: {config.CREDENTIALS_FILE}")

    try:
        print("\n1. Authenticating...")
        client = get_sheets_client()
        print("   OK - Authentication successful")

        print("\n2. Opening spreadsheet...")
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        print(f"   OK - Opened: '{spreadsheet.title}'")
        print(f"   URL: {spreadsheet.url}")

        print("\n3. Accessing worksheet...")
        worksheet = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)
        print(f"   OK - Found worksheet: '{worksheet.title}'")
        print(f"   Rows: {worksheet.row_count}")
        print(f"   Columns: {worksheet.col_count}")

        print("\n4. Reading data...")
        records = worksheet.get_all_records()
        print(f"   OK - Read {len(records)} rows")

        print("\n5. Converting to leave logs format...")
        leave_logs = load_leave_logs_from_sheets()
        print(f"   OK - Converted {len(leave_logs)} valid entries")

        if leave_logs:
            print("\n6. Sample entry:")
            print(f"   {leave_logs[0]}")

        print("\n7. Summary:")
        summary = get_leave_logs_summary()
        print(f"   Total entries: {summary['total_entries']}")
        print(f"   Unique teachers: {len(summary['teachers'])}")
        print(f"   Teachers: {', '.join(sorted(summary['teachers']))}")
        print(f"   Days covered: {', '.join(sorted(summary['days']))}")
        if 'date_range' in summary:
            print(f"   Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")

        print("\n" + "="*60)
        print("SUCCESS! Google Sheets connection is working properly")
        print("="*60)

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\n" + "="*60)
        print("FAILED - Please check the error message above")
        print("="*60)
        return False


if __name__ == "__main__":
    # Run connection test when script is run directly
    test_connection()
