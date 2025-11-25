#!/usr/bin/env python
"""
Run LINE integration tests with coverage reporting.

This script runs all LINE-related tests and generates coverage reports.

Usage:
    python scripts/run_line_tests.py

Reports:
    - Terminal output with coverage summary
    - HTML coverage report in htmlcov/index.html
"""

import subprocess
import sys
import os


def main():
    """Run LINE integration tests with coverage"""
    print("=" * 70)
    print("Running LINE Integration Tests")
    print("=" * 70)
    print()

    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    # Run pytest with coverage
    cmd = [
        "pytest",
        "tests/test_webhook.py",
        "tests/test_ai_parser.py",
        "tests/test_line_messaging.py",
        "tests/test_line_integration.py",
        "tests/test_config.py",
        "-v",
        "--cov=src.web",
        "--cov=src.timetable.ai_parser",
        "--cov-report=html",
        "--cov-report=term-missing"
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, check=False)

        print()
        print("=" * 70)

        if result.returncode == 0:
            print("✓ All LINE tests passed!")
            print()
            print("Coverage report generated:")
            print(f"  HTML: {os.path.join(project_root, 'htmlcov', 'index.html')}")
            print()
            print("Open the HTML report in your browser to see detailed coverage.")
        else:
            print("✗ Some tests failed")
            print()
            print("Review the output above for details.")
            sys.exit(1)

        print("=" * 70)

    except FileNotFoundError:
        print("ERROR: pytest not found")
        print()
        print("Please install test dependencies:")
        print("  pip install -r requirements-dev.txt")
        sys.exit(1)

    except KeyboardInterrupt:
        print()
        print("Tests interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
