"""Mixins for views."""

from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from waffle import flag_is_active

from app.enums import RateLimitedEndpoint
from app.rate_limiting import ViolationRecorder, check_captcha_required, get_client_ip


def is_rate_limiting_active(request):
    """Check if rate limiting feature is active.

    In production (DEBUG=False): always active.
    In development (DEBUG=True): only active if waffle flag is set.
    """
    return (not settings.DEBUG) or flag_is_active(request, "rate_limiting")


class RateLimitCaptchaMixin:
    """Mixin to add rate limiting and CAPTCHA to views that expose coordinates."""

    endpoint_key = RateLimitedEndpoint.COORDINATE_ACCESS

    @method_decorator(
        ratelimit(
            key=lambda _group, request: get_client_ip(request),
            rate="30/h",
            method=["GET", "POST"],
            block=False,  # Don't auto-block, record violation instead
        )
    )
    def dispatch(self, request, *args, **kwargs):
        was_limited = getattr(request, "limited", False)
        if was_limited and is_rate_limiting_active(request):
            ViolationRecorder(request, self.endpoint_key).record()
        return super().dispatch(request, *args, **kwargs)

    def redirect_if_captcha_required(self, request):
        """
        Check if CAPTCHA is required and redirect to verification page if needed.
        Returns redirect response if CAPTCHA required, None otherwise.
        """
        if check_captcha_required(request, self.endpoint_key):
            captcha_url = reverse("captcha_verify")
            next_url = request.get_full_path()
            return HttpResponseRedirect(f"{captcha_url}?{urlencode({'next': next_url})}")
        return None
