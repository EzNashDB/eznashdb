from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from django.conf import settings
from django.core.management import call_command
from django.test import override_settings

# Helper to setup mocks - returns all mocks so tests can modify them


def setup_backup_mocks(mocker):
    """Setup mocks for backup command. Returns dict of all mocks for modification."""
    mock_subprocess = mocker.patch("app.management.commands.backup_db.subprocess")
    mock_os = mocker.patch("app.management.commands.backup_db.os")
    mock_os.getenv.return_value = None
    mock_path = mocker.patch("app.management.commands.backup_db.Path")
    mock_datetime = mocker.patch("app.management.commands.backup_db.datetime")

    mock_datetime.now.return_value = datetime(2024, 12, 14, 2, 0, 0)
    mock_datetime.strptime = datetime.strptime
    mock_datetime.fromtimestamp = datetime.fromtimestamp

    mock_os.environ.copy.return_value = {}

    mock_tmp_path = Mock()
    mock_tmp_path.glob.return_value = []
    mock_path.return_value = mock_tmp_path

    # Mock successful pg_dump and gzip
    dump_process = Mock()
    dump_process.stdout = Mock()
    dump_process.returncode = 0
    dump_process.stderr.read.return_value = b""
    gzip_process = Mock()
    gzip_process.returncode = 0
    gzip_process.communicate.return_value = (b"", b"")

    mock_subprocess.Popen.side_effect = [dump_process, gzip_process]

    def run_side_effect(cmd, **kwargs):
        if cmd[0] == "rclone" and cmd[1] == "lsf":
            return Mock(returncode=0, stdout="")
        return Mock(returncode=0, stderr="", stdout="")

    mock_subprocess.run.side_effect = run_side_effect

    return {
        "subprocess": mock_subprocess,
        "os": mock_os,
        "path": mock_path,
        "tmp_path": mock_tmp_path,
        "datetime": mock_datetime,
        "dump_process": dump_process,
        "gzip_process": gzip_process,
    }


@pytest.fixture
def mock_backup_success(mocker):
    """Fixture for tests that just need successful backup without modifications."""
    mocks = setup_backup_mocks(mocker)
    return mocks["subprocess"], mocks["datetime"]


# Helper functions for clearer assertions


def get_deleted_backup_filenames(mock_subprocess):
    """Extract filenames from rclone delete calls"""
    delete_calls = [
        call
        for call in mock_subprocess.run.call_args_list
        if len(call[0][0]) > 1 and call[0][0][1] == "delete"
    ]
    # Extract filename from path like "gdrive:db-backups/backup_20241205_020000.sql.gz"
    # The path may have quotes, strip them all and take the last part after splitting by '/'
    filenames = []
    for call in delete_calls:
        path = call[0][0][2]
        # Remove all quotes from the path, then split by '/' and take the last part
        filename = path.replace('"', "").split("/")[-1]
        filenames.append(filename)
    return filenames


def create_backup_filename(date):
    """Create a backup filename from a date"""
    return f"backup_{date.strftime('%Y%m%d_%H%M%S')}.sql.gz"


def setup_mock_backups(mock_subprocess, backup_list):
    """Configure mock to return a specific list of backups"""
    backups_output = "\n".join(backup_list)

    def run_side_effect(cmd, **kwargs):
        if cmd[0] == "rclone" and cmd[1] == "lsf":
            return Mock(returncode=0, stdout=backups_output)
        elif cmd[0] == "rclone" and cmd[1] == "delete":
            return Mock(returncode=0)
        return Mock(returncode=0, stderr="", stdout="")

    mock_subprocess.run.side_effect = run_side_effect


# Tests


def describe_backup_creation():
    @override_settings(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "testdb",
                "USER": "testuser",
                "PASSWORD": "testpass",
                "HOST": "db.internal",
                "PORT": "5432",
            }
        }
    )
    def creates_compressed_backup(mocker):
        mocks = setup_backup_mocks(mocker)

        call_command("backup_db")

        pg_dump_call = mocks["subprocess"].Popen.call_args_list[0]
        cmd = pg_dump_call[0][0]

        assert "pg_dump" in cmd
        assert "db.internal" in cmd
        assert "testuser" in cmd
        assert "testdb" in cmd
        assert pg_dump_call[1]["env"]["PGPASSWORD"] == "testpass"

    def handles_pg_dump_failure(mocker):
        mocks = setup_backup_mocks(mocker)
        mocks["dump_process"].returncode = 1
        mocks["dump_process"].stderr.read.return_value = b"connection refused"

        with pytest.raises(Exception, match="pg_dump failed: connection refused"):
            call_command("backup_db")

    def handles_gzip_failure(mocker):
        mocks = setup_backup_mocks(mocker)
        mocks["gzip_process"].returncode = 1
        mocks["gzip_process"].communicate.return_value = (b"", b"gzip: error")

        with pytest.raises(Exception, match="gzip failed: gzip: error"):
            call_command("backup_db")


def describe_upload():
    def uploads_to_DB_BACKUPS_PATH(mock_backup_success):
        mock_subprocess, _ = mock_backup_success

        call_command("backup_db")

        rclone_calls = [
            call
            for call in mock_subprocess.run.call_args_list
            if call[0][0][0] == "rclone" and call[0][0][1] == "copy"
        ]
        assert len(rclone_calls) == 1
        assert settings.DB_BACKUPS_PATH in rclone_calls[0][0][0]

    def handles_upload_failure(mocker):
        mocks = setup_backup_mocks(mocker)

        def run_side_effect(cmd, **kwargs):
            if cmd[0] == "rclone" and cmd[1] == "copy":
                return Mock(returncode=1, stderr="Upload failed")
            return Mock(returncode=0, stderr="", stdout="")

        mocks["subprocess"].run.side_effect = run_side_effect

        with pytest.raises(Exception, match="Upload failed"):
            call_command("backup_db")


