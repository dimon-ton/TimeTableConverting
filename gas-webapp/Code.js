/**
 * Web app entry point - serves the main HTML page
 *
 * @param {Object} e - Event parameter (not used but required by Apps Script)
 * @return {HtmlOutput} The HTML page to display
 */
function doGet(e) {
  // Check if we need to update sheets structure or add mock data
  if (e && e.parameter.update_sheets === 'true') {
    try {
      updateSheetsStructure();
      return HtmlService.createHtmlOutput(`
        <div style="padding: 20px; font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; text-align: center;">
          <h3 style="color: #28a745; margin-bottom: 20px;">
            📊 Google Sheets Structure Updated!
          </h3>
          <p style="margin-bottom: 15px;">The Teacher_Hours_Tracking worksheet has been successfully updated to the new 6-column structure:</p>
          <ul style="line-height: 1.8;">
            <li><strong>Date</strong> - Record date</li>
            <li><strong>Teacher_ID</strong> - Teacher identifier</li>
            <li><strong>Teacher_Name</strong> - Teacher display name</li>
            <li><strong>Regular_Periods_Today</strong> - Scheduled periods from timetable</li>
            <li><strong>Daily_Workload</strong> - Calculated daily workload (Regular - Absence + Substitution)</li>
            <li><strong>Updated_At</strong> - Last update timestamp</li>
          </ul>
          <p style="margin-top: 20px;">
            <a href="${e.scriptUrl}&update_sheets=false" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
              🔄 Continue to Dashboard</a></p>
        </div>
      `);
    } catch (error) {
      return HtmlService.createHtmlOutput(`
        <div style="padding: 20px; font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; text-align: center;">
          <h3 style="color: #dc3545; margin-bottom: 20px;">
            ❌ Error Updating Sheets
          </h3>
          <p style="margin-bottom: 15px;">${error.message}</p>
        </div>
      `);
    }
    } else if (e && e.parameter.add === 'true') {
    try {
      addMockData();
      return HtmlService.createHtmlOutput(
        `<div style="padding: 20px; font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; text-align: center;">
          <h3 style="color: #28a745; margin-bottom: 20px;">
            📊 ข้อมูลจำลองถูวรมแล้วแล้วแล้ว!
          </h3>
          <p style="margin-bottom: 15px;">เพิ่มข้อมูลจำลอง ${e.parameter.count || '5'} รายการเพื่อการทดสอบถูนแล้วแล้วแล้วแล้ว
          </p>
          <p style="margin-top: 30px;">
            <a href="${e.scriptUrl}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
              🔄 กลับไปหน้าาหลัก
            </a>
          </p>
        </div>`
      );
    } catch (error) {
      return HtmlService.createHtmlOutput(`
        <div style="padding: 20px; font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; text-align: center;">
          <h3 style="color: #dc3545; margin-bottom: 20px;">
            ❌ Error Adding Mock Data
          </h3>
          <p style="margin-bottom: 15px;">${error.message}</p>
        </div>
      `);
    }
    } else if (e && e.parameter.clear === 'true') {
    try {
      clearMockData();
      return HtmlService.createHtmlOutput(
        `<div style="padding: 20px; font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; text-align: center;">
          <h3 style="color: #28a745; margin-bottom: 20px;">
            🗑️ ข้อมูลจำลองถูวรมแล้วแล้วแล้วแล้ว!
          </h3>
          <p style="margin-bottom: 15px;">เพิ่มข้อมูลจำลองถูวรมแล้วแล้วแล้วแล้ว ${e.parameter.count || '5'} รายการเพื่อการทดสอบถูนแล้วแล้วแล้วแล้ว
          </p>
          <p style="margin-top: 30px;">
            <a href="${e.scriptUrl}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
              🔄 กลับไปหน้าาหลัก
            </a>
          </p>
        </div>`
      );
    } catch (error) {
      return HtmlService.createHtmlOutput(`
        <div style="padding: 20px; font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; text-align: center;">
          <h3 style="color: #dc3545; margin-bottom: 20px;">
            ❌ Error
          </h3>
          <p style="margin-bottom: 15px;">${error.message}</p>
        </div>
      `);
    }
  }

  return HtmlService.createTemplateFromFile('Index')
    .evaluate()
    .setTitle('Teacher Hours Tracking Dashboard')
    .setFaviconUrl('https://www.gstatic.com/images/branding/product/1x/apps_script_48dp.png')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Include HTML template function
 * Allows including HTML templates within other HTML files
 *
 * @param {string} filename - Name of the HTML file to include
 * @return {string} HTML content of the included file
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

/**
 * Backend configuration constants
 * Spreadsheet ID and sheet name are now in DataConstants.js
 */

/**
 * Get teacher metrics data for the dashboard
 * This is the main data loading function called by the frontend
 *
 * @param {Object} filters - Filter options (teacherId, dateFrom, dateTo, sortBy, sortOrder)
 * @return {Object} Response object with success, data, summary, and message
 */
function getTeacherMetrics(filters) {
  try {
    console.log('Loading teacher metrics with filters:', filters);

    // Default filters if not provided
    filters = filters || {};
    const teacherId = filters.teacherId || 'all';
    const dateFrom = filters.dateFrom || null;
    const dateTo = filters.dateTo || null;
    const sortBy = filters.sortBy || 'daily_workload';
    const sortOrder = filters.sortOrder || 'desc';

    // Open spreadsheet and get data
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = ss.getSheetByName(SHEET_NAME);

    if (!sheet) {
      return {
        success: false,
        message: `Sheet "${SHEET_NAME}" not found. Please update the spreadsheet structure first.`,
        data: [],
        summary: null
      };
    }

    // Get all data
    const range = sheet.getDataRange();
    const values = range.getValues();

    if (values.length <= 1) {
      return {
        success: true,
        message: 'No data found. Add some teacher records to get started.',
        data: [],
        summary: {
          total_teachers: 0,
          average_daily_workload: 0,
          average_cumulative_workload: 0,
          highest_daily_workload_teacher: null,
          latest_date: null
        }
      };
    }

    // Parse data rows (skip header)
    const headers = values[0];
    const teacherData = [];
    const teacherMap = new Map();

    for (let i = 1; i < values.length; i++) {
      const row = values[i];
      if (!row[0]) continue; // Skip empty rows

      const record = {
        date: row[0] ? new Date(row[0]).toISOString().split('T')[0] : null,
        teacher_id: row[1] || '',
        teacher_name: row[2] || '',
        regular_periods_today: parseFloat(row[3]) || 0,
        daily_workload: parseFloat(row[4]) || 0,
        updated_at: row[5] ? new Date(row[5]) : null
      };

      // Apply filters
      if (teacherId !== 'all' && record.teacher_id !== teacherId) continue;
      if (dateFrom && record.date < dateFrom) continue;
      if (dateTo && record.date > dateTo) continue;

      teacherData.push(record);

      // Calculate cumulative workload per teacher
      if (!teacherMap.has(record.teacher_id)) {
        teacherMap.set(record.teacher_id, {
          teacher_id: record.teacher_id,
          teacher_name: record.teacher_name,
          regular_periods_today: 0,
          daily_workload: 0,
          cumulative_workload: 0,
          latest_date: record.date
        });
      }

      const teacherStats = teacherMap.get(record.teacher_id);
      teacherStats.regular_periods_today = record.regular_periods_today;
      teacherStats.daily_workload = record.daily_workload;
      teacherStats.cumulative_workload += record.daily_workload;
      if (record.date > teacherStats.latest_date) {
        teacherStats.latest_date = record.date;
      }
    }

    // Convert to array and sort
    let finalData = Array.from(teacherMap.values());

    // Sort data
    finalData.sort((a, b) => {
      const aVal = a[sortBy] || 0;
      const bVal = b[sortBy] || 0;
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });

    // Calculate summary statistics
    const summary = calculateSummaryStatistics(finalData);

    console.log(`Returning ${finalData.length} teacher records`);

    return {
      success: true,
      data: finalData,
      summary: summary,
      message: `Successfully loaded ${finalData.length} teacher records`
    };

  } catch (error) {
    console.error('Error in getTeacherMetrics:', error);
    return {
      success: false,
      message: error.message || 'Unknown error occurred',
      data: [],
      summary: null
    };
  }
}

/**
 * Calculate summary statistics for dashboard
 *
 * @param {Array} teacherData - Array of teacher records
 * @return {Object} Summary statistics
 */
function calculateSummaryStatistics(teacherData) {
  if (!teacherData || teacherData.length === 0) {
    return {
      total_teachers: 0,
      average_daily_workload: 0,
      average_cumulative_workload: 0,
      highest_daily_workload_teacher: null,
      latest_date: null
    };
  }

  const totalTeachers = teacherData.length;
  const dailyWorkloads = teacherData.map(t => t.daily_workload || 0);
  const cumulativeWorkloads = teacherData.map(t => t.cumulative_workload || 0);
  const avgDaily = dailyWorkloads.reduce((sum, val) => sum + val, 0) / totalTeachers;
  const avgCumulative = cumulativeWorkloads.reduce((sum, val) => sum + val, 0) / totalTeachers;

  // Find teacher with highest daily workload
  let highestWorkloadTeacher = null;
  let maxWorkload = 0;
  teacherData.forEach(teacher => {
    if (teacher.daily_workload > maxWorkload) {
      maxWorkload = teacher.daily_workload;
      highestWorkloadTeacher = {
        teacher_name: teacher.teacher_name,
        teacher_id: teacher.teacher_id,
        daily_workload: teacher.daily_workload
      };
    }
  });

  // Find latest date
  const latestDate = teacherData
    .map(t => t.latest_date)
    .filter(d => d)
    .sort((a, b) => b.localeCompare(a))[0] || null;

  return {
    total_teachers: totalTeachers,
    average_daily_workload: parseFloat(avgDaily.toFixed(2)),
    average_cumulative_workload: parseFloat(avgCumulative.toFixed(2)),
    highest_daily_workload_teacher: highestWorkloadTeacher,
    latest_date: latestDate
  };
}

/**
 * Get filter options for dropdown menus
 *
 * @return {Object} Response with filter options
 */
function getFilterOptions() {
  try {
    // Return teacher options from DataConstants
    const teachers = Object.entries(TEACHER_NAMES).map(([id, name]) => ({
      id: id,
      name: name
    }));

    return {
      success: true,
      teachers: teachers.sort((a, b) => a.name.localeCompare(b.name, 'th')),
      message: 'Filter options loaded successfully'
    };

  } catch (error) {
    console.error('Error in getFilterOptions:', error);
    return {
      success: false,
      message: error.message || 'Failed to load filter options',
      teachers: []
    };
  }
}

/**
 * Clear cache function (for future use)
 * Currently just returns success as Apps Script handles caching automatically
 *
 * @return {Object} Response object
 */
function clearCache() {
  try {
    console.log('Clearing cache...');

    // Apps Script handles caching automatically, but we could implement
    // custom cache clearing here if needed in the future

    return {
      success: true,
      message: 'Cache cleared successfully'
    };

  } catch (error) {
    console.error('Error clearing cache:', error);
    return {
      success: false,
      message: error.message || 'Failed to clear cache'
    };
  }
}