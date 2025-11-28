"""
Google Sheets Utilities

This module provides a centralized set of functions for interacting with the
Google Sheet, including getting the client, logging requests, and reading data.
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import Optional, Dict, List
import json

from src.config import config

def get_sheets_client():
    """Create and return an authenticated Google Sheets client."""
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    try:
        creds = Credentials.from_service_account_file(config.CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Credentials file '{config.CREDENTIALS_FILE}' not found. "
            "Please ensure credentials.json is in the current directory."
        )
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Sheets: {e}")

def log_request_to_sheet(
    raw_message: str,
    leave_data: Optional[Dict],
    status: str
):
    """
    Log the result of a parsing attempt to the 'Leave_Requests' sheet.

    Args:
        raw_message: The original message from the user.
        leave_data: The structured data dictionary returned by the parser, or None if failed.
        status: A string indicating the outcome (e.g., "Success", "Failed").
    """
    if not config.SPREADSHEET_ID:
        print("WARNING: SPREADSHEET_ID not set. Skipping request logging.")
        return

    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)

        # Get or create the worksheet
        try:
            worksheet = spreadsheet.worksheet(config.LEAVE_REQUESTS_WORKSHEET)
        except gspread.WorksheetNotFound:
            print(f"Worksheet '{config.LEAVE_REQUESTS_WORKSHEET}' not found. Creating it...")
            worksheet = spreadsheet.add_worksheet(
                title=config.LEAVE_REQUESTS_WORKSHEET, rows=1, cols=7
            )
            # Add headers to the new sheet
            headers = [
                "Timestamp", "Raw Message", "Teacher Name",
                "Date", "Periods", "Reason", "Status"
            ]
            worksheet.append_row(headers, value_input_option='USER_ENTERED')
            print(f"OK - Created '{config.LEAVE_REQUESTS_WORKSHEET}' worksheet and added headers.")

        # Prepare row data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if leave_data:
            row = [
                timestamp,
                raw_message,
                leave_data.get('teacher_name', ''),
                leave_data.get('date', ''),
                str(leave_data.get('periods', [])), # Convert list to string
                leave_data.get('reason', ''),
                status
            ]
        else:
            row = [
                timestamp,
                raw_message,
                "", "", "", "", # Empty columns for failed parse
                status
            ]

        # Append the row
        worksheet.append_row(row, value_input_option='USER_ENTERED')
        print(f"OK - Logged request to '{config.LEAVE_REQUESTS_WORKSHEET}'")

    except Exception as e:
        import traceback
        print(f"ERROR: Failed to log request to Google Sheets: {e}")
        traceback.print_exc()

def load_requests_from_sheet(target_date: str) -> List[Dict]:
    """
    Reads leave requests from the 'Leave_Requests' sheet for a specific date.

    Args:
        target_date: The date to filter requests for (YYYY-MM-DD).

    Returns:
        A list of leave request dictionaries, each containing:
        - teacher_name (str)
        - date (str)
        - periods (list[int])
        - reason (str)
    """
    print(f"Loading leave requests for {target_date} from '{config.LEAVE_REQUESTS_WORKSHEET}' sheet...")

    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(config.LEAVE_REQUESTS_WORKSHEET)

        all_requests = worksheet.get_all_records() # Reads sheet as a list of dicts

        requests_for_date = []
        for request in all_requests:
            # Filter by date and ensure status is 'Success'
            if request.get('Date') == target_date and str(request.get('Status')).startswith('Success'):
                try:
                    # The 'Periods' column is a string like "[1, 2, 3]"
                    periods_str = request.get('Periods', '[]')
                    periods = json.loads(periods_str)
                    
                    if not isinstance(periods, list):
                        print(f"WARNING: Skipping request with invalid periods format: {request}")
                        continue

                    requests_for_date.append({
                        "teacher_name": request.get("Teacher Name"),
                        "date": request.get("Date"),
                        "periods": periods,
                        "reason": request.get("Reason")
                    })
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"WARNING: Could not parse periods '{periods_str}' for request: {request}. Error: {e}. Skipping.")
                    continue
        
        print(f"Found {len(requests_for_date)} valid leave requests.")
        return requests_for_date

    except Exception as e:
        import traceback
        print(f"ERROR: Failed to load requests from Google Sheets: {e}")
        traceback.print_exc()
        return []

def load_substitute_logs_from_sheet(limit_date: Optional[str] = None) -> List[Dict]:
    """
    Load historical substitute assignments from the 'Leave_Logs' sheet.

    This function reads all substitute assignments from Google Sheets and
    converts them to the format expected by the substitute finding algorithm.

    Args:
        limit_date: Optional date limit (YYYY-MM-DD). Only loads records on or before this date.

    Returns:
        List of dicts with structure:
        {
            "absent_teacher_id": str,
            "substitute_teacher_id": str or None,
            "subject_id": str,
            "class_id": str,
            "day_id": str,
            "period_id": int
        }
    """
    print(f"Loading substitute logs from '{config.LEAVE_LOGS_WORKSHEET}' sheet...")

    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)

        # Get all records (expects headers: Date, Absent_Teacher, Day, Period, Class_ID, Subject, Substitute_Teacher, Notes)
        all_records = worksheet.get_all_records()

        substitute_logs = []
        for record in all_records:
            # Get date and apply filter if needed
            record_date = record.get('Date', '')
            if limit_date and record_date > limit_date:
                continue  # Skip future dates

            # Extract fields
            absent_teacher = record.get('Absent_Teacher', '').strip()
            substitute_teacher = record.get('Substitute_Teacher', '').strip()
            subject = record.get('Subject', '').strip()
            class_id = record.get('Class_ID', '').strip()
            day = record.get('Day', '').strip()
            period = record.get('Period', '')

            # Skip invalid records
            if not absent_teacher or not day or not period:
                continue

            # Convert period to int
            try:
                period_int = int(period)
            except (ValueError, TypeError):
                print(f"WARNING: Invalid period '{period}' in record. Skipping.")
                continue

            # Handle substitute_teacher field
            # Map empty strings, "Not Found", "None", etc. to None
            if not substitute_teacher or substitute_teacher.upper() in ['NOT FOUND', 'NONE', 'N/A', '-']:
                substitute_teacher_id = None
            else:
                substitute_teacher_id = substitute_teacher

            # Add to list in the format expected by substitute.py
            substitute_logs.append({
                "absent_teacher_id": absent_teacher,
                "substitute_teacher_id": substitute_teacher_id,
                "subject_id": subject,
                "class_id": class_id,
                "day_id": day,
                "period_id": period_int
            })

        print(f"Loaded {len(substitute_logs)} historical substitute records from Google Sheets")
        return substitute_logs

    except gspread.WorksheetNotFound:
        print(f"WARNING: Worksheet '{config.LEAVE_LOGS_WORKSHEET}' not found. Returning empty list.")
        return []
    except Exception as e:
        import traceback
        print(f"ERROR: Failed to load substitute logs from Google Sheets: {e}")
        traceback.print_exc()
        return []


def add_absence(
    date: str,
    absent_teacher: str,
    day: str,
    period: int,
    class_id: str,
    subject: str = "",
    substitute_teacher: str = "",
    notes: str = "",
    verified_by: str = "",
    verified_at: str = ""
) -> bool:
    """
    Add a teacher absence entry to the 'Leave_Logs' Google Sheet.

    Args:
        date: Date of absence (YYYY-MM-DD format)
        absent_teacher: Teacher ID (e.g., "T001")
        day: Day of week (e.g., "Mon", "Tue", etc.)
        period: Period number
        class_id: Class ID (e.g., "ป.4", "ม.1")
        subject: Subject name (optional)
        substitute_teacher: Substitute teacher ID (optional)
        notes: Additional notes (optional)
        verified_by: LINE User ID of admin who verified (optional)
        verified_at: Timestamp of verification (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get authenticated client
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)

        # Prepare row data (now includes verified_by and verified_at)
        row = [
            date,
            absent_teacher,
            day,
            str(period),
            class_id,
            subject,
            substitute_teacher,
            notes,
            verified_by,
            verified_at
        ]

        # Append the row
        worksheet.append_row(row, value_input_option='USER_ENTERED')

        print(f"OK - Added absence entry to '{config.LEAVE_LOGS_WORKSHEET}' for {absent_teacher} on {date}")
        return True

    except Exception as e:
        print(f"ERROR: Failed to add absence to '{config.LEAVE_LOGS_WORKSHEET}': {e}")
        return False


