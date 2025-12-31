from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """Custom adapter for allauth integration."""

    def populate_username(self, request, user):
        """Auto-populate username from email for email-only authentication."""
        user.username = user.email
        return user.username
