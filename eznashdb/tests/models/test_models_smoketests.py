from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.models import Room, Shul


def test_models_smoketest(django_user_model):
    # Create user
    user = django_user_model.objects.create()

    # Create shul
    shul = Shul.objects.create(
        created_by=user,
        updated_by=[user.id],
        name="Test shul",
        latitude=123.456,
        longitude=123.456,
    )

    # Create room
    Room.objects.create(
        created_by=user,
        shul=shul,
        name="Test Room",
        relative_size=RelativeSize.S,
        see_hear_score=SeeHearScore._5,
    )

    # Assert all created
    for model in [django_user_model, Shul, Room]:
        assert model.objects.count() == 1
