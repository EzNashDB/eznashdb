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
        has_female_leadership=True,
        can_say_kaddish=False,
    )

    # Create room
    Room.objects.create(
        created_by=user,
        shul=shul,
        name="Test Room",
        relative_size=RelativeSize.S,
        see_hear_score=SeeHearScore._5,
        is_same_height_side=True,
        is_same_height_back=True,
        is_elevated_side=True,
        is_elevated_back=True,
        is_balcony=True,
        is_only_men=True,
        is_mixed_seating=True,
        is_wheelchair_accessible=True,
    )

    # Assert all created
    for model in [django_user_model, Shul, Room]:
        assert model.objects.count() == 1
