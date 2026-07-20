import pytest

from users.models import User


@pytest.fixture(autouse=True)
def _run_background_sync(mocker):
    """Run the signal's backgrounded work inline so tests can assert deterministically."""
    mocker.patch(
        "users.signals.run_in_background",
        side_effect=lambda func, *args, **kwargs: func(*args, **kwargs),
    )


def test_syncs_new_user_and_records_success(mocker, django_capture_on_commit_callbacks):
    sync_contact = mocker.patch("app.brevo.sync_contact", return_value="ok")

    with django_capture_on_commit_callbacks(execute=True):
        user = User.objects.create_user(username="jane", email="jane@example.com")

    sync_contact.assert_called_once_with(user)
    user.refresh_from_db()
    assert user.brevo_synced_at is not None


def test_does_not_record_success_when_sync_fails(mocker, django_capture_on_commit_callbacks):
    mocker.patch("app.brevo.sync_contact", return_value=None)

    with django_capture_on_commit_callbacks(execute=True):
        user = User.objects.create_user(username="jane", email="jane@example.com")

    user.refresh_from_db()
    assert user.brevo_synced_at is None


def test_does_not_sync_user_without_email(mocker, django_capture_on_commit_callbacks):
    sync_contact = mocker.patch("app.brevo.sync_contact")

    with django_capture_on_commit_callbacks(execute=True):
        User.objects.create_user(username="no-email", email="")

    sync_contact.assert_not_called()


def test_does_not_sync_on_update(mocker, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        user = User.objects.create_user(username="jane", email="jane@example.com")

    sync_contact = mocker.patch("app.brevo.sync_contact")

    with django_capture_on_commit_callbacks(execute=True):
        user.first_name = "Jane"
        user.save()

    sync_contact.assert_not_called()
