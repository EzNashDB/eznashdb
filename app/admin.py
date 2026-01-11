"""Admin configuration for app infrastructure models."""

from datetime import timedelta

from django.contrib import admin
from django.utils import timezone

from app.models import RateLimitViolation


@admin.register(RateLimitViolation)
class RateLimitViolationAdmin(admin.ModelAdmin):
    list_display = [
        "ip_address",
        "endpoint",
        "violation_count",
        "last_violation_at",
        "cooldown_until",
        "user",
    ]
    list_filter = ["endpoint", "last_violation_at"]
    search_fields = ["ip_address", "user__email"]
    readonly_fields = ["first_violation_at", "last_violation_at"]
    ordering = ["-last_violation_at"]

    def get_queryset(self, request):
        """Show only active violations by default."""
        qs = super().get_queryset(request)
        return qs.filter(last_violation_at__gte=timezone.now() - timedelta(hours=24))
