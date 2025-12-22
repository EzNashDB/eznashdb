#!/usr/bin/env python3
"""
Sync latest backup from Google Drive to Backblaze B2 and apply retention policy.

Usage:
    python scripts/sync_to_b2.py <source_remote> <dest_remote>

Example:
    python scripts/sync_to_b2.py gdrive:db-backups/prod/ b2:ezrat-nashim-db-backups/prod/
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backups.backup_replicator import BackupReplicator


def main():
    if len(sys.argv) != 3:
        print("Usage: python sync_to_b2.py <source_remote> <dest_remote>", file=sys.stderr)
        print(
            "Example: python sync_to_b2.py gdrive:db-backups/prod/ b2:bucket/prod/",
            file=sys.stderr,
        )
        sys.exit(1)

    source_path = sys.argv[1]
    dest_path = sys.argv[2]

    replicator = BackupReplicator(source_path, dest_path)
    result = replicator.run()

    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ Synced: {result['latest_backup']}")
    print(f"✓ Deleted {result['deleted_count']} old backups")


if __name__ == "__main__":
    main()
