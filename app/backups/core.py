"""Core backup utilities shared across all storage backends."""

import re
import subprocess
from datetime import datetime, timedelta

try:
    from django.conf import settings
except ImportError:
    settings = None


# Default retention policy configuration
DEFAULT_RETENTION = {
    "daily": 7,  # Keep daily backups for 7 days
    "weekly": 4,  # Keep weekly backups for 4 weeks
    "monthly": 12,  # Keep monthly backups for 12 months
    "yearly": True,  # Keep yearly backups forever
}


def parse_backup_filename(filename):
    """
    Extract timestamp from backup filename.

    Args:
        filename: Backup filename (e.g., 'backup_20241214_020000.sql.gz')

    Returns:
        datetime object if valid, None otherwise
    """
    match = re.search(r"backup_(\d{8})_(\d{6})\.sql\.gz", filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        try:
            return datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
        except ValueError:
            return None
    return None


def determine_backups_to_keep(backups, retention_config=None, now=None):
    """
    Determine which backups to keep based on retention policy.

    Args:
        backups: List of (filename, backup_date) tuples
        retention_config: Dict with 'daily', 'weekly', 'monthly', 'yearly' keys
                         (defaults to DEFAULT_RETENTION)
        now: Current datetime (defaults to datetime.now())

    Returns:
        set: Set of filenames to keep
    """
    if retention_config is None:
        retention_config = DEFAULT_RETENTION

    if now is None:
        now = datetime.now()

    keep_backups = set()

    # Calculate cutoff dates
    daily_cutoff = now - timedelta(days=retention_config["daily"])
    weekly_cutoff = now - timedelta(weeks=retention_config["weekly"])
    monthly_cutoff = now - timedelta(days=30 * retention_config["monthly"])

    # Keep all backups from the last N days (daily retention)
    for filename, backup_date in backups:
        if backup_date >= daily_cutoff:
            keep_backups.add(filename)

    # Keep one backup per week for the weekly retention period
    weekly_backups = {}
    for filename, backup_date in backups:
        if daily_cutoff > backup_date >= weekly_cutoff:
            week_key = backup_date.strftime("%Y-W%U")
            if week_key not in weekly_backups:
                weekly_backups[week_key] = filename
                keep_backups.add(filename)

    # Keep one backup per month for the monthly retention period
    monthly_backups = {}
    for filename, backup_date in backups:
        if weekly_cutoff > backup_date >= monthly_cutoff:
            month_key = backup_date.strftime("%Y-%m")
            if month_key not in monthly_backups:
                monthly_backups[month_key] = filename
                keep_backups.add(filename)

    # Keep one backup per year forever
    yearly_backups = {}
    for filename, backup_date in backups:
        if backup_date < monthly_cutoff:
            year_key = backup_date.strftime("%Y")
            if year_key not in yearly_backups:
                yearly_backups[year_key] = filename
                keep_backups.add(filename)

    return keep_backups


def list_remote_backups(remote_path):
    """List all backup files from a remote path."""
    result = subprocess_run(
        ["rclone", "lsf", remote_path],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    backups = []
    for line in result.stdout.strip().split("\n"):
        if not line or not line.startswith("backup_"):
            continue

        backup_date = parse_backup_filename(line.strip())
        if backup_date:
            backups.append((line.strip(), backup_date))

    # Sort by date (newest first)
    backups.sort(key=lambda x: x[1], reverse=True)
    return backups


def list_gdrive_backups():
    return list_remote_backups(settings.DB_BACKUPS_PATH)


def subprocess_run(cmd, **kwargs):
    return subprocess.run(cmd, **kwargs)


def subprocess_Popen(cmd, **kwargs):
    return subprocess.Popen(cmd, **kwargs)
