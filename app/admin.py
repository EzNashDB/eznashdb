"""Admin configuration for app infrastructure models."""

from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from app.models import RateLimitAppeal, RateLimitViolation


@admin.register(RateLimitViolation)
class RateLimitViolationAdmin(admin.ModelAdmin):
    list_display = [
        "ip_address",
        "endpoint",
        "violation_count",
        "user_count",
        "time_span",
        "last_violation_at",
        "is_active",
        "status",
    ]
    list_filter = ["endpoint", "last_violation_at"]
    search_fields = ["ip_address", "user__email"]
    readonly_fields = [
        "user_count",
        "time_span",
        "first_violation_at",
        "last_violation_at",
    ]
    ordering = ["-last_violation_at"]

    @admin.display(boolean=True, description="Active")
    def is_active(self, obj):
        """Display whether violation is active."""
        return obj.is_active()

    @admin.display(description="# Users")
    def user_count(self, obj):
        """Display number of users associated with this IP."""
        return len(obj.user_ids) if obj.user_ids else 0

    @admin.display(description="Time Span")
    def time_span(self, obj):
        """Display time span between first and last violation."""
        span = obj.last_violation_at - obj.first_violation_at
        return str(span)

    @admin.display(description="Status")
    def status(self, obj):
        """Display current status (BANNED or cooldown info)."""
        if obj.violation_count >= 4:
            return "BANNED"
        elif obj.is_in_cooldown():
            cooldown = obj.cooldown_until
            return f"Cooldown until {cooldown}" if cooldown else "Active"
        else:
            return "Active"


@admin.register(RateLimitAppeal)
class RateLimitAppealAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "violation_ip",
        "appealed_by",
        "status",
        "created_at",
        "reviewed_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["violation__ip_address", "explanation", "appealed_by__email"]
    readonly_fields = ["created_at", "violation", "appealed_by", "formatted_snapshot"]

    fieldsets = [
        (
            "Appeal Info",
            {"fields": ["violation", "appealed_by", "explanation", "formatted_snapshot", "created_at"]},
        ),
        ("Review", {"fields": ["status", "admin_notes", "reviewed_by", "reviewed_at"]}),
    ]

    @admin.display(description="IP Address")
    def violation_ip(self, obj):
        """Display IP address from related violation with link to violation record."""
        url = reverse("admin:app_ratelimitviolation_change", args=[obj.violation.pk])
        return format_html('<a href="{}">{}</a>', url, obj.violation.ip_address)

    @admin.display(description="Violation Snapshot")
    def formatted_snapshot(self, obj):
        """Display violation snapshot in readable format."""
        if not obj.violation_snapshot:
            return "-"

        snapshot = obj.violation_snapshot
        html = "<table style='border-collapse: collapse;'>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>IP Address:</th><td style='padding: 4px;'>{snapshot.get('ip_address', '-')}</td></tr>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>Endpoint:</th><td style='padding: 4px;'>{snapshot.get('endpoint', '-')}</td></tr>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>Violation Count:</th><td style='padding: 4px;'>{snapshot.get('violation_count', '-')}</td></tr>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>User IDs:</th><td style='padding: 4px;'>{snapshot.get('user_ids', [])}</td></tr>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>User Email:</th><td style='padding: 4px;'>{snapshot.get('user_email', '-')}</td></tr>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>First Violation:</th><td style='padding: 4px;'>{snapshot.get('first_violation_at', '-')}</td></tr>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>Last Violation:</th><td style='padding: 4px;'>{snapshot.get('last_violation_at', '-')}</td></tr>"
        html += "</table>"
        return format_html(html)

    actions = ["approve_appeal", "deny_appeal"]

    @admin.action(description="Approve selected appeals")
    def approve_appeal(self, request, queryset):
        """Approve appeals and unban by resetting violation records."""
        for appeal in queryset:
            appeal.status = RateLimitAppeal.APPROVED
            appeal.reviewed_by = request.user
            appeal.reviewed_at = timezone.now()
            appeal.save()

            # Unban: reset the violation record to clean state
            violation = appeal.violation
            violation.violation_count = 0
            violation.user_ids = []
            violation.save()

        self.message_user(request, f"{queryset.count()} appeals approved and violations cleared.")

    @admin.action(description="Deny selected appeals")
    def deny_appeal(self, request, queryset):
        """Deny selected appeals."""
        queryset.update(
            status=RateLimitAppeal.DENIED, reviewed_by=request.user, reviewed_at=timezone.now()
        )
        self.message_user(request, f"{queryset.count()} appeals denied.")
