from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView
from django_filters.views import FilterView

from eznashdb.filtersets import ShulFilterSet
from eznashdb.forms import CreateShulForm
from eznashdb.models import Shul


class ShulsFilterView(FilterView):
    template_name = "eznashdb/shuls.html"
    filterset_class = ShulFilterSet


class CreateShulView(CreateView):
    form_class = CreateShulForm
    template_name = "eznashdb/create_shul.html"
    success_url = reverse_lazy("eznashdb:shuls")


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
