from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from tinymce.widgets import TinyMCE

from eznashdb.models import Shul


# Custom admin for Shul — only affects list page
class ShulAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "created_at", "updated_at")


# Register Shul with custom admin
admin.site.register(Shul, ShulAdmin)

# Dynamically register all other models
eznashdb_models = apps.get_app_config("eznashdb").models
for _model_name, model in eznashdb_models.items():
    if model is not Shul:  # skip Shul since we already registered it
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
