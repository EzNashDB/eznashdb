from datetime import date

from django.test import override_settings
from django.urls import reverse
from waffle.testutils import override_flag

from app.models import GooglePlacesUsage, GooglePlacesUserUsage
from eznashdb.enums import GeocodingProvider
from eznashdb.place_search import NormalizedPlace


def test_requires_login(client):
    """Address lookup requires login now."""
    url = reverse("eznashdb:address_lookup")
    query_params = {"q": "city name"}
    response = client.get(url, data=query_params)

    # Should redirect to login
    assert response.status_code == 302


def test_returns_results_when_logged_in(client, mocker, test_user):
    client.force_login(test_user)

    # Mock PlaceSearchMerger

    mock_merger = mocker.patch("eznashdb.views.PlaceSearchMerger")
    mock_merger_instance = mock_merger.return_value
    mock_merger_instance.search.return_value = [
        NormalizedPlace(
            id="osm:1",
            provider=GeocodingProvider.OSM,
            name="osm response",
            display_address="",
            latitude=38.9,
            longitude=-77.0,
            raw_data={"place_id": "1"},
        )
    ]

    url = reverse("eznashdb:address_lookup")
    query_params = {"q": "city name"}
    response = client.get(url, data=query_params)

    assert response.status_code == 200
    results = response.json().get("results")
    assert len(results) == 1
    assert results[0]["source"] == GeocodingProvider.OSM


def test_returns_empty_list_when_search_returns_no_results(client, mocker, test_user):
    client.force_login(test_user)

    # Mock PlaceSearchMerger to return empty list (no results found)
    mock_merger = mocker.patch("eznashdb.views.PlaceSearchMerger")
    mock_merger_instance = mock_merger.return_value
    mock_merger_instance.search.return_value = []

    url = reverse("eznashdb:address_lookup")
    query_params = {"q": "city name"}
    response = client.get(url, data=query_params)

    assert response.status_code == 200
    results = response.json().get("results")
    assert len(results) == 0


def describe_google_places_integration():
    @override_flag("google_places_api", active=True)
    @override_settings(GOOGLE_PLACES_API_KEY="test-key")
    def uses_google_when_flag_enabled(client, test_user, mocker):
        client.force_login(test_user)

        # Mock PlaceSearchMerger
        mock_merger = mocker.patch("eznashdb.views.PlaceSearchMerger")
        mock_merger_instance = mock_merger.return_value
        mock_merger_instance.search.return_value = [
            NormalizedPlace(
                id="google:ChIJ123",
                provider=GeocodingProvider.GOOGLE,
                name="Young Israel of Hollywood",
                display_address="",
                latitude=None,
                longitude=None,
                raw_data={"place_id": "ChIJ123"},
            )
        ]

        url = reverse("eznashdb:address_lookup")
        response = client.get(url, {"q": "young israel", "session_token": "test-token"})

        assert response.status_code == 200
        results = response.json().get("results")
        assert len(results) == 1
        assert results[0]["source"] == GeocodingProvider.GOOGLE
        assert results[0]["place_id"] == "ChIJ123"
        assert results[0]["display_name"] == "Young Israel of Hollywood"

        # Check usage was tracked
        usage = GooglePlacesUsage.objects.get(date=date.today())
        assert usage.autocomplete_requests == 1

        user_usage = GooglePlacesUserUsage.objects.get(user=test_user, date=date.today())
        assert user_usage.autocomplete_requests == 1
