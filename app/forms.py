from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox


class CaptchaVerificationForm(forms.Form):
    """Form for CAPTCHA verification before accessing coordinates."""

    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())
