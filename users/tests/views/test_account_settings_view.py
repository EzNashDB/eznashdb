from allauth.account.models import EmailAddress
from django.urls import reverse

from users.models import User


def describe_account_settings_view():
    def requires_login(client, db):
        """Test that anonymous users are redirected to login"""
        response = client.get(reverse("account_settings"))

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def does_not_show_warning_when_email_verified(client, db):
        """Test that verified users don't see the unverified warning"""
        user = User.objects.create_user(
            username="verified@example.com",
            email="verified@example.com",
            password="testpass123",
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        client.force_login(user)

        response = client.get(reverse("account_settings"))

        assert response.status_code == 200
        assert b"Email not verified" not in response.content

    def shows_warning_when_email_not_verified(client, db):
        """Test that unverified users see the warning banner"""
        user = User.objects.create_user(
            username="unverified@example.com",
            email="unverified@example.com",
            password="testpass123",
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=False, primary=True)
        client.force_login(user)

        response = client.get(reverse("account_settings"))

        assert response.status_code == 200
        assert b"Email not verified" in response.content
        assert b"Verify now" in response.content
