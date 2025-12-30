from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class AccountSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "account/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get email verification status
        email_address = self.request.user.emailaddress_set.first()
        context["email_verified"] = email_address.verified if email_address else False
        return context
