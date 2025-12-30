import re
from smtplib import SMTPException
from unittest.mock import patch

import pytest
from allauth.account.models import EmailAddress
from django.core import mail
from django.urls import reverse

from users.adapters import AccountAdapter
from users.models import User


def describe_signup_flow():
    def creates_user_and_sends_email(client):
        mail.outbox = []

        response = client.post(
            reverse("account_signup"),
            {
                "email": "test@example.com",
                "password1": "complexpass123!",
                "password2": "complexpass123!",
            },
        )

        assert response.status_code == 302
        assert User.objects.filter(email="test@example.com").exists()
        assert len(mail.outbox) == 1
        assert "Confirm Your Email" in mail.outbox[0].subject


def describe_login_flow():
    def can_login_after_verification(client, db):
        user = User.objects.create_user(
            username="verified@example.com",
            email="verified@example.com",
            password="testpass123",
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)

        response = client.post(
            reverse("account_login"),
            {
                "login": "verified@example.com",
                "password": "testpass123",
            },
            follow=True,
        )

        assert response.wsgi_request.user.is_authenticated


def describe_email_confirmation():
    def auto_confirms_on_link_click(client, db):
        """Test that clicking confirmation link auto-confirms and logs in user"""
        mail.outbox = []

        # Signup user
        client.post(
            reverse("account_signup"),
            {
                "email": "newuser@example.com",
                "password1": "complexpass123!",
                "password2": "complexpass123!",
            },
        )

        # Extract confirmation URL from email
        email_body = mail.outbox[0].body
        url_match = re.search(r"/accounts/confirm-email/[\w:-]+/", email_body)
        assert url_match, "Confirmation URL not found in email"
        confirmation_url = url_match.group(0)

        # Click confirmation link (GET request should auto-confirm)
        response = client.get(confirmation_url, follow=True)

        # Verify user is logged in and redirected to homepage
        assert response.wsgi_request.user.is_authenticated
        assert response.wsgi_request.user.email == "newuser@example.com"
        assert response.redirect_chain[-1][0] == "/"

        # Verify email is marked as verified
        user = User.objects.get(email="newuser@example.com")
        email_address = EmailAddress.objects.get(user=user, email=user.email)
        assert email_address.verified

        # Verify success message is shown
        messages = list(response.context["messages"])
        assert any("confirmed" in str(msg).lower() for msg in messages)

    def shows_error_for_invalid_link(client, db):
        """Test that invalid confirmation link shows error message"""
        response = client.get("/accounts/confirm-email/invalid-key-12345/")

        assert not response.wsgi_request.user.is_authenticated
        assert b"expired or is invalid" in response.content
        assert b"Sign Up" in response.content


def describe_navbar():
    def shows_login_for_anonymous(client):
        response = client.get("/")
        content = str(response.content)

        assert "Login" in content
        assert "Sign Up" in content
        assert "Account" not in content  # No account dropdown

    def shows_account_dropdown_for_authenticated(client, db):
        user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="testpass123",
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        client.force_login(user)

        response = client.get("/")
        content = str(response.content)

        assert "Account" in content  # Dropdown button
        assert "Logout" in content  # In dropdown
        assert "test@example.com" in content  # Email shown in dropdown
        assert "Login" not in content  # No login link


def describe_account_settings_view():
    def requires_login(client, db):
        """Test that anonymous users are redirected to login"""
        response = client.get(reverse("account_settings"))

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def shows_verified_status_when_email_verified(client, db):
        """Test that email_verified context is True when user has verified email"""
        user = User.objects.create_user(
            username="verified@example.com",
            email="verified@example.com",
            password="testpass123",
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        client.force_login(user)

        response = client.get(reverse("account_settings"))

        assert response.status_code == 200
        assert response.context["email_verified"] is True

    def shows_unverified_status_when_email_not_verified(client, db):
        """Test that email_verified context is False when user has unverified email"""
        user = User.objects.create_user(
            username="unverified@example.com",
            email="unverified@example.com",
            password="testpass123",
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=False, primary=True)
        client.force_login(user)

        response = client.get(reverse("account_settings"))

        assert response.status_code == 200
        assert response.context["email_verified"] is False

    def shows_unverified_when_no_email_address(client, db):
        """Test that email_verified context is False when user has no EmailAddress"""
        user = User.objects.create_user(
            username="noemail@example.com",
            email="noemail@example.com",
            password="testpass123",
        )
        client.force_login(user)

        response = client.get(reverse("account_settings"))

        assert response.status_code == 200
        assert response.context["email_verified"] is False


def describe_account_adapter():
    def logs_and_reraises_smtp_exception():
        """Test that SMTPException is logged and re-raised"""
        adapter = AccountAdapter()

        with (
            patch(
                "users.adapters.DefaultAccountAdapter.send_mail",
                side_effect=SMTPException("Connection failed"),
            ),
            patch("users.adapters.logger") as mock_logger,
        ):
            with pytest.raises(SMTPException):
                adapter.send_mail(
                    "account/email/email_confirmation",
                    "test@example.com",
                    {},
                )

            # Verify logger.error was called
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Failed to send email to test@example.com" in call_args
            assert "account/email/email_confirmation" in call_args

    def logs_and_reraises_generic_exception():
        """Test that generic exceptions are logged and re-raised"""
        adapter = AccountAdapter()

        with (
            patch(
                "users.adapters.DefaultAccountAdapter.send_mail",
                side_effect=ValueError("Unexpected error"),
            ),
            patch("users.adapters.logger") as mock_logger,
        ):
            with pytest.raises(ValueError, match="Unexpected error"):
                adapter.send_mail(
                    "account/email/password_reset",
                    "test@example.com",
                    {},
                )

            # Verify logger.error was called
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Unexpected error sending email to test@example.com" in call_args
