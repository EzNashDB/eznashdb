import time
import urllib
from collections import defaultdict
from decimal import Decimal
from json.decoder import JSONDecodeError

import requests
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Group shuls by their display coordinates
        grid_groups = defaultdict(list)
        for shul in context["object_list"]:
            grid_key = f"{shul.display_lat}_{shul.display_lon}"
            grid_groups[grid_key].append(shul)

        context["cluster_groups"] = dict(grid_groups)

        return context

    def get_template_names(self) -> list[str]:
        if self.request.htmx:
            return ["eznashdb/shuls.html#shul_markers_js"]
        return super().get_template_names()


class CreateUpdateShulView(UpdateView):
    model = Shul
    form_class = ShulForm
    template_name = "eznashdb/create_update_shul.html"

    def get_success_url(self) -> str:
        url = reverse_lazy("eznashdb:shuls")
        lat = self.object.display_lat
        lon = self.object.display_lon
        url += f"?lat={lat}&lon={lon}&selectedShul={self.object.pk}"
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

    def form_invalid(self, form):
        return TemplateResponse(
            self.request,
            "eznashdb/create_update_shul.html#shul_form",
            self.get_context_data(form=form),
        )

    def form_valid(self, form):
        # UPDATE MODE: existing logic unchanged
        if self.is_update:
            room_fs = self.get_room_fs()
            if not room_fs.is_valid():
                return self.render_to_response(self.get_context_data(form=form))

            check_nearby_shuls = self.request.POST.get("check_nearby_shuls") == "true"

            if check_nearby_shuls:
                nearby_shuls = self.check_nearby_shuls(form)
                if nearby_shuls.exists():
                    partial_template = "eznashdb/create_update_shul.html#shul_form"
                    context = {"nearby_shuls": nearby_shuls, **self.get_context_data(form=form)}
                    return TemplateResponse(self.request, partial_template, context)

            self.object = form.save()
            self.room_fs_valid(room_fs)

            success_url = self.get_success_url()
            messages.success(self.request, "Success! Your shul has been updated.")
            success_url += f"&updatedShul={self.object.pk}"
            return HttpResponseClientRedirect(success_url)

        # CREATE MODE: wizard logic
        else:
            wizard_step = self.request.POST.get("wizard_step", "step1")
            if wizard_step == "step1":
                return self.handle_step1_submit(form)
            elif wizard_step == "step2":
                return self.handle_step2_submit(form)

    def handle_step1_submit(self, form):
        """Handle step 1 submission - validate and check nearby shuls"""
        check_nearby_shuls = self.request.POST.get("check_nearby_shuls") == "true"

        # Check for nearby shuls if requested
        if check_nearby_shuls:
            nearby_shuls = self.check_nearby_shuls(form)
            if nearby_shuls.exists():
                partial_template = "eznashdb/create_update_shul.html#shul_form"
                context = self.get_context_data(form=form)
                context["nearby_shuls"] = nearby_shuls
                context["wizard_step"] = "step1"  # Stay on step 1 to show modal
                return TemplateResponse(self.request, partial_template, context)

        # No nearby shuls or user clicked "Save Anyway" -> proceed to step 2
        partial_template = "eznashdb/create_update_shul.html#shul_form"
        context = self.get_context_data(form=form)
        context["wizard_step"] = "step2"  # Override to step 2
        return TemplateResponse(self.request, partial_template, context)

    def handle_step2_submit(self, form):
        """Handle step 2 submission - save shul and rooms together"""
        # Validate room formset
        room_fs = self.get_room_fs()
        if not room_fs.is_valid():
            context = self.get_context_data(form=form)
            context["wizard_step"] = "step2"  # Stay on step 2 for validation errors
            return TemplateResponse(
                self.request,
                "eznashdb/create_update_shul.html#shul_form",
                context,
            )

        # Check for nearby shuls if requested in step 2
        check_nearby_shuls = self.request.POST.get("check_nearby_shuls") == "true"

        if check_nearby_shuls:
            nearby_shuls = self.check_nearby_shuls(form)
            if nearby_shuls.exists():
                partial_template = "eznashdb/create_update_shul.html#shul_form"
                context = self.get_context_data(form=form)
                context["nearby_shuls"] = nearby_shuls
                context["wizard_step"] = "step2"
                return TemplateResponse(self.request, partial_template, context)

        # Save shul and rooms in transaction
        with transaction.atomic():
            self.object = form.save()  # Use the validated form from POST
            self.room_fs_valid(room_fs)

        # Success!
        success_url = self.get_success_url()
        messages.success(self.request, "Success! Your shul has been added to the map.")
        success_url += f"&newShul={self.object.pk}"
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

        # For create mode, determine current wizard step
        if not self.is_update and self.request.method == "POST":
            wizard_step = self.request.POST.get("wizard_step", "step1")
            context["wizard_step"] = wizard_step

        context["room_fs"] = self.get_room_fs()
        return context

    def get_room_fs(self):
        return self.get_formset(RoomFormSet, "rooms")

    def get_formset(self, formset_class, prefix):
        if self.request.method == "GET":
            return formset_class(prefix=prefix, instance=self.object)
        else:
            wizard_step = self.request.POST.get("wizard_step")

            # UPDATE MODE: always bind with POST data
            if self.is_update:
                return formset_class(
                    self.request.POST or None,
                    self.request.FILES or None,
                    prefix=prefix,
                    instance=self.object,
                )

            # CREATE MODE - STEP 2: bind with POST data for validation
            elif wizard_step == "step2":
                # Create temporary shul instance from POST data for formset validation
                temp_form = ShulForm(self.request.POST)
                temp_instance = None
                if temp_form.is_valid():
                    temp_instance = Shul(**temp_form.cleaned_data)
                return formset_class(
                    self.request.POST or None,
                    self.request.FILES or None,
                    prefix=prefix,
                    instance=temp_instance,
                )

            # CREATE MODE - STEP 1: return unbound formset (no validation)
            else:
                return formset_class(prefix=prefix, instance=None)


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


class GoogleMapsProxyView(View):
    def get(self, request, *args, **kwargs):
        shul_id = request.GET.get("id")
        if not shul_id:
            return HttpResponseBadRequest("Missing 'id' parameter.")

        shul = get_object_or_404(Shul, pk=shul_id)

        lat = round(float(shul.latitude), 5)
        lon = round(float(shul.longitude), 5)

        maps_url = f"https://www.google.com/maps/place/{lat},{lon}/@{lat},{lon},17z"

        context = {"maps_url": maps_url, "shul": shul}

        return render(request, "maps_redirect.html", context)


class ContactUsView(TemplateView):
    template_name = "eznashdb/contact_us.html"
