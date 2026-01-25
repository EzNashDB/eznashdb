import pytest
from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
def test_undelete_restores_soft_deleted_shul(client, test_user, test_shul):
    """Test that posting to undelete view restores a soft-deleted shul"""
    client.force_login(test_user)

    # Soft delete the shul
    test_shul.deleted_by = test_user
    test_shul.deletion_reason = "Test deletion"
    test_shul.save()
    test_shul.delete()

    # Verify it's deleted
    assert test_shul.deleted is not None
    assert test_shul.deleted_by == test_user
    assert test_shul.deletion_reason == "Test deletion"

    # Call the undelete view
    url = reverse("eznashdb:undelete_shul", kwargs={"pk": test_shul.pk})
    response = client.post(url)

    # Verify redirect to browse page
    assert response.status_code == 302
    assert response.url == reverse("eznashdb:shuls")

    # Refresh shul from database
    test_shul.refresh_from_db()

    # Verify shul is restored
    assert test_shul.deleted is None
    assert test_shul.deleted_by is None
    assert test_shul.deletion_reason == ""


@pytest.mark.django_db
def test_undelete_requires_login(client, test_shul):
    """Test that non-authenticated users are redirected to login"""
    url = reverse("eznashdb:undelete_shul", kwargs={"pk": test_shul.pk})
    response = client.post(url)

    assert response.status_code == 302
    assert settings.LOGIN_URL in response.url


@pytest.mark.django_db
def test_undelete_nonexistent_shul_returns_404(client, test_user):
    """Test that attempting to undelete non-existent shul returns 404"""
    client.force_login(test_user)
    url = reverse("eznashdb:undelete_shul", kwargs={"pk": 999999})
    response = client.post(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_undelete_already_active_shul_shows_info_message(client, test_user, test_shul):
    """Test that attempting to undelete an active (non-deleted) shul shows info message"""
    client.force_login(test_user)

    # Ensure shul is not deleted
    assert test_shul.deleted is None

    # Try to undelete
    url = reverse("eznashdb:undelete_shul", kwargs={"pk": test_shul.pk})
    response = client.post(url, follow=True)

    # Verify redirect and message
    assert response.status_code == 200
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "info"
    assert "is not deleted" in messages[0].message
