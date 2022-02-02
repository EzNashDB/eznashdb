from eznashdb.enums import KaddishAlone, RelativeSize, SeeHearScore
from eznashdb.models import Room, Shul, City, Region, Country
from eznashdb.serializers import ShulSerializer, CitySerializer


"""
Helpers
"""
def create_city() -> City:
    country = Country.objects.create()
    region = Region.objects.create(country=country)
    city = City.objects.create(region=region)
    return city

"""
Tests
"""
def test_converts_shul_to_dict(django_user_model):
    name = "test shul"
    has_female_leadership = True
    has_childcare = False
    has_kaddish_with_men = None
    enum_has_kaddish_alone = KaddishAlone.MAN_ALWAYS_SAYS_KADDISH
    username="test user"
    user_email="user@test.com"

    user1 = django_user_model.objects.create(username=username, email=user_email)
    user2 = django_user_model.objects.create(username="test user 2", email=user_email)
    city = create_city()
    shul = Shul.objects.create(
        city=city,
        created_by=user1,
        name=name,
        has_female_leadership=has_female_leadership,
        has_childcare=has_childcare,
        has_kaddish_with_men=has_kaddish_with_men,
        enum_has_kaddish_alone=enum_has_kaddish_alone,
        editted_by=[user1.id, user2.id]
    )
    serializer = ShulSerializer(shul, context={'request': None})
    city_data = CitySerializer(city).data
    data = serializer.data
    assert data["id"] == shul.id
    assert data["name"] == name
    assert data["created_by"]["username"] == username
    assert data["created_by"]["email"] == user_email
    assert data["city"] == city_data
    assert data["editted_by"][0]["username"] == user1.username
    assert data["editted_by"][1]["username"] == user2.username
    assert data["has_female_leadership"] == has_female_leadership
    assert data["has_childcare"] == has_childcare
    assert data["has_kaddish_with_men"] == has_kaddish_with_men
    assert data["enum_has_kaddish_alone"] == enum_has_kaddish_alone


def test_includes_room_data(django_user_model):
    user1 = django_user_model.objects.create()
    city = create_city()
    shul = Shul.objects.create(
        city=city,
        created_by=user1,
    )
    room = Room.objects.create(
        shul=shul,
        name="test room",
        relative_size=RelativeSize.SAME_SIZE,
        see_hear_score=SeeHearScore._3_AVERAGE,
        is_centered=True,
        is_same_floor_side=False,
        is_same_floor_back=True,
        is_same_floor_elevated=False,
        is_same_floor_level=True,
        is_balcony_side=False,
        is_balcony_back=True,
        is_only_men=False,
        is_mixed_seating=True,
        is_wheelchair_accessible=False,
    )
    serializer = ShulSerializer(shul, context={'request': None})
    data = serializer.data

    room_data = data["rooms"][0]
    assert room_data['id'] == room.id
    assert room_data['name'] == room.name
    assert room_data['relative_size'] == room.relative_size
    assert room_data['see_hear_score'] == room.see_hear_score
    assert room_data['is_centered'] == room.is_centered
    assert room_data['is_same_floor_side'] == room.is_same_floor_side
    assert room_data['is_same_floor_back'] == room.is_same_floor_back
    assert room_data['is_same_floor_elevated'] == room.is_same_floor_elevated
    assert room_data['is_same_floor_level'] == room.is_same_floor_level
    assert room_data['is_balcony_side'] == room.is_balcony_side
    assert room_data['is_balcony_back'] == room.is_balcony_back
    assert room_data['is_only_men'] == room.is_only_men
    assert room_data['is_mixed_seating'] == room.is_mixed_seating
    assert room_data['is_wheelchair_accessible'] == room.is_wheelchair_accessible
