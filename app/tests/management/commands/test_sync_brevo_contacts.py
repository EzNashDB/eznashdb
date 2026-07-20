import pytest
from django.core.management import call_command

from users.models import User


@pytest.fixture
def users_with_email(django_user_model):
    return [
        django_user_model.objects.create_user(username="a", email="a@example.com"),
        django_user_model.objects.create_user(username="b", email="b@example.com"),
    ]


def test_skips_and_warns_when_brevo_disabled(settings, users_with_email, mocker):
    settings.BREVO_API_KEY = None
    sync_contact = mocker.patch("app.brevo.sync_contact")

    call_command("sync_brevo_contacts")

    sync_contact.assert_not_called()


def test_syncs_every_user_with_an_email(settings, users_with_email, mocker):
    settings.BREVO_API_KEY = "test-key"
    sync_contact = mocker.patch("app.brevo.sync_contact", return_value="ok")

    call_command("sync_brevo_contacts")

    assert sync_contact.call_count == len(users_with_email)


def test_skips_users_without_an_email(settings, users_with_email, mocker):
    settings.BREVO_API_KEY = "test-key"
    User.objects.create_user(username="no-email", email="")
    sync_contact = mocker.patch("app.brevo.sync_contact", return_value="ok")

    call_command("sync_brevo_contacts")

    assert sync_contact.call_count == len(users_with_email)
