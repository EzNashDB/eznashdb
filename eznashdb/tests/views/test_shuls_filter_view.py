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
        @pytest.mark.parametrize(
            ("field_name", "display_values"),
            [
                ("is_same_height_side", ["same height", "side"]),
                ("is_same_height_back", ["same height", "back"]),
                ("is_elevated_side", ["elevated", "side"]),
                ("is_elevated_back", ["elevated", "back"]),
                ("is_balcony", ["balcony"]),
                ("is_only_men", ["no women's section"]),
                ("is_mixed_seating", ["mixed seating"]),
            ],
        )
        def test_shows_boolean_room_layout_details(GET_request, field_name, display_values):
            shul = Shul.objects.create(name="test shul")
            shul.rooms.create(name="test_room", **{field_name: True})

            response = ShulsFilterView.as_view()(GET_request)
            soup = BeautifulSoup(str(response.render().content), features="html.parser")

            cards = soup.find_all(attrs={"class": "accordion-item"})
            shul_card = [card for card in cards if shul.name in card.text][0]

            for value in display_values:
                assert value.lower() in str(shul_card.text).lower()

        def test_shows_dashes_if_all_boolean_layout_fields_are_False(GET_request):
            shul = Shul.objects.create(name="test shul")
            shul.rooms.create(name="test_room")

            response = ShulsFilterView.as_view()(GET_request)
            soup = BeautifulSoup(str(response.render().content), features="html.parser")

            assert "--" in str(soup).lower()

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
    def filters_by_name(rf_GET):
        Shul.objects.create(name="shul 1")
        Shul.objects.create(name="shul 2")
        request = rf_GET("eznashdb:shuls", query_params={"name": "shul 2", "format": "list"})

        response = ShulsFilterView.as_view()(request)

        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        assert "shul 2" in str(soup)
        assert "shul 1" not in str(soup)

    def filters_by_has_female_leadership(rf_GET):
        Shul.objects.create(name="shul 1", has_female_leadership=False)
        Shul.objects.create(name="shul 2", has_female_leadership=True)
        request = rf_GET(
            "eznashdb:shuls", query_params={"has_female_leadership": ["True"], "format": "list"}
        )

        response = ShulsFilterView.as_view()(request)

        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        assert "shul 2" in str(soup)
        assert "shul 1" not in str(soup)

    def filters_by_can_say_kaddish(rf_GET):
        Shul.objects.create(name="shul 1", can_say_kaddish=False)
        Shul.objects.create(name="shul 2", can_say_kaddish=True)
        request = rf_GET("eznashdb:shuls", query_params={"can_say_kaddish": ["True"], "format": "list"})

        response = ShulsFilterView.as_view()(request)

        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        assert "shul 2" in str(soup)
        assert "shul 1" not in str(soup)

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

    def filters_by_room_layout(rf_GET):
        Shul.objects.create(name="shul 1")
        Shul.objects.create(name="shul 2").rooms.create(is_same_height_side=True)
        request = rf_GET(
            "eznashdb:shuls", query_params={"rooms__layout": ["is_same_height_side"], "format": "list"}
        )

        response = ShulsFilterView.as_view()(request)

        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        assert "shul 2" in str(soup)
        assert "shul 1" not in str(soup)
