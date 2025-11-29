/**
 * Code.gs - Backend API functions for Teacher Hours Tracking Web App
 *
 * Main backend logic for reading teacher hours data from Google Sheets
 * and serving it to the web frontend with caching and filtering capabilities.
 */

// Configuration
const SPREADSHEET_ID = '1KpQZlrJk03ZS_Q0bTWvxHjG9UFiD1xPZGyIsQfRkRWo';
const TRACKING_SHEET_NAME = 'Teacher_Hours_Tracking';
const CACHE_DURATION = 300; // 5 minutes in seconds

/**
 * Web app entry point - serves the main HTML page
 *
 * @param {Object} e - Event parameter (not used but required by Apps Script)
 * @return {HtmlOutput} The HTML page to display
 */
function doGet(e) {
  return HtmlService.createTemplateFromFile('Index')
    .evaluate()
    .setTitle('Teacher Hours Tracking Dashboard')
    .setFaviconUrl('https://www.gstatic.com/images/branding/product/1x/apps_script_48dp.png')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Helper function to include HTML partials (for modular HTML files)
 *
 * @param {string} filename - Name of the HTML file to include (without .html extension)
 * @return {string} The HTML content of the file
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

/**
 * Get teacher hours tracking data from Google Sheets
 * Uses 5-minute cache for performance
 *
 * @return {Array<Object>} Array of teacher tracking records
 */
function getTeacherHoursTracking() {
  const cache = CacheService.getScriptCache();
  const cacheKey = 'teacher_hours_tracking_data';

  // Try to get from cache first
  const cached = cache.get(cacheKey);
  if (cached) {
    Logger.log('Returning cached teacher hours data');
    return JSON.parse(cached);
  }

  Logger.log('Cache miss - reading from Google Sheets');

  try {
    // Open spreadsheet and get tracking sheet
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = ss.getSheetByName(TRACKING_SHEET_NAME);

    if (!sheet) {
      throw new Error(`Sheet "${TRACKING_SHEET_NAME}" not found in spreadsheet`);
    }

    // Get all data (skip header row)
    const dataRange = sheet.getDataRange();
    const values = dataRange.getValues();

    if (values.length <= 1) {
      Logger.log('No data found in tracking sheet');
      return [];
    }

    // Parse data into objects
    // Schema: Date | Teacher_ID | Teacher_Name | Day_of_Week | Regular_Periods_Today |
    //         Cumulative_Substitute | Cumulative_Absence | Net_Total_Burden | Updated_At
    const headers = values[0];
    const data = [];

    for (let i = 1; i < values.length; i++) {
      const row = values[i];

      // Skip empty rows
      if (!row[0] || !row[1]) continue;

      const record = {
        date: row[0] instanceof Date ? Utilities.formatDate(row[0], Session.getScriptTimeZone(), 'yyyy-MM-dd') : row[0],
        teacher_id: row[1],
        teacher_name: row[2],
        day_of_week: row[3],
        regular_periods_today: parseFloat(row[4]) || 0,
        cumulative_substitute: parseFloat(row[5]) || 0,
        cumulative_absence: parseFloat(row[6]) || 0,
        net_total_burden: parseFloat(row[7]) || 0,
        updated_at: row[8] instanceof Date ? row[8] : new Date(row[8])
      };

      data.push(record);
    }

    // Sort by date (most recent first) and teacher_id
    data.sort((a, b) => {
      const dateCompare = b.date.localeCompare(a.date);
      if (dateCompare !== 0) return dateCompare;
      return a.teacher_id.localeCompare(b.teacher_id);
    });

    // Cache the results
    cache.put(cacheKey, JSON.stringify(data), CACHE_DURATION);

    Logger.log(`Successfully read ${data.length} records from tracking sheet`);
    return data;

  } catch (error) {
    Logger.log('Error reading teacher hours tracking: ' + error.message);
    throw error;
  }
}

/**
 * Get teacher metrics with optional filtering
 * Returns the latest snapshot for each teacher by default
 *
 * @param {Object} filters - Optional filters {teacherId, dateFrom, dateTo}
 * @return {Object} Metrics data and metadata
 */
function getTeacherMetrics(filters) {
  filters = filters || {};

  try {
    // Get all tracking data
    const allData = getTeacherHoursTracking();

    if (allData.length === 0) {
      return {
        success: false,
        message: 'No tracking data available',
        data: [],
        summary: {}
      };
    }

    // Apply filters
    let filteredData = allData;

    // Filter by teacher
    if (filters.teacherId && filters.teacherId !== 'all') {
      filteredData = filteredData.filter(record => record.teacher_id === filters.teacherId);
    }

    // Filter by date range
    if (filters.dateFrom) {
      filteredData = filteredData.filter(record => record.date >= filters.dateFrom);
    }

    if (filters.dateTo) {
      filteredData = filteredData.filter(record => record.date <= filters.dateTo);
    }

    // Get latest record for each teacher (for dashboard display)
    const latestByTeacher = {};
    filteredData.forEach(record => {
      const teacherId = record.teacher_id;
      if (!latestByTeacher[teacherId] || record.date > latestByTeacher[teacherId].date) {
        latestByTeacher[teacherId] = record;
      }
    });

    const latestRecords = Object.values(latestByTeacher);

    // Calculate summary statistics
    const summary = {
      total_teachers: latestRecords.length,
      total_substitute_periods: latestRecords.reduce((sum, r) => sum + r.cumulative_substitute, 0),
      total_absence_periods: latestRecords.reduce((sum, r) => sum + r.cumulative_absence, 0),
      total_net_burden: latestRecords.reduce((sum, r) => sum + r.net_total_burden, 0),
      average_net_burden: latestRecords.length > 0
        ? latestRecords.reduce((sum, r) => sum + r.net_total_burden, 0) / latestRecords.length
        : 0,
      latest_date: allData.length > 0 ? allData[0].date : null,
      highest_burden_teacher: latestRecords.length > 0
        ? latestRecords.reduce((max, r) => r.net_total_burden > max.net_total_burden ? r : max)
        : null,
      lowest_burden_teacher: latestRecords.length > 0
        ? latestRecords.reduce((min, r) => r.net_total_burden < min.net_total_burden ? r : min)
        : null
    };

    return {
      success: true,
      data: latestRecords,
      allData: filteredData, // Include all filtered data for historical charts
      summary: summary,
      filters: filters
    };

  } catch (error) {
    Logger.log('Error getting teacher metrics: ' + error.message);
    return {
      success: false,
      message: 'Error: ' + error.message,
      data: [],
      summary: {}
    };
  }
}

/**
 * Get filter options for dropdowns
 * Returns lists of teachers, subjects, and classes from timetable data
 *
 * @return {Object} Filter options for UI dropdowns
 */
function getFilterOptions() {
  try {
    // Get teacher list from DataConstants
    const teachers = Object.keys(TEACHER_NAMES).map(id => ({
      id: id,
      name: TEACHER_NAMES[id]
    })).sort((a, b) => a.id.localeCompare(b.id));

    // Get unique subjects from timetable
    const subjectSet = new Set();
    REAL_TIMETABLE.forEach(entry => {
      if (entry.subject_id) {
        subjectSet.add(entry.subject_id);
      }
    });
    const subjects = Array.from(subjectSet).sort();

    // Get unique classes from timetable
    const classSet = new Set();
    REAL_TIMETABLE.forEach(entry => {
      if (entry.class_id) {
        classSet.add(entry.class_id);
      }
    });
    const classes = Array.from(classSet).sort();

    // Get unique days
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];

    return {
      success: true,
      teachers: teachers,
      subjects: subjects,
      classes: classes,
      days: days
    };

  } catch (error) {
    Logger.log('Error getting filter options: ' + error.message);
    return {
      success: false,
      message: 'Error: ' + error.message,
      teachers: [],
      subjects: [],
      classes: [],
      days: []
    };
  }
}

