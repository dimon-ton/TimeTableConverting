"""
Run all tests for the TimeTableConverting project

This script runs both test suites and provides a summary.
"""

import subprocess
import sys


def run_test_file(test_file):
    """Run a single test file and return the result"""
    print(f"\n{'='*70}")
    print(f"Running {test_file}...")
    print('='*70)

    result = subprocess.run(
        [sys.executable, test_file],
        capture_output=False,
        text=True
    )

    return result.returncode == 0


def main():
    """Main function to run all tests"""
    print("\nTimeTableConverting - Test Suite Runner")
    print("=" * 70)

    test_files = [
        'test_find_substitute.py',
        'test_excel_converting.py'
    ]

    results = {}
    for test_file in test_files:
        results[test_file] = run_test_file(test_file)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    all_passed = True
    for test_file, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        symbol = "[PASS]" if passed else "[FAIL]"
        print(f"{symbol} {test_file}: {status}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\nAll tests passed successfully!")
        return 0
    else:
        print("\nSome tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
