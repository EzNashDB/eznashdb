from django.urls import reverse

from eznashdb.models import Room, Shul
from eznashdb.views import DeleteShulView


def test_deletes_shul(rf, test_user, test_shul):
    request = rf.post(reverse("eznashdb:delete_shul", kwargs={"pk": test_shul.pk}))
    request.user = test_user

    # Act
    DeleteShulView.as_view()(request, pk=test_shul.pk)

    # Assert
    assert Shul.objects.count() == 0


def test_deletes_rooms(rf, test_user, test_shul):
    Room.objects.create(shul=test_shul, name="room1")
    Room.objects.create(shul=test_shul, name="room2")
    request = rf.post(
        reverse("eznashdb:delete_shul", kwargs={"pk": test_shul.pk}),
        # form_data,
    )
    request.user = test_user

    # Act
    DeleteShulView.as_view()(request, pk=test_shul.pk)

    # Assert
    assert Room.objects.count() == 0
