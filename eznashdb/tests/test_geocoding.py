"""Unit tests for geocoding client classes."""

from calendar import monthrange
from datetime import date

import pytest
import requests
from django.contrib.auth import get_user_model
from django.test import override_settings
from waffle.testutils import override_flag

from app.models import GooglePlacesUsage, GooglePlacesUserUsage
from eznashdb.enums import GeocodingProvider
from eznashdb.geocoding import GooglePlacesBudgetChecker, GooglePlacesClient, OSMClient

User = get_user_model()


def describe_google_places_client():
    @pytest.fixture
    def client():
        return GooglePlacesClient(api_key="test-api-key")

    def describe_autocomplete():
        def it_returns_formatted_results_on_success(client, mocker):
            mock_response = mocker.Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "suggestions": [
                    {
                        "placePrediction": {
                            "placeId": "place123",
                            "text": {"text": "Test Synagogue"},
                        }
                    }
                ]
            }

            mocker.patch("requests.post", return_value=mock_response)
            results = client.autocomplete("test query", "session123")

            assert results == [
                {
                    "id": "place123",
                    "place_id": "place123",
                    "display_name": "Test Synagogue",
                    "lat": None,
                    "lon": None,
                    "source": GeocodingProvider.GOOGLE,
                }
            ]

        def it_returns_none_on_api_failure(client, mocker):
            mock_response = mocker.Mock()
            mock_response.status_code = 500

            mocker.patch("requests.post", return_value=mock_response)
            results = client.autocomplete("test query", "session123")

            assert results is None

        def it_handles_empty_suggestions(client, mocker):
            mock_response = mocker.Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"suggestions": []}

            mocker.patch("requests.post", return_value=mock_response)
            results = client.autocomplete("test query", "session123")

            assert results == []

    def describe_get_details():
        def it_returns_place_with_coordinates(client, mocker):
            mock_response = mocker.Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "location": {"latitude": 40.7128, "longitude": -74.0060},
                "formattedAddress": "123 Main St, New York, NY",
            }

            mocker.patch("requests.get", return_value=mock_response)
            result = client.get_details("place123", "session123")

            assert result == {
                "place_id": "place123",
                "lat": 40.7128,
                "lon": -74.0060,
                "display_name": "123 Main St, New York, NY",
                "source": GeocodingProvider.GOOGLE,
            }

        def it_includes_session_token_in_headers(client, mocker):
            mock_response = mocker.Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "location": {"latitude": 40.7128, "longitude": -74.0060},
                "formattedAddress": "Test Address",
            }

            mock_get = mocker.patch("requests.get", return_value=mock_response)
            client.get_details("place123", "session123")

            call_args = mock_get.call_args
            headers = call_args.kwargs["headers"]
            assert headers["X-Goog-Session-Token"] == "session123"

        def it_returns_none_on_api_failure(client, mocker):
            mock_response = mocker.Mock()
            mock_response.status_code = 404

            mocker.patch("requests.get", return_value=mock_response)
            result = client.get_details("invalid_place", "session123")

            assert result is None

    def describe_autocomplete_and_normalize():
        def it_normalizes_autocomplete_result(client, mocker):
            # Mock the autocomplete response
            mock_response = [
                {
                    "id": "ChIJ123",
                    "place_id": "ChIJ123",
                    "display_name": "Beth Israel Synagogue, Washington DC",
                    "lat": None,
                    "lon": None,
                    "source": GeocodingProvider.GOOGLE,
                }
            ]
            mocker.patch.object(client, "autocomplete", return_value=mock_response)

            results = client.autocomplete_and_normalize("beth israel", "token123")

            assert len(results) == 1
            place = results[0]
            assert place.id == "google:ChIJ123"
            assert place.provider == GeocodingProvider.GOOGLE
            assert place.name == "Beth Israel Synagogue, Washington DC"
            assert place.display_address == ""
            assert place.latitude is None
            assert place.longitude is None
            assert place.raw_data["place_id"] == "ChIJ123"

        def it_handles_autocomplete_failure(client, mocker):
            mocker.patch.object(client, "autocomplete", return_value=None)

            results = client.autocomplete_and_normalize("test", "token123")

            assert results is None


