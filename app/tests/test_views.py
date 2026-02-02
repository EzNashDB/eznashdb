import json
from unittest.mock import Mock

from django.contrib.auth import get_user_model

from app.views import RestoreDBView
from eznashdb.views import AddressLookupView

User = get_user_model()


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


def describe_address_lookup_view():
    def returns_results_and_google_available_flag_when_google_available(mocker, rf, django_user_model):
        # Mock the budget checker to allow Google
        mock_checker = mocker.patch("eznashdb.views.GooglePlacesBudgetChecker")
        mock_checker.return_value.can_use.return_value = True

        # Mock the merger to return some results
        mock_merger = mocker.patch("eznashdb.views.PlaceSearchMerger")
        mock_place = Mock()
        mock_place.as_dict.return_value = {"display_name": "Test Place"}
        mock_merger.return_value.search.return_value = [mock_place]

        user = django_user_model.objects.create_user(username="testuser", email="test@example.com")
        request = rf.get("/address-lookup", {"q": "test", "session_token": "token123"})
        request.user = user

        view = AddressLookupView()
        response = view.get(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert "results" in data
        assert "google_available" in data
        assert data["google_available"] is True
        assert len(data["results"]) == 1
        assert data["results"][0]["display_name"] == "Test Place"

    def returns_google_available_false_when_budget_exceeded(mocker, rf, django_user_model):
        # Mock the budget checker to deny Google
        mock_checker = mocker.patch("eznashdb.views.GooglePlacesBudgetChecker")
        mock_checker.return_value.can_use.return_value = False

        # Mock the merger to return OSM results only
        mock_merger = mocker.patch("eznashdb.views.PlaceSearchMerger")
        mock_place = Mock()
        mock_place.as_dict.return_value = {"display_name": "OSM Place"}
        mock_merger.return_value.search.return_value = [mock_place]

        user = django_user_model.objects.create_user(username="testuser", email="test@example.com")
        request = rf.get("/address-lookup", {"q": "test", "session_token": "token123"})
        request.user = user

        view = AddressLookupView()
        response = view.get(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["google_available"] is False
