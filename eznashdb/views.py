from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DeleteView, TemplateView

from eznashdb.models import Shul


class HomeView(TemplateView):
    template_name = "eznashdb/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["shuls"] = Shul.objects.all()
        return context


class CreateUpdateShulView(TemplateView):
    template_name = "eznashdb/create_update_shul.html"


class DeleteShulView(DeleteView):
    model = Shul

    def get_success_url(self) -> str:
        return reverse("eznashdb:home")

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.delete_shul()
        return HttpResponseRedirect(success_url)

    @transaction.atomic()
    def delete_shul(self):
        self.object.rooms.all().delete()
        self.object.delete()
