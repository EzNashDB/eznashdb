from allauth.account.models import EmailAddress
from django.core import mail
from django.urls import reverse

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
    def cannot_login_without_verification(client, db):
        User.objects.create_user(email="test@example.com", password="testpass123")

        response = client.post(
            reverse("account_login"),
            {
                "login": "test@example.com",
                "password": "testpass123",
            },
        )

        assert not response.wsgi_request.user.is_authenticated

    def can_login_after_verification(client, db):
        user = User.objects.create_user(email="verified@example.com", password="testpass123")
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


def describe_navbar():
    def shows_login_for_anonymous(client):
        response = client.get("/")
        content = str(response.content)

        assert "Login" in content
        assert "Sign Up" in content
        assert "Account" not in content  # No account dropdown

    def shows_account_dropdown_for_authenticated(client, db):
        user = User.objects.create_user(email="test@example.com", password="testpass123")
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        client.force_login(user)

        response = client.get("/")
        content = str(response.content)

        assert "Account" in content  # Dropdown button
        assert "Logout" in content  # In dropdown
        assert "test@example.com" in content  # Email shown in dropdown
        assert "Login" not in content  # No login link
