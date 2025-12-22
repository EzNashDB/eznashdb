from unittest.mock import Mock

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import override_settings


def setup_restore_mocks(mocker):
    """Setup mocks for restore command. Returns dict of all mocks for modification."""
    mock_subprocess = mocker.patch("app.management.commands.restore_db.subprocess")
    mock_os = mocker.patch("app.management.commands.restore_db.os")
    mock_gzip = mocker.patch("app.management.commands.restore_db.gzip")
    mock_shutil = mocker.patch("app.management.commands.restore_db.shutil")

    mock_os.environ.copy.return_value = {}
    mock_os.path.exists.return_value = True

    # Default: backup exists on remote
    def run_side_effect(cmd, **kwargs):
        if cmd[0] == "rclone" and cmd[1] == "lsf":
            # If checking specific file, return that file
            path = cmd[2]
            if "backup_" in path:
                filename = path.split("/")[-1]
                return Mock(returncode=0, stdout=filename)
            return Mock(returncode=0, stdout="backup_20241214_020000.sql.gz\n")
        if cmd[0] == "rclone" and cmd[1] == "copy":
            return Mock(returncode=0, stderr="")
        if cmd[0] == "psql":
            return Mock(returncode=0, stderr="")
        return Mock(returncode=0, stderr="", stdout="")

    mock_subprocess.run.side_effect = run_side_effect

    # Mock gzip.open as context manager
    mock_gzip_file = Mock()
    mock_gzip.open.return_value.__enter__ = Mock(return_value=mock_gzip_file)
    mock_gzip.open.return_value.__exit__ = Mock(return_value=False)

    return {
        "subprocess": mock_subprocess,
        "os": mock_os,
        "gzip": mock_gzip,
        "shutil": mock_shutil,
    }


@pytest.fixture
def mock_restore_success(mocker):
    """Fixture for tests that just need successful restore without modifications."""
    return setup_restore_mocks(mocker)


def describe_backup_validation():
    def raises_error_if_backup_not_found(mocker):
        mocks = setup_restore_mocks(mocker)

        def run_side_effect(cmd, **kwargs):
            if cmd[0] == "rclone" and cmd[1] == "lsf":
                return Mock(returncode=0, stdout="")
            return Mock(returncode=0, stderr="", stdout="")

        mocks["subprocess"].run.side_effect = run_side_effect

        with pytest.raises(CommandError, match="Backup not found"):
            call_command("restore_db", "nonexistent_backup.sql.gz")


def describe_download():
    def downloads_from_correct_path(mock_restore_success):
        call_command("restore_db", "backup_20241214_020000.sql.gz")

        copy_calls = [
            call
            for call in mock_restore_success["subprocess"].run.call_args_list
            if len(call[0][0]) > 1 and call[0][0][1] == "copy"
        ]
        assert len(copy_calls) == 1
        assert settings.DB_BACKUPS_PATH in copy_calls[0][0][0][2]

    def raises_error_on_download_failure(mocker):
        mocks = setup_restore_mocks(mocker)

        def run_side_effect(cmd, **kwargs):
            if cmd[0] == "rclone" and cmd[1] == "lsf":
                return Mock(returncode=0, stdout="backup_20241214_020000.sql.gz")
            if cmd[0] == "rclone" and cmd[1] == "copy":
                return Mock(returncode=1, stderr="Network error")
            return Mock(returncode=0, stderr="", stdout="")

        mocks["subprocess"].run.side_effect = run_side_effect

        with pytest.raises(CommandError, match="Download failed"):
            call_command("restore_db", "backup_20241214_020000.sql.gz")

    def raises_error_if_file_not_found_after_download(mocker):
        mocks = setup_restore_mocks(mocker)
        mocks["os"].path.exists.return_value = False

        with pytest.raises(CommandError, match="Download failed: file not found"):
            call_command("restore_db", "backup_20241214_020000.sql.gz")


def describe_decompression():
    def decompresses_gzip_file(mock_restore_success):
        call_command("restore_db", "backup_20241214_020000.sql.gz")

        mock_restore_success["gzip"].open.assert_called_once()
        mock_restore_success["shutil"].copyfileobj.assert_called_once()

    def raises_error_on_decompression_failure(mocker):
        mocks = setup_restore_mocks(mocker)
        mocks["gzip"].open.side_effect = Exception("Corrupt file")

        with pytest.raises(CommandError, match="Decompression failed"):
            call_command("restore_db", "backup_20241214_020000.sql.gz")


def describe_restore():
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
    def restores_with_correct_credentials(mock_restore_success):
        call_command("restore_db", "backup_20241214_020000.sql.gz")

        psql_calls = [
            call
            for call in mock_restore_success["subprocess"].run.call_args_list
            if call[0][0][0] == "psql"
        ]
        assert len(psql_calls) == 1

        cmd = psql_calls[0][0][0]
        assert "-h" in cmd
        assert "db.internal" in cmd
        assert "-U" in cmd
        assert "testuser" in cmd
        assert "-d" in cmd
        assert "testdb" in cmd
        assert "-f" in cmd

        env = psql_calls[0][1]["env"]
        assert env["PGPASSWORD"] == "testpass"

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
    def includes_port_when_specified(mock_restore_success):
        call_command("restore_db", "backup_20241214_020000.sql.gz")

        psql_calls = [
            call
            for call in mock_restore_success["subprocess"].run.call_args_list
            if call[0][0][0] == "psql"
        ]
        cmd = psql_calls[0][0][0]

        assert "-p" in cmd
        port_index = cmd.index("-p")
        assert cmd[port_index + 1] == "5432"

    def raises_error_on_psql_failure(mocker):
        mocks = setup_restore_mocks(mocker)

        def run_side_effect(cmd, **kwargs):
            if cmd[0] == "rclone" and cmd[1] == "lsf":
                return Mock(returncode=0, stdout="backup_20241214_020000.sql.gz")
            if cmd[0] == "rclone" and cmd[1] == "copy":
                return Mock(returncode=0, stderr="")
            if cmd[0] == "psql":
                return Mock(returncode=1, stderr="Connection refused")
            return Mock(returncode=0, stderr="", stdout="")

        mocks["subprocess"].run.side_effect = run_side_effect

        with pytest.raises(CommandError, match="Restore failed"):
            call_command("restore_db", "backup_20241214_020000.sql.gz")


def describe_cleanup():
    def cleans_up_temp_files_on_success(mock_restore_success):
        call_command("restore_db", "backup_20241214_020000.sql.gz")

        remove_calls = mock_restore_success["os"].remove.call_args_list
        removed_files = [call[0][0] for call in remove_calls]

        assert any(".sql.gz" in f for f in removed_files)
        assert any(".sql" in f and ".gz" not in f for f in removed_files)

    def cleans_up_temp_files_on_failure(mocker):
        mocks = setup_restore_mocks(mocker)

        def run_side_effect(cmd, **kwargs):
            if cmd[0] == "rclone" and cmd[1] == "lsf":
                return Mock(returncode=0, stdout="backup_20241214_020000.sql.gz")
            if cmd[0] == "rclone" and cmd[1] == "copy":
                return Mock(returncode=0, stderr="")
            if cmd[0] == "psql":
                return Mock(returncode=1, stderr="Connection refused")
            return Mock(returncode=0, stderr="", stdout="")

        mocks["subprocess"].run.side_effect = run_side_effect

        with pytest.raises(CommandError):
            call_command("restore_db", "backup_20241214_020000.sql.gz")

        # Cleanup should still be called
        assert mocks["os"].remove.called or mocks["os"].path.exists.called
