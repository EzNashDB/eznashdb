"""Mixins for views."""

from urllib.parse import urlencode

from constance import config
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django_ratelimit.core import is_ratelimited
from waffle import flag_is_active

from app.abuse_prevention import (
    get_blocked_response,
    is_sensitive_url,
    process_abuse_state,
    record_abuse_violation,
)
from app.rate_limiting import consume_captcha_token


def is_rate_limiting_active(request):
    """Check if rate limiting feature is active.

    In production (DEBUG=False): always active.
    In development (DEBUG=True): only active if waffle flag is set.
    """
    return (not settings.DEBUG) or flag_is_active(request, "rate_limiting")


class AbusePreventionMixin:
    """Mixin to add user-based abuse prevention to views that expose sensitive data."""

    def dispatch(self, request, *args, **kwargs):
        if self.should_pass_through(request):
            return super().dispatch(request, *args, **kwargs)

        # Check enforcement before processing request
        abuse_enforcement_result = process_abuse_state(request.user)
        if not abuse_enforcement_result.allowed:
            return get_blocked_response(request, abuse_enforcement_result)

        # Check if CAPTCHA is required and user hasn't solved it yet
        # Do this BEFORE counting the request to avoid double-counting
        if abuse_enforcement_result.requires_captcha and not consume_captcha_token(request):
            captcha_url = reverse("captcha_verify")
            next_url = request.get_full_path()
            return HttpResponseRedirect(f"{captcha_url}?{urlencode({'next': next_url})}")

        # Apply django-ratelimit for rate tracking
        was_limited = is_ratelimited(
            request=request,
            group="abuse_prevention",
            key=lambda g, r: str(r.user.pk),
            rate=config.ABUSE_RATE_LIMIT,
            method=["GET", "POST"],
            increment=True,
        )

        # Process the request
        response = super().dispatch(request, *args, **kwargs)

        # Record the outcome (was this request rate-limited?)
        record_abuse_violation(request.user, was_limited)

        return response

    def should_pass_through(self, request):
        return (
            not is_sensitive_url(request)
            or not is_rate_limiting_active(request)
            or not request.user.is_authenticated
        )
