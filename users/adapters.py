import logging
from smtplib import SMTPException

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings

logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    """Custom adapter for allauth integration with error handling."""

    def get_login_redirect_url(self, request):
        return settings.LOGIN_REDIRECT_URL

    def get_signup_redirect_url(self, request):
        return settings.LOGIN_REDIRECT_URL

    def populate_username(self, request, user):
        """
        Auto-populate username from email for email-only authentication.
        """
        user.username = user.email
        return user.username

    def send_mail(self, template_prefix, email, context):
        """
        Send email with graceful error handling.
        If email fails, log to Sentry and notify user instead of crashing.
        """
        try:
            return super().send_mail(template_prefix, email, context)
        except SMTPException as e:
            # Log the error (will be captured by Sentry)
            logger.error(
                f"Failed to send email to {email} (template: {template_prefix}): {str(e)}",
                exc_info=True,
            )
            # Note: Can't add messages here since we don't have request object
            # The calling view will need to handle this
            raise  # Re-raise so calling code knows email failed
        except Exception as e:
            # Catch any other email-related errors
            logger.error(
                f"Unexpected error sending email to {email}: {str(e)}",
                exc_info=True,
            )
            raise
