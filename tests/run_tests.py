"""
Unified test runner for TimeTableConverting project

This script runs all tests with proper Python path configuration.

Usage:
    python tests/run_tests.py
"""

import sys
import os
import unittest

def main():
    # Add project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    print("="*70)
    print("RUNNING TIMETABLE CONVERTING TEST SUITE")
    print("="*70)
    print(f"Project root: {project_root}")
    print(f"Python version: {sys.version}")
    print("="*70)
    print()

    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py', top_level_dir=project_root)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == "__main__":
    main()
