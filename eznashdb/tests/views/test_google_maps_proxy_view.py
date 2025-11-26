import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_google_maps_redirect_uses_coordinates(client, test_shul):
    test_shul.latitude = 48.86837
    test_shul.longitude = 2.29348
    test_shul.save()

    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": test_shul.id})

    assert response.status_code == 302
    assert response.url.startswith("https://www.google.com/maps")
    assert "48.86837,2.29348" in response.url


@pytest.mark.django_db
def test_google_maps_redirect_rounds_coordinates(client, test_shul):
    test_shul.latitude = 40.913415282803335
    test_shul.longitude = -74.01149690151216
    test_shul.save()

    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": test_shul.id})

    assert response.status_code == 302
    # Check that coordinates are rounded to 5 decimal places
    assert "40.91342,-74.0115" in response.url


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
