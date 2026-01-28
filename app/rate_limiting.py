"""Rate limiting and abuse prevention utilities."""

import secrets

CAPTCHA_TOKEN_SESSION_KEY = "_captcha_bypass_token"


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
