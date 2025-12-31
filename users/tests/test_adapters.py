import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialLogin
from django.contrib.sites.models import Site

from users.adapters import SocialAccountAdapter
from users.models import User


@pytest.fixture
def google_social_app(db):
    """Create a Google SocialApp for testing."""
    site = Site.objects.get_current()
    app = SocialApp.objects.create(
        provider="google",
        name="Google",
        client_id="test-client-id",
        secret="test-secret",
    )
    app.sites.add(site)
    return app


@pytest.mark.django_db
def describe_pre_social_login():
    def connects_to_existing_user_with_matching_email(rf, google_social_app):
        """When user exists with same email, should auto-connect accounts."""
        # Create existing user
        existing_user = User.objects.create_user(
            username="test@gmail.com",
            email="test@gmail.com",
            password="testpass123",
        )

        # Create SocialLogin with matching email
        social_account = SocialAccount(provider="google", uid="123456")
        social_login = SocialLogin(account=social_account, user=User())  # New unsaved user
        social_login.email_addresses = [
            EmailAddress(email="test@gmail.com", verified=True, primary=True)
        ]

        # Call pre_social_login
        adapter = SocialAccountAdapter()
        adapter.pre_social_login(rf.get("/"), social_login)

        # Verify account was connected
        assert social_login.user == existing_user

    def does_nothing_when_no_existing_user(rf):
        """When no user exists with email, should not connect."""
        # Ensure no user exists
        assert not User.objects.filter(email="newuser@gmail.com").exists()

        # Create SocialLogin
        social_account = SocialAccount(provider="google", uid="123456")
        new_user = User()  # Unsaved user
        social_login = SocialLogin(account=social_account, user=new_user)
        social_login.email_addresses = [
            EmailAddress(email="newuser@gmail.com", verified=True, primary=True)
        ]

        # Call pre_social_login
        adapter = SocialAccountAdapter()
        adapter.pre_social_login(rf.get("/"), social_login)

        # User should still be the same new user (not connected to anyone)
        assert social_login.user == new_user

    def does_nothing_when_social_account_already_connected(rf):
        """When social account is already connected, should skip processing."""
        # Create user
        user = User.objects.create_user(
            username="test@gmail.com",
            email="test@gmail.com",
            password="testpass123",
        )

        # Create already-connected SocialLogin (user has pk, so is_existing = True)
        social_account = SocialAccount(provider="google", uid="123456")
        social_login = SocialLogin(account=social_account, user=user)
        social_login.email_addresses = [
            EmailAddress(email="test@gmail.com", verified=True, primary=True)
        ]

        # Call pre_social_login
        adapter = SocialAccountAdapter()
        adapter.pre_social_login(rf.get("/"), social_login)

        # User should still be the same (not changed)
        assert social_login.user == user

    def does_nothing_when_no_email_addresses(rf):
        """When social login has no email addresses, should skip processing."""
        social_account = SocialAccount(provider="google", uid="123456")
        new_user = User()
        social_login = SocialLogin(account=social_account, user=new_user)
        social_login.email_addresses = []

        # Call pre_social_login
        adapter = SocialAccountAdapter()
        adapter.pre_social_login(rf.get("/"), social_login)

        # User should still be the same new user (unchanged)
        assert social_login.user == new_user

    def handles_case_insensitive_email_matching(rf, google_social_app):
        """Should match emails case-insensitively."""
        # Create user with uppercase email
        existing_user = User.objects.create_user(
            username="TEST@GMAIL.COM",
            email="TEST@GMAIL.COM",
            password="testpass123",
        )

        # Create SocialLogin with lowercase email
        social_account = SocialAccount(provider="google", uid="123456")
        social_login = SocialLogin(account=social_account, user=User())
        social_login.email_addresses = [
            EmailAddress(email="test@gmail.com", verified=True, primary=True)
        ]

        # Call pre_social_login
        adapter = SocialAccountAdapter()
        adapter.pre_social_login(rf.get("/"), social_login)

        # Should have connected despite case difference
        assert social_login.user == existing_user
