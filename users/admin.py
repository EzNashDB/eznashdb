from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import reverse
from django.utils.html import format_html
from waffle.admin import FlagAdmin as WaffleFlagAdmin
from waffle.admin import SampleAdmin as WaffleSampleAdmin
from waffle.admin import SwitchAdmin as WaffleSwitchAdmin

from users.models import Flag, Sample, Switch, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""

    list_display = [
        "email",
        "full_name",
        "shuls_created_count",
        "shuls_updated_count",
        "shuls_deleted_count",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    ]
    list_filter = ["is_staff", "is_active", "date_joined"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-date_joined"]
    readonly_fields = ["created_shuls_links", "updated_shuls_links", "deleted_shuls_links"]

    # Add custom section to fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Shul Activity",
            {
                "fields": ("created_shuls_links", "updated_shuls_links", "deleted_shuls_links"),
            },
        ),
    )

    @admin.display(description="Name")
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    @admin.display(description="Created")
    def shuls_created_count(self, obj):
        return obj.created_shuls.count()

    @admin.display(description="Updated")
    def shuls_updated_count(self, obj):
        from eznashdb.models import Shul

        return Shul.objects.filter(updated_by__contains=[obj.id]).count()

    @admin.display(description="Deleted")
    def shuls_deleted_count(self, obj):
        return obj.deleted_shuls.count()

    @admin.display(description="Shuls Created")
    def created_shuls_links(self, obj):
        """Show links to shuls created by this user"""
        shuls = obj.created_shuls.order_by("-created_at")
        if not shuls:
            return "-"

        links = []
        for shul in shuls:
            url = reverse("admin:eznashdb_shul_change", args=[shul.pk])
            links.append(f'<a href="{url}">{shul.name}</a>')

        return format_html("<br>".join(links))

    @admin.display(description="Shuls Updated")
    def updated_shuls_links(self, obj):
        """Show links to shuls updated by this user"""
        from eznashdb.models import Shul

        shuls = Shul.objects.filter(updated_by__contains=[obj.id]).order_by("-updated_at")
        if not shuls:
            return "-"

        links = []
        for shul in shuls:
            url = reverse("admin:eznashdb_shul_change", args=[shul.pk])
            links.append(f'<a href="{url}">{shul.name}</a>')

        return format_html("<br>".join(links))

    @admin.display(description="Shuls Deleted")
    def deleted_shuls_links(self, obj):
        """Show links to shuls deleted by this user"""
        shuls = obj.deleted_shuls.order_by("-deleted")
        if not shuls:
            return "-"

        links = []
        for shul in shuls:
            url = reverse("admin:eznashdb_deletedshul_change", args=[shul.pk])
            links.append(f'<a href="{url}">{shul.name}</a>')

        return format_html("<br>".join(links))


@admin.register(Flag)
class FlagAdmin(WaffleFlagAdmin):
    filter_horizontal = tuple(list(WaffleFlagAdmin.filter_horizontal) + ["user_permissions"])


@admin.register(Switch)
class SwitchAdmin(WaffleSwitchAdmin):
    pass


@admin.register(Sample)
class SampleAdmin(WaffleSampleAdmin):
    pass
