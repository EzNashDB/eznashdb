import json
import time
import urllib
from json.decoder import JSONDecodeError
from typing import Any

import requests
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, UpdateView
from django_filters.views import FilterView

from eznashdb.constants import FieldsOptions
from eznashdb.filtersets import ShulFilterSet
from eznashdb.forms import ChildcareProgramFormSet, RoomFormSet, ShulForm, ShulLinkFormSet
from eznashdb.models import Shul
from eznashdb.serializers import ShulSerializer


class ShulsFilterView(FilterView):
    template_name = "eznashdb/shuls.html"
    filterset_class = ShulFilterSet

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["serialized_shuls"] = self.get_serialized_shuls(context["filter"].qs)
        return context

    def get_serialized_shuls(self, qs):
        serialized_shuls = ShulSerializer(qs, many=True).data
        json_shuls = json.dumps(serialized_shuls)
        return json_shuls

    def get_template_names(self) -> list[str]:
        if "Hx-Request" in self.request.headers:
            return ["eznashdb/includes/shuls_js_loader.html"]
        return super().get_template_names()


class CreateUpdateShulView(UpdateView):
    model = Shul
    form_class = ShulForm
    template_name = "eznashdb/create_update_shul.html"

    def get_success_url(self) -> str:
        url = reverse_lazy("eznashdb:shuls")
        lat = self.object.latitude
        lon = self.object.longitude
        url += f"?lat={lat}&lon={lon}&selectedPin={self.object.pk}"
        if lat and lon:
            url += "&zoom=17"
        return url

    def get_object(self, queryset=None):
        try:
            return super().get_object()
        except AttributeError:
            return None

    @property
    def is_update(self):
        return self.get_object() is not None

    def form_valid(self, form):
        room_fs = self.get_room_fs()
        link_fs = self.get_link_fs()
        childcare_fs = self.get_childcare_fs()
        if not room_fs.is_valid() or not link_fs.is_valid() or not childcare_fs.is_valid():
            return self.render_to_response(self.get_context_data(form=form))
        self.object = form.save()
        self.link_fs_valid(link_fs)
        self.childcare_fs_valid(childcare_fs)
        self.room_fs_valid(room_fs)

        return HttpResponseRedirect(self.get_success_url())

    def room_fs_valid(self, room_fs):
        rooms = room_fs.save(commit=False)
        for obj in room_fs.deleted_objects:
            obj.delete()
        for room in rooms:
            room.shul = self.object
            room.save()

    def link_fs_valid(self, link_fs):
        links = link_fs.save(commit=False)
        for obj in link_fs.deleted_objects:
            obj.delete()
        for link in links:
            link.shul = self.object
            link.save()

    def childcare_fs_valid(self, childcare_fs):
        childcare_programs = childcare_fs.save(commit=False)
        for obj in childcare_fs.deleted_objects:
            obj.delete()
        for childcare in childcare_programs:
            childcare.shul = self.object
            childcare.save()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["room_fs"] = self.get_room_fs()
        context["link_fs"] = self.get_link_fs()
        context["childcare_fs"] = self.get_childcare_fs()
        context["FIELDS_OPTIONS"] = FieldsOptions
        return context

    def get_room_fs(self):
        return self.get_formset(RoomFormSet, "rooms")

    def get_link_fs(self):
        return self.get_formset(ShulLinkFormSet, "shul-links")

    def get_childcare_fs(self):
        return self.get_formset(ChildcareProgramFormSet, "childcare-programs")

    def get_formset(self, formset_class, prefix):
        if self.request.method == "GET":
            return formset_class(prefix=prefix, instance=self.object)
        else:
            return formset_class(
                self.request.POST or None,
                self.request.FILES or None,
                prefix=prefix,
                instance=self.object,
            )


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
    def get_OSM_response(self, q):
        OSM_param_dict = {
            "format": "json",
            "addressdetails": 1,
            "namedetails": 1,
            "q": q,
            "api_key": settings.MAPS_CO_API_KEY,
        }
        OSM_params = urllib.parse.urlencode(OSM_param_dict)
        OSM_url = settings.BASE_OSM_URL + "?" + OSM_params
        response = requests.get(OSM_url)
        try:
            if type(response.json()) is not list:
                response.status_code = 500
        except JSONDecodeError:
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
                modified_query = modified_query.replace(israel, palestine)
        if modified_query != query:
            # Sleep to avoid too many requests error
            time.sleep(1)
            response_2 = self.get_OSM_response(modified_query)
            # Leave JSONDecodeError unhandled at this point. Users will get results from first query
            # and errors will get logged
            results.extend(response_2.json().copy())
        if OSM_response.status_code == 200:
            return JsonResponse(self.format_results(results), safe=False)

    def format_results(self, results):
        israel_palestine_pairs = [
            ("ישראל", "الأراضي الفلسطينية"),
            ("Israel", "Palestinian Territory"),
        ]

        for result in results:
            result["id"] = result.get("place_id")
            for israel, palestine in israel_palestine_pairs:
                result["display_name"] = result.get("display_name", "").replace(palestine, israel)
        return results
