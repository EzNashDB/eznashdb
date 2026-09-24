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

        def it_returns_empty_list_on_api_failure(client, mocker):
            mock_response = mocker.Mock()
            mock_response.status_code = 500

            mocker.patch("requests.post", return_value=mock_response)
            results = client.autocomplete("test query", "session123")

            assert results == []

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
            mocker.patch.object(client, "autocomplete", return_value=[])

            results = client.autocomplete_and_normalize("test", "token123")

            assert results == []


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

        def it_times_out_instead_of_hanging_on_a_stalled_provider(client, mocker):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = []

            client.search("test query")

            assert mock_get.call_args.kwargs["timeout"] == 5

        def it_returns_empty_list_on_invalid_json(client, mocker):
            mock_response = mocker.Mock()
            mock_response.json.return_value = {"error": "invalid"}  # Not a list

            mocker.patch("requests.get", return_value=mock_response)
            results = client.search("test query")

            assert results == []

        def it_returns_empty_list_on_request_exception(client, mocker):
            mocker.patch(
                "eznashdb.geocoding.requests.get",
                side_effect=requests.RequestException("Network error"),
            )
            results = client.search("test query")

            assert results == []

    def describe_search_and_format_results():
        def it_formats_results_with_osm_source(client, mocker):
            mock_response = mocker.Mock()
            mock_response.json.return_value = [
                {
                    "place_id": "123",
                    "display_name": "Tel Aviv, Israel",
                }
            ]

            mocker.patch("requests.get", return_value=mock_response)
            results = client.search_and_format_results("tel aviv")

            assert results[0]["id"] == "123"
            assert results[0]["source"] == GeocodingProvider.OSM

        def it_replaces_palestinian_territory_with_israel_in_display_names(client, mocker):
            mock_response = mocker.Mock()
            mock_response.json.return_value = [
                {
                    "place_id": "123",
                    "display_name": "Jerusalem, Palestinian Territory",
                }
            ]

            mocker.patch("requests.get", return_value=mock_response)
            results = client.search_and_format_results("jerusalem")

            assert "Israel" in results[0]["display_name"]
            assert "Palestinian Territory" not in results[0]["display_name"]

    def describe_search_cities():
        def _osm_result(**overrides):
            return {
                "place_id": 1,
                "display_name": "Teaneck, Bergen County, New Jersey, United States",
                "lat": "40.8976",
                "lon": "-74.0116",
                "addresstype": "town",
                "boundingbox": ["40.86", "40.92", "-74.03", "-73.99"],
                **overrides,
            }

        def it_requests_results_in_the_given_language(client, mocker):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = []

            client.search_cities("teaneck", language="he")

            assert all("accept-language=he" in call.args[0] for call in mock_get.call_args_list)

        def it_searches_both_with_and_without_featuretype(client, mocker):
            # Each finds places the other misses: featureType=settlement hides Ma'ale Shomron
            # (tagged as a neighbourhood), while without it the country and county named
            # "Lebanon" crowd every actual Lebanon out of the results
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = []

            client.search_cities("lebanon")

            urls = [call.args[0] for call in mock_get.call_args_list]
            assert len(urls) == 2
            assert sum("featureType=settlement" in url for url in urls) == 1

        def it_merges_both_searches_with_unrestricted_results_first(client, mocker):
            unrestricted = [
                _osm_result(display_name="Ma'ale Shomron, Israel", addresstype="neighbourhood")
            ]
            settlements = [
                _osm_result(display_name="Lebanon, Pennsylvania", lat="40.34", lon="-76.41"),
                _osm_result(display_name="Lebanon, Ohio", lat="39.43", lon="-84.20"),
            ]

            def fake_get(url, **kwargs):
                response = mocker.Mock()
                response.json.return_value = settlements if "featureType" in url else unrestricted
                return response

            mocker.patch("requests.get", side_effect=fake_get)

            results = client.search_cities("lebanon").places

            assert [r["display_name"] for r in results] == [
                "Ma'ale Shomron, Israel",
                "Lebanon, Pennsylvania",
                "Lebanon, Ohio",
            ]

        def it_still_returns_results_when_one_of_the_two_searches_fails(client, mocker):
            def fake_get(url, **kwargs):
                if "featureType" in url:
                    raise requests.RequestException("boom")
                response = mocker.Mock()
                response.json.return_value = [_osm_result(display_name="Teaneck")]
                return response

            mocker.patch("requests.get", side_effect=fake_get)

            result = client.search_cities("teaneck")

            assert [r["display_name"] for r in result.places] == ["Teaneck"]
            assert result.complete is False

        def it_omits_language_when_not_given(client, mocker):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = []

            client.search_cities("teaneck")

            assert "accept-language" not in mock_get.call_args.args[0]

        @pytest.mark.parametrize(
            "addresstype",
            ["city", "town", "village", "municipality"]
            + ["suburb", "neighbourhood", "quarter", "city_district", "borough"],
        )
        def it_keeps_city_and_neighbourhood_level_results(client, mocker, addresstype):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [_osm_result(addresstype=addresstype)]

            assert len(client.search_cities("teaneck").places) == 1

        @pytest.mark.parametrize(
            "addresstype", ["road", "building", "railway", "park", "hamlet", "county", "country"]
        )
        def it_drops_results_that_are_not_places_people_search_for(client, mocker, addresstype):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [_osm_result(addresstype=addresstype)]

            assert client.search_cities("teaneck").places == []

        @pytest.mark.parametrize("addresstype", ["state", "province", "region"])
        def it_falls_back_to_regions_when_there_are_no_city_level_results(client, mocker, addresstype):
            # e.g. Tokyo and Hong Kong, which OSM models as prefectures/regions, not cities
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [_osm_result(addresstype=addresstype)]

            assert len(client.search_cities("tokyo").places) == 1

        def it_keeps_neighbourhoods_alongside_cities_in_provider_order(client, mocker):
            # Brooklyn (NYC) is a suburb in OSM, and the provider ranks it above the small towns
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [
                _osm_result(
                    display_name="Brooklyn, New York", addresstype="suburb", lat="40.65", lon="-73.95"
                ),
                _osm_result(
                    display_name="Brooklyn, Illinois", addresstype="village", lat="38.66", lon="-90.16"
                ),
                _osm_result(
                    display_name="Brooklyn, Ohio", addresstype="town", lat="41.43", lon="-81.74"
                ),
            ]

            results = client.search_cities("brooklyn").places

            assert [r["display_name"] for r in results] == [
                "Brooklyn, New York",
                "Brooklyn, Illinois",
                "Brooklyn, Ohio",
            ]

        def it_removes_results_with_identical_display_names(client, mocker):
            # The provider returns e.g. Karnei Shomron twice (a node and a relation)
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [
                _osm_result(display_name="Elkana, Israel", place_id=1, lat="32.11", lon="35.03"),
                _osm_result(display_name="Elkana, Israel", place_id=2, lat="32.50", lon="35.50"),
                _osm_result(display_name="Elkana, Ohio", place_id=3, lat="40.10", lon="-81.10"),
            ]

            results = client.search_cities("elkana").places

            assert [r["display_name"] for r in results] == ["Elkana, Israel", "Elkana, Ohio"]

        def it_removes_the_same_place_listed_under_slightly_different_names(client, mocker):
            # e.g. Har Nof comes back twice, once with "Yefe Nof" in its display name and once without
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [
                _osm_result(display_name="Har Nof, Yefe Nof, Jerusalem", lat="31.7880", lon="35.1740"),
                _osm_result(display_name="Har Nof, Jerusalem", lat="31.7885", lon="35.1745"),
            ]

            results = client.search_cities("har nof").places

            assert [r["display_name"] for r in results] == ["Har Nof, Yefe Nof, Jerusalem"]

        def it_keeps_same_named_places_that_are_far_apart(client, mocker):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [
                _osm_result(display_name="Lebanon, Pennsylvania", lat="40.34", lon="-76.41"),
                _osm_result(display_name="Lebanon, Ohio", lat="39.43", lon="-84.20"),
            ]

            assert len(client.search_cities("lebanon").places) == 2

        def it_gives_regions_a_center_point_but_no_bounds(client, mocker):
            # A region's bounding box can span far-flung parts (Tokyo's includes islands
            # hundreds of km out to sea), so the map centers on the point instead
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [
                _osm_result(
                    display_name="Tokyo, Japan",
                    addresstype="province",
                    lat="35.6768601",
                    lon="139.7638947",
                    boundingbox=["20.2", "35.9", "135.8", "154.2"],
                )
            ]

            assert client.search_cities("tokyo").places == [
                {"display_name": "Tokyo, Japan", "lat": 35.6768601, "lon": 139.7638947, "bounds": None}
            ]

        def it_includes_regions_alongside_cities_in_provider_order(client, mocker):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [
                _osm_result(display_name="New York City", addresstype="city", lat="40.71", lon="-74.00"),
                _osm_result(
                    display_name="New York State", addresstype="state", lat="42.95", lon="-75.53"
                ),
            ]

            results = client.search_cities("new york").places

            assert [r["display_name"] for r in results] == ["New York City", "New York State"]
            assert results[0]["bounds"] is not None
            assert results[1]["bounds"] is None  # regions are centered on their point instead

        def it_skips_malformed_results_without_dropping_the_good_ones(client, mocker):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [
                _osm_result(display_name="no lat", lat=None),
                {k: v for k, v in _osm_result(display_name="no lon").items() if k != "lon"},
                _osm_result(display_name="bad bounds", boundingbox=["a", "b", "c", "d"]),
                _osm_result(display_name="short bounds", boundingbox=["1", "2"]),
                _osm_result(display_name="Teaneck"),
            ]

            results = client.search_cities("teaneck").places

            assert [r["display_name"] for r in results] == ["Teaneck"]

        def it_returns_display_name_coordinates_and_leaflet_bounds(client, mocker):
            mock_get = mocker.patch("requests.get")
            # Nominatim's boundingbox is [south, north, west, east], as strings
            mock_get.return_value.json.return_value = [_osm_result()]

            assert client.search_cities("teaneck").places == [
                {
                    "display_name": "Teaneck, Bergen County, New Jersey, United States",
                    "lat": 40.8976,
                    "lon": -74.0116,
                    "bounds": [[40.86, -74.03], [40.92, -73.99]],
                }
            ]

        def it_replaces_palestinian_territory_with_israel(client, mocker):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [
                _osm_result(display_name="Efrat, Palestinian Territory")
            ]

            assert client.search_cities("efrat").places[0]["display_name"] == "Efrat, Israel"

        def it_uses_the_hebrew_name_for_israel_when_the_language_is_hebrew(client, mocker):
            # The provider returns "Palestinian Territory" in English even for accept-language=he
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [
                _osm_result(display_name="מעלה שומרון, יהודה ושומרון, Palestinian Territory")
            ]

            results = client.search_cities("מעלה שומרון", language="he").places

            assert results[0]["display_name"] == "מעלה שומרון, יהודה ושומרון, ישראל"

        def it_skips_results_without_a_bounding_box(client, mocker):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [_osm_result(boundingbox=None)]

            assert client.search_cities("teaneck").places == []

        def it_is_complete_when_both_searches_succeeded(client, mocker):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = [_osm_result()]

            assert client.search_cities("teaneck").complete is True

        def it_is_complete_when_the_provider_genuinely_has_no_matches(client, mocker):
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = []

            result = client.search_cities("qwertyuiop")

            assert result.places == []
            assert result.complete is True

        @pytest.mark.parametrize("failure", ["exception", "non_list_response"])
        def it_is_incomplete_when_either_search_fails(client, mocker, failure):
            def fake_get(url, **kwargs):
                if "featureType" not in url:
                    return mocker.Mock(**{"json.return_value": [_osm_result()]})
                if failure == "exception":
                    raise requests.RequestException("boom")
                return mocker.Mock(**{"json.return_value": {"error": "rate limited"}})

            mocker.patch("requests.get", side_effect=fake_get)

            assert client.search_cities("teaneck").complete is False

        def it_uses_a_shorter_timeout_than_the_default(client, mocker):
            # Blocking calls on a public endpoint, with only a few gunicorn threads to spare
            mock_get = mocker.patch("requests.get")
            mock_get.return_value.json.return_value = []

            client.search_cities("teaneck")

            timeouts = [call.kwargs["timeout"] for call in mock_get.call_args_list]
            assert timeouts == [3, 3]

        def it_returns_empty_list_on_request_exception(client, mocker):
            mocker.patch("requests.get", side_effect=requests.RequestException("boom"))

            assert client.search_cities("teaneck").places == []

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
            mocker.patch.object(client, "search_and_format_results", return_value=mock_response)

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
            mocker.patch.object(client, "search_and_format_results", return_value=[])

            results = client.search_and_normalize("test")

            assert results == []


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
