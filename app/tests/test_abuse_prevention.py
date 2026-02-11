"""Tests for user-based abuse prevention system."""

from datetime import timedelta

import pytest
from constance import config
from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from app.abuse_prevention import (
    BlockReason,
    get_blocked_response,
    process_abuse_state,
    record_abuse_violation,
)
from app.admin import AbuseAppealAdmin
from app.models import AbuseAppeal, AbuseState

User = get_user_model()


@pytest.mark.django_db
def describe_points_decay():
    """Points decay logic"""

    def decays_1_point_per_24_hours(test_user):
        """Should decay 1 point per 24 hours"""
        state = AbuseState.get_or_create(test_user)
        state.points = 3
        state.last_points_update_at = timezone.now() - timedelta(hours=48)
        state.save()

        state.apply_points_decay()

        assert state.points == 1  # 3 - 2 (48h / 24h)

    def does_not_decay_below_zero(test_user):
        """Should not decay points below zero"""
        state = AbuseState.get_or_create(test_user)
        state.points = 1
        state.last_points_update_at = timezone.now() - timedelta(hours=72)
        state.save()

        state.apply_points_decay()

        assert state.points == 0  # Cannot go negative

    def does_not_decay_when_permanently_banned(test_user):
        """Should not decay points when user is permanently banned (at threshold)"""
        state = AbuseState.get_or_create(test_user)
        state.points = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.last_points_update_at = timezone.now() - timedelta(hours=48)
        state.save()

        state.apply_points_decay()

        # Points should not decay - permanent ban freezes decay
        assert state.points == config.ABUSE_PERMANENT_BAN_THRESHOLD
        assert state.is_permanently_banned is True

    def updates_last_points_update_at_after_decay(test_user):
        """Should update last_points_update_at timestamp after decay"""
        state = AbuseState.get_or_create(test_user)
        state.points = 2
        old_time = timezone.now() - timedelta(hours=24)
        state.last_points_update_at = old_time
        state.save()

        state.apply_points_decay()

        assert state.last_points_update_at > old_time


@pytest.mark.django_db
def describe_episode_lifecycle():
    """Episode detection and lifecycle"""

    def episode_inactive_when_no_violation(test_user):
        """Episode should be inactive when no violations recorded"""
        state = AbuseState.get_or_create(test_user)

        assert state.is_episode_active() is False

    def episode_active_within_timeout(test_user):
        """Episode should be active within timeout window"""
        state = AbuseState.get_or_create(test_user)
        state.last_violation_at = timezone.now() - timedelta(minutes=30)
        state.save()

        assert state.is_episode_active() is True

    def episode_inactive_after_timeout(test_user):
        """Episode should be inactive after timeout window"""
        state = AbuseState.get_or_create(test_user)
        state.last_violation_at = timezone.now() - timedelta(
            minutes=config.ABUSE_EPISODE_INACTIVITY_MINUTES + 1
        )
        state.save()

        assert state.is_episode_active() is False

    def new_episode_increments_points(test_user):
        """Starting a new episode should increment points and set count to 1"""
        state = AbuseState.get_or_create(test_user)
        initial_points = state.points

        state.record_violation()

        assert state.points == initial_points + 1
        assert state.sensitive_count_in_episode == 1

    def same_episode_does_not_increment_points(test_user):
        """Multiple violations in same episode should not increment points but should increment count"""
        state = AbuseState.get_or_create(test_user)

        # First violation starts episode
        state.record_violation()
        points_after_first = state.points

        # Second violation in same episode
        state.record_violation()

        assert state.points == points_after_first  # No additional point
        assert state.sensitive_count_in_episode == 2  # Count should increment


