from unittest.mock import Mock

from app.views import RestoreDBView


def describe_list_available_backups():
    def returns_sorted_list_newest_first(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")
        mock_subprocess.run.return_value = Mock(
            returncode=0,
            stdout="backup_20241210_020000.sql.gz\nbackup_20241214_020000.sql.gz\nbackup_20241212_020000.sql.gz\n",
        )

        view = RestoreDBView()
        backups = view.list_available_backups()

        assert len(backups) == 3
        assert backups[0]["filename"] == "backup_20241214_020000.sql.gz"
        assert backups[1]["filename"] == "backup_20241212_020000.sql.gz"
        assert backups[2]["filename"] == "backup_20241210_020000.sql.gz"

    def returns_empty_list_on_rclone_failure(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")
        mock_subprocess.run.return_value = Mock(returncode=1, stdout="", stderr="error")

        view = RestoreDBView()
        backups = view.list_available_backups()

        assert backups == []

    def returns_empty_list_when_no_backups(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")
        mock_subprocess.run.return_value = Mock(returncode=0, stdout="")

        view = RestoreDBView()
        backups = view.list_available_backups()

        assert backups == []

    def skips_invalid_filenames(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")
        mock_subprocess.run.return_value = Mock(
            returncode=0,
            stdout="backup_20241214_020000.sql.gz\nsome_other_file.txt\nbackup_invalid.sql.gz\n",
        )

        view = RestoreDBView()
        backups = view.list_available_backups()

        assert len(backups) == 1
        assert backups[0]["filename"] == "backup_20241214_020000.sql.gz"

    def includes_display_date(mocker):
        mock_subprocess = mocker.patch("app.backups.core.subprocess")
        mock_subprocess.run.return_value = Mock(returncode=0, stdout="backup_20241214_140000.sql.gz\n")

        view = RestoreDBView()
        backups = view.list_available_backups()

        assert backups[0]["display_date"] == "December 14, 2024 at 02:00 PM"
