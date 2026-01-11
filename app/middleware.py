from django.contrib import messages as django_messages
from django.shortcuts import render
from django.template.loader import render_to_string

from app.models import RateLimitViolation
from app.rate_limiting import ENDPOINT_COORDINATE_ACCESS, get_client_ip


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
        "/google-maps-proxy/": ENDPOINT_COORDINATE_ACCESS,
        "/shuls/": ENDPOINT_COORDINATE_ACCESS,  # Covers update pages
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if path requires cooldown enforcement
        endpoint_key = None
        for path, key in self.COOLDOWN_PATHS.items():
            if request.path.startswith(path):
                endpoint_key = key
                break

        if endpoint_key:
            ip = get_client_ip(request)
            try:
                violation = RateLimitViolation.objects.get(ip_address=ip, endpoint=endpoint_key)
            except RateLimitViolation.DoesNotExist:
                violation = None

            if violation and violation.is_in_cooldown():
                context = violation.get_cooldown_context()
                response = render(request, "429.html", context)
                response.status_code = 429
                return response

        return self.get_response(request)
