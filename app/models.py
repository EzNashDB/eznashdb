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

    ip_address = models.GenericIPAddressField(db_index=True)
    endpoint = models.CharField(max_length=50, choices=ENDPOINT_CHOICES, db_index=True)
    violation_count = models.IntegerField(default=1)
    first_violation_at = models.DateTimeField(auto_now_add=True)
    last_violation_at = models.DateTimeField(auto_now=True)
    cooldown_until = models.DateTimeField(null=True, blank=True)
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
