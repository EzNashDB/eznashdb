"""Admin configuration for app infrastructure models."""

from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from app.abuse_config import PERMANENT_BAN_THRESHOLD
from app.models import AbuseAppeal, AbuseState


@admin.register(AbuseState)
class AbuseStateAdmin(admin.ModelAdmin):
    list_display = [
        "user_email",
        "points",
        "status",
        "last_violation_at",
        "episode_started_at",
        "sensitive_count_in_episode",
    ]
    list_filter = ["points"]
    search_fields = ["user__email"]
    readonly_fields = [
        "user",
        "episode_started_at",
        "last_violation_at",
        "last_points_update_at",
    ]
    ordering = ["-last_violation_at"]

    @admin.display(description="User Email")
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email

    @admin.display(description="Status")
    def status(self, obj):
        """Display current status."""
        if obj.is_permanently_banned:
            return "PERMANENTLY BANNED"
        elif obj.is_in_cooldown():
            return f"Cooldown until {obj.cooldown_until}"
        elif obj.points > 0:
            return f"Active ({obj.points} points)"
        else:
            return "Clean"

    actions = ["ban_user", "unban_user"]

    @admin.action(description="Permanently ban selected users")
    def ban_user(self, request, queryset):
        """Permanently ban users by setting points to threshold."""
        queryset.update(points=PERMANENT_BAN_THRESHOLD)
        self.message_user(request, f"{queryset.count()} users banned.")

    @admin.action(description="Unban selected users")
    def unban_user(self, request, queryset):
        """Unban users but keep them on thin ice (one more violation = banned)."""
        queryset.update(
            points=PERMANENT_BAN_THRESHOLD - 1,
            sensitive_count_in_episode=0,
            cooldown_until=None,
            last_points_update_at=timezone.now(),
        )
        self.message_user(
            request,
            f"{queryset.count()} users unbanned (set to {PERMANENT_BAN_THRESHOLD - 1} points).",
        )


@admin.register(AbuseAppeal)
class AbuseAppealAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user_email",
        "status",
        "created_at",
        "reviewed_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["abuse_state__user__email", "explanation"]
    readonly_fields = ["created_at", "abuse_state", "formatted_snapshot"]

    fieldsets = [
        (
            "Appeal Info",
            {
                "fields": [
                    "abuse_state",
                    "explanation",
                    "formatted_snapshot",
                    "created_at",
                ]
            },
        ),
        ("Review", {"fields": ["status", "admin_notes", "reviewed_by", "reviewed_at"]}),
    ]

    @admin.display(description="User Email")
    def user_email(self, obj):
        """Display user email from related abuse state with link."""
        url = reverse("admin:app_abusestate_change", args=[obj.abuse_state.pk])
        return format_html('<a href="{}">{}</a>', url, obj.abuse_state.user.email)

    @admin.display(description="State Snapshot")
    def formatted_snapshot(self, obj):
        """Display state snapshot in readable format."""
        if not obj.state_snapshot:
            return "-"

        snapshot = obj.state_snapshot
        html = "<table style='border-collapse: collapse;'>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>User Email:</th><td style='padding: 4px;'>{snapshot.get('user_email', '-')}</td></tr>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>Points:</th><td style='padding: 4px;'>{snapshot.get('points', '-')}</td></tr>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>Permanently Banned:</th><td style='padding: 4px;'>{snapshot.get('is_permanently_banned', snapshot.get('permanently_banned', '-'))}</td></tr>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>Episode Started:</th><td style='padding: 4px;'>{snapshot.get('episode_started_at', '-')}</td></tr>"
        html += f"<tr><th style='text-align: left; padding: 4px;'>Last Violation:</th><td style='padding: 4px;'>{snapshot.get('last_violation_at', '-')}</td></tr>"
        html += "</table>"
        return format_html(html)

    actions = ["approve_appeal", "deny_appeal"]

    @admin.action(description="Approve selected appeals")
    def approve_appeal(self, request, queryset):
        """Approve appeals and unban by resetting abuse states."""
        for appeal in queryset:
            appeal.status = AbuseAppeal.APPROVED
            appeal.reviewed_by = request.user
            appeal.reviewed_at = timezone.now()
            appeal.save()

            # Unban: reset the abuse state to clean state
            state = appeal.abuse_state
            state.points = PERMANENT_BAN_THRESHOLD - 1
            state.sensitive_count_in_episode = 0
            state.cooldown_until = None
            state.last_points_update_at = timezone.now()
            state.save()

        self.message_user(
            request,
            f"{queryset.count()} appeals approved (set to {PERMANENT_BAN_THRESHOLD - 1} points).",
        )

    @admin.action(description="Deny selected appeals")
    def deny_appeal(self, request, queryset):
        """Deny selected appeals and ensure user is banned."""
        for appeal in queryset:
            appeal.status = AbuseAppeal.DENIED
            appeal.reviewed_by = request.user
            appeal.reviewed_at = timezone.now()
            appeal.save()

            # Ensure user is banned
            state = appeal.abuse_state
            state.points = PERMANENT_BAN_THRESHOLD
            state.save(update_fields=["points"])

        self.message_user(request, f"{queryset.count()} appeals denied (users banned).")
