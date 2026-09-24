import pytest
from django.core.cache import caches
from django.core.cache.backends.db import DatabaseCache
from django.urls import reverse
from django.utils import translation
from freezegun import freeze_time

from eznashdb.geocoding import CitySearchResult

CITY = {
    "display_name": "Teaneck, Bergen County, New Jersey, United States",
    "lat": 40.8976,
    "lon": -74.0116,
    "bounds": [[40.86, -74.03], [40.92, -73.99]],
}


@pytest.fixture(autouse=True)
def _clear_caches():
    for alias in ("default", "city_lookup"):
        caches[alias].clear()
    yield
    for alias in ("default", "city_lookup"):
        caches[alias].clear()


@pytest.fixture
def search_cities(mocker):
    mock_client = mocker.patch("eznashdb.views.OSMClient")
    mock_client.return_value.search_cities.return_value = CitySearchResult([CITY], complete=True)
    return mock_client.return_value.search_cities


def get_cities(client, q="teaneck", language="en", **extra):
    # The site picks its language from the URL prefix, e.g. /he/city-lookup/
    with translation.override(language):
        url = reverse("eznashdb:city_lookup")
    return client.get(url, data={"q": q}, **extra)


def test_is_available_to_signed_out_visitors(client, search_cities):
    response = get_cities(client)

    assert response.status_code == 200
    assert response.json() == {"results": [CITY]}


def test_passes_the_active_language_to_the_search(client, search_cities):
    get_cities(client, language="he")

    search_cities.assert_called_once_with("teaneck", language="he")


@pytest.mark.parametrize("q", ["", "  ", "te", "  te  "])
def test_returns_no_results_without_searching_for_short_queries(client, search_cities, q):
    response = get_cities(client, q=q)

    assert response.json() == {"results": []}
    search_cities.assert_not_called()


def describe_caching():
    def it_serves_repeat_queries_from_cache_ignoring_case_and_whitespace(client, search_cities):
        get_cities(client, q="teaneck")
        response = get_cities(client, q="  Teaneck ")

        assert response.json() == {"results": [CITY]}
        search_cities.assert_called_once()

    def it_does_not_share_cache_entries_across_languages(client, search_cities):
        get_cities(client, language="en")
        get_cities(client, language="he")

        assert search_cities.call_count == 2

    def it_does_not_cache_incomplete_results(client, search_cities):
        # A provider hiccup would otherwise be served for the whole TTL
        search_cities.return_value = CitySearchResult([CITY], complete=False)
        get_cities(client)
        get_cities(client)

        assert search_cities.call_count == 2

    def it_caches_a_complete_search_that_found_nothing(client, search_cities):
        search_cities.return_value = CitySearchResult([], complete=True)
        get_cities(client)
        response = get_cities(client)

        assert response.json() == {"results": []}
        search_cities.assert_called_once()

    def it_keeps_results_out_of_the_cache_that_holds_rate_limit_counters(client):
        # The default cache is a small DatabaseCache shared with the rate limiters, and it
        # culls by key order, so a flood of cached lookups could wipe their counters
        assert not isinstance(caches["city_lookup"], DatabaseCache)


@freeze_time("2026-01-01 12:00:10")  # mid-window, so a fixed-window limiter can't roll over mid-test
def describe_throttling():
    def _exhaust(client, ip, count):
        for i in range(count):
            get_cities(client, q=f"city {i}", HTTP_FLY_CLIENT_IP=ip)

    def it_rejects_requests_over_the_per_ip_limit(client, search_cities):
        _exhaust(client, "1.2.3.4", 30)

        assert get_cities(client, HTTP_FLY_CLIENT_IP="1.2.3.4").status_code == 429

    def it_limits_each_client_ip_separately(client, search_cities):
        _exhaust(client, "1.2.3.4", 30)

        assert get_cities(client, HTTP_FLY_CLIENT_IP="5.6.7.8").status_code == 200
