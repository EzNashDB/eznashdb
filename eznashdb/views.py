import urllib
from typing import Any

import requests
from django.core import serializers
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView
from django_filters.views import FilterView

from eznashdb.constants import BASE_OSM_URL
from eznashdb.filtersets import ShulFilterSet
from eznashdb.forms import CreateShulForm, RoomFormSet
from eznashdb.models import Shul


class ShulsFilterView(FilterView):
    template_name = "eznashdb/shuls.html"
    filterset_class = ShulFilterSet


class ShulsMapFilterView(FilterView):
    template_name = "eznashdb/shuls_map.html"
    filterset_class = ShulFilterSet

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["serialized_shuls"] = serializers.serialize("json", context["filter"].qs)
        return context


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


class AddressLookupView(View):
    def replace_substring_if_bounded(self, input_str, substring_a, substring_b):
        words = input_str.split()
        # Initialize an empty result string
        result = ""

        # Iterate through the words
        for i, word in enumerate(words):
            if substring_a in word:
                # Check if the current word contains substring_a
                parts = word.split(substring_a)

                # Check if the substring_a appears at the start or end of the word
                is_start = parts[0] == "" or parts[0][-1] in (",", " ")
                is_end = parts[-1] == "" or parts[-1][0] in (",", " ")

                if is_start and is_end:
                    # Replace substring_a with substring_b
                    result += parts[0] + substring_b + parts[1]
                else:
                    result += word
            else:
                result += word

            # Add a space between words
            if i < len(words) - 1:
                result += " "

        return result

    def get_OSM_response(self, q):
        OSM_param_dict = {
            "format": "json",
            "addressdetails": 1,
            "namedetails": 1,
            "q": q,
        }
        OSM_params = urllib.parse.urlencode(OSM_param_dict)
        OSM_url = BASE_OSM_URL + "?" + OSM_params
        response = requests.get(OSM_url)
        if type(response.json()) != list:
            response.status_code = 500
        return response

    def get(self, request):
        query = request.GET.get("q", "").lower()
        OSM_response = self.get_OSM_response(query)
        if OSM_response.status_code != 200:
            return JsonResponse({"error": "Failed to retrieve city data"}, status=500)
        results = OSM_response.json().copy()

        modified_query = query
        for israel, palestine in [
            ("il", "ps"),
            ("israel", "palestinian territory"),
            ("ישראל", "palestinian territory"),
        ]:
            if israel in query:
                modified_query = self.replace_substring_if_bounded(modified_query, israel, palestine)
        if modified_query != query:
            response_2 = self.get_OSM_response(modified_query)
            results.extend(response_2.json().copy())
        if OSM_response.status_code == 200:
            return JsonResponse(self.format_results(results), safe=False)

    def format_results(self, results):
        for result in results:
            result["id"] = result["place_id"]
        return results
