"""Tests for user-based abuse prevention system."""

from datetime import timedelta
from types import SimpleNamespace

import pytest
from constance import config
from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django_ratelimit.core import _split_rate

from app.abuse_prevention import (
    BlockReason,
    build_block_context,
    get_request_points,
    process_abuse_state,
    record_abuse_violation,
)
from app.admin import AbuseAppealAdmin
from app.models import AbuseAppeal, AbuseState
from app.rate_limiting import consume_rate_budget

User = get_user_model()


@pytest.mark.django_db
def describe_strikes_decay():
    """Strikes decay logic"""

    def decays_1_strike_per_24_hours(test_user):
        """Should decay 1 strike per 24 hours"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = 3
        state.last_strikes_update_at = timezone.now() - timedelta(hours=48)
        state.save()

        state.apply_strikes_decay()

        assert state.strikes == 1  # 3 - 2 (48h / 24h)

    def does_not_decay_below_zero(test_user):
        """Should not decay strikes below zero"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = 1
        state.last_strikes_update_at = timezone.now() - timedelta(hours=72)
        state.save()

        state.apply_strikes_decay()

        assert state.strikes == 0  # Cannot go negative

    def does_not_decay_when_permanently_banned(test_user):
        """Should not decay strikes when user is permanently banned (at threshold)"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.last_strikes_update_at = timezone.now() - timedelta(hours=48)
        state.save()

        state.apply_strikes_decay()

        # Strikes should not decay - permanent ban freezes decay
        assert state.strikes == config.ABUSE_PERMANENT_BAN_THRESHOLD
        assert state.is_permanently_banned is True

    def updates_last_strikes_update_at_after_decay(test_user):
        """Should update last_strikes_update_at timestamp after decay"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = 2
        old_time = timezone.now() - timedelta(hours=24)
        state.last_strikes_update_at = old_time
        state.save()

        state.apply_strikes_decay()

        assert state.last_strikes_update_at > old_time

    def get_strikes_applies_and_persists_decay(test_user):
        """Should apply decay and persist when calling get_strikes()"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = 3
        state.last_strikes_update_at = timezone.now() - timedelta(hours=48)
        state.save()

        strikes = state.get_strikes()

        assert strikes == 1  # 3 - 2 (48h / 24h)
        state.refresh_from_db()
        assert state.strikes == 1  # Should be persisted to DB


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

    def new_episode_increments_strikes(test_user):
        """Starting a new episode should increment strikes and set count to 1"""
        state = AbuseState.get_or_create(test_user)
        initial_strikes = state.strikes

        state.record_violation()

        assert state.strikes == initial_strikes + 1
        assert state.points_in_episode == 1

    def same_episode_does_not_increment_strikes(test_user):
        """Multiple violations in same episode should not increment strikes but should increment count"""
        state = AbuseState.get_or_create(test_user)

        # First violation starts episode
        state.record_violation()
        strikes_after_first = state.strikes

        # Second violation in same episode
        state.record_violation()

        assert state.strikes == strikes_after_first  # No additional strike
        assert state.points_in_episode == 2  # Count should increment


@pytest.mark.django_db
def describe_points_cap():
    """Points cap per episode"""

    def blocks_at_cap(test_user):
        """Should block when points reach cap"""
        state = AbuseState.get_or_create(test_user)
        state.last_violation_at = timezone.now()  # Active episode
        state.points_in_episode = config.ABUSE_POINTS_CAP_PER_EPISODE
        state.save()

        result = process_abuse_state(test_user)

        assert result.allowed is False
        assert result.reason == BlockReason.EPISODE_CAP

    def allows_below_cap(test_user):
        """Should allow when points are below cap"""
        state = AbuseState.get_or_create(test_user)
        state.last_violation_at = timezone.now()  # Active episode
        state.points_in_episode = config.ABUSE_POINTS_CAP_PER_EPISODE - 1
        state.save()

        result = process_abuse_state(test_user)

        assert result.allowed is True

    def increments_count_on_successful_request(test_user):
        """Should add points on non-rate-limited request during episode"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = 1  # Ensure episode context
        state.last_violation_at = timezone.now()  # Active episode
        state.points_in_episode = 5
        state.save()

        record_abuse_violation(test_user, was_rate_limited=False)

        state.refresh_from_db()
        assert state.points_in_episode == 6

    def increments_count_on_rate_limited_request_during_episode(test_user):
        """Should add points even when rate-limited during active episode"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = 1
        state.last_violation_at = timezone.now()  # Active episode
        state.points_in_episode = 5
        state.save()

        # This simulates a request that's rate-limited but during an active episode
        record_abuse_violation(test_user, was_rate_limited=True)

        state.refresh_from_db()
        assert state.strikes == 1  # Strikes should not increment (same episode)
        assert state.points_in_episode == 6  # Should increment, not reset

    def increments_count_by_request_points(test_user):
        """Should add the request's points, not always 1"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = 1
        state.last_violation_at = timezone.now()  # Active episode
        state.points_in_episode = 5
        state.save()

        record_abuse_violation(test_user, was_rate_limited=False, points=4)

        state.refresh_from_db()
        assert state.points_in_episode == 9


