import urllib

import pytest
import requests
from django.urls import reverse

DUMMY_OSM_RECORD = {"name": "osm response", "place_id": 1}


@pytest.fixture
def mock_osm(mocker):
    def _mock_osm(response_data, status_code=200):
        original_get = requests.get

        def side_effect(*args, **kwargs):
            url = kwargs.get("url") or args[0]
            if "openstreetmap" in url:
                mock_response = mocker.Mock()
                mock_response.json.return_value = response_data
                mock_response.status_code = status_code
                return mock_response
            else:
                return original_get(*args, **kwargs)

        return mocker.patch("requests.get", side_effect=side_effect)

    return _mock_osm


def test_returns_osm_response(client, mock_osm):
    osm_response = [DUMMY_OSM_RECORD]
    mock_osm(osm_response)
    url = reverse("eznashdb:address_lookup")
    query_params = {"q": "city name"}
    response = client.get(url, data=query_params)

    assert response.status_code == 200
    assert response.json() == osm_response


def test_returns_error_on_500(client, mock_osm):
    osm_response = "ERROR"
    mock_osm(osm_response, 500)
    url = reverse("eznashdb:address_lookup")
    query_params = {"q": "city name"}
    response = client.get(url, data=query_params)

    assert response.status_code == 500
    assert "failed" in str(response.json()).lower()


def describe_israel_searches():
    @pytest.mark.parametrize(
        ("israel", "palestine"),
        [
            ("ישראל", "Palestinian Territory"),
            ("israel", "Palestinian Territory"),
            ("Israel", "Palestinian Territory"),
            ("il", "ps"),
            ("IL", "ps"),
        ],
    )
    @pytest.mark.parametrize(
        ("word_break"),
        [
            (" "),
            (", "),
        ],
    )
    @pytest.mark.parametrize(
        ("base_query"),
        [
            ("{israel}"),
            ("some city{word_break}{israel}"),
            ("{israel}{word_break}some city"),
            ("some city{word_break}{israel}{word_break}some address"),
        ],
    )
    def includes_palestine_in_israel_searches(
        client, mock_osm, base_query, israel, palestine, word_break
    ):
        query = base_query.format(israel=israel, word_break=word_break)
        osm_response = [DUMMY_OSM_RECORD]
        mocked_get = mock_osm(osm_response)
        url = reverse("eznashdb:address_lookup")
        query_params = {"q": query}
        response = client.get(url, data=query_params)

        assert len(mocked_get.call_args_list) == 2
        call_urls = [args[0][0] for args in mocked_get.call_args_list]
        assert urllib.parse.quote_plus(israel.lower()) in call_urls[0]
        assert urllib.parse.quote_plus(palestine.lower()) in call_urls[1]
        assert response.status_code == 200
        assert response.json() == osm_response * 2

    @pytest.mark.parametrize(
        ("display_name", "israel", "palestine"),
        [
            (
                "מעלה שומרון, קרני שומרון, שטח C, יהודה ושומרון, الأراضي الفلسطينية",
                "ישראל",
                "الأراضي الفلسطينية",
            ),
            (
                "Maale Shomron, Karney Shomron, Area C, Judea and Samaria, Palestinian Territory",
                "Israel",
                "Palestinian Territory",
            ),
        ],
    )
    def returns_israel_for_palestine(client, mock_osm, display_name, israel, palestine):
        DUMMY_OSM_RECORD = {
            "name": "osm response",
            "place_id": 1,
            "display_name": display_name,
        }

        osm_response = [DUMMY_OSM_RECORD]
        mock_osm(osm_response)
        url = reverse("eznashdb:address_lookup")
        query_params = {"q": "something"}
        response = client.get(url, data=query_params)

        response_record = response.json()[0]
        assert israel in response_record["display_name"]
        assert palestine not in response_record["display_name"]
