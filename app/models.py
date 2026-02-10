"""Infrastructure models for the app."""

from calendar import monthrange
from datetime import date as date_type
from datetime import timedelta
from typing import NamedTuple

import sentry_sdk
from constance import config
from django.conf import settings
from django.db import models
from django.utils import timezone

from app.abuse_config import (
    EPISODE_TIMEOUT_MINUTES,
    PERMANENT_BAN_THRESHOLD,
    POINTS_DECAY_HOURS,
    SENSITIVE_CAP_PER_EPISODE,
)


class GooglePlacesCount(NamedTuple):
    """Count of Google Places API requests (autocomplete and details)."""

    autocomplete: int
    details: int


class AbuseState(models.Model):
    """Track abuse state for user-based abuse prevention."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="abuse_state",
    )
    points = models.PositiveIntegerField(default=0)
    last_points_update_at = models.DateTimeField(auto_now_add=True)
    episode_started_at = models.DateTimeField(null=True, blank=True)
    last_violation_at = models.DateTimeField(null=True, blank=True)
    sensitive_count_in_episode = models.PositiveIntegerField(default=0)
    cooldown_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Abuse State"
        verbose_name_plural = "Abuse States"

    def __str__(self):
        return f"{self.user.email} - {self.points} points"

    @property
    def is_permanently_banned(self):
        return self.points >= PERMANENT_BAN_THRESHOLD

    def is_in_cooldown(self):
        """Check if currently in a cooldown period."""
        return self.cooldown_until and self.cooldown_until > timezone.now()

    @classmethod
    def get_or_create(cls, user) -> "AbuseState":
        """Get or create abuse state for a user."""
        state, _ = cls.objects.get_or_create(user=user)
        return state

    def is_episode_active(self) -> bool:
        """Check if episode is active (last violation within timeout window)."""
        if self.last_violation_at is None:
            return False
        timeout = timedelta(minutes=EPISODE_TIMEOUT_MINUTES)
        return self.last_violation_at >= timezone.now() - timeout

    def refresh(self):
        self.apply_points_decay()
        self.apply_episode_cap_cooldown()

    def apply_points_decay(self) -> None:
        """Apply on-demand points decay: -1 point per 24 hours since last update."""
        if self.points == 0 or self.is_permanently_banned:
            return

        now = timezone.now()
        hours_since_update = (now - self.last_points_update_at).total_seconds() / 3600
        points_to_decay = int(hours_since_update // POINTS_DECAY_HOURS)

        if points_to_decay > 0:
            self.points = max(0, self.points - points_to_decay)
            self.last_points_update_at = now
            self.save(update_fields=["points", "last_points_update_at"])

    def apply_episode_cap_cooldown(self) -> None:
        from app.abuse_prevention import get_cooldown_minutes

        if (
            self.is_episode_active()
            and self.sensitive_count_in_episode >= SENSITIVE_CAP_PER_EPISODE
            and not self.is_in_cooldown()
        ):
            cooldown_minutes = get_cooldown_minutes(self.points)
            if cooldown_minutes > 0:
                self.cooldown_until = timezone.now() + timedelta(minutes=cooldown_minutes)
                self.save(update_fields=["cooldown_until"])

    def record_violation(self) -> None:
        from app.abuse_prevention import get_cooldown_minutes

        """Record a sensitive request. Starts new episode if none active."""
        now = timezone.now()
        is_new_episode = not self.is_episode_active()

        if is_new_episode:
            self.points += 1
            self.sensitive_count_in_episode = 1
            self.episode_started_at = now
            self.last_points_update_at = now

            cooldown_minutes = get_cooldown_minutes(self.points)
            if cooldown_minutes > 0:
                self.cooldown_until = now + timedelta(minutes=cooldown_minutes)
            else:
                self.cooldown_until = None

            self._log_violation_to_sentry()
        else:
            # Existing episode - just increment count
            self.sensitive_count_in_episode += 1

        self.last_violation_at = now
        self.save()

    def _log_violation_to_sentry(self) -> None:
        """Log abuse violation to Sentry for monitoring."""
        sentry_sdk.capture_message(
            f"Abuse prevention: user {self.user.email} hit rate limit, now at {self.points} points",
            level="warning",
            extra={
                "user_id": self.user.id,
                "user_email": self.user.email,
                "points": self.points,
                "is_permanently_banned": self.is_permanently_banned,
            },
        )


class AbuseAppeal(models.Model):
    """User appeals for abuse bans."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"

    STATUS_CHOICES = [
        (PENDING, "Pending Review"),
        (APPROVED, "Approved"),
        (DENIED, "Denied"),
    ]

    abuse_state = models.ForeignKey(AbuseState, on_delete=models.CASCADE, related_name="appeals")
    explanation = models.TextField()
    state_snapshot = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_appeals",
    )
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Abuse Appeal"
        verbose_name_plural = "Abuse Appeals"

    def __str__(self):
        return f"Appeal from {self.abuse_state.user.email} - {self.status}"


