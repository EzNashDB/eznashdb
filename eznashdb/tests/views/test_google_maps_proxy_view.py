import urllib
from decimal import Decimal

import pytest
from django.urls import reverse

from eznashdb.models import Shul


@pytest.mark.django_db
def test_redirects_to_google_maps(client):
    # Create a dummy shul
    shul = Shul.objects.create(
        name="Test Shul",
        latitude=Decimal("31.7767"),
        longitude=Decimal("35.2345"),
    )

    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": shul.id})

    # Check that the response is a redirect
    assert response.status_code == 302

    assert response.url.startswith("https://www.google.com/maps/search/")
    assert str(shul.latitude) in response.url
    assert str(shul.longitude) in response.url
    assert shul.name.replace(" ", "+") in response.url


@pytest.mark.django_db
def test_google_maps_redirect_invalid_id(client):
    # Use an ID that doesn't exist
    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": 999999})

    # Should return 404 or some error
    assert response.status_code == 404


@pytest.mark.django_db
def test_google_maps_redirect_missing_id(client):
    # Call the view without an id param
    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url)

    # Should return 400 or some error
    assert response.status_code == 400


@pytest.mark.django_db
def test_google_maps_redirect_name_encoding(client):
    # Shul with special characters
    shul = Shul.objects.create(
        name="בית כנסת",
        latitude=Decimal("31.7767"),
        longitude=Decimal("35.2345"),
    )

    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": shul.id})

    assert response.status_code == 302
    # URL should be properly URL-encoded
    assert urllib.parse.quote_plus(shul.name) in response.url
