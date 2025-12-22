#!/usr/bin/env python3
"""
Apply retention policy to Backblaze B2 backups.

This script mirrors the retention policy from backup_db.py:
- Daily: Keep all backups from last 7 days
- Weekly: Keep 1 backup per week for last 4 weeks
- Monthly: Keep 1 backup per month for last 12 months
- Yearly: Keep 1 backup per year forever

Usage:
    python b2_retention.py <bucket_path>

Example:
    python b2_retention.py b2:ezrat-nashim-db-backups/prod/
"""

import re
import subprocess
import sys
from datetime import datetime, timedelta


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

        # Extract timestamp from filename: backup_YYYYMMDD_HHMMSS.sql.gz
        match = re.search(r"backup_(\d{8})_(\d{6})\.sql\.gz", line)
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            try:
                backup_date = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                backups.append((line.strip(), backup_date))
            except ValueError:
                print(f"Warning: Could not parse date from {line}", file=sys.stderr)
                continue

    return backups


def determine_backups_to_keep(backups, now):
    """
    Determine which backups to keep based on retention policy.

    Policy mirrors backup_db.py:
    - Daily: All backups from last 7 days
    - Weekly: 1 per week for last 4 weeks
    - Monthly: 1 per month for last 12 months
    - Yearly: 1 per year forever
    """
    keep_backups = set()

    # Retention cutoffs
    daily_cutoff = now - timedelta(days=7)
    weekly_cutoff = now - timedelta(weeks=4)
    monthly_cutoff = now - timedelta(days=30 * 12)

    # Daily: Keep all backups from the last 7 days
    for filename, backup_date in backups:
        if backup_date >= daily_cutoff:
            keep_backups.add(filename)

    # Weekly: Keep one backup per week for the last 4 weeks
    weekly_backups = {}
    for filename, backup_date in backups:
        if daily_cutoff > backup_date >= weekly_cutoff:
            week_key = backup_date.strftime("%Y-W%U")
            if week_key not in weekly_backups:
                weekly_backups[week_key] = filename
                keep_backups.add(filename)

    # Monthly: Keep one backup per month for the last 12 months
    monthly_backups = {}
    for filename, backup_date in backups:
        if weekly_cutoff > backup_date >= monthly_cutoff:
            month_key = backup_date.strftime("%Y-%m")
            if month_key not in monthly_backups:
                monthly_backups[month_key] = filename
                keep_backups.add(filename)

    # Yearly: Keep one backup per year forever
    yearly_backups = {}
    for filename, backup_date in backups:
        if backup_date < monthly_cutoff:
            year_key = backup_date.strftime("%Y")
            if year_key not in yearly_backups:
                yearly_backups[year_key] = filename
                keep_backups.add(filename)

    return keep_backups


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

    now = datetime.now()
    backups = list_b2_backups(bucket_path)

    if not backups:
        print("No backups found in B2")
        return

    print(f"Found {len(backups)} backups in B2")

    keep_backups = determine_backups_to_keep(backups, now)
    print(f"Retention policy: keeping {len(keep_backups)} backups")

    deleted_count = delete_old_backups(backups, keep_backups, bucket_path)
    print(f"✓ Deleted {deleted_count} old backups")
    print(f"✓ Remaining backups: {len(keep_backups)}")


if __name__ == "__main__":
    main()
