from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class AccountSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "account/settings.html"
