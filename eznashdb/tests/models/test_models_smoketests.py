from eznashdb.models import Country, Region, City, Shul, Room
from eznashdb.enums import SeeHearScore, KaddishAlone, RelativeSize

def test_models_smoketest(django_user_model):
    # Create country, region, city
    country = Country.objects.create(
        name="United States",
        short_name="US"
    )
    region = Region.objects.create(
        country=country,
        name="New York",
    )
    city = City.objects.create(
        region=region,
        name="New York",
        latitude="40.7128",
        longitude="-74.0060"
    )

    # Create user
    user = django_user_model.objects.create()

    # Create shul (with city, user)
    shul = Shul.objects.create(
        city=city,
        created_by=user,
        editted_by=[user.id],
        name="Test shul",
        has_female_leadership=True,
        has_kaddish_with_men=True,
        enum_has_kaddish_alone=KaddishAlone.MAN_ALWAYS_SAYS_KADDISH,
        has_childcare=True,
    )

    # Create room
    room = Room.objects.create(
        shul=shul,
        name="Test Room",
        relative_size=RelativeSize.SOMEWHAT_SMALLER,
        see_hear_score=SeeHearScore._5_VERY_EASY,
        is_centered=True,
        is_same_floor_side=True,
        is_same_floor_back=True,
        is_same_floor_elevated=True,
        is_same_floor_level=True,
        is_balcony_side=True,
        is_balcony_back=True,
        is_only_men=True,
        is_mixed_seating=True,
        is_wheelchair_accessible=True,
    )

    # Assert all created
    for model in [django_user_model, Country, Region, City, Shul, Room]:
        assert model.objects.count() == 1

