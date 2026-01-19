from django import forms
from django.core.validators import FileExtensionValidator


class FeedbackForm(forms.Form):
    """Form for submitting feedback."""

    details = forms.CharField(
        max_length=2000,
        min_length=50,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "What happened or what would you like to see?",
            }
        ),
        label="Details",
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "your@email.com",
            }
        ),
    )

    # Optional screenshot
    screenshot = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif", "svg"])],
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": "image/png,image/jpeg,image/gif,image/svg+xml",
            }
        ),
    )

    # Hidden/auto-filled fields
    current_url = forms.CharField(required=False, widget=forms.HiddenInput(), max_length=500)

    browser_info = forms.CharField(required=False, widget=forms.HiddenInput(), max_length=500)

    # Honeypot for spam protection
    honeypot = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
    )

    def clean_honeypot(self):
        """Reject submissions with honeypot filled (likely spam)."""
        value = self.cleaned_data.get("honeypot", "")
        if value:
            raise forms.ValidationError("Invalid submission detected.")
        return value

    def clean_screenshot(self):
        """Validate screenshot file size."""
        screenshot = self.cleaned_data.get("screenshot")
        if screenshot and screenshot.size > 5 * 1024 * 1024:
            raise forms.ValidationError("File size too large. Maximum size is 5MB.")
        return screenshot
