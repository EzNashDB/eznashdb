import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from app.backups.core import (
    determine_backups_to_keep,
    list_gdrive_backups,
    subprocess_Popen,
    subprocess_run,
)


class Command(BaseCommand):
    help = "Backup database to Google Drive with retention policy"
    backups_path = settings.DB_BACKUPS_PATH

    def handle(self, *args, **options):
        self.stdout.write("Starting database backup...")

        # Step 0: Clean up old local backup files
        self.stdout.write("Cleaning up old local backup files...")
        self._cleanup_old_local_backups()

        # Configuration
        db_config = settings.DATABASES["default"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.sql.gz"
        backup_path = f"/tmp/{backup_filename}"

        try:
            # Step 1: Create backup using pg_dump
            self.stdout.write("Creating database dump...")
            self._create_backup(db_config, backup_path)

            # Step 1.5: Validate backup size
            self.stdout.write("Validating backup...")
            self._validate_backup(backup_path)

            # Step 2: Upload to Google Drive
            self.stdout.write("Uploading to Google Drive...")
            self._upload_to_gdrive(backup_path)

            # Step 3: Apply retention policy
            self.stdout.write("Applying retention policy...")
            self._apply_retention()

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
            "--clean",
            "--if-exists",
        ]

        # Add port if specified
        if db_config.get("PORT"):
            pg_dump_cmd.extend(["-p", str(db_config["PORT"])])

        # Dump and compress
        with open(backup_path, "wb") as f:
            dump_process = subprocess_Popen(
                pg_dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
            )
            gzip_process = subprocess_Popen(
                ["gzip"], stdin=dump_process.stdout, stdout=f, stderr=subprocess.PIPE
            )
            dump_process.stdout.close()
            _, gzip_stderr = gzip_process.communicate()
            dump_process.wait()

            if dump_process.returncode != 0:
                stderr_output = dump_process.stderr.read().decode()
                raise Exception(f"pg_dump failed: {stderr_output}")
            if gzip_process.returncode != 0:
                raise Exception(f"gzip failed: {gzip_stderr.decode()}")

    def _validate_backup(self, backup_path, min_size_kb=15):
        """Validate backup file meets minimum size requirements"""
        if not os.path.exists(backup_path):
            raise Exception(f"Backup file not found: {backup_path}")

        file_size_bytes = os.path.getsize(backup_path)
        file_size_kb = file_size_bytes / 1024

        if file_size_kb < min_size_kb:
            raise Exception(
                f"Backup validation failed: file size ({file_size_kb:.1f}KB) is below "
                f"minimum threshold ({min_size_kb}KB). This likely indicates an empty "
                f"or incomplete backup."
            )

        self.stdout.write(f"Backup validation passed: {file_size_kb:.1f}KB")

    def _upload_to_gdrive(self, local_path):
        """Upload backup to Google Drive using rclone"""
        result = subprocess_run(
            ["rclone", "copy", local_path, self.backups_path], capture_output=True, text=True
        )

        if result.returncode != 0:
            raise Exception(f"Upload failed: {result.stderr}")

    def _apply_retention(self):
        """Delete old backups based on retention policy"""
        backups = list_gdrive_backups()
        if backups is None:
            self.stdout.write(self.style.WARNING("Could not list backups for retention"))
            return

        keep_backups = determine_backups_to_keep(backups)
        self._delete_old_backups(backups, keep_backups)

    def _delete_old_backups(self, backups, keep_backups):
        """Delete backups that are not in the keep list"""
        for filename, _backup_date in backups:
            if filename not in keep_backups:
                self.stdout.write(f"Deleting old backup: {filename}")
                subprocess_run(
                    ["rclone", "delete", f"{self.backups_path}{filename}"], capture_output=True
                )

    def _cleanup_old_local_backups(self, days=7):
        """Remove local backup files older than N days"""
        cutoff = datetime.now() - timedelta(days=days)
        for filepath in Path("/tmp").glob("backup_*.sql.gz"):
            if datetime.fromtimestamp(filepath.stat().st_mtime) < cutoff:
                self.stdout.write(f"Deleting old local backup: {filepath.name}")
                filepath.unlink(missing_ok=True)
