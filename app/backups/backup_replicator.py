from .core import determine_backups_to_keep, list_remote_backups, subprocess_run


class BackupReplicator:
    """
    Copies latest backup from source to destination with retention policy.

    Example:
        replicator = BackupReplicator('gdrive:db-backups/prod/', 'b2:bucket/prod/')
        result = replicator.run()
    """

    def __init__(self, source_path, dest_path):
        """
        Initialize replicator with source and destination paths.

        Args:
            source_path: Source remote path (e.g., 'gdrive:db-backups/prod/')
            dest_path: Destination remote path (e.g., 'b2:bucket/prod/')
        """
        self.source = source_path if source_path.endswith("/") else source_path + "/"
        self.dest = dest_path if dest_path.endswith("/") else dest_path + "/"

    def run(self):
        """
        Copy latest backup from source to destination and apply retention policy.

        Returns:
            dict with 'success' (bool), 'latest_backup' (str), 'deleted_count' (int)
        """
        # Find latest backup in source
        latest_backup = self._find_latest_backup(self.source)
        if not latest_backup:
            return {"success": False, "error": "No backups found in source"}

        # Copy to destination
        if not self._copy_backup(self.source, self.dest, latest_backup):
            return {"success": False, "error": f"Failed to copy {latest_backup}"}

        # Apply retention policy to destination
        dest_backups = list_remote_backups(self.dest)
        deleted_count = 0
        if dest_backups:
            keep_backups = determine_backups_to_keep(dest_backups)
            deleted_count = self._delete_old_backups(dest_backups, keep_backups, self.dest)

        return {
            "success": True,
            "latest_backup": latest_backup,
            "deleted_count": deleted_count,
        }

    def get_latest_source_backup(self):
        """Get filename of latest backup in source."""
        return self._find_latest_backup(self.source)

    def list_destination_backups(self):
        """List all backups in destination."""
        return list_remote_backups(self.dest)

    def _find_latest_backup(self, remote_path):
        """Find the most recent backup in a remote path."""
        backups = list_remote_backups(remote_path)
        if not backups:
            return None
        return backups[0][0]

    def _copy_backup(self, source_path, dest_path, filename):
        """Copy a backup file from source to destination using rclone."""
        source_file = f"{source_path}{filename}"
        result = subprocess_run(
            ["rclone", "copy", source_file, dest_path, "--checksum"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def _delete_old_backups(self, backups, keep_backups, remote_path):
        """Delete backups that are not in the keep list."""
        deleted_count = 0
        for filename, _backup_date in backups:
            if filename not in keep_backups:
                result = subprocess_run(
                    ["rclone", "delete", f"{remote_path}{filename}"],
                    capture_output=True,
                )
                if result.returncode == 0:
                    deleted_count += 1
        return deleted_count