# ==================== Pending Assignments Functions ====================

def add_pending_assignment(
    date: str,
    absent_teacher: str,
    day: str,
    period: int,
    class_id: str,
    subject: str = "",
    substitute_teacher: str = "",
    notes: str = "",
    processed_at: str = ""
) -> bool:
    """
    Add a substitute assignment to the 'Pending_Assignments' sheet (not yet verified).

    Args:
        date: Date of absence (YYYY-MM-DD format)
        absent_teacher: Teacher ID (e.g., "T001")
        day: Day of week (e.g., "Mon", "Tue", etc.)
        period: Period number
        class_id: Class ID (e.g., "ป.4", "ม.1")
        subject: Subject name (optional)
        substitute_teacher: Substitute teacher ID or "Not Found" (optional)
        notes: Additional notes (optional)
        processed_at: Timestamp when daily processing completed (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get authenticated client
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)

        # Get or create the Pending_Assignments worksheet
        try:
            worksheet = spreadsheet.worksheet(config.PENDING_ASSIGNMENTS_WORKSHEET)
        except Exception:
            print(f"Worksheet '{config.PENDING_ASSIGNMENTS_WORKSHEET}' not found. Creating it...")
            worksheet = spreadsheet.add_worksheet(
                title=config.PENDING_ASSIGNMENTS_WORKSHEET, rows=100, cols=11
            )
            # Add headers
            headers = [
                "Date", "Absent_Teacher", "Day", "Period", "Class_ID",
                "Subject", "Substitute_Teacher", "Notes", "Created_At",
                "Processed_At", "Status"
            ]
            worksheet.append_row(headers, value_input_option='USER_ENTERED')
            print(f"OK - Created '{config.PENDING_ASSIGNMENTS_WORKSHEET}' worksheet")

        # Prepare row data
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            date,
            absent_teacher,
            day,
            str(period),
            class_id,
            subject,
            substitute_teacher,
            notes,
            created_at,
            processed_at,
            "pending"
        ]

        # Append the row
        worksheet.append_row(row, value_input_option='USER_ENTERED')

        print(f"OK - Added pending assignment to '{config.PENDING_ASSIGNMENTS_WORKSHEET}' for {absent_teacher} on {date}")
        return True

    except Exception as e:
        print(f"ERROR: Failed to add pending assignment: {e}")
        return False


def load_pending_assignments(target_date: str) -> List[Dict]:
    """
    Load all pending assignments for a specific date.

    Args:
        target_date: Date in YYYY-MM-DD format

    Returns:
        List of dictionaries with assignment details
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)

        try:
            worksheet = spreadsheet.worksheet(config.PENDING_ASSIGNMENTS_WORKSHEET)
        except Exception:
            print(f"Worksheet '{config.PENDING_ASSIGNMENTS_WORKSHEET}' not found")
            return []

        # Get all rows
        all_rows = worksheet.get_all_records()

        # Filter for target date and pending status
        pending_assignments = [
            row for row in all_rows
            if row.get('Date') == target_date and row.get('Status') == 'pending'
        ]

        print(f"Loaded {len(pending_assignments)} pending assignments for {target_date}")
        return pending_assignments

    except Exception as e:
        print(f"ERROR: Failed to load pending assignments: {e}")
        import traceback
        traceback.print_exc()
        return []


