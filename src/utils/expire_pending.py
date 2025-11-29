"""
Expire Old Pending Assignments

This script automatically expires pending substitute assignments that are older
than the configured expiration period (default: 7 days).

Expired assignments are marked with Status="expired" instead of being deleted,
preserving the audit trail.

Usage:
    python -m src.utils.expire_pending

Recommended to run daily via cron:
    0 23 * * * cd /path/to/TimeTableConverting && python -m src.utils.expire_pending
"""

import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.sheet_utils import expire_old_pending_assignments
from src.config import config


def main():
    """
    Main function to expire old pending assignments.
    """
    print("="*60)
    print("Expiring Old Pending Assignments")
    print("="*60)
    print(f"Expiration threshold: {config.PENDING_EXPIRATION_DAYS} days")
    print()

    try:
        # Run the expiration process
        expired_count = expire_old_pending_assignments()

        if expired_count > 0:
            print(f"\n✅ Successfully expired {expired_count} old pending assignments")
        else:
            print(f"\nℹ️ No pending assignments to expire")

        print("\nDone!")
        return 0

    except Exception as e:
        print(f"\n❌ ERROR: Failed to expire pending assignments")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
