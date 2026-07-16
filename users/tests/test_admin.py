import pytest
from django.urls import reverse

from users.models import User


@pytest.mark.django_db
def describe_user_add_view():
    def creates_user_from_email_only(client, superuser):
        client.force_login(superuser)

        response = client.post(
            reverse("admin:users_user_add"),
            {"email": "newuser@example.com"},
        )

        assert response.status_code == 302
        user = User.objects.get(email="newuser@example.com")
        assert user.username == "newuser@example.com"
        assert not user.has_usable_password()

    def rejects_email_that_already_exists_case_insensitively(client, superuser):
        User.objects.create_user(username="existing", email="Existing.User@example.com")
        client.force_login(superuser)

        response = client.post(
            reverse("admin:users_user_add"),
            {"email": "existing.user@example.com"},
        )

        assert response.status_code == 200  # form re-rendered with error
        assert "already exists" in response.content.decode()
        assert User.objects.filter(email__iexact="existing.user@example.com").count() == 1
