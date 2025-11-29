/**
 * Calculations.gs - Helper functions for data calculations and formatting
 *
 * Provides utility functions for ranking, sorting, formatting numbers/dates,
 * and performing statistical calculations on teacher hours data.
 */

/**
 * Rank teachers by net total burden
 *
 * @param {Array<Object>} teacherData - Array of teacher records
 * @param {string} sortBy - Field to sort by (default: 'net_total_burden')
 * @param {string} order - Sort order 'desc' or 'asc' (default: 'desc')
 * @return {Array<Object>} Ranked teacher data with rank property added
 */
function rankTeachers(teacherData, sortBy, order) {
  sortBy = sortBy || 'net_total_burden';
  order = order || 'desc';

  if (!teacherData || teacherData.length === 0) {
    return [];
  }

  // Create copy to avoid modifying original
  const ranked = teacherData.slice();

  // Sort by specified field
  ranked.sort((a, b) => {
    const aVal = a[sortBy] || 0;
    const bVal = b[sortBy] || 0;

    if (order === 'desc') {
      return bVal - aVal;
    } else {
      return aVal - bVal;
    }
  });

  // Add rank property
  ranked.forEach((teacher, index) => {
    teacher.rank = index + 1;
  });

  return ranked;
}

/**
 * Calculate percentage change between two values
 *
 * @param {number} current - Current value
 * @param {number} previous - Previous value
 * @return {number} Percentage change (e.g., 15.5 for 15.5% increase)
 */
function calculatePercentageChange(current, previous) {
  if (!previous || previous === 0) {
    return current > 0 ? 100 : 0;
  }

  return ((current - previous) / previous) * 100;
}

/**
 * Calculate workload balance metrics
 * Measures how evenly distributed the workload is among teachers
 *
 * @param {Array<Object>} teacherData - Array of teacher records
 * @return {Object} Balance metrics (stdDev, coefficient of variation, etc.)
 */
function calculateWorkloadBalance(teacherData) {
  if (!teacherData || teacherData.length === 0) {
    return {
      mean: 0,
      stdDev: 0,
      coefficientOfVariation: 0,
      min: 0,
      max: 0,
      range: 0
    };
  }

  // Extract net total burden values
  const burdens = teacherData.map(t => t.net_total_burden || 0);

  // Calculate mean
  const mean = burdens.reduce((sum, val) => sum + val, 0) / burdens.length;

  // Calculate standard deviation
  const squaredDiffs = burdens.map(val => Math.pow(val - mean, 2));
  const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / burdens.length;
  const stdDev = Math.sqrt(variance);

  // Calculate coefficient of variation (CV)
  const coefficientOfVariation = mean !== 0 ? (stdDev / mean) * 100 : 0;

  // Find min and max
  const min = Math.min(...burdens);
  const max = Math.max(...burdens);
  const range = max - min;

  return {
    mean: mean,
    stdDev: stdDev,
    coefficientOfVariation: coefficientOfVariation,
    min: min,
    max: max,
    range: range
  };
}

/**
 * Calculate teacher workload category based on burden relative to mean
 *
 * @param {number} burden - Teacher's net total burden
 * @param {number} mean - Average burden across all teachers
 * @param {number} stdDev - Standard deviation of burdens
 * @return {string} Category: 'Very High', 'High', 'Normal', 'Low', 'Very Low'
 */
function getWorkloadCategory(burden, mean, stdDev) {
  const deviation = burden - mean;

  if (deviation > stdDev * 1.5) {
    return 'Very High';
  } else if (deviation > stdDev * 0.5) {
    return 'High';
  } else if (deviation < -stdDev * 1.5) {
    return 'Very Low';
  } else if (deviation < -stdDev * 0.5) {
    return 'Low';
  } else {
    return 'Normal';
  }
}

/**
 * Get Bootstrap badge class for workload category
 *
 * @param {string} category - Workload category
 * @return {string} Bootstrap badge class
 */
function getBadgeClass(category) {
  const badges = {
    'Very High': 'badge bg-danger',
    'High': 'badge bg-warning text-dark',
    'Normal': 'badge bg-success',
    'Low': 'badge bg-info text-dark',
    'Very Low': 'badge bg-secondary'
  };

  return badges[category] || 'badge bg-secondary';
}

/**
 * Format number with Thai thousand separator
 *
 * @param {number} num - Number to format
 * @param {number} decimals - Number of decimal places (default: 0)
 * @return {string} Formatted number string
 */
