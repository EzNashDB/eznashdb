from datetime import timedelta
from urllib.parse import urlencode

import pytest
from bs4 import BeautifulSoup
from constance import config
from django.urls import reverse
from django.utils import timezone

from app.models import AbuseState


def _block_with_cooldown(user, minutes=30) -> AbuseState:
    """Put the user into a temporary cooldown block (not a permanent ban)."""
    state = AbuseState.get_or_create(user)
    state.strikes = 2
    state.cooldown_until = timezone.now() + timedelta(minutes=minutes)
    state.save()
    return state


def _require_captcha(user) -> AbuseState:
    state = AbuseState.get_or_create(user)
    state.strikes = config.ABUSE_CAPTCHA_THRESHOLD
    state.save()
    return state


def _require_captcha_and_verify(user) -> AbuseState:
    state = _require_captcha(user)
    state.mark_captcha_verified()
    return state


def _permanently_ban(user) -> AbuseState:
    state = AbuseState.get_or_create(user)
    state.strikes = config.ABUSE_PERMANENT_BAN_THRESHOLD
    state.save()
    return state


WIZARD_STEP1_DATA = {
    "name": "New Test Shul",
    "address": "123 Test St",
    "latitude": "1.0",
    "longitude": "1.0",
    "wizard_step": "1",
    "check_nearby_shuls": "true",
}


@pytest.mark.django_db
def describe_htmx_delivery():
    def blocked_returns_modal_partial_for_cooldown(client, test_user):
        client.force_login(test_user)
        _block_with_cooldown(test_user)

        response = client.get(reverse("eznashdb:create_shul"), headers={"HX-Request": "true"})

        assert response.status_code == 429
        assert response["HX-Retarget"] == "#abuse-modal-container"
        assert response["HX-Reswap"] == "innerHTML"
        assert response["HX-Trigger-After-Swap"] == "abuseBlocked"
        assert response["X-Abuse-Enforcement"] == "blocked"
        assert b'id="abuse-modal"' in response.content
        # Guards against rendering a full document into the modal container -
        # makeFragment would hoist <body> (navbar, footer, scripts) into it.
        assert b"<html" not in response.content

    def blocked_returns_modal_partial_for_permanent_ban(client, test_user):
        client.force_login(test_user)
        _permanently_ban(test_user)

        response = client.get(reverse("eznashdb:create_shul"), headers={"HX-Request": "true"})

        assert response.status_code == 429
        assert response["X-Abuse-Enforcement"] == "blocked"
        assert b"Access Restricted" in response.content
        assert b"Submit an Appeal" in response.content

    def captcha_returns_modal_partial_via_retarget(client, test_user):
        client.force_login(test_user)
        _require_captcha(test_user)

        response = client.post(
            reverse("eznashdb:create_shul"), data=WIZARD_STEP1_DATA, headers={"HX-Request": "true"}
        )

        assert response.status_code == 200
        assert response["HX-Retarget"] == "#abuse-modal-container"
        assert response["HX-Trigger-After-Swap"] == "abuseCaptchaRequired"
        assert b'id="abuse-captcha-modal"' in response.content

    def captcha_modal_form_carries_next_field(client, test_user):
        client.force_login(test_user)
        _require_captcha(test_user)

        response = client.post(
            reverse("eznashdb:create_shul"), data=WIZARD_STEP1_DATA, headers={"HX-Request": "true"}
        )

        soup = BeautifulSoup(response.content, features="html.parser")
        next_input = soup.find("input", {"name": "next"})

        assert next_input is not None
        assert next_input["value"] == reverse("eznashdb:create_shul")

    def proceeds_when_captcha_already_verified(client, test_user):
        client.force_login(test_user)
        _require_captcha_and_verify(test_user)

        response = client.post(
            reverse("eznashdb:create_shul"), data=WIZARD_STEP1_DATA, headers={"HX-Request": "true"}
        )

        assert response.status_code == 200
        assert "X-Abuse-Enforcement" not in response
        assert b'id="shul_form"' in response.content

    def captcha_gate_verify_and_retry_chain_end_to_end(client, test_user, mocker):
        client.force_login(test_user)
        _require_captcha(test_user)
        mocker.patch("app.forms.CaptchaVerificationForm.is_valid", return_value=True)

        gated = client.post(
            reverse("eznashdb:create_shul"), data=WIZARD_STEP1_DATA, headers={"HX-Request": "true"}
        )
        assert gated["X-Abuse-Enforcement"] == "captcha"

        verify = client.post(
            reverse("captcha_verify"), data={"next": "/shuls/create/"}, headers={"HX-Request": "true"}
        )
        assert verify["HX-Trigger"] == "abuseCaptchaVerified"

        retry = client.post(
            reverse("eznashdb:create_shul"), data=WIZARD_STEP1_DATA, headers={"HX-Request": "true"}
        )
        assert retry.status_code == 200
        assert "X-Abuse-Enforcement" not in retry


