from allauth.account.forms import SignupForm
from django import forms

HONEYPOT_FIELD_CLASS = "form-field-name"


class HoneypotSignupForm(SignupForm):
    """Signup form with honeypot field to catch bots."""

    # Honeypot field - bots will fill this, humans won't see it
    name = forms.CharField(
        required=False,
        label="Name",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "tabindex": "-1",
                "class": HONEYPOT_FIELD_CLASS,
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        # If honeypot field is filled, silently reject (bots fill hidden fields)
        if cleaned_data.get("name"):
            raise forms.ValidationError("Form submission failed.")
        return cleaned_data
