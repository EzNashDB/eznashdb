import time
import urllib
from decimal import Decimal
from json.decoder import JSONDecodeError

import requests
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, TemplateView, UpdateView
from django_filters.views import FilterView
from django_htmx.http import HttpResponseClientRedirect

from eznashdb.filtersets import ShulFilterSet
from eznashdb.forms import RoomFormSet, ShulForm
from eznashdb.models import Shul


class ShulsFilterView(FilterView):
    template_name = "eznashdb/shuls.html"
    filterset_class = ShulFilterSet

    def get_template_names(self) -> list[str]:
        if self.request.htmx:
            return ["eznashdb/shuls.html#shul_markers_js"]
        return super().get_template_names()


class CreateUpdateShulView(UpdateView):
    model = Shul
    form_class = ShulForm
    template_name = "eznashdb/create_update_shul.html"

    def get_success_url(self) -> str:
        if self.is_update:
            url = reverse_lazy("eznashdb:shuls")
            lat = self.object.latitude
            lon = self.object.longitude
            url += f"?lat={lat}&lon={lon}&selectedPin={self.object.pk}"
            if lat and lon:
                url += "&zoom=17"
            return url
        else:
            return reverse_lazy("eznashdb:update_shul", kwargs={"pk": self.object.pk})

    def get_object(self, queryset=None):
        try:
            return super().get_object()
        except AttributeError:
            return None

    @property
    def is_update(self):
        return self.get_object() is not None

    def form_invalid(self, form):
        return TemplateResponse(
            self.request,
            "eznashdb/create_update_shul.html#shul_form",
            self.get_context_data(form=form),
        )

    def form_valid(self, form):
        if self.is_update:
            room_fs = self.get_room_fs()
            if not room_fs.is_valid():
                return self.render_to_response(self.get_context_data(form=form))
        submit_type = self.request.POST.get("submit_type")
        if submit_type == "main_submit":
            nearby_shuls = self.check_nearby_shuls(form)
            if nearby_shuls.exists():
                partial_template = "eznashdb/create_update_shul.html#shul_form"
                context = {"nearby_shuls": nearby_shuls, **self.get_context_data(form=form)}
                return TemplateResponse(self.request, partial_template, context)
        self.object = form.save()
        if self.is_update:
            self.room_fs_valid(room_fs)
        success_url = self.get_success_url()
        if not self.is_update:
            success_url += "?from=create_new_shul"
        else:
            if self.request.POST.get("from") == "create_new_shul":
                messages.success(self.request, "Success! Your shul has been added to the map.")
                success_url += f"&newShul={self.object.pk}"
            else:
                messages.success(self.request, "Success! Your shul has been updated.")
                success_url += f"&updatedShul={self.object.pk}"
        return HttpResponseClientRedirect(success_url)

    def check_nearby_shuls(self, form):
        lat = form.cleaned_data.get("latitude")
        lon = form.cleaned_data.get("longitude")

        if lat is None or lon is None:
            return Shul.objects.none()

        # Define the search box (±0.001 degrees)
        lat_delta = Decimal("0.001")
        lon_delta = Decimal("0.001")

        return Shul.objects.filter(
            latitude__gte=lat - lat_delta,
            latitude__lte=lat + lat_delta,
            longitude__gte=lon - lon_delta,
            longitude__lte=lon + lon_delta,
        ).exclude(pk=self.object.pk if self.object else None)

    def room_fs_valid(self, room_fs):
        rooms = room_fs.save(commit=False)
        for obj in room_fs.deleted_objects:
            obj.delete()
        for room in rooms:
            room.shul = self.object
            room.save()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["room_fs"] = self.get_room_fs()
        return context

    def get_room_fs(self):
        return self.get_formset(RoomFormSet, "rooms")

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


class ContactUsView(TemplateView):
    template_name = "eznashdb/contact_us.html"
