import logging
from smtplib import SMTPException

from allauth.account.adapter import DefaultAccountAdapter

logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    """Custom adapter for allauth integration with error handling."""

    def populate_username(self, request, user):
        """Auto-populate username from email for email-only authentication."""
        user.username = user.email
        return user.username

    def send_mail(self, template_prefix, email, context):
        """Send email with graceful error handling."""
        try:
            return super().send_mail(template_prefix, email, context)
        except SMTPException as e:
            logger.error(
                f"Failed to send email to {email} (template: {template_prefix}): {str(e)}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error sending email to {email}: {str(e)}",
                exc_info=True,
            )
            raise
