import contextlib
import math
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
from eznashdb.mixins import LoginRequiredMixin
from eznashdb.models import Shul


class ShulsFilterView(FilterView):
    template_name = "eznashdb/shuls.html"
    filterset_class = ShulFilterSet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get exact pin shul if justSaved param exists
        exact_pin_shul = None
        new_shul_id = self.request.GET.get("justSaved")
        if new_shul_id:
            with contextlib.suppress(Shul.DoesNotExist):
                exact_pin_shul = Shul.objects.get(pk=new_shul_id)

        # Filter exact_pin_shul out of object_list to prevent double-display
        object_list = context["object_list"]
        if exact_pin_shul:
            object_list = object_list.exclude(pk=exact_pin_shul.pk)
            context["object_list"] = object_list

        # Group shuls by their display coordinates
        grid_groups = defaultdict(list)
        for shul in object_list:
            grid_key = f"{shul.display_lat}_{shul.display_lon}"
            grid_groups[grid_key].append(shul)

        context["cluster_groups"] = dict(grid_groups)

        # Calculate cluster offset if needed
        cluster_offset = None
        if exact_pin_shul:
            cluster_offset = self._calculate_cluster_offset(exact_pin_shul, grid_groups)

        context["cluster_offset"] = cluster_offset
        context["exact_pin_shul"] = exact_pin_shul

        return context

    def _calculate_cluster_offset(self, exact_pin_shul, grid_groups):
        """
        Calculate offset for cluster that would have contained the exact_pin_shul.
        Returns dict with grid_key and offset values, or None if no offset needed.
        """

        # Minimum separation distance
        # If cluster is closer than this, push it out to this distance
        MIN_SEPARATION = 0.005

        # Find the grid_key where exact_pin_shul would have appeared
        target_grid_key = f"{exact_pin_shul.display_lat}_{exact_pin_shul.display_lon}"

        # Check if that cluster exists in our filtered results
        if target_grid_key not in grid_groups:
            # No cluster at that location (shul was the only one there)
            return None

        # Get cluster's position (use first shul's display coords as cluster centroid)
        cluster_shuls = grid_groups[target_grid_key]
        cluster_lat = cluster_shuls[0].display_lat
        cluster_lon = cluster_shuls[0].display_lon

        # Calculate distance between exact pin and cluster
        exact_lat = float(exact_pin_shul.latitude)
        exact_lon = float(exact_pin_shul.longitude)

        delta_lat = cluster_lat - exact_lat
        delta_lon = cluster_lon - exact_lon
        distance = math.sqrt(delta_lat**2 + delta_lon**2)

        # If far enough apart, no offset needed
        if distance >= MIN_SEPARATION:
            return None

        # Calculate offset to push cluster to MIN_SEPARATION distance
        # Push east or west (not north/south) to avoid marker icon overlap
        if delta_lon >= 0:
            # Cluster is east of (or at same longitude as) exact pin - push further east
            offset_lat = 0
            offset_lon = MIN_SEPARATION - distance
        else:
            # Cluster is west of exact pin - push further west
            offset_lat = 0
            offset_lon = -(MIN_SEPARATION - distance)

        return {
            "grid_key": target_grid_key,
            "offset_lat": offset_lat,
            "offset_lon": offset_lon,
        }

    def get_template_names(self) -> list[str]:
        if self.request.htmx:
            return ["eznashdb/shuls.html#map_updates"]
        return super().get_template_names()


