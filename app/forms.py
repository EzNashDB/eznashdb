from crispy_forms.helper import FormHelper
from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

from app.models import AbuseAppeal, AbuseState


class CaptchaVerificationForm(forms.Form):
    """Form for CAPTCHA verification before accessing coordinates."""

    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())


class AbuseAppealForm(forms.ModelForm):
    """Form for appealing abuse bans."""

    abuse_state = forms.ModelChoiceField(queryset=AbuseState.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = AbuseAppeal
        fields = ["abuse_state", "explanation"]
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
        """Save appeal with state snapshot."""
        appeal = super().save(commit=False)

        # Capture snapshot of abuse state
        state = appeal.abuse_state
        appeal.state_snapshot = {
            "user_email": state.user.email,
            "points": state.points,
            "is_permanently_banned": state.is_permanently_banned,
            "episode_started_at": state.episode_started_at.isoformat()
            if state.episode_started_at
            else None,
            "last_violation_at": state.last_violation_at.isoformat()
            if state.last_violation_at
            else None,
            "sensitive_count_in_episode": state.sensitive_count_in_episode,
        }

        if commit:
            appeal.save()
        return appeal
