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
    list_display = ("name", "short_address", "view_on_map", "room_count", "created_at", "updated_at")

    def view_on_map(self, obj):
        """Generate a link to view the shul on the map"""
        if obj.pk:
            lat = obj.display_lat
            lon = obj.display_lon
            url = reverse("eznashdb:shuls")
            url += f"?lat={lat}&lon={lon}&selectedShul={obj.pk}"
            if lat and lon:
                url += "&zoom=17"
            return format_html('<a href="{}" target="_blank">View on Map</a>', url)
        return "-"

    view_on_map.short_description = "Map"

    def room_count(self, obj):
        """Display the number of rooms for this shul"""
        return obj.rooms.count()

    room_count.short_description = "Rooms"
    room_count.admin_order_field = "rooms__count"

    def get_queryset(self, request):
        """Optimize queryset with annotation for sorting"""
        from django.db.models import Count

        qs = super().get_queryset(request)
        return qs.annotate(rooms__count=Count("rooms"))

    def short_address(self, obj):
        """Truncate long addresses but show full address on hover"""
        if obj.address:
            max_length = 40
            if len(obj.address) > max_length:
                truncated = obj.address[:max_length] + "..."
                return format_html('<span title="{}">{}</span>', obj.address, truncated)
            return obj.address
        return "-"

    short_address.short_description = "Address"
    short_address.admin_order_field = "address"


# Register Shul with custom admin
admin.site.register(Shul, ShulAdmin)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "shul_link", "created_at", "updated_at")
    list_select_related = ("shul",)

    def shul_link(self, obj):
        """Link to the related Shul admin page"""
        if not obj.shul_id:
            return "-"
        url = reverse("admin:eznashdb_shul_change", args=[obj.shul_id])
        return format_html('<a href="{}">{}</a>', url, obj.shul.name)

    shul_link.short_description = "Shul"
    shul_link.admin_order_field = "shul__name"


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
