from django.apps import apps
from django.contrib import admin

from .models import Shul  # explicitly import Shul for customization


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
