"""Mixins for views."""

import logging
from urllib.parse import urlencode

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from app.rate_limiting import (
    ENDPOINT_COORDINATE_ACCESS,
    ViolationRecorder,
    check_captcha_required,
    get_client_ip,
)

logger = logging.getLogger(__name__)


class RateLimitCaptchaMixin:
    """Mixin to add rate limiting and CAPTCHA to views that expose coordinates."""

    rate_limit = "30/h"  # Can be overridden in view
    endpoint_key = ENDPOINT_COORDINATE_ACCESS

    @method_decorator(
        ratelimit(
            key=lambda g, r: get_client_ip(r),
            rate="30/h",
            method=["GET", "POST"],
            block=False,  # Don't auto-block, record violation instead
        )
    )
    def dispatch(self, request, *args, **kwargs):
        # Check if rate limited
        if getattr(request, "limited", False):
            violation = ViolationRecorder(request, self.endpoint_key).record()
            logger.warning(
                f"Rate limit hit: {get_client_ip(request)} - {self.endpoint_key} "
                f"(violation #{violation.violation_count})"
            )

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
