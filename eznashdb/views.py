from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DeleteView, TemplateView
from django_filters.views import FilterView

from eznashdb.filtersets import ShulFilterSet
from eznashdb.models import Shul


class ShulsFilterView(FilterView):
    template_name = "eznashdb/shuls.html"
    filterset_class = ShulFilterSet


class CreateUpdateShulView(TemplateView):
    template_name = "eznashdb/create_update_shul.html"


class DeleteShulView(DeleteView):
    model = Shul

    def get_success_url(self) -> str:
        return reverse("eznashdb:shuls")

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.delete_shul()
        return HttpResponseRedirect(success_url)

    @transaction.atomic()
    def delete_shul(self):
        self.object.rooms.all().delete()
        self.object.delete()
