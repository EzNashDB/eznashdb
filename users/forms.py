from allauth.account.forms import SignupForm

from app.fields import HoneyPotField


class HoneypotSignupForm(SignupForm):
    """Signup form with honeypot field to catch bots."""

    # Honeypot field - bots will fill this, humans won't see it
    website = HoneyPotField()