/**
 * Get teacher schedule for a specific teacher and day
 * Used for detailed views and tooltips
 *
 * @param {string} teacherId - Teacher ID (e.g., "T001")
 * @param {string} dayId - Day of week (e.g., "Mon", "Tue")
 * @return {Array<Object>} Array of scheduled periods
 */
function getTeacherSchedule(teacherId, dayId) {
  if (!teacherId) {
    return [];
  }

  try {
    // Filter timetable for specific teacher and day
    const schedule = REAL_TIMETABLE.filter(entry => {
      const teacherMatch = !teacherId || entry.teacher_id === teacherId;
      const dayMatch = !dayId || entry.day_id === dayId;
      return teacherMatch && dayMatch;
    });

    // Sort by day and period
    const dayOrder = {Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6, Sun: 7};
    schedule.sort((a, b) => {
      const dayCompare = dayOrder[a.day_id] - dayOrder[b.day_id];
      if (dayCompare !== 0) return dayCompare;
      return a.period_id - b.period_id;
    });

    return schedule;

  } catch (error) {
    Logger.log('Error getting teacher schedule: ' + error.message);
    return [];
  }
}

/**
 * Clear cache manually (for testing/debugging)
 * Can be called from Apps Script editor or via web app
 *
 * @return {Object} Status message
 */
function clearCache() {
  try {
    const cache = CacheService.getScriptCache();
    cache.remove('teacher_hours_tracking_data');

    Logger.log('Cache cleared successfully');
    return {
      success: true,
      message: 'Cache cleared successfully'
    };
  } catch (error) {
    Logger.log('Error clearing cache: ' + error.message);
    return {
      success: false,
      message: 'Error: ' + error.message
    };
  }
}

/**
 * Test function to verify backend is working
 * Can be run from Apps Script editor
 *
 * @return {void}
 */
function testBackend() {
  Logger.log('Testing backend functions...');

  // Test 1: Get filter options
  Logger.log('\n=== Test 1: Filter Options ===');
  const filterOptions = getFilterOptions();
  Logger.log('Teachers: ' + filterOptions.teachers.length);
  Logger.log('Subjects: ' + filterOptions.subjects.length);
  Logger.log('Classes: ' + filterOptions.classes.length);

  // Test 2: Get teacher metrics
  Logger.log('\n=== Test 2: Teacher Metrics ===');
  const metrics = getTeacherMetrics({});
  Logger.log('Success: ' + metrics.success);
  Logger.log('Records: ' + metrics.data.length);
  if (metrics.data.length > 0) {
    Logger.log('Sample record: ' + JSON.stringify(metrics.data[0]));
  }
  Logger.log('Summary: ' + JSON.stringify(metrics.summary));

  // Test 3: Get teacher schedule
  Logger.log('\n=== Test 3: Teacher Schedule ===');
  const schedule = getTeacherSchedule('T001', 'Mon');
  Logger.log('T001 Monday schedule: ' + schedule.length + ' periods');

  Logger.log('\nAll tests completed!');
}
