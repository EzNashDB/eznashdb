from datetime import date

from django.test import override_settings
from django.urls import reverse
from waffle.testutils import override_flag

from app.models import GooglePlacesUsage, GooglePlacesUserUsage

DUMMY_OSM_RECORD = {"name": "osm response", "place_id": 1, "id": 1, "source": "osm"}


def test_requires_login(client):
    """Address lookup requires login now."""
    url = reverse("eznashdb:address_lookup")
    query_params = {"q": "city name"}
    response = client.get(url, data=query_params)

    # Should redirect to login
    assert response.status_code == 302


def test_returns_osm_response_when_logged_in(client, mocker, test_user):
    client.force_login(test_user)

    # Mock OSMClient
    mock_client = mocker.patch("eznashdb.views.OSMClient")
    mock_instance = mock_client.return_value
    mock_instance.search_with_israel_fallback.return_value = [DUMMY_OSM_RECORD]

    url = reverse("eznashdb:address_lookup")
    query_params = {"q": "city name"}
    response = client.get(url, data=query_params)

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["source"] == "osm"


def test_returns_500_when_osm_fails(client, mocker, test_user):
    client.force_login(test_user)

    # Mock OSMClient to return None (failure)
    mock_client = mocker.patch("eznashdb.views.OSMClient")
    mock_instance = mock_client.return_value
    mock_instance.search_with_israel_fallback.return_value = None

    url = reverse("eznashdb:address_lookup")
    query_params = {"q": "city name"}
    response = client.get(url, data=query_params)

    assert response.status_code == 500
    assert "failed" in str(response.json()).lower()


def describe_google_places_integration():
    @override_flag("google_places_api", active=False)
    def uses_osm_when_flag_disabled(client, test_user, mocker):
        client.force_login(test_user)

        # Mock OSMClient
        mock_osm_client = mocker.patch("eznashdb.views.OSMClient")
        mock_osm_instance = mock_osm_client.return_value
        mock_osm_instance.search_with_israel_fallback.return_value = [DUMMY_OSM_RECORD]

        url = reverse("eznashdb:address_lookup")
        response = client.get(url, {"q": "test"})

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["source"] == "osm"

    @override_flag("google_places_api", active=True)
    @override_settings(GOOGLE_PLACES_API_KEY="test-key")
    def uses_google_when_flag_enabled(client, test_user, mocker):
        client.force_login(test_user)

        # Mock GooglePlacesClient
        mock_google_client = mocker.patch("eznashdb.views.GooglePlacesClient")
        mock_google_instance = mock_google_client.return_value
        mock_google_instance.autocomplete.return_value = [
            {
                "id": "ChIJ123",
                "place_id": "ChIJ123",
                "display_name": "Young Israel of Hollywood",
                "lat": None,
                "lon": None,
                "source": "google",
            }
        ]

        url = reverse("eznashdb:address_lookup")
        response = client.get(url, {"q": "young israel", "session_token": "test-token"})

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["source"] == "google"
        assert results[0]["place_id"] == "ChIJ123"
        assert results[0]["display_name"] == "Young Israel of Hollywood"

        # Check usage was tracked
        usage = GooglePlacesUsage.objects.get(date=date.today())
        assert usage.autocomplete_requests == 1

        user_usage = GooglePlacesUserUsage.objects.get(user=test_user, date=date.today())
        assert user_usage.autocomplete_requests == 1

    @override_flag("google_places_api", active=True)
    @override_settings(GOOGLE_PLACES_API_KEY="test-key")
    def falls_back_to_osm_when_daily_limit_reached(client, test_user, mocker):
        client.force_login(test_user)

        # Create usage that definitely exceeds monthly quota
        GooglePlacesUsage.objects.create(
            date=date.today(),
            autocomplete_requests=10001,
            details_requests=0,
        )

        # Mock OSMClient
        mock_osm_client = mocker.patch("eznashdb.views.OSMClient")
        mock_osm_instance = mock_osm_client.return_value
        mock_osm_instance.search_with_israel_fallback.return_value = [DUMMY_OSM_RECORD]

        url = reverse("eznashdb:address_lookup")
        response = client.get(url, {"q": "test"})

        assert response.status_code == 200
        results = response.json()
        assert results[0]["source"] == "osm"

    @override_flag("google_places_api", active=True)
    @override_settings(
        GOOGLE_PLACES_API_KEY="test-key",
        GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT=5,
    )
    def falls_back_to_osm_when_user_limit_reached(client, test_user, mocker):
        client.force_login(test_user)

        # Create existing usage at limit
        GooglePlacesUserUsage.objects.create(user=test_user, date=date.today(), autocomplete_requests=5)

        # Mock OSMClient
        mock_osm_client = mocker.patch("eznashdb.views.OSMClient")
        mock_osm_instance = mock_osm_client.return_value
        mock_osm_instance.search_with_israel_fallback.return_value = [DUMMY_OSM_RECORD]

        url = reverse("eznashdb:address_lookup")
        response = client.get(url, {"q": "test"})

        assert response.status_code == 200
        results = response.json()
        assert results[0]["source"] == "osm"
