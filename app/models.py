"""Infrastructure models for the app."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from app.rate_limiting import ENDPOINT_COORDINATE_ACCESS


class RateLimitViolation(models.Model):
    """Track rate limit violations for progressive enforcement."""

    ENDPOINT_CHOICES = [
        (ENDPOINT_COORDINATE_ACCESS, "Coordinate Access"),
    ]

    # Cooldown durations by violation count (in minutes)
    COOLDOWN_MINUTES = {
        1: 0,  # 1st violation: no cooldown, but captcha required
        2: 15,  # 2nd violation: 15 minutes
        3: 60,  # 3rd violation: 1 hour
        4: 60 * 24 * 7,  # 4th+ violation: 7 days
    }

    ip_address = models.GenericIPAddressField(db_index=True)
    endpoint = models.CharField(max_length=50, choices=ENDPOINT_CHOICES, db_index=True)
    violation_count = models.IntegerField(default=1)
    first_violation_at = models.DateTimeField(auto_now_add=True)
    last_violation_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User if authenticated during violation",
    )

    class Meta:
        verbose_name = "Rate Limit Violation"
        verbose_name_plural = "Rate Limit Violations"
        indexes = [
            models.Index(fields=["ip_address", "endpoint", "last_violation_at"]),
        ]
        unique_together = [["ip_address", "endpoint"]]

    def __str__(self):
        return f"{self.ip_address} - {self.endpoint} ({self.violation_count}x)"

    def is_active(self):
        """Check if violation is within 24-hour window."""
        return self.last_violation_at >= timezone.now() - timedelta(hours=24)

    def requires_captcha(self):
        """CAPTCHA required if violation is active."""
        return self.is_active()

    @property
    def cooldown_until(self):
        """Calculate cooldown end time based on violation count."""
        # For 4+ violations, use the 4th violation cooldown
        count = min(self.violation_count, 4)
        minutes = self.COOLDOWN_MINUTES.get(count, 0)
        if minutes:
            return self.last_violation_at + timedelta(minutes=minutes)
        return None

    def is_in_cooldown(self):
        """Check if currently in a cooldown period."""
        cooldown_end = self.cooldown_until
        return cooldown_end is not None and cooldown_end > timezone.now()

    def get_cooldown_context(self):
        """Get context dict for 429 template."""
        cooldown_end = self.cooldown_until
        if not cooldown_end:
            return {"is_long_block": False, "retry_after": 0}

        remaining_seconds = (cooldown_end - timezone.now()).total_seconds()
        remaining_days = remaining_seconds / (60 * 60 * 24)

        # Long block (7-day) vs short cooldowns
        if remaining_days > 2:
            return {"is_long_block": True}
        else:
            return {
                "is_long_block": False,
                "retry_after": max(1, int(remaining_seconds / 60)),
            }
