from django import forms

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
            raise forms.ValidationError("Form submission failed.")
        return super().clean(value)
