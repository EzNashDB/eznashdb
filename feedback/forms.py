from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from app.fields import HoneyPotField


class TranslatedFileInput(forms.FileInput):
    """FileInput that hides the browser's untranslatable native button/placeholder text."""

    template_name = "feedback/widgets/screenshot_file_input.html"


class FeedbackForm(forms.Form):
    """Form for submitting feedback."""

    details = forms.CharField(
        label=_("Details"),
        max_length=2000,
        min_length=50,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": _("What happened or what would you like to see?"),
            }
        ),
        help_text=_("50-2000 characters"),
    )
    email = forms.EmailField(
        label=pgettext_lazy("feedback form field", "Email"),
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "your@email.com",
            }
        ),
    )
    screenshot = forms.ImageField(
        label=_("Screenshot"),
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "gif", "svg"])],
        widget=TranslatedFileInput(
            attrs={
                "class": "visually-hidden",
                "accept": "image/png,image/jpeg,image/gif,image/svg+xml",
                "@change": "handleScreenshotChange($event)",
            }
        ),
        help_text=_("Up to 5mb"),
    )
    # Hidden/auto-filled fields
    current_url = forms.CharField(required=False, widget=forms.HiddenInput(), max_length=500)
    browser_info = forms.CharField(required=False, widget=forms.HiddenInput(), max_length=500)
    # Honeypot field to catch spam
    website = HoneyPotField()

    def clean_screenshot(self):
        """Validate screenshot file size."""
        screenshot = self.cleaned_data.get("screenshot")
        if screenshot and screenshot.size > 5 * 1024 * 1024:
            raise forms.ValidationError(_("File size too large. Maximum size is 5MB."))
        return screenshot
