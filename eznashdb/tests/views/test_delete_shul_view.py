from django.urls import reverse

from eznashdb.models import Room, Shul
from eznashdb.views import DeleteShulView


def test_deletes_shul(rf, test_user):
    shul = Shul.objects.create(created_by=test_user, name="test shul")
    request = rf.post(reverse("eznashdb:delete_shul", kwargs={"pk": shul.pk}))
    request.user = test_user

    # Act
    DeleteShulView.as_view()(request, pk=shul.pk)

    # Assert
    assert Shul.objects.count() == 0


def test_deletes_rooms(rf, test_user):
    shul = Shul.objects.create(created_by=test_user, name="test shul")
    Room.objects.create(created_by=test_user, shul=shul, name="room1")
    Room.objects.create(created_by=test_user, shul=shul, name="room2")
    request = rf.post(
        reverse("eznashdb:delete_shul", kwargs={"pk": shul.pk}),
        # form_data,
    )
    request.user = test_user

    # Act
    DeleteShulView.as_view()(request, pk=shul.pk)

    # Assert
    assert Room.objects.count() == 0
