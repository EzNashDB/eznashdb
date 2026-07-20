import pytest
import requests

from app import brevo
from app.brevo import _post as real_post  # captured before the autouse fixture patches it


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="jane",
        email="jane@example.com",
        first_name="Jane",
        last_name="Doe",
    )


def describe_is_enabled():
    def true_when_api_key_set(settings):
        settings.BREVO_API_KEY = "test-key"
        assert brevo.is_enabled()

    def false_when_api_key_unset(settings):
        settings.BREVO_API_KEY = None
        assert not brevo.is_enabled()


def describe_post():
    """Tests the real _post, bypassing the autouse fixture's mock of it."""

    def skips_request_when_brevo_disabled(settings, mocker):
        settings.BREVO_API_KEY = None
        request = mocker.patch("app.brevo.requests.post")

        result = real_post("/contacts", {"email": "jane@example.com"})

        request.assert_not_called()
        assert result is None

    def swallows_request_failures(settings, mocker):
        """A Brevo outage must not raise - callers rely on this being best-effort."""
        settings.BREVO_API_KEY = "test-key"
        mocker.patch("app.brevo.requests.post", side_effect=requests.RequestException("boom"))

        result = real_post("/contacts", {"email": "jane@example.com"})

        assert result is None


@pytest.mark.django_db
def describe_sync_contact():
    def upserts_contact_with_user_details(settings, user, mocker):
        settings.BREVO_CONTACT_LIST_ID = "5"
        post = mocker.patch("app.brevo._post")

        brevo.sync_contact(user)

        post.assert_called_once_with(
            "/contacts",
            {
                "email": "jane@example.com",
                "attributes": {"FIRSTNAME": "Jane", "LASTNAME": "Doe"},
                "listIds": [5],
                "updateEnabled": True,
            },
        )

    def defaults_to_empty_list_ids_when_unconfigured(settings, user, mocker):
        settings.BREVO_CONTACT_LIST_ID = None
        post = mocker.patch("app.brevo._post")

        brevo.sync_contact(user)

        assert post.call_args[0][1]["listIds"] == []

    def skips_user_without_email(django_user_model, mocker):
        post = mocker.patch("app.brevo._post")
        user_without_email = django_user_model.objects.create_user(username="no-email", email="")

        brevo.sync_contact(user_without_email)

        post.assert_not_called()