@pytest.mark.django_db
def describe_get_request_points():
    """Per-endpoint request points"""

    def create_shul_costs_one_unit(rf_GET):
        request = rf_GET("eznashdb:create_shul")

        assert get_request_points(request) == 1

    def update_shul_costs_four_units(rf_GET, test_shul):
        request = rf_GET("eznashdb:update_shul", url_params={"pk": test_shul.pk})

        assert get_request_points(request) == 4

    def google_maps_proxy_costs_four_units(rf_GET):
        request = rf_GET("eznashdb:google_maps_proxy")

        assert get_request_points(request) == 4

    def non_sensitive_url_costs_nothing(rf_GET):
        request = rf_GET("eznashdb:shuls")

        assert get_request_points(request) == 0


@pytest.mark.django_db
def describe_consume_rate_budget():
    """The weighted rate-limit counter"""

    def stays_under_budget_at_exactly_the_limit(test_user):
        limit, _period = _split_rate(config.ABUSE_RATE_LIMIT)
        request = SimpleNamespace(user=test_user)

        over_budget = consume_rate_budget(request, limit)

        assert over_budget is False

    def trips_the_moment_budget_is_exceeded(test_user):
        limit, _period = _split_rate(config.ABUSE_RATE_LIMIT)
        request = SimpleNamespace(user=test_user)
        consume_rate_budget(request, limit)  # spend the whole budget

        over_budget = consume_rate_budget(request, 1)

        assert over_budget is True

    def charges_accumulate_across_calls_of_different_points(test_user):
        """Mixed traffic (e.g. some updates, some creates) sums against one budget."""
        limit, _period = _split_rate(config.ABUSE_RATE_LIMIT)
        request = SimpleNamespace(user=test_user)
        consume_rate_budget(request, limit - 4)  # leave room for exactly one 4-point request

        over_budget = consume_rate_budget(request, 4)

        assert over_budget is False

    def treats_a_vanished_cache_key_as_over_budget(test_user, mocker):
        """cache.incr() raises ValueError if the key vanished between add() and
        incr() (e.g. culled or expired). django_ratelimit's own get_usage()
        treats that as a failure and blocks by default (RATELIMIT_FAIL_OPEN=False);
        consume_rate_budget must do the same rather than propagate the exception.
        """
        fake_cache = mocker.Mock()
        fake_cache.add.return_value = False
        fake_cache.incr.side_effect = ValueError("Key not found")
        mocker.patch("app.rate_limiting.caches", {"default": fake_cache})
        request = SimpleNamespace(user=test_user)

        over_budget = consume_rate_budget(request, 1)

        assert over_budget is True

    def honors_RATELIMIT_ENABLE_setting(test_user, settings):
        """django_ratelimit's get_usage() no-ops entirely when RATELIMIT_ENABLE
        is False - a global escape hatch for incidents. consume_rate_budget
        must honor the same setting rather than always charging."""
        settings.RATELIMIT_ENABLE = False
        request = SimpleNamespace(user=test_user)

        over_budget = consume_rate_budget(request, 1_000_000)

        assert over_budget is False


@pytest.mark.django_db
def describe_rate_limited_methods():
    """Only GET/POST are charged against the budget, matching the previous
    django-ratelimit `method=["GET", "POST"]` filter. Other methods are
    rejected by Django's own dispatch (405) before reaching the view, so
    charging them would let a client burn a user's budget for free."""

    def charges_budget_on_get(client, test_user, mocker):
        client.force_login(test_user)
        spy = mocker.patch("app.mixins.consume_rate_budget", return_value=False)

        client.get(reverse("eznashdb:google_maps_proxy"))

        spy.assert_called_once()

    def does_not_charge_budget_for_unsupported_methods(client, test_user, mocker):
        client.force_login(test_user)
        spy = mocker.patch("app.mixins.consume_rate_budget", return_value=False)

        response = client.delete(reverse("eznashdb:google_maps_proxy"))

        assert response.status_code == 405
        spy.assert_not_called()

    def does_not_record_against_an_active_episode_for_unsupported_methods(client, test_user):
        """Regression: an unsupported method used to still call
        record_abuse_violation whenever the user was already mid-episode,
        silently adding to points_in_episode even though the request never
        touched the rate budget."""
        client.force_login(test_user)
        state = AbuseState.get_or_create(test_user)
        state.last_violation_at = timezone.now()  # active episode
        state.points_in_episode = 5
        state.save()

        client.delete(reverse("eznashdb:google_maps_proxy"))

        state.refresh_from_db()
        assert state.points_in_episode == 5


