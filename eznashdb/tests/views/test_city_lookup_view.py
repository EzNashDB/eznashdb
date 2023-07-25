import pytest
import requests
from django.urls import reverse


@pytest.fixture()
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

        mocker.patch("requests.get", side_effect=side_effect)

    return _mock_osm


def test_returns_osm_response(client, mock_osm):
    osm_response = "osm response"
    mock_osm(osm_response)
    url = reverse("eznashdb:city_lookup")
    query_params = {"q": "city name"}
    response = client.get(url, data=query_params)

    assert response.status_code == 200
    assert response.json() == osm_response


def test_returns_error_on_500(client, mock_osm):
    osm_response = "ERROR"
    mock_osm(osm_response, 500)
    url = reverse("eznashdb:city_lookup")
    query_params = {"q": "city name"}
    response = client.get(url, data=query_params)

    assert response.status_code == 500
    assert "failed" in str(response.json()).lower()