def describe_osm_client():
    @pytest.fixture
    def client():
        return OSMClient(base_url="https://test-osm.com/search", api_key="test-key")

    def describe_search():
        def it_returns_results_on_success(client, mocker):
            mock_response = mocker.Mock()
            mock_response.json.return_value = [
                {
                    "place_id": "123",
                    "display_name": "Test Location",
                    "lat": "40.7128",
                    "lon": "-74.0060",
                }
            ]

            mocker.patch("requests.get", return_value=mock_response)
            results = client.search("test query")

            assert results == [
                {
                    "place_id": "123",
                    "display_name": "Test Location",
                    "lat": "40.7128",
                    "lon": "-74.0060",
                }
            ]

        def it_returns_none_on_invalid_json(client, mocker):
            mock_response = mocker.Mock()
            mock_response.json.return_value = {"error": "invalid"}  # Not a list

            mocker.patch("requests.get", return_value=mock_response)
            results = client.search("test query")

            assert results is None

        def it_returns_none_on_request_exception(client, mocker):
            mocker.patch(
                "eznashdb.geocoding.requests.get",
                side_effect=requests.RequestException("Network error"),
            )
            results = client.search("test query")

            assert results is None

    def describe_search_with_israel_fallback():
        def it_formats_results_with_osm_source(client, mocker):
            mock_response = mocker.Mock()
            mock_response.json.return_value = [
                {
                    "place_id": "123",
                    "display_name": "Tel Aviv, Israel",
                }
            ]

            mocker.patch("requests.get", return_value=mock_response)
            results = client.search_with_israel_fallback("tel aviv")

            assert results[0]["id"] == "123"
            assert results[0]["source"] == GeocodingProvider.OSM

        def it_expands_israel_queries_to_include_palestine(client, mocker):
            mock_response = mocker.Mock()
            mock_response.json.return_value = [{"place_id": "123"}]

            mock_get = mocker.patch("requests.get", return_value=mock_response)
            mocker.patch("time.sleep")  # Skip the sleep delay
            client.search_with_israel_fallback("tel aviv, israel")

            # Should make two requests: original and modified
            assert mock_get.call_count == 2

        def it_replaces_palestinian_territory_with_israel_in_display_names(client, mocker):
            mock_response_1 = mocker.Mock()
            mock_response_1.json.return_value = [
                {
                    "place_id": "123",
                    "display_name": "Jerusalem, Palestinian Territory",
                }
            ]
            mock_response_2 = mocker.Mock()
            mock_response_2.json.return_value = []

            mocker.patch("requests.get", side_effect=[mock_response_1, mock_response_2])
            mocker.patch("time.sleep")
            results = client.search_with_israel_fallback("jerusalem, israel")

            assert "Israel" in results[0]["display_name"]
            assert "Palestinian Territory" not in results[0]["display_name"]

    def describe_search_and_normalize():
        def it_normalizes_place_with_coordinates(client, mocker):
            mock_response = [
                {
                    "place_id": "12345",
                    "display_name": "Ohev Sholom Synagogue, Washington, DC",
                    "lat": "38.9",
                    "lon": "-77.0",
                    "type": "place_of_worship",
                    "class": "amenity",
                    "extratags": {"religion": "jewish"},
                }
            ]
            mocker.patch.object(client, "search_with_israel_fallback", return_value=mock_response)

            results = client.search_and_normalize("ohev sholom")

            assert len(results) == 1
            place = results[0]
            assert place.id == "osm:12345"
            assert place.provider == GeocodingProvider.OSM
            assert place.name == "Ohev Sholom Synagogue, Washington, DC"
            assert place.display_address == ""
            assert place.latitude == 38.9
            assert place.longitude == -77.0
            assert place.raw_data["place_id"] == "12345"

        def it_handles_search_failure(client, mocker):
            mocker.patch.object(client, "search_with_israel_fallback", return_value=None)

            results = client.search_and_normalize("test")

            assert results is None


