from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from waffle import flag_is_active

from app.abuse_prevention import (
    build_block_context,
    get_request_points,
    process_abuse_state,
    record_abuse_violation,
)
from app.forms import CaptchaVerificationForm
from app.rate_limiting import RATE_LIMITED_METHODS, consume_rate_budget


def is_rate_limiting_active(request):
    """Check if rate limiting feature is active.

    In production (DEBUG=False): always active.
    In development (DEBUG=True): only active if waffle flag is set.
    """
    return (not settings.DEBUG) or flag_is_active(request, "rate_limiting")


class EnforcementType:
    BLOCKED = "blocked"
    CAPTCHA = "captcha"


class HtmxRequestMixin:
    @property
    def is_htmx(self):
        return getattr(self.request, "htmx", False)


class AbusePreventionMixin(HtmxRequestMixin):
    """Mixin to add user-based abuse prevention to views that expose sensitive data."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not is_rate_limiting_active(request):
            return super().dispatch(request, *args, **kwargs)

        points = get_request_points(request)
        if points == 0:
            return super().dispatch(request, *args, **kwargs)

        # Check enforcement before processing request
        abuse_enforcement_result = process_abuse_state(request.user)
        if not abuse_enforcement_result.allowed:
            return self.get_blocked_response(abuse_enforcement_result)

        # Check if CAPTCHA is required and user hasn't solved it yet
        # Do this BEFORE counting the request to avoid double-counting
        if abuse_enforcement_result.requires_captcha:
            return self.get_captcha_required_response()

        if request.method not in RATE_LIMITED_METHODS:
            return super().dispatch(request, *args, **kwargs)

        # Charge this request's points against the rolling budget
        was_limited = consume_rate_budget(request, points)

        # Process the request
        response = super().dispatch(request, *args, **kwargs)

        # Record the outcome (was this request rate-limited?)
        record_abuse_violation(request.user, was_limited, points)

        return response

    def get_blocked_response(self, result):
        """Generate a response for a blocked request.

        - htmx: 429 + the modal partial, swapped in via HX-Retarget.
        - Otherwise: a plain full-page 429 rendered directly at the blocked URL.
        """
        context = build_block_context(result)

        if self.is_htmx:
            response = render(self.request, "includes/abuse_modal.html", context)
            response.status_code = 429
            self._set_htmx_enforcement_headers(response, EnforcementType.BLOCKED)
            return response

        response = render(self.request, "429.html", context)
        response.status_code = 429
        return response

    def get_captcha_required_response(self):
        """Generate a response gating a request behind CAPTCHA verification.

        - htmx: 200 + the modal partial, swapped in via HX-Retarget.
        - Otherwise: redirect to the dedicated CAPTCHA page, carrying `next` so
          the client can continue to the original destination once verified.
        """
        next_url = self.get_captcha_next_url()

        if self.is_htmx:
            response = render(
                self.request,
                "includes/captcha_modal.html",
                {"form": CaptchaVerificationForm(), "next_url": next_url},
            )
            self._set_htmx_enforcement_headers(response, EnforcementType.CAPTCHA)
            return response

        captcha_url = reverse("captcha_verify")
        return HttpResponseRedirect(f"{captcha_url}?{urlencode({'next': next_url})}")

    def get_captcha_next_url(self):
        """Where to send the user once CAPTCHA is solved. Defaults to the current URL; override
        on fragment-only views where that would land the user on a bare partial with no base
        template."""
        return self.request.get_full_path()

    @staticmethod
    def _set_htmx_enforcement_headers(response, enforcement_type):
        response["X-Abuse-Enforcement"] = enforcement_type
        response["HX-Retarget"] = "#abuse-modal-container"
        response["HX-Reswap"] = "innerHTML"
        response["HX-Trigger-After-Swap"] = (
            "abuseBlocked" if enforcement_type == EnforcementType.BLOCKED else "abuseCaptchaRequired"
        )
