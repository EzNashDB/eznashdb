#!/usr/bin/env python3
"""
Apply retention policy to Backblaze B2 backups.

This script uses the shared retention policy from app.backups:
- Daily: Keep all backups from last 7 days
- Weekly: Keep 1 backup per week for last 4 weeks
- Monthly: Keep 1 backup per month for last 12 months
- Yearly: Keep 1 backup per year forever

Usage:
    python b2_retention.py <bucket_path>

Example:
    python b2_retention.py b2:ezrat-nashim-db-backups/prod/
"""

import subprocess
import sys
from pathlib import Path

# Add parent directory to path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backups import determine_backups_to_keep, parse_backup_filename


def list_b2_backups(bucket_path):
    """List all backups from B2 bucket."""
    result = subprocess.run(["rclone", "lsf", bucket_path], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Warning: Could not list B2 backups: {result.stderr}", file=sys.stderr)
        return []

    backups = []
    for line in result.stdout.strip().split("\n"):
        if not line or not line.startswith("backup_"):
            continue

        backup_date = parse_backup_filename(line.strip())
        if backup_date:
            backups.append((line.strip(), backup_date))

    return backups


def delete_old_backups(backups, keep_backups, bucket_path):
    """Delete backups that are not in the keep list."""
    deleted_count = 0
    for filename, _backup_date in backups:
        if filename not in keep_backups:
            print(f"Deleting old backup: {filename}")
            result = subprocess.run(
                ["rclone", "delete", f"{bucket_path}{filename}"], capture_output=True
            )
            if result.returncode == 0:
                deleted_count += 1
            else:
                print(f"Warning: Failed to delete {filename}", file=sys.stderr)

    return deleted_count


def main():
    if len(sys.argv) != 2:
        print("Usage: python b2_retention.py <bucket_path>", file=sys.stderr)
        print("Example: python b2_retention.py b2:ezrat-nashim-db-backups/prod/", file=sys.stderr)
        sys.exit(1)

    bucket_path = sys.argv[1]

    # Ensure bucket_path ends with /
    if not bucket_path.endswith("/"):
        bucket_path += "/"

    print(f"Applying retention policy to: {bucket_path}")

    backups = list_b2_backups(bucket_path)

    if not backups:
        print("No backups found in B2")
        return

    print(f"Found {len(backups)} backups in B2")

    keep_backups = determine_backups_to_keep(backups)
    print(f"Retention policy: keeping {len(keep_backups)} backups")

    deleted_count = delete_old_backups(backups, keep_backups, bucket_path)
    print(f"✓ Deleted {deleted_count} old backups")
    print(f"✓ Remaining backups: {len(keep_backups)}")


if __name__ == "__main__":
    main()
