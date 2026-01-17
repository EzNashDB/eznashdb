from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
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


@admin.register(Flag)
class FlagAdmin(WaffleFlagAdmin):
    filter_horizontal = tuple(list(WaffleFlagAdmin.filter_horizontal) + ["user_permissions"])


@admin.register(Switch)
class SwitchAdmin(WaffleSwitchAdmin):
    pass


@admin.register(Sample)
class SampleAdmin(WaffleSampleAdmin):
    pass
