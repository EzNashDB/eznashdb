from allauth.account.models import EmailAddress

from users.models import User


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