class CreateUpdateShulView(LoginRequiredMixin, UpdateView):
    login_required_message = "Log in to add or edit shuls."
    model = Shul
    form_class = ShulForm
    template_name = "eznashdb/create_update_shul.html"
    NEARBY_SEARCH_RADIUS = Decimal("0.001")  # ~111 meters at the equator

    def get_success_url(self) -> str:
        url = reverse_lazy("eznashdb:shuls")
        lat = self.object.latitude
        lon = self.object.longitude
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

    def form_valid(self, form):
        if self.is_update:
            return self.handle_update_submit(form)
        else:
            wizard_step = self.request.POST.get("wizard_step", "1")
            if wizard_step == "1":
                return self.handle_step1_submit(form)
            elif wizard_step == "2":
                return self.handle_step2_submit(form)

    def form_invalid(self, form):
        """Handle form validation errors"""
        # Different messages based on context
        wizard_step = self.request.POST.get("wizard_step", "1")
        if self.is_update or wizard_step == "2":
            messages.error(self.request, "Unable to save. Check the form for errors.")
        else:
            messages.error(self.request, "Fix the form errors to continue.")
        return self.reload_shul_form(form)

    def handle_update_submit(self, form):
        """Handle update submission"""
        return self.save_shul_with_rooms(form)

    def handle_step1_submit(self, form):
        """Handle step 1 submission - validate and check nearby shuls"""
        # Check for nearby shuls and show modal if found
        nearby_response = self.check_and_show_nearby_shuls(form, wizard_step="1")
        if nearby_response:
            return nearby_response

        # No nearby shuls or user clicked "Save Anyway" -> proceed to step 2
        return self.reload_shul_form(form, wizard_step="2")

    def handle_step2_submit(self, form):
        """Handle step 2 submission"""
        return self.save_shul_with_rooms(form, wizard_step="2")

    def save_shul_with_rooms(self, form, wizard_step=None):
        """Validate rooms, check nearby shuls, and save atomically"""
        room_fs = self.get_room_fs()
        if not room_fs.is_valid():
            messages.error(self.request, "Unable to save. Check the form for errors.")
            return self.reload_shul_form(form, wizard_step=wizard_step)

        nearby_response = self.check_and_show_nearby_shuls(form, wizard_step=wizard_step)
        if nearby_response:
            return nearby_response

        with transaction.atomic():
            shul = form.save(commit=False)
            if not self.is_update:
                shul.created_by = self.request.user
            if self.is_update:
                shul.updated_by = list(set(shul.updated_by + [self.request.user.pk]))
            shul.save()
            self.object = shul
            self.room_fs_valid(room_fs)

        success_url = self.get_success_url()
        success_message = "Success! Your shul has been saved."
        messages.success(self.request, success_message)
        success_url += f"&justSaved={self.object.pk}"
        return HttpResponseClientRedirect(success_url)

    def check_and_show_nearby_shuls(self, form, wizard_step=None):
        """
        Check for nearby shuls and return modal response if found.
        Returns None if no check requested or no nearby shuls found.
        """
        check_nearby_shuls = self.request.POST.get("check_nearby_shuls") == "true"

        if not check_nearby_shuls:
            return None

        nearby_shuls = self.get_nearby_shuls(form)
        if not nearby_shuls.exists():
            return None

        # Show nearby shuls modal
        return self.reload_shul_form(form, nearby_shuls=nearby_shuls, wizard_step=wizard_step)

    def reload_shul_form(self, form, **context_overrides):
        """Reload the shul form partial with updated context"""
        context = self.get_context_data(form=form)
        context.update(context_overrides)
        return TemplateResponse(self.request, "eznashdb/create_update_shul.html#shul_form", context)

    def get_nearby_shuls(self, form):
        lat = form.cleaned_data.get("latitude")
        lon = form.cleaned_data.get("longitude")

        if lat is None or lon is None:
            return Shul.objects.none()

        return Shul.objects.filter(
            latitude__gte=lat - self.NEARBY_SEARCH_RADIUS,
            latitude__lte=lat + self.NEARBY_SEARCH_RADIUS,
            longitude__gte=lon - self.NEARBY_SEARCH_RADIUS,
            longitude__lte=lon + self.NEARBY_SEARCH_RADIUS,
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
        if not self.is_update:
            wizard_step = self.request.POST.get("wizard_step", "1")
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
                    self.request.POST, self.request.FILES, prefix=prefix, instance=self.object
                )

            # CREATE MODE - STEP 2: bind with POST data for validation
            elif wizard_step == "2":
                # Create temporary shul instance from POST data for formset validation
                temp_form = ShulForm(self.request.POST)
                temp_instance = None
                if temp_form.is_valid():
                    temp_instance = Shul(**temp_form.cleaned_data)
                return formset_class(
                    self.request.POST, self.request.FILES, prefix=prefix, instance=temp_instance
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


class GoogleMapsProxyView(LoginRequiredMixin, View):
    login_required_message = "Log in to open in Google Maps."

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
