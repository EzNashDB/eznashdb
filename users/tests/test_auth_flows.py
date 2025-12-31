from allauth.account.models import EmailAddress
from django.urls import reverse

from users.models import User


def describe_signup_flow():
    def creates_user_and_sends_email(client, mailoutbox):
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
        assert len(mailoutbox) == 1
        assert "Confirm Your Email" in mailoutbox[0].subject


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
