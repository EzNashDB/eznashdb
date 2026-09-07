from django.contrib import messages as django_messages
from django.http import Http404
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

    A request to a "/he/..." URL (from i18n_patterns) is a stronger signal than a
    negotiated language: the URL itself claims Hebrew. Downgrading it to English content
    at a "/he/" address would be a confusing half-broken state, so those 404 outright
    instead - "unreachable" per the flag, not "silently shown in the wrong language".

    English is activated before that 404 is raised, not after: LocaleMiddleware has
    already activated Hebrew from the URL prefix, and the 404 handler renders with
    whatever language is active when the exception propagates. Raising first would serve
    a fully Hebrew, RTL error page - Hebrew content at the very moment the flag says
    Hebrew is unreachable.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not flag_is_active(request, "hebrew_translation"):
            if translation.get_language() != "en":
                translation.activate("en")
                request.LANGUAGE_CODE = "en"
            if request.path_info.startswith("/he/"):
                raise Http404

        return self.get_response(request)
