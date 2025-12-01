
import sys
import os
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from src.utils.sheet_utils import write_teacher_hours_snapshot

def test_snapshot_logic_6_columns():
    print("="*60)
    print("TESTING: write_teacher_hours_snapshot logic (6 columns)")
    print("="*60)

    # 1. Mock Data
    mock_leave_logs = [
        {'Date': '2025-11-25', 'Absent_Teacher': 'T001', 'Substitute_Teacher': 'T002'}, # T001 absent, T002 sub
        {'Date': '2025-11-26', 'Absent_Teacher': 'T002', 'Substitute_Teacher': 'Not Found'}, # T002 absent, no sub
        {'Date': '2025-11-29', 'Absent_Teacher': 'T003', 'Substitute_Teacher': 'T001'}, # T003 absent, T001 sub
    ]

    # 2. Mock Sheets Client
    mock_client = MagicMock()
    mock_spreadsheet = MagicMock()
    mock_leave_ws = MagicMock()
    mock_tracking_ws = MagicMock()

    # Setup chain
    mock_client.open_by_key.return_value = mock_spreadsheet
    
    def get_worksheet_side_effect(name):
        if name == 'Leave_Logs':
            return mock_leave_ws
        elif name == 'Teacher_Hours_Tracking':
            return mock_tracking_ws
        return MagicMock()
    
    mock_spreadsheet.worksheet.side_effect = get_worksheet_side_effect
    
    # Setup return values
    mock_leave_ws.get_all_records.return_value = mock_leave_logs

    # 3. Run Test with Patch
    print("Running write_teacher_hours_snapshot('2025-11-29')...")
    
    with patch('src.utils.sheet_utils.get_sheets_client', return_value=mock_client):
        write_teacher_hours_snapshot('2025-11-29')

    # 4. Verify Results
    print("\nVerifying calls to 'Teacher_Hours_Tracking' sheet...")
    
    # Check if append_row was called
    if not mock_tracking_ws.append_row.called:
        print("FAILED: append_row was not called!")
        return

    calls = mock_tracking_ws.append_row.call_args_list
    print(f"append_row called {len(calls)} times (once per teacher).")
    
    # Inspect a specific call (e.g., for T001)
    # T001: Absent once (25th), Subbed once (29th)
    # T001 Name: ครูสุกฤษฎิ์ (from teacher_full_names.json) 
    
    found_t001 = False
    for call in calls:
        args, kwargs = call
        row_data = args[0]
        
        # Check if this row is for T001
        if row_data[1] == 'T001':
            found_t001 = True
            print("\nVerifying T001 Record:")
            print(f"  Row Data: {row_data}")
            
            # Expected Indices for 6 columns:
            # 0: Date (2025-11-29)
            # 1: ID (T001)
            # 2: Name (ครูสุกฤษฎิ์)
            # 3: Regular_Periods_Today (depends on timetable, T001 has classes on Sat? -> 0)
            # 4: Daily_Workload (Cum Sub - Cum Abs) -> (1 - 1 = 0)
            # 5: Updated At
            
            if len(row_data) != 6:
                print(f"  FAILED: Expected 6 columns, got {len(row_data)}")
            else:
                print(f"  PASSED: Column count is 6")

            # Daily_Workload = cumulative_substitute - cumulative_absence
            # T001: subbed once (29th), absent once (25th)
            # Cumulative Sub = 1, Cumulative Abs = 1
            # Daily_Workload = 1 - 1 = 0
            if row_data[4] == 0:
                 print(f"  PASSED: Daily_Workload is 0 (1-1)")
            else:
                 print(f"  FAILED: Daily_Workload is {row_data[4]} (Expected 0)")

    if not found_t001:
        print("FAILED: T001 record not found in writes.")

    print("\nTEST COMPLETED")

if __name__ == "__main__":
    test_snapshot_logic_6_columns()