@pytest.mark.django_db
def describe_non_htmx_delivery():
    def blocked_renders_full_page_for_cooldown(client, test_user):
        client.force_login(test_user)
        _block_with_cooldown(test_user)

        response = client.get(reverse("eznashdb:create_shul"))

        assert response.status_code == 429
        assert b"<html" in response.content
        assert b"Temporarily Blocked" in response.content
        assert b"too many requests" in response.content

    def blocked_renders_full_page_for_permanent_ban(client, test_user):
        client.force_login(test_user)
        _permanently_ban(test_user)

        response = client.get(reverse("eznashdb:create_shul"))

        assert response.status_code == 429
        assert b"<html" in response.content
        assert b"Access Restricted" in response.content
        assert b"Submit an Appeal" in response.content

    def captcha_redirects_to_dedicated_page(client, test_user):
        client.force_login(test_user)
        _require_captcha(test_user)

        response = client.get(reverse("eznashdb:create_shul"))

        expected_next = urlencode({"next": reverse("eznashdb:create_shul")})
        assert response.status_code == 302
        assert response.url == f"{reverse('captcha_verify')}?{expected_next}"


@pytest.mark.django_db
def describe_captcha_verify_view():
    def htmx_success_returns_no_swap_and_triggers_event(client, test_user, mocker):
        client.force_login(test_user)
        _require_captcha(test_user)
        mocker.patch("app.forms.CaptchaVerificationForm.is_valid", return_value=True)

        response = client.post(
            reverse("captcha_verify"),
            data={"next": "/shuls/create/"},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200
        assert response["HX-Reswap"] == "none"
        assert response["HX-Trigger"] == "abuseCaptchaVerified"
        assert AbuseState.get_or_create(test_user).captcha_verified_at is not None

    def htmx_failure_rerenders_modal_with_error(client, test_user):
        client.force_login(test_user)
        _require_captcha(test_user)

        response = client.post(
            reverse("captcha_verify"),
            data={"next": "/shuls/create/"},  # no captcha field -> invalid
            headers={"HX-Request": "true"},
        )

        soup = BeautifulSoup(response.content, features="html.parser")

        assert response.status_code == 200
        assert "CAPTCHA verification failed" in str(soup)
        assert AbuseState.get_or_create(test_user).captcha_verified_at is None
        assert response["HX-Trigger-After-Swap"] == "abuseCaptchaRequired"

    def verifying_below_threshold_does_not_pre_arm(client, test_user, mocker):
        client.force_login(test_user)
        mocker.patch("app.forms.CaptchaVerificationForm.is_valid", return_value=True)

        response = client.post(
            reverse("captcha_verify"),
            data={"next": "/shuls/create/"},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200
        assert AbuseState.get_or_create(test_user).captcha_verified_at is None

    def anonymous_user_can_complete_captcha_without_error(client, mocker):
        mocker.patch("app.forms.CaptchaVerificationForm.is_valid", return_value=True)

        response = client.post(
            reverse("captcha_verify"),
            data={"next": "/shuls/create/"},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200
        assert not AbuseState.objects.exists()

    def non_htmx_get_renders_captcha_page(client, test_user):
        client.force_login(test_user)

        response = client.get(reverse("captcha_verify"), data={"next": "/shuls/create/"})

        soup = BeautifulSoup(response.content, features="html.parser")

        assert response.status_code == 200
        assert b"<html" in response.content
        assert "Verification Required" in str(soup)
        assert soup.find("input", {"name": "next"})["value"] == "/shuls/create/"

    def redirects_to_next_when_rate_limiting_disabled(client, test_user, settings):
        client.force_login(test_user)
        settings.DEBUG = True

        response = client.get(reverse("captcha_verify"), data={"next": "/shuls/create/"})

        assert response.status_code == 302
        assert response.url == "/shuls/create/"

    def non_htmx_success_still_redirects_to_next(client, test_user, mocker):
        client.force_login(test_user)
        mocker.patch("app.forms.CaptchaVerificationForm.is_valid", return_value=True)

        response = client.post(reverse("captcha_verify"), data={"next": "/shuls/create/"})

        assert response.status_code == 302
        assert response.url == "/shuls/create/"

    def rejects_offsite_next_on_post(client, test_user, mocker):
        client.force_login(test_user)
        mocker.patch("app.forms.CaptchaVerificationForm.is_valid", return_value=True)

        response = client.post(reverse("captcha_verify"), data={"next": "https://evil.example/"})

        assert response.status_code == 302
        assert response.url == "/"

    def sanitizes_offsite_next_in_rendered_form(client, test_user):
        client.force_login(test_user)

        response = client.get(reverse("captcha_verify"), data={"next": "https://evil.example/"})

        soup = BeautifulSoup(response.content, features="html.parser")

        assert response.status_code == 200
        assert soup.find("input", {"name": "next"})["value"] == "/"
