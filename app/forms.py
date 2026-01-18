from crispy_forms.helper import FormHelper
from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

from app.models import RateLimitAppeal, RateLimitViolation


class CaptchaVerificationForm(forms.Form):
    """Form for CAPTCHA verification before accessing coordinates."""

    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())


class RateLimitAppealForm(forms.ModelForm):
    """Form for appealing rate limit bans."""

    violation = forms.ModelChoiceField(
        queryset=RateLimitViolation.objects.all(), widget=forms.HiddenInput()
    )

    class Meta:
        model = RateLimitAppeal
        fields = ["violation", "explanation"]
        widgets = {
            "explanation": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Please describe what you were doing when you got blocked...",
                }
            )
        }
        labels = {"explanation": "Why do you think this is a mistake?"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def save(self, commit=True):
        """Save appeal with violation snapshot."""
        appeal = super().save(commit=False)

        # Capture snapshot of violation state
        appeal.violation_snapshot = {
            "ip_address": appeal.violation.ip_address,
            "endpoint": appeal.violation.endpoint,
            "violation_count": appeal.violation.violation_count,
            "first_violation_at": appeal.violation.first_violation_at.isoformat(),
            "last_violation_at": appeal.violation.last_violation_at.isoformat(),
            "user_id": appeal.violation.user.id if appeal.violation.user else None,
            "user_email": appeal.violation.user.email if appeal.violation.user else None,
            "user_ids": appeal.violation.user_ids,
        }

        if commit:
            appeal.save()
        return appeal
