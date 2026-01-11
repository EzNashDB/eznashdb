"""Rate limiting and abuse prevention utilities."""

import secrets

import sentry_sdk
from django.utils import timezone

CAPTCHA_TOKEN_SESSION_KEY = "_captcha_bypass_token"

# Constants
ENDPOINT_COORDINATE_ACCESS = "coordinate_access"


def get_client_ip(request):
    """
    Extract real client IP from Fly.io headers.

    Per Fly.io docs: https://fly.io/docs/networking/request-headers/
    Fly-Client-IP contains the client's actual IP address.
    """
    # Primary: Fly.io's client IP header (most reliable)
    if ip := request.META.get("HTTP_FLY_CLIENT_IP"):
        return ip

    # Fallback: X-Forwarded-For (first IP = client in Fly.io)
    if xff := request.META.get("HTTP_X_FORWARDED_FOR"):
        # Fly.io format: client, proxy1, proxy2
        return xff.split(",")[0].strip()

    # Last resort: REMOTE_ADDR
    return request.META.get("REMOTE_ADDR", "")


def record_violation(request, endpoint_key=ENDPOINT_COORDINATE_ACCESS):
    """
    Record rate limit violation and apply progressive escalation with CAPTCHA.

    Args:
        request: Django request object
        endpoint_key: One of ENDPOINT_* constants

    Returns:
        RateLimitViolation instance
    """
    from app.models import RateLimitViolation

    ip = get_client_ip(request)

    # Get or create violation record (unique per IP+endpoint)
    violation, created = RateLimitViolation.objects.get_or_create(
        ip_address=ip,
        endpoint=endpoint_key,
        defaults={
            "user": request.user if request.user.is_authenticated else None,
        },
    )

    # If not newly created, check if it's still within 24h window
    if not created:
        if violation.is_active():
            # Still within window - increment count
            violation.violation_count += 1
            violation.last_violation_at = timezone.now()
            if request.user.is_authenticated and not violation.user:
                violation.user = request.user
        else:
            # Outside 24h window - reset
            violation.violation_count = 1
            violation.first_violation_at = timezone.now()
            violation.last_violation_at = timezone.now()

    violation.save()

    # Log to Sentry for violations >= 3
    if violation.violation_count >= 3:
        sentry_sdk.capture_message(
            f"Rate limit abuse: {ip} hit {endpoint_key} {violation.violation_count}x",
            level="warning",
            extra={
                "ip": ip,
                "endpoint": endpoint_key,
                "violation_count": violation.violation_count,
                "user_id": request.user.id if request.user.is_authenticated else None,
            },
        )

    return violation


def check_captcha_required(request, endpoint_key=ENDPOINT_COORDINATE_ACCESS):
    """
    Check if CAPTCHA is required for this IP on this endpoint.
    CAPTCHA is required if there are active violations (within 24h)
    AND user doesn't have a valid one-time bypass token.

    Returns:
        bool: True if CAPTCHA required
    """
    from app.models import RateLimitViolation

    # Check for one-time bypass token (consume it if present)
    if consume_captcha_token(request):
        return False

    ip = get_client_ip(request)

    try:
        violation = RateLimitViolation.objects.get(ip_address=ip, endpoint=endpoint_key)
        return violation.requires_captcha()
    except RateLimitViolation.DoesNotExist:
        return False


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
