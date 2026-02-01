from calendar import monthrange
from datetime import date

from django.conf import settings
from django.contrib import admin
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from app.abuse_config import PERMANENT_BAN_THRESHOLD
from app.models import AbuseAppeal, AbuseState, GooglePlacesUsage, GooglePlacesUserUsage


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


@admin.register(GooglePlacesUsage)
class GooglePlacesUsageAdmin(admin.ModelAdmin):
    list_display = [
        "date",
        "autocomplete_requests",
        "details_requests",
        "total_requests",
        "estimated_cost",
        "budget_status",
    ]
    ordering = ["-date"]
    date_hierarchy = "date"

    def has_add_permission(self, request):
        """Prevent manual creation - usage is tracked automatically."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing - usage is tracked automatically."""
        return False

    @admin.display(description="Total Requests")
    def total_requests(self, obj):
        """Display total requests (autocomplete + details)."""
        return obj.autocomplete_requests + obj.details_requests

    @admin.display(description="Estimated Cost")
    def estimated_cost(self, obj):
        """Estimate cost based on current usage."""
        autocomplete_cost = obj.autocomplete_requests * 0.00283
        details_cost = obj.details_requests * 0.005
        total = autocomplete_cost + details_cost
        return f"${total:.2f}"

    @admin.display(description="Daily Budget Status")
    def budget_status(self, obj):
        """Display remaining daily budget for this day."""
        # Calculate daily budgets for this date based on previous usage
        budget = GooglePlacesUsage.get_daily_budget(obj.date)

        # Check if there's rollover (daily budget higher than base rate)
        _, days_in_month = monthrange(obj.date.year, obj.date.month)
        base_daily_budget = GooglePlacesUsage.MONTHLY_AUTOCOMPLETE_LIMIT // days_in_month
        has_rollover = budget.autocomplete > base_daily_budget

        # Calculate usage percentage (use autocomplete as the limiting factor)
        if budget.autocomplete > 0:
            percent_used = (obj.autocomplete_requests / budget.autocomplete) * 100
        else:
            percent_used = 100

        if percent_used < 50:
            color = "green"
            status = "Good"
        elif percent_used < 90:
            color = "orange"
            status = "Warning"
        else:
            color = "red"
            status = "Critical"

        rollover_text = " (rollover)" if has_rollover else ""

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{} ({}%)</span><br>'
            "<small>Budget: {}/{} autocomplete, {}/{} details</small>",
            color,
            status,
            rollover_text,
            int(percent_used),
            obj.autocomplete_requests,
            budget.autocomplete,
            obj.details_requests,
            budget.details,
        )

    def changelist_view(self, request, extra_context=None):
        """Add monthly summary to changelist."""
        extra_context = extra_context or {}

        # Get current month's usage
        today = date.today()
        first_day = date(today.year, today.month, 1)

        monthly_usage = GooglePlacesUsage.objects.filter(date__gte=first_day).aggregate(
            total_autocomplete=Sum("autocomplete_requests"),
            total_details=Sum("details_requests"),
        )

        total_autocomplete = monthly_usage["total_autocomplete"] or 0
        total_details = monthly_usage["total_details"] or 0

        # Calculate costs
        autocomplete_cost = total_autocomplete * 0.00283
        details_cost = total_details * 0.005
        total_cost = autocomplete_cost + details_cost

        # Get today's budget and usage
        budget = GooglePlacesUsage.get_daily_budget(today)
        today_usage = GooglePlacesUsage.get_usage_for_date(today)

        extra_context["monthly_summary"] = {
            "autocomplete_requests": total_autocomplete,
            "autocomplete_limit": GooglePlacesUsage.MONTHLY_AUTOCOMPLETE_LIMIT,
            "details_requests": total_details,
            "details_limit": GooglePlacesUsage.MONTHLY_DETAILS_LIMIT,
            "total_cost": total_cost,
            "today_autocomplete": today_usage.autocomplete,
            "today_autocomplete_budget": budget.autocomplete,
            "today_details": today_usage.details,
            "today_details_budget": budget.details,
        }

        return super().changelist_view(request, extra_context)


@admin.register(GooglePlacesUserUsage)
class GooglePlacesUserUsageAdmin(admin.ModelAdmin):
    list_display = [
        "user_email",
        "date",
        "autocomplete_requests",
        "percent_of_limit",
    ]
    list_filter = ["date"]
    search_fields = ["user__email"]
    ordering = ["-date", "-autocomplete_requests"]
    date_hierarchy = "date"

    def has_add_permission(self, request):
        """Prevent manual creation - usage is tracked automatically."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing - usage is tracked automatically."""
        return False

    @admin.display(description="User Email")
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email

    @admin.display(description="% of Daily Limit")
    def percent_of_limit(self, obj):
        """Show percentage of user's daily limit."""
        limit = settings.GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT
        percent = (obj.autocomplete_requests / limit * 100) if limit > 0 else 0

        if percent < 50:
            color = "green"
        elif percent < 90:
            color = "orange"
        else:
            color = "red"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color,
            f"{percent:.1f}",
        )