function formatNumber(num, decimals) {
  decimals = decimals || 0;

  if (num === null || num === undefined || isNaN(num)) {
    return '-';
  }

  return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Format date to Thai Buddhist year format
 *
 * @param {Date|string} date - Date to format
 * @param {boolean} shortFormat - Use short format (default: false)
 * @return {string} Formatted date string
 */
function formatDate(date, shortFormat) {
  if (!date) return '-';

  // Convert string to Date if needed
  if (typeof date === 'string') {
    date = new Date(date);
  }

  if (!(date instanceof Date) || isNaN(date)) {
    return '-';
  }

  const thaiMonths = [
    'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน',
    'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม',
    'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
  ];

  const thaiMonthsShort = [
    'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.',
    'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.',
    'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'
  ];

  const day = date.getDate();
  const month = shortFormat ? thaiMonthsShort[date.getMonth()] : thaiMonths[date.getMonth()];
  const year = date.getFullYear() + 543; // Convert to Buddhist year

  return shortFormat
    ? `${day} ${month} ${year}`
    : `${day} ${month} ${year}`;
}

/**
 * Format time duration in hours and minutes
 *
 * @param {number} periods - Number of periods
 * @param {number} minutesPerPeriod - Minutes per period (default: 50)
 * @return {string} Formatted duration (e.g., "25 ชั่วโมง 0 นาที")
 */
function formatDuration(periods, minutesPerPeriod) {
  minutesPerPeriod = minutesPerPeriod || 50;

  if (!periods || periods === 0) {
    return '0 ชั่วโมง';
  }

  const totalMinutes = periods * minutesPerPeriod;
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (minutes === 0) {
    return `${hours} ชั่วโมง`;
  }

  return `${hours} ชั่วโมง ${minutes} นาที`;
}

/**
 * Calculate comparison metrics between two teachers
 *
 * @param {Object} teacher1 - First teacher record
 * @param {Object} teacher2 - Second teacher record
 * @return {Object} Comparison metrics
 */
function compareTeachers(teacher1, teacher2) {
  if (!teacher1 || !teacher2) {
    return null;
  }

  return {
    burden_diff: teacher1.net_total_burden - teacher2.net_total_burden,
    substitute_diff: teacher1.cumulative_substitute - teacher2.cumulative_substitute,
    absence_diff: teacher1.cumulative_absence - teacher2.cumulative_absence,
    burden_pct_diff: calculatePercentageChange(teacher1.net_total_burden, teacher2.net_total_burden)
  };
}

/**
 * Get top N teachers by specified metric
 *
 * @param {Array<Object>} teacherData - Array of teacher records
 * @param {string} metric - Metric to rank by (e.g., 'net_total_burden')
 * @param {number} n - Number of top teachers to return (default: 5)
 * @param {string} order - 'desc' for highest, 'asc' for lowest (default: 'desc')
 * @return {Array<Object>} Top N teachers
 */
function getTopTeachers(teacherData, metric, n, order) {
  metric = metric || 'net_total_burden';
  n = n || 5;
  order = order || 'desc';

  const ranked = rankTeachers(teacherData, metric, order);
  return ranked.slice(0, n);
}

/**
 * Calculate historical trend for a teacher
 *
 * @param {Array<Object>} historicalData - Array of historical records for one teacher
 * @param {string} metric - Metric to analyze (e.g., 'net_total_burden')
 * @return {Object} Trend analysis (direction, rate, etc.)
 */
function calculateTrend(historicalData, metric) {
  metric = metric || 'net_total_burden';

  if (!historicalData || historicalData.length < 2) {
    return {
      direction: 'stable',
      rate: 0,
      points: []
    };
  }

  // Sort by date (oldest first)
  const sorted = historicalData.slice().sort((a, b) => {
    return new Date(a.date) - new Date(b.date);
  });

  // Extract values
  const values = sorted.map(record => record[metric] || 0);
  const points = sorted.map((record, index) => ({
    date: record.date,
    value: values[index]
  }));

  // Calculate simple linear trend (first vs last)
  const first = values[0];
  const last = values[values.length - 1];
  const change = last - first;

  // Determine direction
  let direction;
  if (Math.abs(change) < 1) {
    direction = 'stable';
  } else if (change > 0) {
    direction = 'increasing';
  } else {
    direction = 'decreasing';
  }

  // Calculate rate of change per day
  const daysDiff = (new Date(sorted[sorted.length - 1].date) - new Date(sorted[0].date)) / (1000 * 60 * 60 * 24);
  const rate = daysDiff > 0 ? change / daysDiff : 0;

  return {
    direction: direction,
    rate: rate,
    change: change,
    points: points
  };
}

/**
 * Get color gradient for visualization based on value
 *
 * @param {number} value - Value to map to color
 * @param {number} min - Minimum value in range
 * @param {number} max - Maximum value in range
 * @param {string} colorScheme - Color scheme: 'green-red' or 'blue-red' (default: 'green-red')
 * @return {string} RGB color string
 */
function getColorGradient(value, min, max, colorScheme) {
  colorScheme = colorScheme || 'green-red';

  if (max === min) {
    return 'rgb(200, 200, 200)'; // Gray for no variation
  }

  // Normalize value to 0-1 range
  const normalized = (value - min) / (max - min);

  let r, g, b;

  if (colorScheme === 'green-red') {
    // Low values = green, high values = red
    r = Math.round(255 * normalized);
    g = Math.round(255 * (1 - normalized));
    b = 50;
  } else if (colorScheme === 'blue-red') {
    // Low values = blue, high values = red
    r = Math.round(255 * normalized);
    g = 50;
    b = Math.round(255 * (1 - normalized));
  }

  return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Test function for calculations
 */
function testCalculations() {
  Logger.log('Testing calculation functions...');

  // Sample data
  const sampleData = [
    {teacher_id: 'T001', teacher_name: 'Teacher A', net_total_burden: 120},
    {teacher_id: 'T002', teacher_name: 'Teacher B', net_total_burden: 100},
    {teacher_id: 'T003', teacher_name: 'Teacher C', net_total_burden: 150}
  ];

  // Test ranking
  Logger.log('\n=== Test Ranking ===');
  const ranked = rankTeachers(sampleData);
  Logger.log(JSON.stringify(ranked, null, 2));

  // Test workload balance
  Logger.log('\n=== Test Workload Balance ===');
  const balance = calculateWorkloadBalance(sampleData);
  Logger.log(JSON.stringify(balance, null, 2));

  // Test formatting
  Logger.log('\n=== Test Formatting ===');
  Logger.log('Number: ' + formatNumber(12345.67, 2));
  Logger.log('Date: ' + formatDate(new Date()));
  Logger.log('Duration: ' + formatDuration(30));

  Logger.log('\nCalculations tests completed!');
}