@pytest.mark.django_db
def describe_escalation_ladder():
    """Escalation ladder thresholds"""

    def no_captcha_at_zero_strikes(test_user):
        """Should not require CAPTCHA at 0 strikes"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = 0
        state.save()

        result = process_abuse_state(test_user)

        assert result.requires_captcha is False

    def captcha_required_at_one_strike(test_user):
        """Should require CAPTCHA at 1+ strikes"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = 1
        state.save()

        result = process_abuse_state(test_user)

        assert result.requires_captcha is True

    def cooldown_applied_at_two_strikes(test_user):
        """Should apply 1-hour cooldown at 2 strikes"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = 1  # Will become 2 after violation
        state.save()

        state.record_violation()

        assert state.strikes == 2
        assert state.cooldown_until is not None
        # Should be approximately 1 hour from now
        expected_cooldown = timezone.now() + timedelta(minutes=60)
        assert abs((state.cooldown_until - expected_cooldown).total_seconds()) < 5

    def permanent_ban_at_threshold(test_user):
        """Should be permanently banned when strikes reach threshold"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = config.ABUSE_PERMANENT_BAN_THRESHOLD - 1
        state.save()

        state.record_violation()

        assert state.strikes == config.ABUSE_PERMANENT_BAN_THRESHOLD
        assert state.is_permanently_banned is True


@pytest.mark.django_db
def describe_enforcement_order():
    """Enforcement check order"""

    def permanent_ban_blocks_first(test_user):
        """Permanent ban should block before other checks"""
        state = AbuseState.get_or_create(test_user)
        state.strikes = config.ABUSE_PERMANENT_BAN_THRESHOLD
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

        # Create abuse state with permanent ban (strikes at threshold)
        state = AbuseState.get_or_create(test_user)
        state.strikes = config.ABUSE_PERMANENT_BAN_THRESHOLD
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
        assert appeal.state_snapshot["strikes"] == config.ABUSE_PERMANENT_BAN_THRESHOLD
        assert appeal.state_snapshot["is_permanently_banned"] is True

        # Check email was sent to superuser
        assert len(mailoutbox) == 1
        assert "New Abuse Appeal" in mailoutbox[0].subject
        assert superuser.email in mailoutbox[0].to

    def invalid_submission_renders_429_with_correct_title(client, test_user):
        """Regression test: the invalid-form branch must show "Access
        Restricted", not the default "Temporarily Blocked" a missing
        abuse_state would produce."""
        client.force_login(test_user)

        state = AbuseState.get_or_create(test_user)
        state.strikes = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.save()

        url = reverse("appeal_ban")
        response = client.post(url, {"explanation": "", "abuse_state": state.id})

        assert response.status_code == 200
        assert b"<html" in response.content
        assert b"Access Restricted" in response.content


@pytest.mark.django_db
def describe_429_context():
    def includes_form_for_authenticated_permanent_ban(test_user):
        """Should include form for authenticated users with permanent ban.

        Guards the context-building + template pair directly, independent of
        which delivery path (htmx modal vs. full-page 429) is in play - those
        have their own coverage in test_abuse_enforcement_delivery.py.
        """
        state = AbuseState.get_or_create(test_user)
        state.strikes = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.save()

        result = process_abuse_state(test_user)
        context = build_block_context(result)
        html = render_to_string("includes/abuse_modal.html", context)

        assert "Submit an Appeal" in html


@pytest.mark.django_db
def describe_appeal_admin_actions():
    """Admin actions for appeals"""

    def approve_appeal_resets_state(superuser, test_user):
        """Approving appeal should reset abuse state to clean state"""
        # Create abuse state and appeal
        state = AbuseState.get_or_create(test_user)
        state.strikes = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.save()

        appeal = AbuseAppeal.objects.create(
            abuse_state=state,
            explanation="Test appeal",
            state_snapshot={"strikes": config.ABUSE_PERMANENT_BAN_THRESHOLD},
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
        assert state.strikes == config.ABUSE_PERMANENT_BAN_THRESHOLD - 1
        assert state.is_permanently_banned is False
        assert state.cooldown_until is None

    def deny_appeal_updates_status(superuser, test_user):
        """Denying appeal should update status but keep abuse state"""
        # Create abuse state and appeal
        state = AbuseState.get_or_create(test_user)
        state.strikes = config.ABUSE_PERMANENT_BAN_THRESHOLD
        state.save()

        appeal = AbuseAppeal.objects.create(
            abuse_state=state,
            explanation="Test appeal",
            state_snapshot={"strikes": config.ABUSE_PERMANENT_BAN_THRESHOLD},
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

        # Check abuse state is banned (strikes set to threshold)
        state.refresh_from_db()
        assert state.strikes == config.ABUSE_PERMANENT_BAN_THRESHOLD
        assert state.is_permanently_banned is True