@pytest.mark.django_db
def describe_sensitive_cap():
    """Sensitive request cap per episode"""

    def blocks_at_cap(test_user):
        """Should block when sensitive count reaches cap"""
        state = AbuseState.get_or_create(test_user)
        state.last_violation_at = timezone.now()  # Active episode
        state.sensitive_count_in_episode = config.ABUSE_SENSITIVE_CAP_PER_EPISODE
        state.save()

        result = process_abuse_state(test_user)

        assert result.allowed is False
        assert result.reason == BlockReason.EPISODE_CAP

    def allows_below_cap(test_user):
        """Should allow when sensitive count below cap"""
        state = AbuseState.get_or_create(test_user)
        state.last_violation_at = timezone.now()  # Active episode
        state.sensitive_count_in_episode = config.ABUSE_SENSITIVE_CAP_PER_EPISODE - 1
        state.save()

        result = process_abuse_state(test_user)

        assert result.allowed is True

    def increments_count_on_successful_request(test_user):
        """Should increment sensitive count on non-rate-limited request during episode"""
        state = AbuseState.get_or_create(test_user)
        state.points = 1  # Ensure episode context
        state.last_violation_at = timezone.now()  # Active episode
        state.sensitive_count_in_episode = 5
        state.save()

        record_abuse_violation(test_user, was_rate_limited=False)

        state.refresh_from_db()
        assert state.sensitive_count_in_episode == 6

    def increments_count_on_rate_limited_request_during_episode(test_user):
        """Should increment sensitive count even when rate-limited during active episode"""
        state = AbuseState.get_or_create(test_user)
        state.points = 1
        state.last_violation_at = timezone.now()  # Active episode
        state.sensitive_count_in_episode = 5
        state.save()

        # This simulates a request that's rate-limited but during an active episode
        record_abuse_violation(test_user, was_rate_limited=True)

        state.refresh_from_db()
        assert state.points == 1  # Points should not increment (same episode)
        assert state.sensitive_count_in_episode == 6  # Should increment, not reset


@pytest.mark.django_db
def describe_escalation_ladder():
    """Escalation ladder thresholds"""

    def no_captcha_at_zero_points(test_user):
        """Should not require CAPTCHA at 0 points"""
        state = AbuseState.get_or_create(test_user)
        state.points = 0
        state.save()

        result = process_abuse_state(test_user)

        assert result.requires_captcha is False

    def captcha_required_at_one_point(test_user):
        """Should require CAPTCHA at 1+ points"""
        state = AbuseState.get_or_create(test_user)
        state.points = 1
        state.save()

        result = process_abuse_state(test_user)

        assert result.requires_captcha is True

    def cooldown_applied_at_two_points(test_user):
        """Should apply 1-hour cooldown at 2 points"""
        state = AbuseState.get_or_create(test_user)
        state.points = 1  # Will become 2 after violation
        state.save()

        state.record_violation()

        assert state.points == 2
        assert state.cooldown_until is not None
        # Should be approximately 1 hour from now
        expected_cooldown = timezone.now() + timedelta(minutes=60)
        assert abs((state.cooldown_until - expected_cooldown).total_seconds()) < 5

    def permanent_ban_at_threshold(test_user):
        """Should be permanently banned when points reach threshold"""
        state = AbuseState.get_or_create(test_user)
        state.points = config.ABUSE_PERMANENT_BAN_THRESHOLD - 1
        state.save()

        state.record_violation()

        assert state.points == config.ABUSE_PERMANENT_BAN_THRESHOLD
        assert state.is_permanently_banned is True


@pytest.mark.django_db
def describe_enforcement_order():
    """Enforcement check order"""

    def permanent_ban_blocks_first(test_user):
        """Permanent ban should block before other checks"""
        state = AbuseState.get_or_create(test_user)
        state.points = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.save()

        result = process_abuse_state(test_user)

        assert result.allowed is False
        assert result.reason == BlockReason.PERMANENTLY_BANNED

    def cooldown_blocks_when_active(test_user):
        """Cooldown should block when active"""
        state = AbuseState.get_or_create(test_user)
        state.cooldown_until = timezone.now() + timedelta(minutes=30)
        state.save()

        result = process_abuse_state(test_user)

        assert result.allowed is False
        assert result.reason == BlockReason.COOLDOWN


