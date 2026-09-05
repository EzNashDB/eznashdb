from django import forms
from django.utils.translation import gettext_lazy as _

HONEYPOT_FIELD_CLASS = "form-field-website"


class HoneyPotField(forms.CharField):
    """Custom field for honeypot spam protection (hidden via CSS)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "tabindex": "-1",
                    "class": HONEYPOT_FIELD_CLASS,
                }
            ),
        )
        super().__init__(*args, **kwargs)

    def clean(self, value):
        """Reject submissions where honeypot is filled"""
        if value:
            raise forms.ValidationError(_("Form submission failed."))
        return super().clean(value)
