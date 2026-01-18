from django.conf import settings
from django.contrib import messages as django_messages
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from waffle import flag_is_active

from app.enums import RateLimitedEndpoint
from app.forms import RateLimitAppealForm
from app.models import RateLimitViolation
from app.rate_limiting import get_client_ip


class HTMXMessagesMiddleware:
    """
    Middleware that automatically appends Django messages to HTMX responses
    using out-of-band swap, so messages appear even when only a partial is swapped.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only process HTMX requests with HTML responses (not redirects)
        # Skip both regular redirects (3xx) and HTMX client-side redirects (HX-Redirect header)
        if (
            hasattr(request, "htmx")
            and request.htmx
            and response.get("Content-Type", "").startswith("text/html")
            and not (300 <= response.status_code < 400)
            and "HX-Redirect" not in response
        ):
            # Render messages template (template iteration will consume messages)
            # Always render to ensure messages are consumed, even if empty
            messages_html = render_to_string(
                "includes/messages.html",
                {"messages": django_messages.get_messages(request)},
                request=request,
            )

            # Append messages HTML to response content
            if hasattr(response, "content"):
                response.content = response.content + messages_html.encode("utf-8")

        return response


class RateLimitViolationMiddleware:
    """Check for active cooldowns before processing requests."""

    # Map URL paths to endpoint keys
    COOLDOWN_PATHS = {
        "/google-maps-proxy/": RateLimitedEndpoint.COORDINATE_ACCESS,
        "/shuls/": RateLimitedEndpoint.COORDINATE_ACCESS,  # Covers update pages
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        violation = self.get_violation(request)
        feature_is_active = (not settings.DEBUG) or flag_is_active(request, "rate_limiting")
        if feature_is_active and violation and violation.is_in_cooldown():
            return self.get_cooldown_response(request, violation)
        return self.get_response(request)

    def get_violation(self, request):
        endpoint_key = self.get_endpoint_key(request)
        if endpoint_key:
            ip = get_client_ip(request)
            try:
                return RateLimitViolation.objects.get(ip_address=ip, endpoint=endpoint_key)
            except RateLimitViolation.DoesNotExist:
                return None

    def get_endpoint_key(self, request):
        endpoint_key = None
        for path, key in self.COOLDOWN_PATHS.items():
            if request.path.startswith(path):
                endpoint_key = key
                break
        return endpoint_key

    def get_cooldown_response(self, request, violation):
        context = self.get_cooldown_context(violation, request)
        response = render(request, "429.html", context)
        response.status_code = 429
        return response

    def get_cooldown_context(self, violation, request=None):
        cooldown_end = violation.cooldown_until
        context = {"violation": violation}

        # For permanent bans, include appeal form if user is authenticated
        if violation.is_permanent_ban and request and request.user.is_authenticated:
            context["appeal_form"] = RateLimitAppealForm(initial={"violation": violation.id})

        # For temporary bans, calculate retry time
        if not violation.is_permanent_ban and cooldown_end:
            remaining_seconds = (cooldown_end - timezone.now()).total_seconds()
            context["retry_after"] = max(1, int(remaining_seconds / 60))

        return context
