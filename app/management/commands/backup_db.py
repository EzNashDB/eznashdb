import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Backup database to Google Drive with retention policy"
    backups_path = settings.DB_BACKUPS_PATH

    def handle(self, *args, **options):
        # Set up rclone config from environment
        if os.getenv("RCLONE_CONFIG_CONTENT"):
            config_dir = os.path.expanduser("~/.config/rclone")
            os.makedirs(config_dir, exist_ok=True)
            with open(f"{config_dir}/rclone.conf", "w") as f:
                f.write(os.getenv("RCLONE_CONFIG_CONTENT"))

        self.stdout.write("Starting database backup...")

        # Step 0: Clean up old local backup files
        self.stdout.write("Cleaning up old local backup files...")
        self._cleanup_old_local_backups()

        # Configuration
        db_config = settings.DATABASES["default"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.sql.gz"
        backup_path = f"/tmp/{backup_filename}"

        # Retention windows (keep backups for these periods)
        retention_config = {
            "daily": 7,  # Keep daily backups for 7 days
            "weekly": 4,  # Keep weekly backups for 4 weeks
            "monthly": 12,  # Keep monthly backups for 12 months
            "yearly": True,  # Keep yearly backups forever
        }

        try:
            # Step 1: Create backup using pg_dump
            self.stdout.write("Creating database dump...")
            self._create_backup(db_config, backup_path)

            # Step 2: Upload to Google Drive
            self.stdout.write("Uploading to Google Drive...")
            self._upload_to_gdrive(backup_path)

            # Step 3: Apply retention policy
            self.stdout.write("Applying retention policy...")
            self._apply_retention(retention_config)

            # Step 4: Cleanup local file
            os.remove(backup_path)

            self.stdout.write(self.style.SUCCESS(f"Backup completed successfully: {backup_filename}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Backup failed: {str(e)}"))
            raise

    def _create_backup(self, db_config, backup_path):
        """Create compressed PostgreSQL backup"""
        env = os.environ.copy()
        env["PGPASSWORD"] = db_config["PASSWORD"]

        pg_dump_cmd = [
            "pg_dump",
            "-h",
            db_config["HOST"],
            "-U",
            db_config["USER"],
            "-d",
            db_config["NAME"],
            "--format=plain",
        ]

        # Add port if specified
        if db_config.get("PORT"):
            pg_dump_cmd.extend(["-p", str(db_config["PORT"])])

        # Dump and compress
        with open(backup_path, "wb") as f:
            dump_process = subprocess.Popen(
                pg_dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
            )
            gzip_process = subprocess.Popen(
                ["gzip"], stdin=dump_process.stdout, stdout=f, stderr=subprocess.PIPE
            )
            dump_process.stdout.close()
            gzip_process.communicate()

            if gzip_process.returncode != 0:
                raise Exception("Failed to create compressed backup")

    def _upload_to_gdrive(self, local_path):
        """Upload backup to Google Drive using rclone"""
        result = subprocess.run(
            ["rclone", "copy", local_path, self.backups_path], capture_output=True, text=True
        )

        if result.returncode != 0:
            raise Exception(f"Upload failed: {result.stderr}")

    def _apply_retention(self, retention_config):
        """Delete old backups based on retention policy"""
        now = datetime.now()

        backups = self._list_remote_backups()
        if backups is None:
            return

        keep_backups = self._determine_backups_to_keep(backups, retention_config, now)
        self._delete_old_backups(backups, keep_backups)

    def _list_remote_backups(self):
        """List all backup files from Google Drive"""
        result = subprocess.run(["rclone", "lsf", self.backups_path], capture_output=True, text=True)

        if result.returncode != 0:
            self.stdout.write(self.style.WARNING("Could not list backups for retention"))
            return None

        backups = []
        for filename in result.stdout.strip().split("\n") if result.stdout.strip() else []:
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

    def _determine_backups_to_keep(self, backups, retention_config, now):
        """Determine which backups should be kept based on retention policy"""
        keep_backups = set()

        # Keep all backups from the last N days (daily retention)
        daily_cutoff = now - timedelta(days=retention_config["daily"])
        for filename, backup_date in backups:
            if backup_date >= daily_cutoff:
                keep_backups.add(filename)

        # Keep one backup per week for the weekly retention period
        weekly_cutoff = now - timedelta(weeks=retention_config["weekly"])
        weekly_backups = {}
        for filename, backup_date in backups:
            if daily_cutoff > backup_date >= weekly_cutoff:
                week_key = backup_date.strftime("%Y-W%U")
                if week_key not in weekly_backups:
                    weekly_backups[week_key] = filename
                    keep_backups.add(filename)

        # Keep one backup per month for the monthly retention period
        monthly_cutoff = now - timedelta(days=30 * retention_config["monthly"])
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

    def _delete_old_backups(self, backups, keep_backups):
        """Delete backups that are not in the keep list"""
        for filename, _backup_date in backups:
            if filename not in keep_backups:
                self.stdout.write(f"Deleting old backup: {filename}")
                subprocess.run(
                    ["rclone", "delete", f"{self.backups_path}{filename}"], capture_output=True
                )

    def _cleanup_old_local_backups(self, days=7):
        """Remove local backup files older than N days"""
        cutoff = datetime.now() - timedelta(days=days)
        for filepath in Path("/tmp").glob("backup_*.sql.gz"):
            if datetime.fromtimestamp(filepath.stat().st_mtime) < cutoff:
                self.stdout.write(f"Deleting old local backup: {filepath.name}")
                filepath.unlink(missing_ok=True)