class GooglePlacesUsage(models.Model):
    """Global daily usage tracking for Google Places API."""

    date = models.DateField(unique=True, db_index=True)
    autocomplete_requests = models.PositiveIntegerField(default=0)
    details_requests = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Google Places Usage"
        verbose_name_plural = "Google Places Usage"

    def __str__(self):
        return f"{self.date}: {self.autocomplete_requests} autocomplete, {self.details_requests} details"

    @classmethod
    def get_monthly_usage_before_date(cls, target_date: date_type) -> GooglePlacesCount:
        """Get total autocomplete and details requests before target_date (not including it)."""
        first_day = date_type(target_date.year, target_date.month, 1)
        monthly_records = cls.objects.filter(date__gte=first_day, date__lt=target_date)
        autocomplete = sum(r.autocomplete_requests for r in monthly_records)
        details = sum(r.details_requests for r in monthly_records)
        return GooglePlacesCount(autocomplete, details)

    @classmethod
    def get_usage_for_date(cls, target_date: date_type) -> GooglePlacesCount:
        """Get autocomplete and details requests for a specific date."""
        record = cls.objects.filter(date=target_date).first()
        if not record:
            return GooglePlacesCount(0, 0)
        return GooglePlacesCount(record.autocomplete_requests, record.details_requests)

    @classmethod
    def get_daily_budget(cls, target_date: date_type) -> GooglePlacesCount:
        """
        Calculate daily budget for target_date based on usage from previous days.
        Returns GooglePlacesCount with autocomplete and details budgets.
        """
        # Get usage before this date (not including it)
        usage = cls.get_monthly_usage_before_date(target_date)

        # Calculate remaining quota
        autocomplete_remaining = config.GOOGLE_PLACES_MONTHLY_AUTOCOMPLETE_LIMIT - usage.autocomplete
        details_remaining = config.GOOGLE_PLACES_MONTHLY_DETAILS_LIMIT - usage.details

        # Calculate days remaining in month (including target_date)
        _, days_in_month = monthrange(target_date.year, target_date.month)
        days_remaining = days_in_month - target_date.day + 1

        # Spread remaining quota over remaining days
        autocomplete_budget = max(0, autocomplete_remaining // days_remaining)
        details_budget = max(0, details_remaining // days_remaining)

        return GooglePlacesCount(autocomplete_budget, details_budget)


class GooglePlacesUserUsage(models.Model):
    """
    Per-user daily usage tracking for Google Places API (abuse prevention).

    Note: Only tracks autocomplete requests, not details requests. This is intentional
    because details requests can only be made after selecting an autocomplete result,
    so limiting autocomplete inherently limits details. Tracking autocomplete is
    sufficient for preventing abuse (e.g., users spamming the search box).
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    autocomplete_requests = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ["user", "date"]
        verbose_name = "Google Places User Usage"
        verbose_name_plural = "Google Places User Usage"

    def __str__(self):
        return f"{self.user.email} on {self.date}: {self.autocomplete_requests} requests"
