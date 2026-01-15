from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.urls import reverse
from django.utils.html import format_html
from safedelete.models import HARD_DELETE
from tinymce.widgets import TinyMCE

from eznashdb.models import DeletedShul, Room, Shul


# Base admin with shared methods for Shul and DeletedShul
class BaseShulAdmin(admin.ModelAdmin):
    """Base class with common display methods for Shul admins"""

    class Meta:
        abstract = True

    @admin.display(description="Address", ordering="address")
    def short_address(self, obj):
        """Truncate long addresses but show full address on hover"""
        if obj.address:
            max_length = 40
            if len(obj.address) > max_length:
                truncated = obj.address[:max_length] + "..."
                return format_html('<span title="{}">{}</span>', obj.address, truncated)
            return obj.address
        return "-"

    @admin.display(description="Map")
    def view_on_map(self, obj):
        """Generate a link to view the shul on the map"""
        if obj.pk:
            return format_html('<a href="{}" target="_blank">View on Map</a>', obj.get_map_url())
        return "-"

    @admin.display(description="Rooms", ordering="rooms__count")
    def room_count(self, obj):
        """Display the number of rooms for this shul"""
        return obj.rooms.count()

    @admin.display(description="Room Links")
    def rooms_links(self, obj):
        """Show links to related Room admin pages"""
        rooms = obj.rooms.all()
        if not rooms:
            return "-"

        links = []
        for room in rooms:
            url = reverse("admin:eznashdb_room_change", args=[room.pk])
            links.append(f'<a href="{url}">{room.name}</a>')

        return format_html("<br>".join(links))


@admin.register(Shul)
class ShulAdmin(BaseShulAdmin):
    list_display = (
        "name",
        "short_address",
        "view_on_map",
        "room_count",
        "rooms_links",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")

    def get_queryset(self, request):
        from django.db.models import Count

        qs = Shul.objects.annotate(rooms__count=Count("rooms")).prefetch_related("rooms")
        return qs


@admin.register(DeletedShul)
class DeletedShulAdmin(BaseShulAdmin):
    """Admin interface specifically for soft-deleted shuls"""

    list_display = (
        "name",
        "short_address",
        "room_count",
        "rooms_links",
        "deleted_by_link",
        "short_deletion_reason",
        "deleted_at",
    )
    list_filter = ("deleted_by", "deleted")
    list_select_related = ("deleted_by",)
    search_fields = ("name", "address", "city")
    readonly_fields = ("deleted_by", "deletion_reason", "deleted")
    actions = ["undelete_shuls", "destroy_shuls"]

    def get_actions(self, request):
        """Remove the default delete action since shuls are already deleted"""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_queryset(self, request):
        """Use the default manager which only shows deleted shuls"""
        from django.db.models import Count

        # The DeletedShul proxy model uses SafeDeleteDeletedManager,
        # so we just need to call the parent get_queryset and add optimizations
        qs = super().get_queryset(request)
        qs = qs.annotate(rooms__count=Count("rooms")).prefetch_related("rooms")
        return qs

    @admin.display(description="Deleted By", ordering="deleted_by__username")
    def deleted_by_link(self, obj):
        """Link to the user who deleted this shul"""
        if not obj.deleted_by:
            return "-"
        url = reverse("admin:users_user_change", args=[obj.deleted_by.pk])
        return format_html('<a href="{}">{}</a>', url, obj.deleted_by)

    @admin.display(description="Deletion Reason", ordering="deletion_reason")
    def short_deletion_reason(self, obj):
        """Show truncated deletion reason"""
        if obj.deletion_reason:
            max_length = 50
            if len(obj.deletion_reason) > max_length:
                truncated = obj.deletion_reason[:max_length] + "..."
                return format_html('<span title="{}">{}</span>', obj.deletion_reason, truncated)
            return obj.deletion_reason
        return "-"

    @admin.display(description="Deleted At", ordering="deleted")
    def deleted_at(self, obj):
        """Show when the shul was deleted"""
        if obj.deleted:
            return obj.deleted
        return "-"

    @admin.action(description="Undelete selected shuls")
    def undelete_shuls(self, request, queryset):
        """Undelete selected shuls and clear deletion audit fields"""
        count = queryset.count()

        if count == 0:
            self.message_user(request, "No deleted shuls selected.", level="warning")
            return

        # Undelete using safedelete's undelete method
        queryset.undelete()

        # Clear deletion audit fields for each shul
        for shul in queryset:
            shul.clear_deletion()

        self.message_user(
            request, f"Successfully undeleted {count} shul{'s' if count != 1 else ''}.", level="success"
        )

    @admin.action(description="⚠️ DESTROY selected shuls (PERMANENT)")
    def destroy_shuls(self, request, queryset):
        """Permanently hard delete soft-deleted shuls - THIS CANNOT BE UNDONE"""
        count = queryset.count()

        if count == 0:
            self.message_user(request, "No deleted shuls selected.", level="warning")
            return

        # Hard delete using safedelete's HARD_DELETE policy
        deleted_count, _ = queryset.delete(force_policy=HARD_DELETE)

        self.message_user(
            request,
            f"PERMANENTLY DESTROYED {deleted_count} shul{'s' if deleted_count != 1 else ''}. This action cannot be undone.",
            level="warning",
        )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "shul_link", "created_at", "updated_at")
    list_select_related = ("shul",)

    @admin.display(description="Shul", ordering="shul__name")
    def shul_link(self, obj):
        """Link to the related Shul admin page"""
        if not obj.shul_id:
            return "-"
        url = reverse("admin:eznashdb_shul_change", args=[obj.shul_id])
        return format_html('<a href="{}">{}</a>', url, obj.shul.name)


# Dynamically register all other models
eznashdb_models = apps.get_app_config("eznashdb").models
for _model_name, model in eznashdb_models.items():
    if model not in [Shul, Room, DeletedShul]:  # skip models we already registered
        admin.site.register(model)


class FlatPageForm(forms.ModelForm):
    content = forms.CharField(widget=TinyMCE())

    class Meta:
        model = FlatPage
        fields = ["url", "title", "content", "sites", "registration_required", "template_name"]


admin.site.unregister(FlatPage)


@admin.register(FlatPage)
class CustomFlatPageAdmin(FlatPageAdmin):
    form = FlatPageForm