def delete_pending_assignments(target_date: str) -> int:
    """
    Delete pending assignments after they've been finalized.

    Args:
        target_date: Date in YYYY-MM-DD format

    Returns:
        Number of rows deleted
    """
    try:
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)

        try:
            worksheet = spreadsheet.worksheet(config.PENDING_ASSIGNMENTS_WORKSHEET)
        except Exception:
            print(f"Worksheet '{config.PENDING_ASSIGNMENTS_WORKSHEET}' not found")
            return 0

        # Get all rows
        all_rows = worksheet.get_all_values()

        # Find rows to delete (skip header)
        rows_to_delete = []
        for idx, row in enumerate(all_rows[1:], start=2):  # Start from row 2 (1-indexed)
            if len(row) >= 11:  # Ensure row has enough columns
                date_val = row[0]  # Date column
                status_val = row[10]  # Status column
                if date_val == target_date and status_val == 'pending':
                    rows_to_delete.append(idx)

        # Delete rows in reverse order to maintain indices
        deleted_count = 0
        for row_idx in reversed(rows_to_delete):
            worksheet.delete_rows(row_idx)
            deleted_count += 1

        print(f"Deleted {deleted_count} pending assignments for {target_date}")
        return deleted_count

    except Exception as e:
        print(f"ERROR: Failed to delete pending assignments: {e}")
        import traceback
        traceback.print_exc()
        return 0


