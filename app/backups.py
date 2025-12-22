"""Shared utilities for database backup and restore operations."""

import subprocess
from datetime import datetime

from django.conf import settings


def list_remote_backups():
    """
    List all backup files from Google Drive.

    Returns:
        list: List of tuples (filename, backup_date) sorted by date (newest first),
              or None if the rclone command fails.
    """
    result = subprocess.run(
        ["rclone", "lsf", settings.DB_BACKUPS_PATH],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    backups = []
    filenames = result.stdout.strip().split("\n") if result.stdout.strip() else []

    for filename in filenames:
        if not filename or not filename.startswith("backup_"):
            continue

        try:
            # Parse timestamp from filename: backup_20241214_020000.sql.gz
            timestamp_str = filename.replace("backup_", "").replace(".sql.gz", "")
            backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            backups.append((filename, backup_date))
        except ValueError:
            continue

    # Sort by date (newest first)
    backups.sort(key=lambda x: x[1], reverse=True)
    return backups
