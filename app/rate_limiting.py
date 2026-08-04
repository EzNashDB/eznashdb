"""Rate limiting and abuse prevention utilities."""

import secrets

from constance import config
from django.conf import settings
from django.core.cache import caches
from django_ratelimit.core import EXPIRATION_FUDGE, _get_window, _make_cache_key, _split_rate

CAPTCHA_TOKEN_SESSION_KEY = "_captcha_bypass_token"

RATE_LIMIT_GROUP = "abuse_prevention"

RATE_LIMITED_METHODS = ("GET", "POST")


def consume_rate_budget(request, points: int) -> bool:
    """Charge `points` budget units against the user's rolling window.

    Mirrors `django_ratelimit.core.is_ratelimited`'s fixed-window algorithm
    (same window/key derivation, via its private `_get_window`/`_make_cache_key`/
    `_split_rate` helpers) but increments the cache counter by an arbitrary
    amount instead of always 1.

    Returns True if the user is now over budget.
    """
    if not getattr(settings, "RATELIMIT_ENABLE", True):
        return False

    rate = config.ABUSE_RATE_LIMIT
    limit, period = _split_rate(rate)
    value = str(request.user.pk)
    window = _get_window(value, period)

    cache_name = getattr(settings, "RATELIMIT_USE_CACHE", "default")
    cache = caches[cache_name]
    cache_key = _make_cache_key(RATE_LIMIT_GROUP, window, rate, value, RATE_LIMITED_METHODS)

    # set if doesn't exist yet
    if cache.add(cache_key, points, period + EXPIRATION_FUDGE):
        count = points
    else:
        try:
            count = cache.incr(cache_key, points)
        except ValueError:
            # Key expired/was culled between add() and incr() (DatabaseCache's
            # incr() is get-then-set and raises if the row is gone).
            count = None

    if count is None:
        return not getattr(settings, "RATELIMIT_FAIL_OPEN", False)

    return count > limit


def generate_captcha_token(request):
    """
    Generate a one-time bypass token after successful captcha verification.
    Token is stored in session and can only be used once.
    """
    token = secrets.token_urlsafe(32)
    request.session[CAPTCHA_TOKEN_SESSION_KEY] = token
    return token


def consume_captcha_token(request):
    """
    Check for and consume a one-time captcha bypass token.
    Returns True if valid token was present (and is now consumed), False otherwise.
    """
    token = request.session.get(CAPTCHA_TOKEN_SESSION_KEY)
    if token:
        del request.session[CAPTCHA_TOKEN_SESSION_KEY]
        return True
    return False
