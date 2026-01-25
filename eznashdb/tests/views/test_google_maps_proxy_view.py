import pytest
from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
def test_requires_login(client, test_shul):
    """Test that non-authenticated users are redirected to login"""
    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": test_shul.id})

    assert response.status_code == 302
    assert settings.LOGIN_URL in response.url


@pytest.mark.django_db
def test_google_maps_redirect_uses_coordinates(client, test_user, test_shul):
    client.force_login(test_user)
    test_shul.latitude = 48.86837
    test_shul.longitude = 2.29348
    test_shul.save()

    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": test_shul.id})

    assert response.status_code == 200
    assert "https://www.google.com/maps" in str(response.content)
    assert "48.86837,2.29348" in str(response.content)


@pytest.mark.django_db
def test_google_maps_redirect_rounds_coordinates(client, test_user, test_shul):
    client.force_login(test_user)
    test_shul.latitude = 40.913415282803335
    test_shul.longitude = -74.01149690151216
    test_shul.save()

    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": test_shul.id})

    assert response.status_code == 200
    # Check that coordinates are rounded to 5 decimal places
    assert "40.91342,-74.0115" in str(response.content)


@pytest.mark.django_db
def test_google_maps_redirect_includes_analytics(client, test_user, test_shul):
    """Test that GA tracking is included in response"""
    client.force_login(test_user)
    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": test_shul.id})

    assert response.status_code == 200
    assert "gtag" in str(response.content)
    assert "shul_map_redirect" in str(response.content)
    assert "shul_id" in str(response.content)


@pytest.mark.django_db
def test_google_maps_redirect_invalid_id(client, test_user):
    client.force_login(test_user)
    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url, data={"id": 999999})
    assert response.status_code == 404


@pytest.mark.django_db
def test_google_maps_redirect_missing_id(client, test_user):
    client.force_login(test_user)
    url = reverse("eznashdb:google_maps_proxy")
    response = client.get(url)
    assert response.status_code == 400
