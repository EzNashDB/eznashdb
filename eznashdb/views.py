from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView
from django_filters.views import FilterView

from eznashdb.filtersets import ShulFilterSet
from eznashdb.forms import CreateShulForm, RoomFormSet
from eznashdb.models import Shul


class ShulsFilterView(FilterView):
    template_name = "eznashdb/shuls.html"
    filterset_class = ShulFilterSet


class CreateShulView(CreateView):
    form_class = CreateShulForm
    template_name = "eznashdb/create_shul.html"
    success_url = reverse_lazy("eznashdb:shuls")

    def form_valid(self, form):
        room_fs = self.get_room_formset()
        if not room_fs.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        self.object = form.save()
        self.room_fs_valid(room_fs)

        return HttpResponseRedirect(self.get_success_url())

    def room_fs_valid(self, room_fs):
        rooms = room_fs.save(commit=False)
        for obj in room_fs.deleted_objects:
            obj.delete()
        for room in rooms:
            room.shul = self.object
            room.save()

    def get_context_data(self, **kwargs):
        context = super(CreateShulView, self).get_context_data(**kwargs)
        context["room_fs"] = self.get_room_formset()
        return context

    def get_room_formset(self):
        if self.request.method == "GET":
            return RoomFormSet(prefix="rooms")
        else:
            return RoomFormSet(self.request.POST or None, self.request.FILES or None, prefix="rooms")


class DeleteShulView(DeleteView):
    model = Shul
    success_url = reverse_lazy("eznashdb:shuls")

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.delete_shul()
        return HttpResponseRedirect(success_url)

    @transaction.atomic()
    def delete_shul(self):
        self.object.rooms.all().delete()
        self.object.delete()
