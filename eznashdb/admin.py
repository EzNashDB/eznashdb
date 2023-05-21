from django.apps import apps
from django.contrib import admin

eznashdb_models = apps.get_app_config("eznashdb").models


for _model_name, model in eznashdb_models.items():
    admin.site.register(model)
