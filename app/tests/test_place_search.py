"""Tests for place search merger."""

import pytest

from eznashdb.enums import GeocodingProvider
from eznashdb.place_search import NormalizedPlace, PlaceSearchMerger, score_place


def describe_score_place():
    def it_scores_first_result_higher_than_second():
        place_first = NormalizedPlace(
            id="osm:1",
            provider=GeocodingProvider.OSM,
            name="Test Place",
            display_address="City",
            latitude=38.9,
            longitude=-77.0,
            raw_data={},
        )
        place_second = NormalizedPlace(
            id="osm:2",
            provider=GeocodingProvider.OSM,
            name="Test Place",
            display_address="City",
            latitude=38.9,
            longitude=-77.0,
            raw_data={},
        )

        score_first = score_place(place_first, result_rank=0)
        score_second = score_place(place_second, result_rank=1)

        # First result (rank 0) should score higher than second (rank 1)
        assert score_first > score_second

    def it_gives_address_precision_bonus():
        # Same rank, different comma counts
        place_no_commas = NormalizedPlace(
            id="osm:1",
            provider=GeocodingProvider.OSM,
            name="Test Place",  # 0 commas
            display_address="City",
            latitude=38.9,
            longitude=-77.0,
            raw_data={},
        )
        place_eight_commas = NormalizedPlace(
            id="osm:2",
            provider=GeocodingProvider.OSM,
            name="A, B, C, D, E, F, G, H, I",  # 8 commas = 1.0 * 0.35 = 0.35 bonus
            display_address="City",
            latitude=38.9,
            longitude=-77.0,
            raw_data={},
        )

        score_no_commas = score_place(place_no_commas, result_rank=0)
        score_eight_commas = score_place(place_eight_commas, result_rank=0)

        # Same rank, but 8 commas should give address precision bonus
        assert score_eight_commas > score_no_commas

    def it_applies_multiplier_to_google_comma_count():
        google_place = NormalizedPlace(
            id="google:1",
            provider=GeocodingProvider.GOOGLE,
            name="Place, City",  # 1 comma * 2 = 2 effective commas
            display_address="Address",
            latitude=None,
            longitude=None,
            raw_data={},
        )
        osm_place = NormalizedPlace(
            id="osm:1",
            provider=GeocodingProvider.OSM,
            name="Place, City",  # 1 comma (no multiplier)
            display_address="Address",
            latitude=38.9,
            longitude=-77.0,
            raw_data={},
        )

        google_score = score_place(google_place, result_rank=0)
        osm_score = score_place(osm_place, result_rank=0)

        assert google_score > osm_score

    def it_decays_score_by_results_rank():
        place = NormalizedPlace(
            id="osm:1",
            provider=GeocodingProvider.OSM,
            name="Test",
            display_address="City",
            latitude=38.9,
            longitude=-77.0,
            raw_data={},
        )

        score_rank_0 = score_place(place, result_rank=0)  # 1.0 * 0.65 = 0.65
        score_rank_1 = score_place(place, result_rank=1)  # 0.9 * 0.65 = 0.585
        score_rank_5 = score_place(place, result_rank=5)  # 0.5 * 0.65 = 0.325

        assert score_rank_0 > score_rank_1 > score_rank_5


