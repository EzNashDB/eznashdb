from allauth.account.models import EmailAddress
from waffle.testutils import override_flag

from users.models import User


def describe_navbar():
    def shows_sign_in_for_anonymous(client):
        response = client.get("/")
        content = str(response.content)

        assert "Sign in" in content
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
        assert "Sign in" not in content  # No sign in link


def describe_language_switcher():
    @override_flag("hebrew_translation", active=False)
    def hidden_by_default(client):
        response = client.get("/")

        assert "languageSwitcher" not in str(response.content)

    @override_flag("hebrew_translation", active=True)
    def shown_when_flag_active(client):
        response = client.get("/")

        assert "languageSwitcher" in str(response.content)
