from datetime import date

from django.test import override_settings
from django.urls import reverse
from waffle.testutils import override_flag

from app.models import GooglePlacesUsage


def describe_google_places_details():
    @override_flag("google_places_api", active=True)
    @override_settings(GOOGLE_PLACES_API_KEY="test-key")
    def fetches_place_details_successfully(client, test_user, mocker):
        client.force_login(test_user)

        # Mock GooglePlacesClient
        mock_google_client = mocker.patch("eznashdb.views.GooglePlacesClient")
        mock_google_instance = mock_google_client.return_value
        mock_google_instance.get_details.return_value = {
            "place_id": "ChIJ123",
            "lat": 40.7128,
            "lon": -74.0060,
            "display_name": "123 Main St, City",
            "source": "google",
        }

        url = reverse("eznashdb:address_lookup_details")
        response = client.get(url, {"place_id": "ChIJ123", "session_token": "test-token"})

        assert response.status_code == 200
        result = response.json()
        assert result["lat"] == 40.7128
        assert result["lon"] == -74.0060
        assert result["source"] == "google"

        # Verify session_token was passed to get_details
        mock_google_instance.get_details.assert_called_once_with("ChIJ123", "test-token")

        # Check details usage was tracked
        usage = GooglePlacesUsage.objects.get(date=date.today())
        assert usage.details_requests == 1

    @override_flag("google_places_api", active=True)
    def returns_error_when_place_id_missing(client, test_user):
        client.force_login(test_user)
        url = reverse("eznashdb:address_lookup_details")
        response = client.get(url)

        assert response.status_code == 400
