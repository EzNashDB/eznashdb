"""Admin configuration for app infrastructure models."""

from django.contrib import admin

from app.models import RateLimitViolation


@admin.register(RateLimitViolation)
class RateLimitViolationAdmin(admin.ModelAdmin):
    list_display = [
        "ip_address",
        "endpoint",
        "violation_count",
        "last_violation_at",
        "is_active",
        "cooldown_until",
        "user",
    ]
    list_filter = ["endpoint", "last_violation_at"]
    search_fields = ["ip_address", "user__email"]
    readonly_fields = ["first_violation_at", "last_violation_at"]
    ordering = ["-last_violation_at"]

    @admin.display(boolean=True, description="Active")
    def is_active(self, obj):
        """Display whether violation is active."""
        return obj.is_active()
