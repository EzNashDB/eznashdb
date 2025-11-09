import pytest
from bs4 import BeautifulSoup

from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.models import Shul
from eznashdb.views import ShulsFilterView


@pytest.fixture
def GET_request(rf_GET):
    return rf_GET("eznashdb:shuls", query_params={"format": "list"})


def test_shows_app_name(GET_request):
    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "Ezrat Nashim Database" in soup.get_text()

    def test_shows_shul_address(GET_request):
        Shul.objects.create(name="test shul", address="test address")

        response = ShulsFilterView.as_view()(GET_request)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert "test address" in str(soup)

    def test_shows_room_name(GET_request):
        shul = Shul.objects.create(name="test shul")
        room = shul.rooms.create(name="test_room")

        response = ShulsFilterView.as_view()(GET_request)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert room.name in soup.get_text()

    def describe_rooms():
        @pytest.mark.parametrize(("relative_size"), list(RelativeSize))
        def test_shows_room_relative_size(GET_request, relative_size):
            shul = Shul.objects.create(name="test shul")
            shul.rooms.create(name="test_room", relative_size=relative_size)

            response = ShulsFilterView.as_view()(GET_request)
            soup = BeautifulSoup(str(response.render().content), features="html.parser")

            assert relative_size.value in str(soup)

        def test_displays_dashes_for_unknown_relative_size(GET_request):
            shul = Shul.objects.create(name="test shul")
            shul.rooms.create(name="test_room", relative_size="", see_hear_score=SeeHearScore._3)

            response = ShulsFilterView.as_view()(GET_request)
            soup = BeautifulSoup(str(response.render().content), features="html.parser")

            assert "--" in soup.text

        @pytest.mark.parametrize(("see_hear_score"), list(SeeHearScore))
        def test_shows_room_see_hear_score(GET_request, see_hear_score):
            shul = Shul.objects.create(name="test shul")
            shul.rooms.create(name="test_room", see_hear_score=see_hear_score)

            response = ShulsFilterView.as_view()(GET_request)
            soup = BeautifulSoup(str(response.render().content), features="html.parser")

            expected_filled_star_count = int(see_hear_score.value)
            expected_empty_star_count = 5 - expected_filled_star_count

            filled_class = "fa-solid fa-star"
            empty_class = "fa-regular fa-star"

            assert str(soup).count(filled_class) == expected_filled_star_count
            assert str(soup).count(empty_class) == expected_empty_star_count

        def test_shows_dashes_for_unknown_see_hear_score(GET_request):
            shul = Shul.objects.create(name="test shul")
            shul.rooms.create(name="test_room", see_hear_score="", relative_size=RelativeSize.M)

            response = ShulsFilterView.as_view()(GET_request)
            soup = BeautifulSoup(str(response.render().content), features="html.parser")

            assert "--" in soup.text


def describe_filter():
    def filters_by_relative_size(rf_GET):
        Shul.objects.create(name="shul 1")
        Shul.objects.create(name="shul 2").rooms.create(relative_size=RelativeSize.M)
        request = rf_GET(
            "eznashdb:shuls", query_params={"rooms__relative_size": ["M"], "format": "list"}
        )

        response = ShulsFilterView.as_view()(request)

        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        assert "shul 2" in str(soup)
        assert "shul 1" not in str(soup)

    def filters_by_see_hear_score(rf_GET):
        Shul.objects.create(name="shul 1")
        Shul.objects.create(name="shul 2").rooms.create(see_hear_score=SeeHearScore._3)
        request = rf_GET(
            "eznashdb:shuls", query_params={"rooms__see_hear_score": ["3"], "format": "list"}
        )

        response = ShulsFilterView.as_view()(request)

        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        assert "shul 2" in str(soup)
        assert "shul 1" not in str(soup)
