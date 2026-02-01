"""Geocoding client classes for Google Places and OpenStreetMap."""

import time
import urllib.parse
from datetime import date
from json.decoder import JSONDecodeError

import requests
from django.conf import settings
from django.db.models import F
from waffle import flag_is_active

from app.models import GooglePlacesUsage, GooglePlacesUserUsage


class GooglePlacesClient:
    """Handles Google Places API calls."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def autocomplete(self, query: str, session_token: str) -> list[dict] | None:
        """
        Get autocomplete suggestions from Google Places API.
        Returns list of suggestions without coordinates, or None on failure.
        """
        url = "https://places.googleapis.com/v1/places:autocomplete"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
        }
        payload = {
            "input": query,
            "sessionToken": session_token,
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            return None

        data = response.json()
        suggestions = data.get("suggestions", [])

        results = []
        for suggestion in suggestions:
            place_prediction = suggestion.get("placePrediction")
            if place_prediction:
                results.append(
                    {
                        "id": place_prediction.get("placeId"),
                        "place_id": place_prediction.get("placeId"),
                        "display_name": place_prediction.get("text", {}).get("text", ""),
                        "lat": None,
                        "lon": None,
                        "source": "google",
                    }
                )

        return results

    def get_details(self, place_id: str, session_token: str) -> dict | None:
        """
        Get place details including coordinates from Google Places API.
        Returns place data with coordinates, or None on failure.
        Passes session_token to complete billing session.
        """
        url = f"https://places.googleapis.com/v1/places/{place_id}"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "id,displayName,formattedAddress,location",
        }

        # Include session token to complete the billing session
        if session_token:
            headers["X-Goog-Session-Token"] = session_token

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return None

        data = response.json()
        location = data.get("location", {})

        return {
            "place_id": place_id,
            "lat": location.get("latitude"),
            "lon": location.get("longitude"),
            "display_name": data.get("formattedAddress", ""),
            "source": "google",
        }


class OSMClient:
    """Handles OpenStreetMap/Nominatim geocoding."""

    def __init__(self, base_url: str, api_key: str | None = None):
        self.base_url = base_url
        self.api_key = api_key

    def search(self, query: str) -> list[dict] | None:
        """
        Search for locations using Nominatim API.
        Returns list of results with coordinates, or None on failure.
        """
        params = {
            "format": "json",
            "addressdetails": 1,
            "namedetails": 1,
            "q": query,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        url = self.base_url + "?" + urllib.parse.urlencode(params)

        try:
            response = requests.get(url)

            # Validate response is a list
            data = response.json()
            if not isinstance(data, list):
                return None

            return data

        except (JSONDecodeError, requests.RequestException):
            return None

    def search_with_israel_fallback(self, query: str) -> list[dict] | None:
        """
        Search with automatic Israel/Palestine query expansion.
        Returns combined results from original query and Palestine variant.
        """
        results = self.search(query)
        if results is None:
            return None

        # Create modified query with Palestine instead of Israel
        modified_query = query
        for israel, palestine in [
            ("il", "ps"),
            ("israel", "palestinian territory"),
            ("ישראל", "palestinian territory"),
        ]:
            if israel in query:
                modified_query = modified_query.replace(israel, palestine)

        # If query was modified, fetch additional results
        if modified_query != query:
            # Sleep to avoid too many requests error
            time.sleep(1)
            additional_results = self.search(modified_query)
            if additional_results is not None:
                results.extend(additional_results)

        # Format results to match standard format
        return self._format_results(results)

    def _format_results(self, results: list[dict]) -> list[dict]:
        """Format OSM results to standardized structure."""
        israel_palestine_pairs = [
            ("ישראל", "الأراضي الفلسطينية"),
            ("Israel", "Palestinian Territory"),
        ]

        for result in results:
            result["id"] = result.get("place_id")
            result["source"] = "osm"
            # Replace Palestinian Territory with Israel in display names
            for israel, palestine in israel_palestine_pairs:
                result["display_name"] = result.get("display_name", "").replace(palestine, israel)

        return results


class GooglePlacesBudgetChecker:
    """Checks if Google Places API usage is within free tier limits."""

    def can_use(self, request, user) -> bool:
        """Check feature flag and budget limits."""
        if not flag_is_active(request, "google_places_api"):
            return False

        if not settings.GOOGLE_PLACES_API_KEY:
            return False

        today = date.today()

        # Get today's budget based on usage from previous days
        budget = GooglePlacesUsage.get_daily_budget(today)

        # Get today's usage
        today_usage = GooglePlacesUsage.get_usage_for_date(today)

        # Check if we've exceeded today's budget
        if today_usage.autocomplete >= budget.autocomplete:
            return False

        if today_usage.details >= budget.details:
            return False

        # Check per-user daily limit (abuse prevention)
        user_usage, _ = GooglePlacesUserUsage.objects.get_or_create(user=user, date=today)
        return user_usage.autocomplete_requests < settings.GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT

    def increment_autocomplete(self, user) -> None:
        """Track autocomplete request for both global and per-user usage."""
        today = date.today()

        # Increment global usage
        global_usage, _ = GooglePlacesUsage.objects.get_or_create(date=today)
        global_usage.autocomplete_requests = F("autocomplete_requests") + 1
        global_usage.save()

        # Increment user usage
        user_usage, _ = GooglePlacesUserUsage.objects.get_or_create(user=user, date=today)
        user_usage.autocomplete_requests = F("autocomplete_requests") + 1
        user_usage.save()

    def increment_details(self) -> None:
        """
        Track details request for global usage.

        Note: Does not track per-user usage. Details requests are inherently limited
        by autocomplete requests (can only get details after selecting an autocomplete
        result), so per-user autocomplete limits are sufficient for abuse prevention.
        """
        today = date.today()
        global_usage, _ = GooglePlacesUsage.objects.get_or_create(date=today)
        global_usage.details_requests = F("details_requests") + 1
        global_usage.save()
