"""Place search merger for Google Places and OSM Nominatim."""

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from dataclasses import dataclass

import requests

from eznashdb.enums import GeocodingProvider

logger = logging.getLogger(__name__)

# Scoring weights (must sum to 1.0)
WEIGHT_RESULTS_RANK = 0.65
WEIGHT_PRECISION = 0.35

# Address completeness normalization (OSM detailed addresses typically have ~8 commas)
MAX_COMMA_COUNT = 8.0

# Google addresses use fewer commas for same precision as OSM
GOOGLE_COMMA_MULTIPLIER = 2


@dataclass
class NormalizedPlace:
    """Normalized place representation from any provider."""

    id: str  # "google:ChIJ..." or "osm:12345"
    provider: GeocodingProvider
    name: str
    display_address: str
    latitude: float | None  # None for Google autocomplete
    longitude: float | None
    raw_data: dict  # Original response for details fetch

    def as_dict(self):
        return {
            "id": self.id,
            "place_id": self.id.split(":", 1)[1],
            "display_name": self.name,
            "lat": self.latitude,
            "lon": self.longitude,
            "source": self.provider,
        }


def score_place(place: NormalizedPlace, result_rank: int) -> float:
    """
    Score a place based on provider rank and address precision.

    Args:
        place: Normalized place to score
        rank: Rank in provider's result list (0-indexed)

    Returns:
        Score between 0.0 and 1.0
    """
    # Rank-based score (first = 1.0, decays by 0.1 per rank)
    rank_score = max(1.0 - (result_rank * 0.1), 0.0)

    # Address completeness - count commas in name
    comma_count = place.name.count(",")

    # Google addresses are more concise, compensate with multiplier
    if place.provider == GeocodingProvider.GOOGLE:
        comma_count *= GOOGLE_COMMA_MULTIPLIER

    precision_score = min(comma_count / MAX_COMMA_COUNT, 1.0)

    return rank_score * WEIGHT_RESULTS_RANK + precision_score * WEIGHT_PRECISION


class PlaceSearchMerger:
    """Merges results from Google Places and OSM Nominatim."""

    def __init__(self, google_client, osm_client):
        """
        Initialize merger with provider clients.

        Args:
            google_client: GooglePlacesClient instance
            osm_client: OSMClient instance
        """
        self.google_client = google_client
        self.osm_client = osm_client

    def search(self, query: str, session_token: str) -> list[NormalizedPlace]:
        """
        Search both providers and return merged, scored results.

        Args:
            query: User's search query
            session_token: Session token for Google Places

        Returns:
            List of NormalizedPlace objects, sorted by score (highest first)
        """
        google_results = []
        osm_results = []

        # Query both providers in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}

            # Submit Google Places query (if client is available)
            if self.google_client:
                google_future = executor.submit(
                    self.google_client.autocomplete_and_normalize, query, session_token
                )
                futures[google_future] = GeocodingProvider.GOOGLE

            # Submit OSM query
            osm_future = executor.submit(self.osm_client.search_and_normalize, query)
            futures[osm_future] = GeocodingProvider.OSM

            # Collect results with 5 second timeout per provider
            for future in as_completed(futures, timeout=5):
                try:
                    provider_results = future.result(timeout=5)
                    if provider_results:
                        if futures[future] == GeocodingProvider.GOOGLE:
                            google_results = provider_results
                        else:
                            osm_results = provider_results
                except (TimeoutError, requests.RequestException) as e:
                    # Network/timeout failure - continue with other provider
                    logger.warning(f"Provider {futures[future]} failed: {e}")

        # Score results preserving provider rank
        scored_results = []
        for provider_results in [google_results, osm_results]:
            if provider_results:
                for rank, place in enumerate(provider_results):
                    scored_results.append((place, score_place(place, rank)))

        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Return sorted places (without scores)
        return [place for place, _ in scored_results]