def describe_retention_policy():
    def keeps_all_daily_backups_for_7_days(mock_backup_success):
        mock_subprocess, mock_datetime = mock_backup_success
        now = mock_datetime.now.return_value

        # Backups 0-7 days old are kept by daily retention (>= cutoff)
        # Backups 8+ days old fall into weekly retention
        backups = [create_backup_filename(now - timedelta(days=i)) for i in range(10)]
        setup_mock_backups(mock_subprocess, backups)

        call_command("backup_db")

        deleted = get_deleted_backup_filenames(mock_subprocess)

        # Day 7 is still within daily retention (>= 7 days ago)
        assert create_backup_filename(now - timedelta(days=7)) not in deleted
        # Days 8-9 fall into weekly - one kept per week, so 1 deleted
        assert len(deleted) == 1

    def keeps_one_backup_per_week_for_4_weeks(mock_backup_success):
        mock_subprocess, mock_datetime = mock_backup_success
        now = mock_datetime.now.return_value

        # 3 backups in week 2 (days 8-10), clearly in weekly window
        backups = [create_backup_filename(now - timedelta(days=d)) for d in [8, 9, 10]]
        setup_mock_backups(mock_subprocess, backups)

        call_command("backup_db")

        deleted = get_deleted_backup_filenames(mock_subprocess)

        assert len(deleted) == 2  # 3 backups, 1 kept per week

    def keeps_one_backup_per_month_for_12_months(mock_backup_success):
        mock_subprocess, mock_datetime = mock_backup_success
        now = mock_datetime.now.return_value

        # 3 backups in month 2 (days 35-37), clearly in monthly window
        backups = [create_backup_filename(now - timedelta(days=d)) for d in [35, 36, 37]]
        setup_mock_backups(mock_subprocess, backups)

        call_command("backup_db")

        deleted = get_deleted_backup_filenames(mock_subprocess)

        assert len(deleted) == 2  # 3 backups, 1 kept per month

    def keeps_yearly_backups_forever(mock_backup_success):
        mock_subprocess, mock_datetime = mock_backup_success
        now = mock_datetime.now.return_value

        backups = [
            create_backup_filename(now - timedelta(days=365 * 2)),
            create_backup_filename(now - timedelta(days=365 * 3)),
            create_backup_filename(now - timedelta(days=365 * 4)),
            create_backup_filename(now - timedelta(days=365 * 5)),
        ]

        setup_mock_backups(mock_subprocess, backups)

        call_command("backup_db")

        deleted = get_deleted_backup_filenames(mock_subprocess)

        assert len(deleted) == 0

    def keeps_backups_from_previous_year_if_within_retention_window(mock_backup_success):
        """Year boundaries don't affect retention - only age matters"""
        mock_subprocess, mock_datetime = mock_backup_success
        mock_datetime.now.return_value = datetime(2025, 1, 1, 2, 0, 0)

        backups = [
            "backup_20241231_020000.sql.gz",  # 1 day ago
            "backup_20241230_020000.sql.gz",  # 2 days ago
            "backup_20241201_020000.sql.gz",  # 31 days ago
        ]

        setup_mock_backups(mock_subprocess, backups)

        call_command("backup_db")

        deleted = get_deleted_backup_filenames(mock_subprocess)

        assert len(deleted) == 0


def describe_error_handling():
    def cleans_up_current_backup_file_on_success(mocker):
        mocks = setup_backup_mocks(mocker)

        call_command("backup_db")

        assert mocks["os"].remove.called
        removed_file = mocks["os"].remove.call_args[0][0]
        assert "backup_" in removed_file
        assert ".sql.gz" in removed_file

    def does_not_clean_up_on_failure(mocker):
        mocks = setup_backup_mocks(mocker)

        def run_side_effect(cmd, **kwargs):
            if cmd[0] == "rclone" and cmd[1] == "copy":
                return Mock(returncode=1, stderr="Upload failed")
            return Mock(returncode=0, stderr="", stdout="")

        mocks["subprocess"].run.side_effect = run_side_effect

        with pytest.raises(Exception, match="Upload failed"):
            call_command("backup_db")

        assert not mocks["os"].remove.called

    def cleans_up_old_local_backups_before_creating_new_one(mocker):
        """Old local backup files (>7 days) should be deleted before creating new backup"""
        mocks = setup_backup_mocks(mocker)
        now = mocks["datetime"].now.return_value

        old_file = Mock()
        old_file.stat.return_value.st_mtime = (now - timedelta(days=10)).timestamp()
        old_file.name = "backup_20241204_020000.sql.gz"

        recent_file = Mock()
        recent_file.stat.return_value.st_mtime = (now - timedelta(days=3)).timestamp()
        recent_file.name = "backup_20241211_020000.sql.gz"

        mocks["tmp_path"].glob.return_value = [old_file, recent_file]

        call_command("backup_db")

        assert old_file.unlink.called
        assert not recent_file.unlink.called

    def fails_if_cleanup_has_permission_error(mocker):
        """If old file cleanup fails due to permissions, should fail the backup"""
        mocks = setup_backup_mocks(mocker)
        now = mocks["datetime"].now.return_value

        old_file = Mock()
        old_file.stat.return_value.st_mtime = (now - timedelta(days=10)).timestamp()
        old_file.name = "backup_20241204_020000.sql.gz"
        old_file.unlink.side_effect = OSError("Permission denied")

        mocks["tmp_path"].glob.return_value = [old_file]

        with pytest.raises(OSError, match="Permission denied"):
            call_command("backup_db")
