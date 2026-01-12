"""Mixins for views."""

from urllib.parse import urlencode

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from app.enums import RateLimitedEndpoint
from app.rate_limiting import ViolationRecorder, check_captcha_required, get_client_ip


class RateLimitCaptchaMixin:
    """Mixin to add rate limiting and CAPTCHA to views that expose coordinates."""

    rate_limit = "30/h"  # Can be overridden in view
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
        if was_limited:
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
