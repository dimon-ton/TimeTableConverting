"""
Test runner with detailed reporting

Runs all tests and generates a comprehensive report saved to test_results/ directory.

Usage:
    python tests/test_runner_with_report.py
"""

import sys
import os
import unittest
from datetime import datetime
import platform

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class DetailedTestResult(unittest.TextTestResult):
    """Extended test result class that tracks timing and details"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_times = []
        self.start_time = None

    def startTest(self, test):
        super().startTest(test)
        self.start_time = datetime.now()

    def stopTest(self, test):
        super().stopTest(test)
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            self.test_times.append((test, duration))


class ReportingTestRunner(unittest.TextTestRunner):
    """Test runner that generates detailed reports"""

    resultclass = DetailedTestResult

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self, test):
        """Run tests and generate report"""
        result = super().run(test)
        return result


def generate_report(result: DetailedTestResult, total_duration: float) -> str:
    """Generate detailed test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("TEST EXECUTION REPORT")
    report_lines.append("=" * 70)
    report_lines.append(f"Date: {timestamp}")
    report_lines.append(f"Python: {sys.version.split()[0]}")
    report_lines.append(f"Platform: {platform.system()} {platform.release()}")
    report_lines.append("")

    # Test summary
    total_tests = result.testsRun
    passed = total_tests - len(result.failures) - len(result.errors) - len(result.skipped)
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)

    report_lines.append("=" * 70)
    report_lines.append("RESULTS SUMMARY")
    report_lines.append("=" * 70)
    report_lines.append(f"Total Tests: {total_tests}")
    report_lines.append(f"Passed: {passed} ({passed/total_tests*100:.1f}%)" if total_tests > 0 else "Passed: 0")
    report_lines.append(f"Failed: {failed} ({failed/total_tests*100:.1f}%)" if total_tests > 0 else "Failed: 0")
    report_lines.append(f"Errors: {errors} ({errors/total_tests*100:.1f}%)" if total_tests > 0 else "Errors: 0")
    report_lines.append(f"Skipped: {skipped} ({skipped/total_tests*100:.1f}%)" if total_tests > 0 else "Skipped: 0")
    report_lines.append(f"Total Duration: {total_duration:.2f} seconds")
    report_lines.append(f"Average per test: {total_duration/total_tests:.3f} seconds" if total_tests > 0 else "Average: N/A")
    report_lines.append("")

    # Failed tests
    if result.failures or result.errors:
        report_lines.append("=" * 70)
        report_lines.append("FAILED TESTS")
        report_lines.append("=" * 70)

        for i, (test, traceback) in enumerate(result.failures, 1):
            report_lines.append(f"\n[{i}] {test}")
            report_lines.append("    " + "\n    ".join(traceback.split("\n")))

        for i, (test, traceback) in enumerate(result.errors, len(result.failures) + 1):
            report_lines.append(f"\n[{i}] {test} (ERROR)")
            report_lines.append("    " + "\n    ".join(traceback.split("\n")))

        report_lines.append("")

    # Performance metrics
    if result.test_times:
        report_lines.append("=" * 70)
        report_lines.append("PERFORMANCE METRICS")
        report_lines.append("=" * 70)

        # Sort by duration
        sorted_times = sorted(result.test_times, key=lambda x: x[1], reverse=True)

        report_lines.append("\nSlowest tests:")
        for i, (test, duration) in enumerate(sorted_times[:10], 1):  # Top 10
            test_name = str(test).split()[0]
            report_lines.append(f"{i:2d}. {test_name:50s} - {duration:.3f}s")

        if len(sorted_times) > 10:
            report_lines.append(f"\n... and {len(sorted_times) - 10} more tests")

        report_lines.append("")

    # Final summary
    report_lines.append("=" * 70)
    if result.wasSuccessful():
        report_lines.append("OVERALL: ALL TESTS PASSED")
    else:
        report_lines.append("OVERALL: TESTS FAILED")
    report_lines.append("=" * 70)

    return "\n".join(report_lines)


def main():
    """Main entry point"""
    print("=" * 70)
    print("RUNNING TESTS WITH DETAILED REPORTING")
    print("=" * 70)
    print(f"Project root: {project_root}")
    print(f"Python version: {sys.version}")
    print("=" * 70)
    print()

    # Create test_results directory if it doesn't exist
    results_dir = os.path.join(project_root, 'test_results')
    os.makedirs(results_dir, exist_ok=True)

    # Discover tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py', top_level_dir=project_root)

    # Run tests
    start_time = datetime.now()
    runner = ReportingTestRunner(verbosity=2)
    result = runner.run(suite)
    end_time = datetime.now()

    total_duration = (end_time - start_time).total_seconds()

    # Generate report
    report = generate_report(result, total_duration)

    # Print report to console
    print("\n")
    print(report)

    # Save report to file
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_file = os.path.join(results_dir, f"report_{timestamp_str}.txt")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport saved to: {report_file}")

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
