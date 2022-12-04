from django.views.generic import TemplateView
from eznashdb.models import Shul

class HomeView(TemplateView):
    template_name = "eznashdb/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["shuls"] = Shul.objects.all()
        return context

class CreateUpdateShulView(TemplateView):
    template_name = "eznashdb/create_update_shul.html"