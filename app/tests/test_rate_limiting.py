"""Tests for rate limiting and abuse prevention."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone

from app.models import RateLimitViolation
from app.rate_limiting import (
    check_captcha_required,
    get_client_ip,
    record_violation,
)

User = get_user_model()


def describe_ip_extraction():
    """IP address extraction from request headers"""

    def uses_fly_client_ip_header_when_present():
        """Should use Fly-Client-IP header as primary source"""
        factory = RequestFactory()
        request = factory.get("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        assert get_client_ip(request) == "1.2.3.4"

    def falls_back_to_x_forwarded_for():
        """Should use first IP from X-Forwarded-For when Fly header missing"""
        factory = RequestFactory()
        request = factory.get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8")
        assert get_client_ip(request) == "1.2.3.4"


@pytest.mark.django_db
def describe_violation_recording():
    """Recording and escalation of rate limit violations"""

    def first_violation_has_no_cooldown(test_user):
        """First violation should not apply cooldown"""
        factory = RequestFactory()
        request = factory.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        violation = record_violation(request)

        assert violation.violation_count == 1
        assert violation.cooldown_until is None
        assert violation.requires_captcha() is True

    def second_violation_applies_15min_cooldown(test_user):
        """Second violation should apply 15-minute cooldown"""
        factory = RequestFactory()
        request = factory.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        # First violation
        record_violation(request)
        # Second violation
        violation = record_violation(request)

        assert violation.violation_count == 2
        assert violation.cooldown_until is not None
        assert violation.cooldown_until > timezone.now() + timedelta(minutes=14)
        assert violation.cooldown_until < timezone.now() + timedelta(minutes=16)

    def violations_reset_after_24_hours(test_user):
        """Violations should reset after 24-hour window"""
        factory = RequestFactory()
        request = factory.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        # Create violation
        violation = record_violation(request)
        assert violation.violation_count == 1

        # Simulate 25 hours passing (use update to bypass auto_now)
        RateLimitViolation.objects.filter(pk=violation.pk).update(
            last_violation_at=timezone.now() - timedelta(hours=25)
        )
        # Reload from database
        violation.refresh_from_db()

        # Should not be active
        assert violation.is_active() is False
        assert violation.requires_captcha() is False


@pytest.mark.django_db
def describe_captcha_requirement():
    """CAPTCHA requirement logic"""

    def required_after_first_violation(test_user):
        """CAPTCHA should be required after first violation"""
        factory = RequestFactory()
        request = factory.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        # No violation yet
        assert check_captcha_required(request) is False

        # Create violation
        record_violation(request)

        # CAPTCHA now required
        assert check_captcha_required(request) is True

    def not_required_after_24h_window(test_user):
        """CAPTCHA should not be required after 24h window expires"""
        factory = RequestFactory()
        request = factory.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        # Create violation
        violation = record_violation(request)

        # Simulate 25 hours passing (use update to bypass auto_now)
        RateLimitViolation.objects.filter(pk=violation.pk).update(
            last_violation_at=timezone.now() - timedelta(hours=25)
        )

        # CAPTCHA no longer required
        assert check_captcha_required(request) is False
