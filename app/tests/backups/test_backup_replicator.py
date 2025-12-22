from datetime import datetime, timedelta
from unittest.mock import Mock

from freezegun import freeze_time

from app.backups.backup_replicator import BackupReplicator


def create_backup_filename(date):
    """Helper to create a backup filename from a date"""
    return f"backup_{date.strftime('%Y%m%d_%H%M%S')}.sql.gz"


@freeze_time("2024-12-14 02:00:00")
def describe_backup_replicator():
    def runs_successfully(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")

        # Mock finding latest in source
        source_backups = "backup_20241214_020000.sql.gz\nbackup_20241213_020000.sql.gz"

        # Mock listing dest backups after copy
        dest_backups = "\n".join([f"backup_202412{i:02d}_020000.sql.gz" for i in range(1, 15)])

        def run_side_effect(cmd, **kwargs):
            if cmd[1] == "lsf" and "gdrive" in cmd[2]:
                return Mock(returncode=0, stdout=source_backups)
            elif cmd[1] == "lsf" and "b2" in cmd[2]:
                return Mock(returncode=0, stdout=dest_backups)
            elif cmd[1] == "copy" or cmd[1] == "delete":
                return Mock(returncode=0)
            return Mock(returncode=0)

        mock_subprocess.run.side_effect = run_side_effect

        replicator = BackupReplicator("gdrive:source/", "b2:dest/")
        result = replicator.run()

        assert result["success"] is True
        assert result["latest_backup"] == "backup_20241214_020000.sql.gz"
        assert result["deleted_count"] >= 0

    def returns_error_when_no_source_backups(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")
        mock_subprocess.run.return_value = Mock(returncode=0, stdout="")

        replicator = BackupReplicator("gdrive:source/", "b2:dest/")
        result = replicator.run()

        assert result["success"] is False
        assert "No backups found" in result["error"]

    def returns_error_when_copy_fails(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")

        def run_side_effect(cmd, **kwargs):
            if cmd[1] == "lsf":
                return Mock(returncode=0, stdout="backup_20241214_020000.sql.gz")
            elif cmd[1] == "copy":
                return Mock(returncode=1)
            return Mock(returncode=0)

        mock_subprocess.run.side_effect = run_side_effect

        replicator = BackupReplicator("gdrive:source/", "b2:dest/")
        result = replicator.run()

        assert result["success"] is False
        assert "Failed to copy" in result["error"]

    def normalizes_paths_without_trailing_slash(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")
        mock_subprocess.run.return_value = Mock(returncode=0, stdout="backup_20241214_020000.sql.gz")

        replicator = BackupReplicator("gdrive:source", "b2:dest")

        assert replicator.source == "gdrive:source/"
        assert replicator.dest == "b2:dest/"

    def applies_retention_policy_to_destination(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")
        now = datetime.now()

        # Source has latest backup
        source_backups = "backup_20241214_020000.sql.gz"

        # Destination has many old backups
        dest_backups = "\n".join([create_backup_filename(now - timedelta(days=i)) for i in range(30)])

        def run_side_effect(cmd, **kwargs):
            if cmd[1] == "lsf" and "gdrive" in cmd[2]:
                return Mock(returncode=0, stdout=source_backups)
            elif cmd[1] == "lsf" and "b2" in cmd[2]:
                return Mock(returncode=0, stdout=dest_backups)
            elif cmd[1] == "copy" or cmd[1] == "delete":
                return Mock(returncode=0)
            return Mock(returncode=0)

        mock_subprocess.run.side_effect = run_side_effect

        replicator = BackupReplicator("gdrive:source/", "b2:dest/")
        result = replicator.run()

        assert result["success"] is True
        # Should have deleted some old backups based on retention policy
        assert result["deleted_count"] > 0

    def get_latest_source_backup_returns_filename(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")
        mock_subprocess.run.return_value = Mock(
            returncode=0, stdout="backup_20241214_020000.sql.gz\nbackup_20241213_020000.sql.gz"
        )

        replicator = BackupReplicator("gdrive:source/", "b2:dest/")
        latest = replicator.get_latest_source_backup()

        assert latest == "backup_20241214_020000.sql.gz"

    def list_destination_backups_returns_sorted_list(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")
        backups_output = "\n".join(
            [
                "backup_20241214_020000.sql.gz",
                "backup_20241213_020000.sql.gz",
                "backup_20241212_020000.sql.gz",
            ]
        )
        mock_subprocess.run.return_value = Mock(returncode=0, stdout=backups_output)

        replicator = BackupReplicator("gdrive:source/", "b2:dest/")
        backups = replicator.list_destination_backups()

        assert len(backups) == 3
        assert backups[0][0] == "backup_20241214_020000.sql.gz"
        assert backups[1][0] == "backup_20241213_020000.sql.gz"
        assert backups[2][0] == "backup_20241212_020000.sql.gz"
