/**
 * Test Friday Absence Scenario
 * Creates mock data for Friday with 3 absent teachers
 * This simulates realistic teacher absence patterns
 *
 * Note: Constants (SPREADSHEET_ID, SHEET_NAME, TEACHER_NAMES)
 * are imported from DataConstants.js
 */

/**
 * Add Friday test data with 3 absent teachers
 * Randomly selects teachers who are absent on Friday
 */
function addFridayTestData() {
  try {
    console.log('Adding Friday test data with 3 absent teachers...');

    // Open spreadsheet and get the sheet
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = ss.getSheetByName(SHEET_NAME);

    if (!sheet) {
      throw new Error(`Sheet "${SHEET_NAME}" not found`);
    }

    // Clear existing data for clean test
    sheet.getRange(2, 1, sheet.getLastRow(), 6).clearContent();

    // Randomly select 3 teachers to be absent on Friday
    const allTeacherIds = Object.keys(TEACHER_NAMES);
    const absentTeacherIds = randomlySelectTeachers(allTeacherIds, 3);

    console.log('Absent teachers on Friday:', absentTeacherIds.map(id => `${id} - ${TEACHER_NAMES[id]}`));

    // Friday test data with absences and substitutions
    const fridayData = [
      // Regular Friday schedule for most teachers (5-6 periods)
      ['2024-11-29', 'T001', 'ครูสุกฤษฎิ์', 5, 5, new Date()], // Present - normal schedule
      ['2024-11-29', 'T002', 'ครูอำพร', 4, 4, new Date()], // Present - normal schedule
      ['2024-11-29', 'T003', 'ครูกฤตชยากร', 6, 6, new Date()], // Present - normal schedule
      ['2024-11-29', 'T004', 'ครูพิมล', 5, 5, new Date()], // Present - normal schedule
      ['2024-11-29', 'T005', 'ครูสุจิตร', 4, 4, new Date()], // Present - normal schedule

      // ABSENT Teacher 1: Reduced workload due to absence
      ...absentTeacherIds.includes('T006') ? [] : [['2024-11-29', 'T006', 'ครูปาณิสรา', 3, 2, new Date()]], // 3 periods, but only 2 due to absence
      ...absentTeacherIds.includes('T007') ? [] : [['2024-11-29', 'T007', 'ครูวิยะดา', 2, 2, new Date()]], // 2 periods, but only 1 due to absence

      // Present teachers with normal Friday schedule
      ['2024-11-29', 'T008', 'ครูดวงใจ', 8, 8, new Date()], // Present - high workload
      ['2024-11-29', 'T010', 'ครูพัฒนศักดิ์', 7, 7, new Date()], // Present - normal schedule
      ['2024-11-29', 'T011', 'ครูบัวลอย', 6, 6, new Date()], // Present - normal schedule
      ['2024-11-29', 'T012', 'ครูอภิชญา', 5, 5, new Date()], // Present - normal schedule

      // ABSENT Teacher 2: Reduced workload due to absence
      ...absentTeacherIds.includes('T013') ? [] : [['2024-11-29', 'T013', 'ครูสรัญญา', 5, 3, new Date()]], // 5 periods, but only 3 due to absence

      // ABSENT Teacher 3: Reduced workload due to absence
      ...absentTeacherIds.includes('T015') ? [] : [['2024-11-29', 'T015', 'ครูจุฑารัตน์', 4, 2, new Date()]], // 4 periods, but only 2 due to absence

      // Additional present teachers
      ['2024-11-29', 'T016', 'ครูจิตยาภรณ์', 5, 5, new Date()], // Present - normal schedule
      ['2024-11-29', 'T017', 'ครูจรรยาภรณ์', 6, 6, new Date()], // Present - normal schedule
      ['2024-11-29', 'T018', 'ครูสิทธิศักดิ์', 4, 4, new Date()], // Present - normal schedule
    ].filter(row => row.length > 0); // Filter out empty arrays for absent teachers

    // Create headers and data rows
    const headers = ['Date', 'Teacher_ID', 'Teacher_Name', 'Regular_Periods_Today', 'Daily_Workload', 'Updated_At'];
    const allData = [headers, ...fridayData];

    // Write data to sheet
    sheet.getRange(1, 1, allData.length, allData[0].length).setValues(allData);

    // Calculate summary statistics
    const presentTeachers = fridayData.length;
    const totalRegularPeriods = fridayData.reduce((sum, teacher) => sum + teacher[3], 0);
    const totalActualWorkload = fridayData.reduce((sum, teacher) => sum + teacher[4], 0);
    const avgWorkload = (totalActualWorkload / presentTeachers).toFixed(1);

    Logger.log(`Friday test data created successfully:`);
    Logger.log(`- Total teachers: ${presentTeachers}`);
    Logger.log(`- Absent teachers: ${absentTeacherIds.length}`);
    Logger.log(`- Present teachers: ${presentTeachers}`);
    Logger.log(`- Total regular periods: ${totalRegularPeriods}`);
    Logger.log(`- Total actual workload: ${totalActualWorkload}`);
    Logger.log(`- Average workload: ${avgWorkload}`);

    return {
      success: true,
      message: `Friday test data added with ${absentTeacherIds.length} absent teachers`,
      absentTeachers: absentTeacherIds.map(id => ({id, name: TEACHER_NAMES[id]})),
      presentTeachers: presentTeachers,
      summary: {
        total_teachers: presentTeachers,
        absent_teachers: absentTeacherIds.length,
        average_daily_workload: parseFloat(avgWorkload),
        total_regular_periods: totalRegularPeriods,
        total_actual_workload: totalActualWorkload
      }
    };

  } catch (error) {
    Logger.log('Error adding Friday test data: ' + error.message);
    return {
      success: false,
      message: error.message
    };
  }
}

/**
 * Randomly select specified number of teachers to be absent
 *
 * @param {Array} teacherIds - Array of all teacher IDs
 * @param {number} count - Number of teachers to select as absent
 * @return {Array} Array of randomly selected teacher IDs
 */
function randomlySelectTeachers(teacherIds, count) {
  const shuffled = [...teacherIds].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}

/**
 * Clear Friday test data
 */
function clearFridayTestData() {
  try {
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = ss.getSheetByName(SHEET_NAME);

    if (!sheet) {
      throw new Error(`Sheet "${SHEET_NAME}" not found`);
    }

    // Clear all data except headers
    sheet.getRange(2, 1, sheet.getLastRow(), 6).clearContent();

    Logger.log('Friday test data cleared successfully');

    return {
      success: true,
      message: 'Friday test data cleared'
    };

  } catch (error) {
    Logger.log('Error clearing Friday test data: ' + error.message);
    return {
      success: false,
      message: error.message
    };
  }
}

// Export functions for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    addFridayTestData,
    clearFridayTestData,
    randomlySelectTeachers
  };
}