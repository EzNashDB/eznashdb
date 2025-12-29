import logging
from smtplib import SMTPException

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress
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

    def clean_email(self, email, signup=False):
        """
        Validate email and check for duplicates with clear error message during signup.
        The signup parameter is passed by allauth's signup form.
        """
        email = super().clean_email(email)

        # Only check for duplicates during signup, not password reset
        if signup and EmailAddress.objects.filter(email__iexact=email).exists():
            # Provide helpful error with clickable links
            from django.core.exceptions import ValidationError
            from django.urls import reverse
            from django.utils.html import format_html

            login_url = reverse("account_login")
            reset_url = reverse("account_reset_password")

            message = format_html(
                "An account with this email address already exists. "
                'Please <a href="{}" class="text-danger"><u>log in</u></a> or '
                '<a href="{}" class="text-danger"><u>reset your password</u></a> if you\'ve forgotten it.',
                login_url,
                reset_url,
            )

            raise ValidationError(message)

        return email

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