@pytest.mark.django_db
def describe_google_places_budget_checker():
    @pytest.fixture
    def checker():
        return GooglePlacesBudgetChecker()

    @pytest.fixture
    def user():
        return User.objects.create_user(username="test@example.com", email="test@example.com")

    def describe_get_daily_budget():
        def it_calculates_budget_at_start_of_month():
            test_date = date(2026, 1, 1)

            budget = GooglePlacesUsage.get_daily_budget(test_date)

            # January has 31 days, so daily budget = 10000 / 31 = 322
            assert budget.autocomplete == 322
            assert budget.details == 322

        def it_calculates_budget_mid_month_with_usage():
            test_date = date(2026, 1, 15)

            # Create usage before day 15
            GooglePlacesUsage.objects.create(
                date=date(2026, 1, 10), autocomplete_requests=2000, details_requests=2000
            )

            budget = GooglePlacesUsage.get_daily_budget(test_date)

            # 17 days remaining (15-31), 8000 quota left
            # Daily budget = 8000 / 17 = 470
            assert budget.autocomplete == 470
            assert budget.details == 470

        def it_calculates_budget_at_end_of_month():
            test_date = date(2026, 1, 31)

            # Create usage before last day
            GooglePlacesUsage.objects.create(
                date=date(2026, 1, 15), autocomplete_requests=8000, details_requests=8000
            )

            budget = GooglePlacesUsage.get_daily_budget(test_date)

            # Last day: all remaining quota (10000 - 8000 = 2000) available
            assert budget.autocomplete == 2000
            assert budget.details == 2000

        def it_returns_zero_when_quota_exhausted():
            test_date = date(2026, 1, 15)

            # Use all quota before day 15
            GooglePlacesUsage.objects.create(
                date=date(2026, 1, 10), autocomplete_requests=10000, details_requests=10000
            )

            budget = GooglePlacesUsage.get_daily_budget(test_date)

            assert budget.autocomplete == 0
            assert budget.details == 0

    def describe_can_use():
        @override_settings(GOOGLE_PLACES_API_KEY="test-key")
        @override_flag("google_places_api", active=False)
        def it_returns_false_when_flag_is_inactive(checker, user, rf):
            request = rf.get("/")
            result = checker.can_use(request, user)

            assert result is False

        @override_settings(GOOGLE_PLACES_API_KEY=None)
        @override_flag("google_places_api", active=True)
        def it_returns_false_when_api_key_not_configured(checker, user, rf):
            request = rf.get("/")
            result = checker.can_use(request, user)

            assert result is False

        @override_settings(GOOGLE_PLACES_API_KEY="test-key")
        @override_flag("google_places_api", active=True)
        def it_returns_false_when_daily_budget_exceeded(checker, user, rf):
            request = rf.get("/")

            # Calculate what the daily budget would be for today
            today = date.today()
            _, days_in_month = monthrange(today.year, today.month)
            days_remaining = days_in_month - today.day + 1
            daily_budget = 10000 // days_remaining

            # Use more than the daily budget to exceed it
            GooglePlacesUsage.objects.create(
                date=today,
                autocomplete_requests=daily_budget,
                details_requests=0,
            )

            result = checker.can_use(request, user)

            assert result is False

        @override_settings(
            GOOGLE_PLACES_API_KEY="test-key",
            GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT=50,
        )
        @override_flag("google_places_api", active=True)
        def it_returns_false_when_user_daily_limit_exceeded(checker, user, rf):
            request = rf.get("/")

            # Create user usage that exceeds limit
            GooglePlacesUserUsage.objects.create(
                user=user,
                date=date.today(),
                autocomplete_requests=50,
            )

            result = checker.can_use(request, user)

            assert result is False

        @override_settings(
            GOOGLE_PLACES_API_KEY="test-key",
            GOOGLE_PLACES_USER_DAILY_AUTOCOMPLETE_LIMIT=50,
        )
        @override_flag("google_places_api", active=True)
        def it_returns_true_when_all_checks_pass(checker, user, rf):
            request = rf.get("/")
            result = checker.can_use(request, user)

            assert result is True

    def describe_increment_autocomplete():
        def it_increments_global_and_user_usage(checker, user):
            checker.increment_autocomplete(user)

            global_usage = GooglePlacesUsage.objects.get(date=date.today())
            assert global_usage.autocomplete_requests == 1

            user_usage = GooglePlacesUserUsage.objects.get(user=user, date=date.today())
            assert user_usage.autocomplete_requests == 1

    def describe_increment_details():
        def it_increments_global_usage(checker):
            checker.increment_details()

            global_usage = GooglePlacesUsage.objects.get(date=date.today())
            assert global_usage.details_requests == 1
