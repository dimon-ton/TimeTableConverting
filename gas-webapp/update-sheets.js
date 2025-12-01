/**
 * Update Google Sheets Structure
 * This script updates the Teacher_Hours_Tracking worksheet to match the new 6-column structure
 *
 * Spreadsheet constants are now in DataConstants.js
 */

function updateSheetsStructure() {
  try {
    // Open spreadsheet and get the sheet
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = ss.getSheetByName(SHEET_NAME);

    if (!sheet) {
      throw new Error(`Sheet "${SHEET_NAME}" not found`);
    }

    // Get all data
    const range = sheet.getDataRange();
    const values = range.getValues();

    if (values.length <= 1) {
      Logger.log('No data found in sheet');
      return;
    }

    // Get headers
    const headers = values[0];

    // Find column indices
    const dateCol = headers.indexOf('Date');
    const teacherIdCol = headers.indexOf('Teacher_ID');
    const teacherNameCol = headers.indexOf('Teacher_Name');
    const regularPeriodsCol = headers.indexOf('Regular_Periods_Today');
    const dailyWorkloadCol = headers.indexOf('Daily_Workload');

    // Define target headers
    const targetHeaders = ['Date', 'Teacher_ID', 'Teacher_Name', 'Regular_Periods_Today', 'Daily_Workload', 'Updated_At'];

    // Create new data structure with target headers
    const newValues = [targetHeaders];

    for (let i = 1; i < values.length; i++) {
      const row = values[i];
      if (row[0]) { // Skip empty rows
        // Calculate daily workload if not present
        const regularPeriods = parseFloat(row[regularPeriodsCol]) || 0;
        const dailyWorkload = regularPeriods; // Default to regular periods if no absences/substitutions
        const now = new Date();
        const updatedAt = now.toISOString();

        // Create new row with 6 columns
        const newRow = [
          row[dateCol] || new Date().toISOString().split('T')[0], // Date
          row[teacherIdCol] || '', // Teacher_ID
          row[teacherNameCol] || '', // Teacher_Name
          row[regularPeriodsCol] || 0, // Regular_Periods_Today
          dailyWorkload, // Daily_Workload (calculated)
          updatedAt // Updated_At
        ];

        newValues.push(newRow);
      }
    }

    // Clear existing data and write new structure
    sheet.clearContents();
    sheet.getRange(1, 1, newValues.length, 6).setValues(newValues);

    Logger.log(`Updated ${newValues.length} rows with new 6-column structure`);

  } catch (error) {
    Logger.log('Error updating sheets: ' + error.message);
    throw error;
  }
}

// Run the update function
if (typeof updateSheetsStructure === 'function') {
  updateSheetsStructure();
}