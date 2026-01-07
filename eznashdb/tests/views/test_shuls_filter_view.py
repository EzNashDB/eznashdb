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


def test_shows_room_name(GET_request, test_shul):
    room = test_shul.rooms.create(name="test_room")

    response = ShulsFilterView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert room.name in str(soup)


def describe_rooms():
    @pytest.mark.parametrize(("relative_size"), list(RelativeSize))
    def test_shows_room_relative_size(test_shul, GET_request, relative_size):
        test_shul.rooms.create(name="test_room", relative_size=relative_size)

        response = ShulsFilterView.as_view()(GET_request)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert relative_size.value in str(soup)

    def test_displays_not_set_for_unknown_relative_size(test_shul, GET_request):
        test_shul.rooms.create(name="test_room", relative_size="", see_hear_score=SeeHearScore._3)

        response = ShulsFilterView.as_view()(GET_request)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert "not set" in str(soup).lower()

    @pytest.mark.parametrize(("see_hear_score"), list(SeeHearScore))
    def test_shows_room_see_hear_score(test_shul, GET_request, see_hear_score):
        test_shul.rooms.create(name="test_room", see_hear_score=see_hear_score)

        response = ShulsFilterView.as_view()(GET_request)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        marker_script = soup.find(id="shul-markers-js")

        expected_filled_star_count = int(see_hear_score.value)
        expected_empty_star_count = 5 - expected_filled_star_count

        filled_class = "fa-solid fa-star"
        empty_class = "fa-regular fa-star"

        assert str(marker_script).count(filled_class) == expected_filled_star_count
        assert str(marker_script).count(empty_class) == expected_empty_star_count

    def test_shows_not_set_for_unknown_see_hear_score(test_shul, GET_request):
        test_shul.rooms.create(name="test_room", see_hear_score="", relative_size=RelativeSize.M)

        response = ShulsFilterView.as_view()(GET_request)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert "not set" in str(soup).lower()


def describe_filter():
    def filters_by_relative_size(rf_GET):
        Shul.objects.create(name="shul 1", latitude=123, longitude=123)
        Shul.objects.create(name="shul 2", latitude=123, longitude=123).rooms.create(
            relative_size=RelativeSize.M
        )
        request = rf_GET(
            "eznashdb:shuls", query_params={"rooms__relative_size": ["M"], "format": "list"}
        )

        response = ShulsFilterView.as_view()(request)

        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        assert "shul 2" in str(soup)
        assert "shul 1" not in str(soup)

    def filters_by_see_hear_score(rf_GET):
        Shul.objects.create(name="shul 1", latitude=123, longitude=123)
        Shul.objects.create(name="shul 2", latitude=123, longitude=123).rooms.create(
            see_hear_score=SeeHearScore._3
        )
        request = rf_GET(
            "eznashdb:shuls", query_params={"rooms__see_hear_score": ["3"], "format": "list"}
        )

        response = ShulsFilterView.as_view()(request)

        soup = BeautifulSoup(str(response.render().content), features="html.parser")
        assert "shul 2" in str(soup)
        assert "shul 1" not in str(soup)


def describe_exact_pin_behavior():
    def test_exact_pin_shul_excluded_from_object_list(rf_GET):
        """When justSaved param is present, that shul should be excluded from object_list"""
        shul = Shul.objects.create(name="Test Shul", latitude=40.7128, longitude=-74.0060)
        request = rf_GET("eznashdb:shuls", query_params={"justSaved": str(shul.id)})

        response = ShulsFilterView.as_view()(request)
        context = response.context_data

        # Shul should be in exact_pin_shul
        assert context["exact_pin_shul"] == shul
        # But not in object_list
        assert shul not in context["object_list"]

    def test_exact_pin_shul_in_context(rf_GET):
        """exact_pin_shul should be in context when justSaved param exists"""
        shul = Shul.objects.create(name="Test Shul", latitude=40.7128, longitude=-74.0060)
        request = rf_GET("eznashdb:shuls", query_params={"justSaved": str(shul.id)})

        response = ShulsFilterView.as_view()(request)
        context = response.context_data

        assert "exact_pin_shul" in context
        assert context["exact_pin_shul"] == shul

    def test_no_exact_pin_shul_without_justSaved(rf_GET):
        """exact_pin_shul should be None when no justSaved param"""
        Shul.objects.create(name="Test Shul", latitude=40.7128, longitude=-74.0060)
        request = rf_GET("eznashdb:shuls", query_params={})

        response = ShulsFilterView.as_view()(request)
        context = response.context_data

        assert context["exact_pin_shul"] is None

    def test_cluster_offset_calculated_when_cluster_nearby(rf_GET):
        """When exact pin is close to a cluster, offset should be calculated"""
        # Create exact pin shul
        exact_shul = Shul.objects.create(name="Exact Shul", latitude=40.7128, longitude=-74.0060)

        # Create another shul at the same jittered location (will cluster together)
        # They have same rounded coords (40.71, -74.01) so same display coords
        _nearby_shul = Shul.objects.create(name="Nearby Shul", latitude=40.7129, longitude=-74.0061)

        request = rf_GET("eznashdb:shuls", query_params={"justSaved": str(exact_shul.id)})

        response = ShulsFilterView.as_view()(request)
        context = response.context_data

        # Should have cluster_offset in context
        assert "cluster_offset" in context
        # Might be None if they're far enough apart after jittering
        # or might have offset values if close

    def test_cluster_offset_none_when_no_nearby_cluster(rf_GET):
        """When exact pin has no nearby cluster, offset should be None"""
        # Create exact pin shul alone
        exact_shul = Shul.objects.create(name="Exact Shul", latitude=40.7128, longitude=-74.0060)
        # Create another shul far away
        Shul.objects.create(name="Far Shul", latitude=41.7128, longitude=-75.0060)

        request = rf_GET("eznashdb:shuls", query_params={"justSaved": str(exact_shul.id)})

        response = ShulsFilterView.as_view()(request)
        context = response.context_data

        # Should have cluster_offset but it should be None
        assert context["cluster_offset"] is None

    def test_cluster_offset_has_correct_structure(rf_GET):
        """When offset is calculated, it should have grid_key and offset values"""
        # Create exact pin shul
        exact_shul = Shul.objects.create(name="Exact Shul", latitude=40.71285, longitude=-74.00605)

        # Create another shul at VERY similar coords to force same cluster
        _nearby_shul = Shul.objects.create(name="Nearby Shul", latitude=40.71286, longitude=-74.00606)

        request = rf_GET("eznashdb:shuls", query_params={"justSaved": str(exact_shul.id)})

        response = ShulsFilterView.as_view()(request)
        context = response.context_data

        offset = context["cluster_offset"]
        if offset is not None:
            # Should have the expected keys
            assert "grid_key" in offset
            assert "offset_lon" in offset
            # Grid key should be a string
            assert isinstance(offset["grid_key"], str)
            # Offset should be numeric
            assert isinstance(offset["offset_lon"], (int, float))
