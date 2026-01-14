from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.urls import reverse
from django.utils.html import format_html
from tinymce.widgets import TinyMCE

from eznashdb.models import Room, Shul


# Custom admin for Shul — only affects list page
class ShulAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "short_address",
        "view_on_map",
        "room_count",
        "rooms_links",
        "created_at",
        "updated_at",
    )

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

    def get_queryset(self, request):
        from django.db.models import Count

        qs = super().get_queryset(request)
        return qs.annotate(rooms__count=Count("rooms")).prefetch_related("rooms")

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


# Register Shul with custom admin
admin.site.register(Shul, ShulAdmin)


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
    if model not in [Shul, Room]:  # skip Shul since we already registered it
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
