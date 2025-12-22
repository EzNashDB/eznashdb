import gzip
import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from app.backups.core import subprocess_run


class Command(BaseCommand):
    help = "Restore database from a Google Drive backup"
    backups_path = settings.DB_BACKUPS_PATH

    def add_arguments(self, parser):
        parser.add_argument("backup_filename", type=str, help="Name of backup file to restore")

    def handle(self, *args, **options):
        backup_filename = options["backup_filename"]

        self.stdout.write(f"Starting database restore from {backup_filename}...")

        # Validate backup exists
        if not self._backup_exists(backup_filename):
            raise CommandError(f"Backup not found: {backup_filename}")

        local_gz_path = f"/tmp/{backup_filename}"
        local_sql_path = local_gz_path.replace(".sql.gz", ".sql")

        try:
            # Step 1: Download backup from Google Drive
            self.stdout.write("Downloading backup from Google Drive...")
            self._download_backup(backup_filename, local_gz_path)

            # Step 2: Decompress backup
            self.stdout.write("Decompressing backup...")
            self._decompress_backup(local_gz_path, local_sql_path)

            # Step 3: Restore database
            self.stdout.write("Restoring database...")
            self._restore_database(local_sql_path)

            self.stdout.write(
                self.style.SUCCESS(f"Database restored successfully from {backup_filename}")
            )

        finally:
            # Cleanup temp files
            self._cleanup(local_gz_path, local_sql_path)

    def _backup_exists(self, filename):
        """Check if backup file exists on remote"""
        result = subprocess_run(
            ["rclone", "lsf", f"{self.backups_path}{filename}"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and filename in result.stdout

    def _download_backup(self, filename, local_path):
        """Download backup from Google Drive using rclone"""
        result = subprocess_run(
            ["rclone", "copy", f"{self.backups_path}{filename}", "/tmp/"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise CommandError(f"Download failed: {result.stderr}")

        if not os.path.exists(local_path):
            raise CommandError(f"Download failed: file not found at {local_path}")

    def _decompress_backup(self, gz_path, sql_path):
        """Decompress .sql.gz to .sql"""
        try:
            with gzip.open(gz_path, "rb") as f_in, open(sql_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        except Exception as e:
            raise CommandError(f"Decompression failed: {str(e)}")

    def _restore_database(self, sql_path):
        """Restore database using psql"""
        db_config = settings.DATABASES["default"]
        env = os.environ.copy()
        env["PGPASSWORD"] = db_config["PASSWORD"]

        psql_cmd = [
            "psql",
            "-h",
            db_config["HOST"],
            "-U",
            db_config["USER"],
            "-d",
            db_config["NAME"],
            "-f",
            sql_path,
        ]

        if db_config.get("PORT"):
            psql_cmd.extend(["-p", str(db_config["PORT"])])

        result = subprocess_run(psql_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise CommandError(f"Restore failed: {result.stderr}")

    def _cleanup(self, gz_path, sql_path):
        """Remove temporary files"""
        for path in [gz_path, sql_path]:
            if os.path.exists(path):
                os.remove(path)
