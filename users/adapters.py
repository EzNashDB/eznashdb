from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class AccountAdapter(DefaultAccountAdapter):
    """Custom adapter for allauth integration."""

    def populate_username(self, request, user):
        """Auto-populate username from email for email-only authentication."""
        user.username = user.email
        return user.username


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter for social account integration."""

    def pre_social_login(self, request, sociallogin):
        """
        Auto-connect social accounts to existing users with matching verified email.

        If a user logs in with Google using person@gmail.com, and there's already
        an account with that email, automatically connect them.
        """
        # If this social account is already connected, do nothing
        if sociallogin.is_existing:
            return

        # Try to get email from social account
        if not sociallogin.email_addresses:
            return

        email = sociallogin.email_addresses[0].email.lower()

        # Check if a user with this email already exists
        try:
            existing_user = User.objects.get(email__iexact=email)
            # Connect the social account to the existing user
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass
