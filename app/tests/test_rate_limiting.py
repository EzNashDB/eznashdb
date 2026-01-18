"""Tests for rate limiting and abuse prevention."""

from datetime import timedelta

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from app.admin import RateLimitAppealAdmin
from app.emails import send_appeal_notification
from app.enums import RateLimitedEndpoint
from app.forms import RateLimitAppealForm
from app.middleware import RateLimitViolationMiddleware
from app.models import RateLimitAppeal, RateLimitViolation
from app.rate_limiting import ViolationRecorder, check_captcha_required, get_client_ip

User = get_user_model()


def describe_ip_extraction():
    """IP address extraction from request headers"""

    def uses_fly_client_ip_header_when_present(rf):
        """Should use Fly-Client-IP header as primary source"""
        request = rf.get("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        assert get_client_ip(request) == "1.2.3.4"

    def falls_back_to_x_forwarded_for(rf):
        """Should use first IP from X-Forwarded-For when Fly header missing"""
        request = rf.get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8")
        assert get_client_ip(request) == "1.2.3.4"


@pytest.mark.django_db
def describe_violation_recording():
    """Recording and escalation of rate limit violations"""

    def first_violation_has_no_cooldown(rf, test_user):
        """First violation should not apply cooldown"""
        request = rf.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        violation = ViolationRecorder(request).record()

        assert violation.violation_count == 1
        assert violation.cooldown_until is None
        assert violation.requires_captcha() is True

    def second_violation_applies_15min_cooldown(rf, test_user):
        """Second violation should apply 15-minute cooldown"""
        request = rf.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        # First violation
        ViolationRecorder(request).record()
        # Second violation
        violation = ViolationRecorder(request).record()

        assert violation.violation_count == 2
        assert violation.cooldown_until is not None
        assert violation.cooldown_until > timezone.now() + timedelta(minutes=14)
        assert violation.cooldown_until < timezone.now() + timedelta(minutes=16)

    def violations_reset_after_24_hours(rf, test_user):
        """Violations should reset after 24-hour window"""
        request = rf.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        # Create violation
        violation = ViolationRecorder(request).record()
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

    def required_after_first_violation(rf, test_user):
        """CAPTCHA should be required after first violation"""
        request = rf.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user
        request.session = {}

        # No violation yet
        assert check_captcha_required(request) is False

        # Create violation
        ViolationRecorder(request).record()

        # CAPTCHA now required
        assert check_captcha_required(request) is True

    def not_required_after_24h_window(rf, test_user):
        """CAPTCHA should not be required after 24h window expires"""
        request = rf.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user
        request.session = {}

        # Create violation
        violation = ViolationRecorder(request).record()

        # Simulate 25 hours passing (use update to bypass auto_now)
        RateLimitViolation.objects.filter(pk=violation.pk).update(
            last_violation_at=timezone.now() - timedelta(hours=25)
        )

        # CAPTCHA no longer required
        assert check_captcha_required(request) is False


@pytest.mark.django_db
def describe_permanent_ban_logic():
    """Permanent ban property and behavior"""

    def is_permanent_ban_returns_true_for_4_violations(rf, test_user):
        """is_permanent_ban should return True for 4+ violations"""
        request = rf.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        # Create 4 violations
        recorder = ViolationRecorder(request)
        for _ in range(4):
            violation = recorder.record()

        assert violation.violation_count == 4
        assert violation.is_permanent_ban is True


@pytest.mark.django_db
def describe_user_ids_tracking():
    """Tracking multiple users from same IP"""

    def tracks_single_user_id(rf, test_user):
        """Should track user ID in user_ids array"""
        request = rf.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        violation = ViolationRecorder(request).record()

        assert test_user.id in violation.user_ids
        assert len(violation.user_ids) == 1

    def tracks_multiple_users_from_same_ip(rf, test_user):
        """Should track multiple user IDs from same IP"""
        # First user
        request = rf.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user
        violation = ViolationRecorder(request).record()

        # Second user
        second_user = User.objects.create_user(username="user2", email="user2@example.com")
        request.user = second_user
        violation = ViolationRecorder(request).record()

        assert test_user.id in violation.user_ids
        assert second_user.id in violation.user_ids
        assert len(violation.user_ids) == 2

    def does_not_duplicate_user_ids(rf, test_user):
        """Should not duplicate user IDs in array"""
        request = rf.post("/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        # Same user triggers multiple violations
        recorder = ViolationRecorder(request)
        recorder.record()
        violation = recorder.record()

        assert violation.user_ids.count(test_user.id) == 1


@pytest.mark.django_db
def describe_rate_limit_appeal_view():
    """RateLimitAppealView behavior"""

    def requires_login(client):
        """Appeal view should require authentication"""
        url = reverse("appeal_rate_limit")
        response = client.post(url, {"explanation": "Test"})

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def creates_appeal_with_snapshot(client, test_user, superuser):
        """Should create appeal with violation snapshot and send email"""
        client.force_login(test_user)

        # Create permanent ban
        violation = RateLimitViolation.objects.create(
            ip_address="1.2.3.4",
            endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
            violation_count=4,
            first_violation_at=timezone.now(),
            last_violation_at=timezone.now(),
            user_ids=[test_user.id],
        )

        url = reverse("appeal_rate_limit")
        response = client.post(
            url, {"explanation": "I was just browsing normally", "violation": violation.id}
        )

        assert response.status_code == 302
        assert response.url == "/"

        # Check appeal was created
        appeal = RateLimitAppeal.objects.get(violation=violation)
        assert appeal.appealed_by == test_user
        assert appeal.explanation == "I was just browsing normally"
        assert appeal.status == RateLimitAppeal.PENDING

        # Check snapshot was captured
        assert appeal.violation_snapshot is not None
        assert appeal.violation_snapshot["ip_address"] == "1.2.3.4"
        assert appeal.violation_snapshot["violation_count"] == 4
        assert test_user.id in appeal.violation_snapshot["user_ids"]

        # Check email was sent to superuser
        assert len(mail.outbox) == 1
        assert "New Rate Limit Appeal" in mail.outbox[0].subject
        assert superuser.email in mail.outbox[0].to


@pytest.mark.django_db
def describe_middleware_429_context():
    """Middleware 429 page context"""

    def includes_violation_in_context(rf, test_user):
        """Should include violation in context"""

        violation = RateLimitViolation.objects.create(
            ip_address="1.2.3.4",
            endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
            violation_count=4,
            first_violation_at=timezone.now(),
            last_violation_at=timezone.now(),
        )

        request = rf.get("/shuls/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        middleware = RateLimitViolationMiddleware(lambda r: None)
        context = middleware.get_cooldown_context(violation, request)

        assert "violation" in context
        assert context["violation"] == violation

    def includes_form_for_authenticated_permanent_ban(rf, test_user):
        """Should include form for authenticated users with permanent ban"""
        violation = RateLimitViolation.objects.create(
            ip_address="1.2.3.4",
            endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
            violation_count=4,
            first_violation_at=timezone.now(),
            last_violation_at=timezone.now(),
        )

        request = rf.get("/shuls/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        middleware = RateLimitViolationMiddleware(lambda r: None)
        context = middleware.get_cooldown_context(violation, request)

        assert "appeal_form" in context
        assert isinstance(context["appeal_form"], RateLimitAppealForm)

    def no_form_for_temporary_ban(rf, test_user):
        """Should not include form for temporary bans"""
        violation = RateLimitViolation.objects.create(
            ip_address="1.2.3.4",
            endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
            violation_count=2,
            first_violation_at=timezone.now(),
            last_violation_at=timezone.now(),
        )

        request = rf.get("/shuls/", HTTP_FLY_CLIENT_IP="1.2.3.4")
        request.user = test_user

        middleware = RateLimitViolationMiddleware(lambda r: None)
        context = middleware.get_cooldown_context(violation, request)

        assert "form" not in context
        assert "retry_after" in context


@pytest.mark.django_db
def describe_appeal_admin_actions():
    """Admin actions for appeals"""

    def approve_appeal_resets_violation(superuser, test_user):
        """Approving appeal should reset violation to clean state"""
        # Create violation and appeal
        violation = RateLimitViolation.objects.create(
            ip_address="1.2.3.4",
            endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
            violation_count=4,
            first_violation_at=timezone.now(),
            last_violation_at=timezone.now(),
            user_ids=[test_user.id],
        )

        appeal = RateLimitAppeal.objects.create(
            violation=violation,
            appealed_by=test_user,
            explanation="Test appeal",
            violation_snapshot={"violation_count": 4},
        )

        # Execute admin action
        rf = RequestFactory()
        request = rf.post("/admin/")
        request.user = superuser
        request.session = {}
        request._messages = FallbackStorage(request)

        admin = RateLimitAppealAdmin(RateLimitAppeal, AdminSite())
        queryset = RateLimitAppeal.objects.filter(pk=appeal.pk)
        admin.approve_appeal(request, queryset)

        # Check appeal status
        appeal.refresh_from_db()
        assert appeal.status == RateLimitAppeal.APPROVED
        assert appeal.reviewed_by == superuser
        assert appeal.reviewed_at is not None

        # Check violation was reset
        violation.refresh_from_db()
        assert violation.violation_count == 0
        assert violation.user_ids == []

    def deny_appeal_updates_status(superuser, test_user):
        """Denying appeal should update status but keep violation"""
        # Create violation and appeal
        violation = RateLimitViolation.objects.create(
            ip_address="1.2.3.4",
            endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
            violation_count=4,
            first_violation_at=timezone.now(),
            last_violation_at=timezone.now(),
        )

        appeal = RateLimitAppeal.objects.create(
            violation=violation,
            appealed_by=test_user,
            explanation="Test appeal",
            violation_snapshot={"violation_count": 4},
        )

        # Execute admin action
        rf = RequestFactory()
        request = rf.post("/admin/")
        request.user = superuser
        request.session = {}
        request._messages = FallbackStorage(request)

        admin = RateLimitAppealAdmin(RateLimitAppeal, AdminSite())
        queryset = RateLimitAppeal.objects.filter(pk=appeal.pk)
        admin.deny_appeal(request, queryset)

        # Check appeal status
        appeal.refresh_from_db()
        assert appeal.status == RateLimitAppeal.DENIED
        assert appeal.reviewed_by == superuser
        assert appeal.reviewed_at is not None

        # Check violation unchanged
        violation.refresh_from_db()
        assert violation.violation_count == 4


@pytest.mark.django_db
def describe_appeal_email_notifications():
    """Email notifications for appeals"""

    def sends_to_all_superusers(test_user):
        """Should send appeal notification to all superusers"""
        # Create superusers
        superuser1 = User.objects.create_superuser(
            username="super1", email="super1@example.com", password="pass"
        )
        superuser2 = User.objects.create_superuser(
            username="super2", email="super2@example.com", password="pass"
        )

        # Create violation and appeal
        violation = RateLimitViolation.objects.create(
            ip_address="1.2.3.4",
            endpoint=RateLimitedEndpoint.COORDINATE_ACCESS,
            violation_count=4,
            first_violation_at=timezone.now(),
            last_violation_at=timezone.now(),
            user_ids=[test_user.id],
        )

        appeal = RateLimitAppeal.objects.create(
            violation=violation,
            appealed_by=test_user,
            explanation="Test appeal",
            violation_snapshot={
                "ip_address": "1.2.3.4",
                "violation_count": 4,
                "user_ids": [test_user.id],
                "first_violation_at": timezone.now().isoformat(),
                "last_violation_at": timezone.now().isoformat(),
            },
        )

        # Send notification

        send_appeal_notification(appeal)

        # Check email sent to both superusers
        assert len(mail.outbox) == 1
        assert superuser1.email in mail.outbox[0].to
        assert superuser2.email in mail.outbox[0].to
        assert "New Rate Limit Appeal" in mail.outbox[0].subject
        assert "1.2.3.4" in mail.outbox[0].alternatives[0][0]
