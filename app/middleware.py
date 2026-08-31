from django.contrib import messages as django_messages
from django.template.loader import render_to_string
from django.utils import translation
from waffle import flag_is_active


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


class HebrewTranslationGateMiddleware:
    """
    Forces English regardless of whatever LocaleMiddleware negotiated, until the
    "hebrew_translation" flag is active.

    LocaleMiddleware activates a non-English language from several independent
    sources - the language cookie, or (notably) the browser's Accept-Language header -
    and set_language's flag check only guards the cookie path. This is the single place
    that enforces the flag regardless of how a language got activated, so a new
    negotiation source added later can't silently reopen the gate.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if translation.get_language() != "en" and not flag_is_active(request, "hebrew_translation"):
            translation.activate("en")
            request.LANGUAGE_CODE = "en"

        return self.get_response(request)