def describe_place_search_merger():
    @pytest.fixture
    def google_client_mock(mocker):
        return mocker.Mock()

    @pytest.fixture
    def osm_client_mock(mocker):
        return mocker.Mock()

    @pytest.fixture
    def merger(google_client_mock, osm_client_mock):
        return PlaceSearchMerger(google_client_mock, osm_client_mock)

    def it_merges_and_sorts_by_score(merger, google_client_mock, osm_client_mock):
        # Setup: Google returns a short-address place, OSM returns a detailed-address place
        # OSM's detailed address should rank it first despite both being rank 0 in their providers
        google_place = NormalizedPlace(
            id="google:1",
            provider=GeocodingProvider.GOOGLE,
            name="Test Place, City, Country",  # 2 commas / 8.0 = 0.25 * 0.35 = 0.09
            display_address="Address",
            latitude=None,
            longitude=None,
            raw_data={},
        )
        osm_place = NormalizedPlace(
            id="osm:1",
            provider=GeocodingProvider.OSM,
            name="Test Place, Street, District, City, Region, Postal, Country, Extra",  # 7 commas / 8.0 = 0.875 * 0.35 = 0.31
            display_address="Full Address",
            latitude=38.9,
            longitude=-77.0,
            raw_data={},
        )

        google_client_mock.autocomplete_and_normalize.return_value = [google_place]
        osm_client_mock.search_and_normalize.return_value = [osm_place]

        results = merger.search("test place", session_token="token123")

        # OSM should be first due to more detailed address (higher completeness score)
        # OSM: 0.65 + 0.31 = 0.96
        # Google: 0.65 + 0.09 = 0.74
        assert len(results) == 2
        assert results[0].id == "osm:1"
        assert results[1].id == "google:1"

    def it_handles_google_failure(merger, google_client_mock, osm_client_mock):
        osm_place = NormalizedPlace(
            id="osm:1",
            provider=GeocodingProvider.OSM,
            name="Test Synagogue",
            display_address="City",
            latitude=38.9,
            longitude=-77.0,
            raw_data={},
        )

        google_client_mock.autocomplete_and_normalize.return_value = None
        osm_client_mock.search_and_normalize.return_value = [osm_place]

        results = merger.search("test", session_token="token123")

        # Should still return OSM results
        assert len(results) == 1
        assert results[0].id == "osm:1"

    def it_handles_osm_failure(merger, google_client_mock, osm_client_mock):
        google_place = NormalizedPlace(
            id="google:1",
            provider=GeocodingProvider.GOOGLE,
            name="Test Place",
            display_address="City",
            latitude=None,
            longitude=None,
            raw_data={},
        )

        google_client_mock.autocomplete_and_normalize.return_value = [google_place]
        osm_client_mock.search_and_normalize.return_value = None

        results = merger.search("test", session_token="token123")

        # Should still return Google results
        assert len(results) == 1
        assert results[0].id == "google:1"

    def it_handles_both_failures(merger, google_client_mock, osm_client_mock):
        google_client_mock.autocomplete_and_normalize.return_value = None
        osm_client_mock.search_and_normalize.return_value = None

        results = merger.search("test", session_token="token123")

        # Should return empty list
        assert results == []

    def it_returns_all_results_without_deduplication(merger, google_client_mock, osm_client_mock):
        # Both providers return similar-looking places
        google_place = NormalizedPlace(
            id="google:1",
            provider=GeocodingProvider.GOOGLE,
            name="Beth Israel Synagogue",
            display_address="123 Main St, Washington DC",
            latitude=None,
            longitude=None,
            raw_data={},
        )
        osm_place = NormalizedPlace(
            id="osm:1",
            provider=GeocodingProvider.OSM,
            name="Beth Israel Synagogue",
            display_address="123 Main St, Washington DC",
            latitude=38.9,
            longitude=-77.0,
            raw_data={},
        )

        google_client_mock.autocomplete_and_normalize.return_value = [google_place]
        osm_client_mock.search_and_normalize.return_value = [osm_place]

        results = merger.search("beth israel", session_token="token123")

        # Should return both (no deduplication)
        assert len(results) == 2

    def it_queries_both_providers(merger, google_client_mock, osm_client_mock):
        google_place = NormalizedPlace(
            id="google:1",
            provider=GeocodingProvider.GOOGLE,
            name="Test Place",
            display_address="City",
            latitude=None,
            longitude=None,
            raw_data={},
        )
        osm_place = NormalizedPlace(
            id="osm:1",
            provider=GeocodingProvider.OSM,
            name="Test Synagogue",
            display_address="City",
            latitude=38.9,
            longitude=-77.0,
            raw_data={},
        )

        google_client_mock.autocomplete_and_normalize.return_value = [google_place]
        osm_client_mock.search_and_normalize.return_value = [osm_place]

        results = merger.search("test", session_token="token123")

        # Should call both providers
        google_client_mock.autocomplete_and_normalize.assert_called_once_with("test", "token123")
        osm_client_mock.search_and_normalize.assert_called_once_with("test")

        # Should return results from both
        assert len(results) == 2
