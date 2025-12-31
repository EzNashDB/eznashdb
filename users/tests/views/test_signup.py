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