@pytest.mark.django_db
def describe_appeal_ban_view():
    def requires_login(client):
        """Appeal view should require authentication"""
        url = reverse("appeal_ban")
        response = client.post(url, {"explanation": "Test"})

        assert response.status_code == 302
        assert settings.LOGIN_URL in response.url

    def creates_appeal_with_snapshot(client, test_user, superuser, mailoutbox):
        """Should create appeal with state snapshot and send email"""
        client.force_login(test_user)

        # Create abuse state with permanent ban (points at threshold)
        state = AbuseState.get_or_create(test_user)
        state.points = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.episode_started_at = timezone.now() - timedelta(hours=1)
        state.last_violation_at = timezone.now()
        state.save()

        url = reverse("appeal_ban")
        response = client.post(
            url, {"explanation": "I was just browsing normally", "abuse_state": state.id}
        )

        assert response.status_code == 302
        assert response.url == "/"

        # Check appeal was created
        appeal = AbuseAppeal.objects.get(abuse_state=state)
        assert appeal.explanation == "I was just browsing normally"
        assert appeal.status == AbuseAppeal.PENDING

        # Check snapshot was captured
        assert appeal.state_snapshot is not None
        assert appeal.state_snapshot["user_email"] == test_user.email
        assert appeal.state_snapshot["points"] == config.ABUSE_PERMANENT_BAN_THRESHOLD
        assert appeal.state_snapshot["is_permanently_banned"] is True

        # Check email was sent to superuser
        assert len(mailoutbox) == 1
        assert "New Abuse Appeal" in mailoutbox[0].subject
        assert superuser.email in mailoutbox[0].to


@pytest.mark.django_db
def describe_429_context():
    def includes_form_for_authenticated_permanent_ban(rf, test_user):
        """Should include form for authenticated users with permanent ban"""
        state = AbuseState.get_or_create(test_user)
        state.points = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.save()

        request = rf.get("/shuls/")
        request.user = test_user

        result = process_abuse_state(test_user)
        response = get_blocked_response(request, result)

        # Check that the response contains the appeal form
        assert b"Submit an Appeal" in response.content


@pytest.mark.django_db
def describe_appeal_admin_actions():
    """Admin actions for appeals"""

    def approve_appeal_resets_state(superuser, test_user):
        """Approving appeal should reset abuse state to clean state"""
        # Create abuse state and appeal
        state = AbuseState.get_or_create(test_user)
        state.points = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.save()

        appeal = AbuseAppeal.objects.create(
            abuse_state=state,
            explanation="Test appeal",
            state_snapshot={"points": config.ABUSE_PERMANENT_BAN_THRESHOLD},
        )

        # Execute admin action
        rf = RequestFactory()
        request = rf.post("/admin/")
        request.user = superuser
        request.session = {}
        request._messages = FallbackStorage(request)

        admin = AbuseAppealAdmin(AbuseAppeal, AdminSite())
        queryset = AbuseAppeal.objects.filter(pk=appeal.pk)
        admin.approve_appeal(request, queryset)

        # Check appeal status
        appeal.refresh_from_db()
        assert appeal.status == AbuseAppeal.APPROVED
        assert appeal.reviewed_by == superuser
        assert appeal.reviewed_at is not None

        # Check abuse state was set to threshold - 1 (unbanned but on thin ice)
        state.refresh_from_db()
        assert state.points == config.ABUSE_PERMANENT_BAN_THRESHOLD - 1
        assert state.is_permanently_banned is False
        assert state.cooldown_until is None

    def deny_appeal_updates_status(superuser, test_user):
        """Denying appeal should update status but keep abuse state"""
        # Create abuse state and appeal
        state = AbuseState.get_or_create(test_user)
        state.points = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.save()

        appeal = AbuseAppeal.objects.create(
            abuse_state=state,
            explanation="Test appeal",
            state_snapshot={"points": config.ABUSE_PERMANENT_BAN_THRESHOLD},
        )

        # Execute admin action
        rf = RequestFactory()
        request = rf.post("/admin/")
        request.user = superuser
        request.session = {}
        request._messages = FallbackStorage(request)

        admin = AbuseAppealAdmin(AbuseAppeal, AdminSite())
        queryset = AbuseAppeal.objects.filter(pk=appeal.pk)
        admin.deny_appeal(request, queryset)

        # Check appeal status
        appeal.refresh_from_db()
        assert appeal.status == AbuseAppeal.DENIED
        assert appeal.reviewed_by == superuser
        assert appeal.reviewed_at is not None

        # Check abuse state is banned (points set to threshold)
        state.refresh_from_db()
        assert state.points == config.ABUSE_PERMANENT_BAN_THRESHOLD
        assert state.is_permanently_banned is True
