import pytest
from bs4 import BeautifulSoup

from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.models import Shul
from eznashdb.views import ShulsFilterView


@pytest.fixture()
def GET_request(rf_GET):
    return rf_GET("eznashdb:shuls")


def test_shows_app_name(GET_request):
    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "Ezrat Nashim Database" in soup.get_text()


def test_shows_shul_name(GET_request, test_user):
    shul = Shul.objects.create(created_by=test_user, name="test shul")

    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert shul.name in soup.get_text()


@pytest.mark.parametrize(
    ("field_name", "field_value", "display_value"),
    [
        ("has_female_leadership", True, "fa-check"),
        ("has_female_leadership", False, "fa-times"),
        ("has_childcare", True, "fa-check"),
        ("has_childcare", False, "fa-times"),
        ("can_say_kaddish", True, "fa-check"),
        ("can_say_kaddish", False, "fa-times"),
    ],
)
def test_shows_shul_details(GET_request, test_user, field_name, field_value, display_value):
    Shul.objects.create(created_by=test_user, name="test shul", **{field_name: field_value})

    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert display_value in str(soup)


def test_shows_room_name(GET_request, test_user):
    shul = Shul.objects.create(created_by=test_user, name="test shul")
    room = shul.rooms.create(created_by=test_user, name="test_room")

    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert room.name in soup.get_text()


@pytest.mark.parametrize(
    ("field_name", "display_values"),
    [
        ("is_same_floor_side", ["same floor", "side"]),
        ("is_same_floor_back", ["same floor", "back"]),
        ("is_same_floor_elevated", ["same floor", "elevated"]),
        ("is_same_floor_level", ["same floor", "level"]),
        ("is_balcony", ["balcony"]),
        ("is_only_men", ["no", "only men"]),
        ("is_mixed_seating", ["no", "mixed seating"]),
    ],
)
def test_shows_boolean_room_layout_details(GET_request, test_user, field_name, display_values):
    shul = Shul.objects.create(created_by=test_user, name="test shul")
    shul.rooms.create(created_by=test_user, name="test_room", **{field_name: True})

    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    for value in display_values:
        assert value.lower() in str(soup).lower()


@pytest.mark.parametrize(("is_wheelchair_accessible", "expected"), [(True, "check"), (False, "times")])
def test_shows_wheelchair_data(GET_request, test_user, is_wheelchair_accessible, expected):
    shul = Shul.objects.create(created_by=test_user, name="test shul")
    shul.rooms.create(
        created_by=test_user,
        name="test_room",
        is_wheelchair_accessible=is_wheelchair_accessible,
    )

    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert expected in str(soup)


@pytest.mark.parametrize(("relative_size"), list(RelativeSize))
def test_shows_room_relative_size(GET_request, test_user, relative_size):
    shul = Shul.objects.create(created_by=test_user, name="test shul")
    shul.rooms.create(created_by=test_user, name="test_room", relative_size=relative_size)

    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert relative_size.value in str(soup)


def test_displays_dashes_for_unknown_relative_size(GET_request, test_user):
    shul = Shul.objects.create(created_by=test_user, name="test shul")
    shul.rooms.create(
        created_by=test_user,
        name="test_room",
        relative_size="",
        see_hear_score=SeeHearScore._3,
    )

    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "--" in soup.text


@pytest.mark.parametrize(("see_hear_score"), list(SeeHearScore))
def test_shows_room_see_hear_score(GET_request, test_user, see_hear_score):
    shul = Shul.objects.create(created_by=test_user, name="test shul")
    shul.rooms.create(created_by=test_user, name="test_room", see_hear_score=see_hear_score)

    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    expected_filled_star_count = int(see_hear_score.value)
    expected_empty_star_count = 5 - expected_filled_star_count

    filled_class = "fa-solid fa-star"
    empty_class = "fa-regular fa-star"

    assert str(soup).count(filled_class) == expected_filled_star_count
    assert str(soup).count(empty_class) == expected_empty_star_count


def test_shows_dashes_for_unknown_see_hear_score(GET_request, test_user):
    shul = Shul.objects.create(created_by=test_user, name="test shul")
    shul.rooms.create(
        created_by=test_user,
        name="test_room",
        see_hear_score="",
        relative_size=RelativeSize.M,
    )

    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "--" in soup.text


def test_shows_message_if_no_shuls(GET_request):
    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "No Shuls Found" in soup.get_text()


def describe_filter():
    def filters_by_name(rf_GET, test_user):
        Shul.objects.create(created_by=test_user, name="shul 1")
        Shul.objects.create(created_by=test_user, name="shul 2")
        request = rf_GET("eznashdb:shuls", {"name": "shul 2"})

        response = ShulsFilterView.as_view()(request)

        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        soup_text = soup.get_text().lower()
        assert "shul 2" in soup_text
        assert "shul 1" not in soup_text

    def filters_by_has_female_leadership(rf_GET, test_user):
        Shul.objects.create(created_by=test_user, name="shul 1", has_female_leadership=False)
        Shul.objects.create(created_by=test_user, name="shul 2", has_female_leadership=True)
        request = rf_GET("eznashdb:shuls", {"has_female_leadership": ["True"]})

        response = ShulsFilterView.as_view()(request)

        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        soup_text = soup.get_text().lower()
        assert "shul 2" in soup_text
        assert "shul 1" not in soup_text

    def filters_by_has_childcare(rf_GET, test_user):
        Shul.objects.create(created_by=test_user, name="shul 1", has_childcare=False)
        Shul.objects.create(created_by=test_user, name="shul 2", has_childcare=True)
        request = rf_GET("eznashdb:shuls", {"has_childcare": ["True"]})

        response = ShulsFilterView.as_view()(request)

        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        soup_text = soup.get_text().lower()
        assert "shul 2" in soup_text
        assert "shul 1" not in soup_text