def expire_old_pending_assignments() -> int:
    """
    Expire pending assignments older than PENDING_EXPIRATION_DAYS.
    Changes Status from "pending" to "expired" for audit trail.

    Returns:
        Number of assignments expired
    """
    try:
        from datetime import timedelta

        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)

        try:
            worksheet = spreadsheet.worksheet(config.PENDING_ASSIGNMENTS_WORKSHEET)
        except Exception:
            print(f"Worksheet '{config.PENDING_ASSIGNMENTS_WORKSHEET}' not found")
            return 0

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=config.PENDING_EXPIRATION_DAYS)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")

        # Get all rows
        all_rows = worksheet.get_all_values()

        # Find rows to expire
        expired_count = 0
        for idx, row in enumerate(all_rows[1:], start=2):  # Start from row 2 (1-indexed)
            if len(row) >= 11:
                created_at = row[8]  # Created_At column
                status = row[10]  # Status column

                # Check if pending and older than cutoff
                if status == 'pending' and created_at < cutoff_str:
                    # Update status to "expired"
                    worksheet.update_cell(idx, 11, "expired")  # Column 11 is Status
                    expired_count += 1

        print(f"Expired {expired_count} old pending assignments (older than {config.PENDING_EXPIRATION_DAYS} days)")
        return expired_count

    except Exception as e:
        print(f"ERROR: Failed to expire old pending assignments: {e}")
        import traceback
        traceback.print_exc()
        return 0


def finalize_pending_assignment(target_date: str, verified_by: str) -> int:
    """
    Move pending assignments to Leave_Logs after admin verification.

    Args:
        target_date: Date in YYYY-MM-DD format
        verified_by: LINE User ID of admin who verified

    Returns:
        Number of assignments finalized
    """
    try:
        # Load pending assignments
        pending_assignments = load_pending_assignments(target_date)

        if not pending_assignments:
            print(f"No pending assignments found for {target_date}")
            return 0

        # Current timestamp for verification
        verified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Finalize each assignment
        finalized_count = 0
        for assignment in pending_assignments:
            success = add_absence(
                date=assignment.get('Date', ''),
                absent_teacher=assignment.get('Absent_Teacher', ''),
                day=assignment.get('Day', ''),
                period=int(assignment.get('Period', 0)),
                class_id=assignment.get('Class_ID', ''),
                subject=assignment.get('Subject', ''),
                substitute_teacher=assignment.get('Substitute_Teacher', ''),
                notes=assignment.get('Notes', ''),
                verified_by=verified_by,
                verified_at=verified_at
            )

            if success:
                finalized_count += 1

        # Delete pending assignments after successful finalization
        if finalized_count > 0:
            delete_pending_assignments(target_date)

        print(f"Finalized {finalized_count}/{len(pending_assignments)} pending assignments for {target_date}")
        return finalized_count

    except Exception as e:
        print(f"ERROR: Failed to finalize pending assignments: {e}")
        import traceback
        traceback.print_exc()
        return 0
