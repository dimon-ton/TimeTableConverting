def add_absence(
    date: str,
    absent_teacher: str,
    day: str,
    period: int,
    class_id: str,
    subject: str = "",
    substitute_teacher: str = "",
    notes: str = ""
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

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get authenticated client
        client = get_sheets_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(config.LEAVE_LOGS_WORKSHEET)

        # Prepare row data
        row = [
            date,
            absent_teacher,
            day,
            str(period),
            class_id,
            subject,
            substitute_teacher,
            notes
        ]

        # Append the row
        worksheet.append_row(row, value_input_option='USER_ENTERED')

        print(f"OK - Added absence entry to '{config.LEAVE_LOGS_WORKSHEET}' for {absent_teacher} on {date}")
        return True

    except Exception as e:
        print(f"ERROR: Failed to add absence to '{config.LEAVE_LOGS_WORKSHEET}': {e}")
        return False