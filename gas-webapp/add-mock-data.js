/**
 * Add Mock Data to Teacher_Hours_Tracking Sheet
 *
 * PRODUCTION READY - Mock data functionality has been removed.
 * This script now only contains production-ready functions.
 *
 * For production use:
 * - Google Sheets should contain real teacher hours data
 * - Daily leave processor will write actual snapshots based on real assignments
 * - No test/mock data will interfere with production metrics
 */

// Legacy function references removed - mock data generation disabled
function addMockData() {
  console.log('Mock data generation disabled in production mode');
  console.log('Use daily_leave_processor to generate real teacher hours snapshots');
  return {
    success: false,
    message: 'Production mode detected - real teacher hours tracking will be used instead of mock data.'
  };
}