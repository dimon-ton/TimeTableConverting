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
    // Schema: Date | Teacher_ID | Teacher_Name | Regular_Periods_Today | Daily_Workload | Updated_At
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
        regular_periods_today: parseFloat(row[3]) || 0,
        daily_workload: parseFloat(row[4]) || 0,
        updated_at: row[5] instanceof Date ? row[5] : new Date(row[5])
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
 * Calculate regular periods for a teacher on a specific date
 * Uses the hardcoded REAL_TIMETABLE data
 *
 * @param {string} teacherId - Teacher identifier (e.g., "T001")
 * @param {string} date - Date in YYYY-MM-DD format
 * @return {number} Number of regular periods scheduled
 */
function calculateRegularPeriods(teacherId, date) {
  const dayOfWeek = new Date(date).toLocaleDateString('en-US', {weekday: 'short'});
  const dayMap = {'Mon': 'Mon', 'Tue': 'Tue', 'Wed': 'Wed', 'Thu': 'Thu', 'Fri': 'Fri'};
  const dayId = dayMap[dayOfWeek];

  if (!dayId) return 0;

  const periods = REAL_TIMETABLE.filter(entry =>
    entry.teacher_id === teacherId && entry.day_id === dayId
  );

  return periods.length;
}

/**
 * Calculate daily workload for a teacher
 * Formula: Regular_Period_Today - Absent_Period + Substitution_Period
 *
 * @param {string} teacherId - Teacher identifier
 * @param {string} date - Date in YYYY-MM-DD format
 * @param {number} absentPeriods - Number of absent periods
 * @param {number} substitutionPeriods - Number of substitution periods taught
 * @return {number} Daily workload
 */
function calculateDailyWorkload(teacherId, date, absentPeriods, substitutionPeriods) {
  const regularPeriods = calculateRegularPeriods(teacherId, date);
  return regularPeriods - (absentPeriods || 0) + (substitutionPeriods || 0);
}

/**
 * Calculate cumulative workload for a teacher up to a specific date
 * Sums all daily workload values from the start of the school year
 *
 * @param {string} teacherId - Teacher identifier
 * @param {string} targetDate - Target date in YYYY-MM-DD format
 * @return {number} Cumulative workload
 */
function calculateCumulativeWorkload(teacherId, targetDate) {
  const allData = getTeacherHoursTracking();

  // Filter data for this teacher and dates up to target date
  const teacherData = allData.filter(record =>
    record.teacher_id === teacherId && record.date <= targetDate
  );

  // Sort by date
  teacherData.sort((a, b) => a.date.localeCompare(b.date));

  // Sum daily workloads
  return teacherData.reduce((sum, record) => sum + record.daily_workload, 0);
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

    // Calculate summary statistics with cumulative workload for each teacher
    const latestRecordsWithCumulative = latestRecords.map(record => ({
      ...record,
      cumulative_workload: calculateCumulativeWorkload(record.teacher_id, record.date)
    }));

    const summary = {
      total_teachers: latestRecords.length,
      average_daily_workload: latestRecords.length > 0
        ? latestRecords.reduce((sum, r) => sum + r.daily_workload, 0) / latestRecords.length
        : 0,
      average_cumulative_workload: latestRecordsWithCumulative.length > 0
        ? latestRecordsWithCumulative.reduce((sum, r) => sum + r.cumulative_workload, 0) / latestRecordsWithCumulative.length
        : 0,
      highest_daily_workload_teacher: latestRecords.length > 0
        ? latestRecords.reduce((max, r) => r.daily_workload > max.daily_workload ? r : max)
        : null,
      lowest_daily_workload_teacher: latestRecords.length > 0
        ? latestRecords.reduce((min, r) => r.daily_workload < min.daily_workload ? r : min)
        : null,
      highest_cumulative_workload_teacher: latestRecordsWithCumulative.length > 0
        ? latestRecordsWithCumulative.reduce((max, r) => r.cumulative_workload > max.cumulative_workload ? r : max)
        : null,
      lowest_cumulative_workload_teacher: latestRecordsWithCumulative.length > 0
        ? latestRecordsWithCumulative.reduce((min, r) => r.cumulative_workload < min.cumulative_workload ? r : min)
        : null,
      latest_date: allData.length > 0 ? allData[0].date : null
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
