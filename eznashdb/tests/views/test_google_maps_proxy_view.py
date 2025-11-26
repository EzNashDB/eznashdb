import urllib.parse

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_google_maps_redirect_uses_address_field_with_full_street_address(client, test_shul):
    test_shul.address = "Synagogue Ohel Abraham, Rue de Montévidéo, Paris 75116"
    test_shul.save()

    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": test_shul.id})

    assert response.status_code == 302
    assert response.url.startswith("https://www.google.com/maps")
    assert urllib.parse.quote_plus(test_shul.address) in response.url


@pytest.mark.django_db
def test_google_maps_redirect_uses_address_field_with_lat_lon_coords(client, test_shul):
    test_shul.address = "40.913415282803335,-74.01149690151216"
    test_shul.save()

    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": test_shul.id})
    assert response.status_code == 302
    assert response.url.startswith("https://www.google.com/maps")
    assert urllib.parse.quote_plus(test_shul.address) in response.url


@pytest.mark.django_db
def test_google_maps_redirect_invalid_id(client):
    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": 999999})
    assert response.status_code == 404


@pytest.mark.django_db
def test_google_maps_redirect_missing_id(client):
    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url)
    assert response.status_code == 400


@pytest.mark.django_db
def test_google_maps_redirect_unicode_address(client, test_shul):
    test_shul.address = "בית הכנסת הגדול, 56, המלך ג׳ורג׳, מחנה ישראל, ירושלים | القدس, נפת ירושלים, מחוז ירושלים, 9426222, ישראל"
    test_shul.save()

    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": test_shul.id})

    assert response.status_code == 302
    assert urllib.parse.quote_plus(test_shul.address) in response.url
